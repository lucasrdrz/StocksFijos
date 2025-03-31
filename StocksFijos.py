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

# **Actualizar stock en Google Sheets**
def actualizar_stock(sitio, parte, cantidad, operacion):
    sheet = service.spreadsheets()

    # Obtener el rango de celdas donde está el stock físico
    rango = f"StockFijo!A:E"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=rango).execute()
    values = result.get('values', [])

    # Buscar la parte específica en el sitio seleccionado
    for i, row in enumerate(values[1:], start=2):  # Empezamos en 2 para omitir el encabezado
        if row[0] == sitio and row[1] == parte:
            stock_fisico = row[2]  # La columna 'Stock Físico' es la 3ra (índice 2)
            break
    else:
        st.error("Parte no encontrada en el sitio seleccionado.")
        return

    try:
        # Asegurarse de que el stock_fisico sea un número válido
        stock_fisico = float(stock_fisico) if stock_fisico else 0  # Si está vacío, se asigna 0
    except ValueError as e:
        st.error(f"Error al convertir el stock a número: {e}")
        return

    # Realizar la operación (sumar o restar)
    if operacion == "sumar":
        nuevo_stock = stock_fisico + cantidad
    elif operacion == "restar":
        nuevo_stock = stock_fisico - cantidad
    else:
        st.error("Operación no válida. Solo se puede sumar o restar.")
        return

    # Asegurarse de que el valor es un número entero o flotante
    nuevo_stock = int(nuevo_stock) if nuevo_stock.is_integer() else nuevo_stock

    # Actualizar el stock en Google Sheets
    range_update = f"StockFijo!C{i}"  # Columna 'Stock Físico' en la fila correspondiente
    body = {
        'values': [[nuevo_stock]]
    }

    try:
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_update,
            valueInputOption='RAW',
            body=body
        ).execute()
        st.success(f"Stock actualizado correctamente para {parte} en {sitio}. Nuevo stock: {nuevo_stock}")
    except Exception as e:
        st.error(f"Error al actualizar stock: {e}")

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer stock
df_stock = leer_stock()

# Desplegable para elegir el sitio
sitio_seleccionado = st.selectbox("Selecciona un sitio", df_stock['Sitio
