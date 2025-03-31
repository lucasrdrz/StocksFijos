import streamlit as st
import pandas as pd
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configurar credenciales y servicio de Google Sheets
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
sheet = service.spreadsheets()
SPREADSHEET_ID = '1uC3qyYAmThXMfJ9Pwkompbf9Zs6MWhuTqT8jTVLYdr0'

# Función para leer datos desde Google Sheets
def leer_stock():
    """Lee los datos de stock desde Google Sheets y los devuelve como un DataFrame."""
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:C').execute()
        values = result.get("values", [])
        if not values:
            return pd.DataFrame(columns=["Sitio", "Parte", "Stock Fisico"])
        df = pd.DataFrame(values[1:], columns=values[0])
        df["Stock Fisico"] = pd.to_numeric(df["Stock Fisico"], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"❌ Error al leer datos de Google Sheets: {e}")
        return pd.DataFrame(columns=["Sitio", "Parte", "Stock Fisico"])

# Función para actualizar stock en Google Sheets
def actualizar_stock(df):
    """Envía los datos actualizados a Google Sheets."""
    try:
        valores = df.values.tolist()
        body = {"values": [df.columns.tolist()] + valores}
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="StockFijo!A:C",
            valueInputOption="RAW",
            body=body
        ).execute()
    except Exception as e:
        st.error(f"❌ Error al actualizar Google Sheets: {e}")

# Función para modificar el stock
def modificar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()

    # Filtrar por sitio y parte
    mask = (df['Sitio'] == sitio) & (df['Parte'] == parte)

    if not df[mask].empty:
        df.loc[mask, 'Stock Fisico'] = pd.to_numeric(df.loc[mask, 'Stock Fisico'], errors='coerce').fillna(0)
        if operacion == "sumar":
            df.loc[mask, 'Stock Fisico'] += cantidad
        elif operacion == "restar":
            df.loc[mask, 'Stock Fisico'] -= cantidad
            df.loc[mask, 'Stock Fisico'] = df.loc[mask, 'Stock Fisico'].clip(lower=0)  # Evitar negativos
    else:
        if operacion == "sumar":
            nuevo_registro = pd.DataFrame([[sitio, parte, cantidad]], columns=['Sitio', 'Parte', 'Stock Fisico'])
            df = pd.concat([df, nuevo_registro], ignore_index=True)

    # Actualizar en Google Sheets
    actualizar_stock(df)

# **Interfaz en Streamlit**
st.title("📊 Gestión de Stock Fijo")

df_stock = leer_stock()
sitios = df_stock["Sitio"].unique().tolist()
partes = df_stock["Parte"].unique().tolist()

# **Formulario para modificar stock**
st.subheader("🔄 Actualizar Stock")
sitio = st.selectbox("🏢 Sitio:", sitios + ["Otro..."])
parte = st.selectbox("🔢 Número de Parte:", partes + ["Otro..."])
cantidad = st.number_input("📦 Cantidad:", min_value=1, step=1)
operacion = st.radio("🔄 Operación:", ["sumar", "restar"])

# Ingreso manual si el sitio o parte no existen en la lista
if sitio == "Otro...":
    sitio = st.text_input("✏️ Ingresa el nuevo sitio:")
if parte == "Otro...":
    parte = st.text_input("✏️ Ingresa el nuevo número de parte:")

# **Botón para actualizar stock**
if st.button("✅ Actualizar Stock"):
    if sitio and parte and cantidad > 0:
        modificar_stock(sitio, parte, cantidad, operacion)
        st.success(f"✅ Stock actualizado para {sitio} - {parte}")
    else:
        st.error("⚠️ Completa todos los campos correctamente.")

# **Botón para refrescar datos manualmente**
if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()
