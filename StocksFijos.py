import streamlit as st
import gspread
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Configurar las credenciales y el servicio de la API de Google Sheets
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
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='StockFijo!A:E').execute()  # Cambiar a A:E para incluir la descripción
    values = result.get('values', [])

    if not values:
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])

    # Convertimos la primera fila en encabezados, eliminando espacios extra
    headers = [h.strip().lower() for h in values[0]]  
    df = pd.DataFrame(values[1:], columns=headers)

    # Renombramos las columnas asegurando que coincidan
    column_map = {
        'sitio': 'Sitio', 
        'parte': 'Parte', 
        'descripcion': 'Descripción', 
        'stock': 'Stock Físico', 
        'stock deberia': 'Stock Óptimo'
    }
    df.rename(columns=column_map, inplace=True)

    # Convertimos las columnas numéricas correctamente
    df['Stock Físico'] = pd.to_numeric(df['Stock Físico'], errors='coerce').fillna(0)
    df['Stock Óptimo'] = pd.to_numeric(df['Stock Óptimo'], errors='coerce').fillna(0)

    return df

# **Función para actualizar stock en Google Sheets**
def actualizar_stock(df):
    sheet = service.spreadsheets()
    data = [df.columns.tolist()] + df.values.tolist()  
    body = {'values': data}
    
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='StockFijo!A:E',  # Actualizar el rango a A:E para incluir la columna "Descripción"
        valueInputOption='RAW',
        body=body
    ).execute()

# **Interfaz en Streamlit**
st.title("📦 Control de Stock Fijo - Logística")

st.subheader("📍 Selecciona un sitio para ver su stock:")

# Leer el stock una vez para evitar múltiples llamadas a la API
df_stock = leer_stock()

# Obtener los sitios únicos
sitios_unicos = sorted(df_stock['Sitio'].unique())

# Crear expanders por cada sitio
for sitio in sitios_unicos:
    with st.expander(f"📌 {sitio}", expanded=False):
        df_filtrado = df_stock[df_stock['Sitio'] == sitio]
        # Configurar "Stock Óptimo" como solo lectura
        st.data_editor(
            df_filtrado, 
            height=300, 
            use_container_width=True, 
            column_config={"Stock Óptimo": st.column_config.NumberColumn(disabled=True)}
        )

# **Formulario para modificar stock**
st.subheader("Actualizar Stock")
sitio = st.text_input("🏢 Sitio:")
parte = st.text_input("🔢 Número de Parte:")
cantidad = st.number_input("📦 Cantidad:", min_value=1, step=1)
operacion = st.radio("🔄 Operación:", ["sumar", "restar"])

# **Función para modificar stock**
def modificar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()

    # Filtrar por sitio y parte
    mask = (df['Sitio'] == sitio) & (df['Parte'] == parte)

    if not df[mask].empty:
        if operacion == "sumar":
            df.loc[mask, 'Stock Físico'] += cantidad
        elif operacion == "restar":
            df.loc[mask, 'Stock Físico'] -= cantidad
            df.loc[mask, 'Stock Físico'] = df['Stock Físico'].clip(lower=0)  # Evitar valores negativos
    else:
        if operacion == "sumar":
            nuevo_registro = pd.DataFrame([[sitio, parte, '', cantidad, 0]], columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])
            df = pd.concat([df, nuevo_registro], ignore_index=True)

    # **Llamar a la función que actualiza Google Sheets**
    actualizar_stock(df)

# **Botón para actualizar stock**
if st.button("Actualizar"):
    if sitio and parte and cantidad > 0:
        modificar_stock(sitio, parte, cantidad, operacion)
        st.success(f"✅ Stock actualizado para {sitio} - {parte}")
        st.experimental_rerun()  # Recargar datos automáticamente
    else:
        st.error("⚠️ Completa todos los campos correctamente.")

# **Botón para refrescar datos manualmente**
if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()

