import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Configurar credenciales y servicio de la API de Google Sheets
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

# Función para leer el stock desde Google Sheets
def leer_stock():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()
    values = result.get('values', [])

    if not values:
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])

    # Convertimos la primera fila en encabezados
    headers = [h.strip().lower() for h in values[0]]
    df = pd.DataFrame(values[1:], columns=headers)

    # Mostrar nombres de columnas originales para depuración
    print("Columnas originales:", df.columns.tolist())

    # Mapeo de nombres de columnas
    column_map = {
        'sitio': 'Sitio',
        'parte': 'Parte',
        'descripcion': 'Descripción',
        'stock': 'Stock Físico',
        'stock deberia': 'Stock Óptimo'
    }

    # Renombramos solo las columnas que existen en el DataFrame
    df.rename(columns={col: column_map[col] for col in df.columns if col in column_map}, inplace=True)

    # Mostrar nombres de columnas después del renombrado
    print("Columnas después del renombrado:", df.columns.tolist())

    # Verificar que las columnas necesarias existen
    required_columns = ['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Faltan las siguientes columnas en Google Sheets: {', '.join(missing_columns)}")
        return pd.DataFrame()

    # Convertir a numérico las columnas necesarias
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)

    return df

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")

st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer el stock una vez para evitar múltiples llamadas a la API
df_stock = leer_stock()

if not df_stock.empty:
    # Obtener los sitios únicos
    sitios_unicos = sorted(df_stock['Sitio'].unique())

    # Crear expanders por cada sitio con la vista de datos
    for sitio in sitios_unicos:
        with st.expander(f"📌 {sitio}", expanded=False):
            df_filtrado = df_stock[df_stock['Sitio'] == sitio]
            st.dataframe(df_filtrado, use_container_width=True)
else:
    st.error("No se pudo cargar el stock. Verifica los nombres de las columnas en Google Sheets.")
