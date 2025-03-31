import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# **Configurar credenciales**
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

# **Leer stock desde Google Sheets**
def leer_stock():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:C').execute()
    values = result.get('values', [])

    if not values:
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Stock Físico'])

    df = pd.DataFrame(values[1:], columns=['Sitio', 'Parte', 'Stock Físico'])
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0).astype(int)
    return df

# **Actualizar stock en Google Sheets**
def actualizar_stock(sitio, parte, cantidad, operacion):
    sheet = service.spreadsheets()
    df_stock = leer_stock()
    fila_index = df_stock[(df_stock["Sitio"] == sitio) & (df_stock["Parte"] == parte)].index

    if fila_index.empty:
        st.error("⚠️ No se encontró la parte en el stock.")
        return

    fila = fila_index[0] + 2  # +2 porque los índices en Sheets empiezan en 1 y hay encabezados
    stock_actual = df_stock.loc[fila_index[0], "Stock Físico"]
    cantidad_nueva = stock_actual + cantidad if operacion == "sumar" else stock_actual - cantidad
    cantidad_nueva = max(0, int(cantidad_nueva))

    body = {"values": [[cantidad_nueva]]}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'StockFijo!C{fila}',  # Asegurar que actualiza la columna correcta
        valueInputOption="RAW",
        body=body
    ).execute()

    st.success(f"✅ Stock actualizado: {stock_actual} → {cantidad_nueva}")

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
df_stock = leer_stock()

if not df_stock.empty:
    sitio_seleccionado = st.selectbox("🏢 Selecciona un sitio:", sorted(df_stock["Sitio"].unique()))
    df_filtrado = df_stock[df_stock["Sitio"] == sitio_seleccionado]
    
    st.subheader(f"📍 Stock en {sitio_seleccionado}")
    st.dataframe(df_filtrado, use_container_width=True)
    
    parte_seleccionada = st.selectbox("🔧 Selecciona una parte:", sorted(df_filtrado["Parte"].unique()))
    stock_actual = df_filtrado[df_filtrado["Parte"] == parte_seleccionada]["Stock Físico"].values[0]
    
    st.write(f"📊 **Stock Actual:** {stock_actual}")
    operacion = st.radio("➕➖ Operación:", ["sumar", "restar"], horizontal=True)
    cantidad = st.number_input("📌 Cantidad:", min_value=1, step=1)

    if st.button("Actualizar Stock"):
        actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)
else:
    st.error("⚠️ No se pudo cargar el stock. Verifica los nombres de las columnas en Google Sheets.")
