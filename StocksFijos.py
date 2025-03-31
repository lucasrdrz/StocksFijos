import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Configurar credenciales
def load_credentials():
    try:
        SERVICE_ACCOUNT_INFO = st.secrets["GCP_KEY_JSON"]
        info = json.loads(SERVICE_ACCOUNT_INFO)
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        st.error(f"Error al configurar las credenciales: {e}")
        st.stop()

service = load_credentials()
SPREADSHEET_ID = '1uC3qyYAmThXMfJ9Pwkompbf9Zs6MWhuTqT8jTVLYdr0'

# Leer stock desde Google Sheets
def leer_stock():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()
    values = result.get('values', [])

    if not values:
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Stock Físico', 'Stock Óptimo'])

    headers = [h.strip().lower() for h in values[0]]
    df = pd.DataFrame(values[1:], columns=headers)

    column_map = {
        'sitio': 'Sitio',
        'parte': 'Parte',
        'stock físico': 'Stock Físico',
        'stock óptimo': 'Stock Óptimo'
    }
    df.rename(columns=column_map, inplace=True)

    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)

    return df

# Actualizar stock en Google Sheets
def actualizar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()
    sheet = service.spreadsheets()
    
    if df.empty:
        st.error("No se pudo cargar el stock.")
        return
    
    # Buscar la fila correspondiente
    mask = (df['Sitio'] == sitio) & (df['Parte'] == parte)
    if not mask.any():
        st.error("El sitio y parte seleccionados no existen en la base de datos.")
        return

    index = df[mask].index[0]
    stock_actual = df.at[index, 'Stock Físico']
    nuevo_stock = stock_actual + cantidad if operacion == 'sumar' else stock_actual - cantidad
    nuevo_stock = max(0, nuevo_stock)  # Evitar números negativos

    # Actualizar en Google Sheets
    cell_range = f"C{index + 2}"
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'StockFijo!{cell_range}',
        valueInputOption='RAW',
        body={'values': [[nuevo_stock]]}
    ).execute()
    
    st.success(f"Stock actualizado: {stock_actual} -> {nuevo_stock}")

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
st.subheader("📍 Selecciona un sitio para ver su stock:")

df_stock = leer_stock()

if not df_stock.empty:
    sitios_unicos = sorted(df_stock['Sitio'].unique())
    sitio_seleccionado = st.selectbox("Selecciona un sitio", sitios_unicos)
    df_filtrado = df_stock[df_stock['Sitio'] == sitio_seleccionado]
    st.dataframe(df_filtrado, use_container_width=True)

    partes_unicas = sorted(df_filtrado['Parte'].unique())
    parte_seleccionada = st.selectbox("Selecciona una parte", partes_unicas)
    cantidad = st.number_input("Cantidad a modificar", min_value=1, value=1)
    operacion = st.radio("Operación", ['sumar', 'restar'])
    
    if st.button("Actualizar Stock"):
        actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)
else:
    st.error("⚠️ No se pudo cargar el stock. Verifica los nombres de las columnas en Google Sheets.")

