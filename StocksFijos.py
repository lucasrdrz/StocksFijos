import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# ================== CREDENCIALES ==================

def load_credentials():
    SERVICE_ACCOUNT_INFO = st.secrets["GCP_KEY_JSON"]
    info = json.loads(SERVICE_ACCOUNT_INFO)
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('sheets', 'v4', credentials=credentials)

service = load_credentials()
sheet = service.spreadsheets()

SPREADSHEET_ID = '1uC3qyYAmThXMfJ9Pwkompbf9Zs6MWhuTqT8jTVLYdr0'


# ================== LEER STOCK ==================

def leer_stock():
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="StockFijo!A1:Z"
    ).execute()

    values = result.get('values', [])

    headers = [h.strip() for h in values[0]]
    max_cols = len(headers)

    # 🔴 NORMALIZAR TODAS LAS FILAS AL MISMO LARGO
    filas_normalizadas = []
    for row in values[1:]:
        if len(row) < max_cols:
            row = row + [""] * (max_cols - len(row))
        elif len(row) > max_cols:
            row = row[:max_cols]
        filas_normalizadas.append(row)

    df = pd.DataFrame(filas_normalizadas, columns=headers)

    # Nos quedamos solo con las que importan
    df = df[['Sitio', 'Parte', 'Stock Físico', 'Stock Óptimo']]

    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)

    return df


# ================== ACTUALIZAR STOCK ==================

def actualizar_stock(sitio, parte, cantidad, operacion):
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="StockFijo!A1:Z"
    ).execute()

    values = result.get('values', [])
    headers = [h.strip() for h in values[0]]

    col_sitio = headers.index('Sitio')
    col_parte = headers.index('Parte')
    col_stock_fisico = headers.index('Stock Físico')

    fila_encontrada = None

    for i, row in enumerate(values[1:], start=2):
        if len(row) <= max(col_sitio, col_parte):
            continue

        if row[col_sitio] == sitio and row[col_parte] == parte:
            stock_actual = row[col_stock_fisico] if len(row) > col_stock_fisico else "0"
            fila_encontrada = i
            break

    if fila_encontrada is None:
        st.error("❌ Parte no encontrada en el sitio seleccionado.")
        return

    stock_actual = float(stock_actual) if str(stock_actual).replace('.', '', 1).isdigit() else 0

    if operacion == "sumar":
        nuevo_stock = stock_actual + cantidad
    else:
        nuevo_stock = stock_actual - cantidad

    nuevo_stock = int(nuevo_stock) if nuevo_stock.is_integer() else nuevo_stock

    # Convertimos número de columna a letra (para armar el rango)
    letra_columna = chr(65 + col_stock_fisico)

    range_update = f"StockFijo!{letra_columna}{fila_encontrada}"

    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_update,
        valueInputOption='RAW',
        body={'values': [[nuevo_stock]]}
    ).execute()

    st.success(f"✅ Stock actualizado. Nuevo stock: {nuevo_stock}")


# ================== INTERFAZ STREAMLIT ==================

st.title("📦 Control de Stock Fijo - Logística")

df_stock = leer_stock()

sitio_seleccionado = st.selectbox(
    "Selecciona un sitio",
    sorted(df_stock['Sitio'].unique())
)

df_sitio = df_stock[df_stock['Sitio'] == sitio_seleccionado]
st.dataframe(df_sitio, use_container_width=True)

parte_seleccionada = st.selectbox(
    "Selecciona una parte",
    df_sitio['Parte']
)

cantidad = st.number_input("Cantidad a sumar/restar", min_value=1)

operacion = st.radio("Operación", ("sumar", "restar"))

if st.button("Actualizar stock"):
    actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)







