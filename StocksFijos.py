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
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Stock Físico', 'Stock Óptimo'])
    
    df = pd.DataFrame(values[1:], columns=values[0])
    df.rename(columns={
        'Sitio': 'Sitio',
        'Parte': 'Parte',
        'Stock Físico': 'Stock Físico',
        'Stock Óptimo': 'Stock Óptimo'
    }, inplace=True)
    
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)
    return df

# Actualizar stock en Google Sheets
def actualizar_stock(sitio, parte, cantidad, operacion):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()
    values = result.get('values', [])
    
    if not values:
        st.error("No se encontraron datos en la hoja de cálculo.")
        return
    
    for i, row in enumerate(values[1:], start=2):  # Empezamos en 2 para omitir el encabezado
        if row[0] == sitio and row[1] == parte:
            try:
                stock_fisico = float(row[2])  # Convertir stock físico a número
            except ValueError:
                st.error(f"Error: El valor de stock físico para {parte} en {sitio} no es un número válido.")
                return
            
            nuevo_stock = stock_fisico + cantidad if operacion == 'sumar' else stock_fisico - cantidad
            nuevo_stock = max(0, nuevo_stock)  # Evitar valores negativos
            
            range_update = f"StockFijo!C{i}"
            body = {'values': [[nuevo_stock]]}
            
            try:
                sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_update, valueInputOption='RAW', body=body).execute()
                st.success(f"Stock actualizado: {parte} en {sitio} ahora tiene {nuevo_stock} unidades.")
            except Exception as e:
                st.error(f"Error al actualizar stock: {e}")
            return
    
    st.error("Parte no encontrada en el sitio seleccionado.")

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer stock
df_stock = leer_stock()

# Seleccionar sitio
sitios_unicos = sorted(df_stock['Sitio'].unique())
sitio_seleccionado = st.selectbox("Selecciona un sitio", sitios_unicos)

# Filtrar datos por sitio
df_filtrado = df_stock[df_stock['Sitio'] == sitio_seleccionado].copy()
st.dataframe(df_filtrado, use_container_width=True)

# Seleccionar parte y cantidad
parte_seleccionada = st.selectbox("Selecciona una parte", df_filtrado['Parte'].unique())
cantidad = st.number_input("Cantidad a modificar", min_value=1, step=1)
operacion = st.radio("Operación", ('sumar', 'restar'))

# Botón para actualizar stock
if st.button("Actualizar Stock"):
    actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)
