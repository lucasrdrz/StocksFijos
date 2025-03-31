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
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:D').execute()
    values = result.get('values', [])

    if not values:
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Stock Físico', 'Stock Óptimo'])

    # Ver nombres de columnas originales
    headers_original = values[0]
    print("Encabezados originales:", headers_original)

    # Convertir encabezados a minúsculas y eliminar espacios
    headers = [h.strip().lower() for h in values[0]]
    print("Encabezados normalizados:", headers)

    df = pd.DataFrame(values[1:], columns=headers)

    # Mapeo de nombres de columnas
    column_map = {
        'sitio': 'Sitio',
        'parte': 'Parte',
        'stock físico': 'Stock Físico',
        'stock óptimo': 'Stock Óptimo'
    }

    # Renombrar columnas según el mapeo
    df.rename(columns=column_map, inplace=True)
    print("Columnas después del renombrado:", df.columns.tolist())

    # Verificar que "Stock Físico" y "Stock Óptimo" existan
    if 'Stock Físico' not in df.columns:
        st.error("❌ La columna 'Stock Físico' no se encontró en los datos.")
        return pd.DataFrame()

    if 'Stock Óptimo' not in df.columns:
        st.error("❌ La columna 'Stock Óptimo' no se encontró en los datos.")
        return pd.DataFrame()

    # Convertir a numérico las columnas necesarias
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)

    return df

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer stock
df_stock = leer_stock()

# Mostrar tablas por sitio
if not df_stock.empty:
    sitios_unicos = sorted(df_stock['Sitio'].unique())
    for sitio in sitios_unicos:
        with st.expander(f"📌 {sitio}", expanded=False):
            df_filtrado = df_stock[df_stock['Sitio'] == sitio].copy()
            df_filtrado.reset_index(drop=True, inplace=True)
            st.dataframe(df_filtrado, use_container_width=True)
else:
    st.error("⚠️ No se pudo cargar el stock. Verifica los nombres de las columnas en Google Sheets.")
