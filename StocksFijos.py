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
        return pd.DataFrame(columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])

    # Convertir la primera fila en encabezados normalizados
    headers = [h.strip().lower() for h in values[0]]  
    df = pd.DataFrame(values[1:], columns=headers)

    # Mapeo correcto de nombres de columnas
    column_map = {
        'sitio': 'Sitio', 
        'parte': 'Parte', 
        'descripcion': 'Descripción', 
        'stock': 'Stock Físico', 
        'stock deberia': 'Stock Óptimo'
    }

    # Asegurar que las columnas esperadas existan
    df.rename(columns={col: column_map[col] for col in df.columns if col in column_map}, inplace=True)

    # Convertir columnas numéricas
    for col in ['Stock Físico', 'Stock Óptimo']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            st.error(f"❌ La columna '{col}' no se encontró en los datos.")

    return df

# **Función para actualizar stock en Google Sheets**
def actualizar_stock(df):
    sheet = service.spreadsheets()
    data = [df.columns.tolist()] + df.astype(str).values.tolist()  
    body = {'values': data}
    
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='StockFijo!A:E',
        valueInputOption='RAW',
        body=body
    ).execute()

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

# **Formulario para modificar stock**
st.subheader("📊 Actualizar Stock")
sitio = st.text_input("🏢 Sitio:")
parte = st.text_input("🔢 Número de Parte:")
cantidad = st.number_input("📦 Cantidad:", min_value=1, step=1)
operacion = st.radio("🔄 Operación:", ["sumar", "restar"])

# **Función para modificar stock**
def modificar_stock(sitio, parte, cantidad, operacion):
    df = leer_stock()

    if 'Stock Físico' not in df.columns:
        st.error("⚠️ La columna 'Stock Físico' no se encuentra en los datos.")
        return

    # Filtrar por sitio y parte
    mask = (df['Sitio'] == sitio) & (df['Parte'] == parte)

    if df[mask].empty:
        if operacion == "sumar":
            nuevo_registro = pd.DataFrame([[sitio, parte, '', cantidad, 0]], 
                                          columns=['Sitio', 'Parte', 'Descripción', 'Stock Físico', 'Stock Óptimo'])
            df = pd.concat([df, nuevo_registro], ignore_index=True)
    else:
        if operacion == "sumar":
            df.loc[mask, 'Stock Físico'] += cantidad
        elif operacion == "restar":
            df.loc[mask, 'Stock Físico'] -= cantidad
            df.loc[mask, 'Stock Físico'] = df['Stock Físico'].clip(lower=0)  # Evitar negativos

    # **Actualizar Google Sheets**
    actualizar_stock(df)

# **Botón para actualizar stock**
if st.button("✅ Actualizar Stock"):
    if sitio and parte and cantidad > 0:
        modificar_stock(sitio, parte, cantidad, operacion)
        st.success(f"✅ Stock actualizado para {sitio} - {parte}")
        st.experimental_rerun()
    else:
        st.error("⚠️ Completa todos los campos correctamente.")

# **Botón para refrescar datos manualmente**
if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()

