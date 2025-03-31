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

# Función para leer datos desde Google Sheets
def leer_stock():
    """Lee los datos de stock desde Google Sheets y los devuelve como un DataFrame."""
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()
    values = result.get("values", [])
    
    if not values:
        return pd.DataFrame(columns=["Sitio", "Parte", "Stock Fisico"])

    df = pd.DataFrame(values[1:], columns=values[0])  # Asigna nombres de columnas desde la primera fila
    df["Stock Fisico"] = pd.to_numeric(df["Stock Fisico"], errors='coerce').fillna(0)  # Convertir a número
    return df

# Función para actualizar stock en Google Sheets
def actualizar_stock(df):
    """Envía los datos actualizados a Google Sheets."""
    valores = df.values.tolist()
    body = {"values": [df.columns.tolist()] + valores}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="StockFijo!A:E",
        valueInputOption="RAW",
        body=body
    ).execute()

# Función para modificar el stock
def modificar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()

    # Filtrar por sitio y parte
    mask = (df['Sitio'] == sitio) & (df['Parte'] == parte)

    if not df[mask].empty:
        try:
            df.loc[mask, 'Stock Fisico'] = pd.to_numeric(df.loc[mask, 'Stock Fisico'], errors='coerce').fillna(0)
        except Exception as e:
            st.error(f"❌ Error convirtiendo stock a número: {e}")
            return

        if operacion == "sumar":
            df.loc[mask, 'Stock Fisico'] += cantidad
        elif operacion == "restar":
            df.loc[mask, 'Stock Fisico'] = max(0, df.loc[mask, 'Stock Fisico'] - cantidad)

    else:
        if operacion == "sumar":
            nuevo_registro = pd.DataFrame([[sitio, parte, cantidad]], columns=['Sitio', 'Parte', 'Stock Fisico'])
            df = pd.concat([df, nuevo_registro], ignore_index=True)

    # Actualizar en Google Sheets
    actualizar_stock(df)

# **Interfaz en Streamlit**
st.title("Gestión de Stock Fijo")

df_stock = leer_stock()
sitios = df_stock["Sitio"].unique().tolist()
partes = df_stock["Parte"].unique().tolist()

# **Formulario para modificar stock**
st.subheader("Actualizar Stock")
sitio = st.selectbox("🏢 Sitio:", sitios + ["Otro..."])
parte = st.selectbox("🔢 Número de Parte:", partes + ["Otro..."])
cantidad = st.number_input("📦 Cantidad:", min_value=1, step=1)
operacion = st.radio("🔄 Operación:", ["sumar", "restar"])

# Ingreso manual si el sitio o parte no existen en la lista
if sitio == "Otro...":
    sitio = st.text_input("Ingresa el nuevo sitio:")
if parte == "Otro...":
    parte = st.text_input("Ingresa el nuevo número de parte:")

# **Botón para actualizar stock**
if st.button("Actualizar Stock"):
    if sitio and parte and cantidad > 0:
        modificar_stock(sitio, parte, cantidad, operacion)
        st.success(f"✅ Stock actualizado para {sitio} - {parte}")
        st.experimental_rerun()  # Recargar datos automáticamente
    else:
        st.error("⚠️ Completa todos los campos correctamente.")

# **Botón para refrescar datos manualmente**
if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()

