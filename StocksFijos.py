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
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range="StockFijo!A1:Z").execute()

    values = result.get('values', [])
    headers = values[0]

    df = pd.DataFrame(values[1:], columns=headers)

    # Normalizar nombres (por si tienen espacios raros)
    df.columns = df.columns.str.strip()

    # Seleccionar por NOMBRE, no por posición
    df = df.rename(columns={
        'Sitio': 'Sitio',
        'Parte': 'Parte',
        'Stock Físico': 'Stock Físico',
        'Stock Óptimo': 'Stock Óptimo'
    })

    df = df[['Sitio', 'Parte', 'Stock Físico', 'Stock Óptimo']]

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
    fila_encontrada = None
    for i, row in enumerate(values[1:], start=2):  # Empezamos en 2 para omitir el encabezado
        if len(row) < 2:  # si la fila está incompleta, la ignoramos
            continue
        if row[0] == sitio and row[1] == parte:
            stock_fisico = row[3] if len(row) > 3 else "0"  # Columna D (índice 3)
            fila_encontrada = i
            break

    if fila_encontrada is None:
        st.error("❌ Parte no encontrada en el sitio seleccionado.")
        return

    try:
        # Convertir el stock actual a número, si no es válido se usa 0
        stock_fisico = float(stock_fisico) if str(stock_fisico).replace('.', '', 1).isdigit() else 0
    except ValueError:
        stock_fisico = 0

    # Realizar la operación (sumar o restar)
    if operacion == "sumar":
        nuevo_stock = stock_fisico + cantidad
    elif operacion == "restar":
        nuevo_stock = stock_fisico - cantidad
    else:
        st.error("Operación no válida. Solo se puede sumar o restar.")
        return

    # Asegurarse de que el valor es un número entero o flotante
    nuevo_stock = int(nuevo_stock) if float(nuevo_stock).is_integer() else nuevo_stock

    # Actualizar el stock en Google Sheets en la columna correcta (D)
    range_update = f"StockFijo!D{fila_encontrada}"  
    body = {'values': [[nuevo_stock]]}

    try:
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_update,
            valueInputOption='RAW',
            body=body
        ).execute()
        st.success(f"✅ Stock actualizado correctamente para {parte} en {sitio}. Nuevo stock: {nuevo_stock}")
    except Exception as e:
        st.error(f"❌ Error al actualizar stock: {e}")
        
# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")
st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer stock
df_stock = leer_stock()

# Desplegable para elegir el sitio
sitio_seleccionado = st.selectbox("Selecciona un sitio", df_stock['Sitio'].unique())

# Mostrar datos del sitio seleccionado
df_sitio = df_stock[df_stock['Sitio'] == sitio_seleccionado]
st.write(df_sitio)

# Seleccionar la parte
parte_seleccionada = st.selectbox("Selecciona una parte", df_sitio['Parte'])

# Ingresar la cantidad para sumar o restar
cantidad = st.number_input("Cantidad a sumar/restar", min_value=1)

# Seleccionar operación (sumar o restar)
operacion = st.radio("Selecciona una operación", ("sumar", "restar"))

# Botón para actualizar stock
if st.button("Actualizar stock"):
    actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)




