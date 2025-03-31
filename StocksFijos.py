import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Configurar credenciales
@st.cache_resource
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
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])
    
    df = pd.DataFrame(values[1:], columns=values[0])
    
    # Convertir a numérico
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)
    
    return df

# Actualizar stock en Google Sheets
def actualizar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()
    fila = df[(df['Sitio'] == sitio) & (df['Parte'] == parte)].index
    
    if not fila.empty:
        fila = fila[0] + 2  # Ajustar índice para Google Sheets
        stock_actual = df.at[fila - 2, 'Stock Físico']
        nuevo_stock = stock_actual + cantidad if operacion == 'sumar' else stock_actual - cantidad
        
        sheet = service.spreadsheets()
        range_update = f'StockFijo!D{fila}'
        body = {'values': [[nuevo_stock]]}
        
        try:
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, 
                range=range_update, 
                valueInputOption='RAW', 
                body=body
            ).execute()
            st.success(f"Stock actualizado: {stock_actual} → {nuevo_stock}")
        except Exception as e:
            st.error(f"Error al actualizar stock: {e}")
    else:
        st.error("No se encontró la parte en el sitio seleccionado.")

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")

df_stock = leer_stock()

if not df_stock.empty:
    sitio_seleccionado = st.selectbox("Selecciona un sitio:", df_stock['Sitio'].unique())
    df_filtrado = df_stock[df_stock['Sitio'] == sitio_seleccionado]
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    parte_seleccionada = st.selectbox("Selecciona una parte:", df_filtrado['Parte'].unique())
    cantidad = st.number_input("Cantidad a modificar:", min_value=1, step=1)
    operacion = st.radio("Operación:", ['sumar', 'restar'])
    
    if st.button("Actualizar Stock"):
        actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)
else:
    st.error("⚠️ No se pudo cargar el stock.")
