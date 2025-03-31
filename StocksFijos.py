import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configurar credenciales y acceso a Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "credenciales.json"  # Ruta a tus credenciales
SPREADSHEET_ID = "TU_SPREADSHEET_ID"

# Autenticación con Google Sheets
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

def leer_stock():
    """Lee los datos de stock desde Google Sheets y los devuelve como un DataFrame."""
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()
    values = result.get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])  # Asigna nombres de columnas desde la primera fila
    df["Stock Fisico"] = pd.to_numeric(df["Stock Fisico"], errors='coerce')  # Convierte a número
    return df

def actualizar_stock(sitio, parte, cantidad, operacion):
    """Actualiza el stock de una parte en un sitio específico."""
    df = leer_stock()
    filtro = (df['Sitio'] == sitio) & (df['Parte'] == parte)
    
    if not df[filtro].empty:
        stock_fisico = df.loc[filtro, 'Stock Fisico'].values[0]
        
        if pd.isna(stock_fisico):  # Verifica si es un valor inválido
            st.error(f"Error: El valor de stock físico para {parte} en {sitio} no es un número válido.")
            return
        
        nuevo_stock = stock_fisico + cantidad if operacion == "sumar" else stock_fisico - cantidad
        df.loc[filtro, 'Stock Fisico'] = nuevo_stock
        
        # Enviar la actualización a Google Sheets
        range_update = f"StockFijo!C{df.index[filtro][0] + 2}"
        body = {"values": [[nuevo_stock]]}
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_update, valueInputOption='RAW', body=body).execute()
        st.success(f"Stock actualizado: {parte} en {sitio} ahora tiene {nuevo_stock} unidades.")
    else:
        st.error(f"Error: No se encontró la parte {parte} en {sitio}.")

# Interfaz en Streamlit
st.title("Gestión de Stock Fijo")
df_stock = leer_stock()

sitios = df_stock["Sitio"].unique()
partes = df_stock["Parte"].unique()

sitio_seleccionado = st.selectbox("Selecciona un sitio:", sitios)
parte_seleccionada = st.selectbox("Selecciona una parte:", partes)
cantidad = st.number_input("Cantidad a sumar/restar:", min_value=1, step=1)
operacion = st.radio("Operación:", ["sumar", "restar"])

if st.button("Actualizar Stock"):
    actualizar_stock(sitio_seleccionado, parte_seleccionada, cantidad, operacion)
