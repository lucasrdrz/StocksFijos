import streamlit as st
import pandas as pd

# **Leer Stock desde Google Sheets**
def leer_stock():
    # Aquí va el código que lee desde Google Sheets y devuelve un DataFrame
    # Simulación de datos de ejemplo
    data = {
        "Sitio": ["JUJUY", "SALTA"],
        "Parte": ["1750349661", "123456789"],
        "Stock": [50, 30]
    }
    return pd.DataFrame(data)

# **Actualizar Stock en Google Sheets**
def actualizar_stock(df):
    # Aquí va el código para actualizar Google Sheets con df
    pass  # Reemplaza con tu código

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
        # Asegurar que 'Stock' sea un número
        try:
            df.loc[mask, 'Stock'] = pd.to_numeric(df.loc[mask, 'Stock'], errors='coerce').fillna(0)
        except Exception as e:
            st.error(f"❌ Error convirtiendo el stock a número: {e}")
            return
        
        # Aplicar la operación
        if operacion == "sumar":
            df.loc[mask, 'Stock'] += cantidad
        elif operacion == "restar":
            df.loc[mask, 'Stock'] -= cantidad
            df.loc[mask, 'Stock'] = df['Stock'].clip(lower=0)  # Evitar valores negativos

    else:
        # Si la parte no existe, agregarla con el stock ingresado
        if operacion == "sumar":
            nuevo_registro = pd.DataFrame([[sitio, parte, cantidad]], columns=['Sitio', 'Parte', 'Stock'])
            df = pd.concat([df, nuevo_registro], ignore_index=True)

    # **Actualizar Google Sheets**
    actualizar_stock(df)

# **Botón para actualizar stock**
if st.button("Actualizar"):
    if sitio and parte and cantidad > 0:
        modificar_stock(sitio, parte, cantidad, operacion)
        st.success(f"✅ Stock actualizado para {sitio} - {parte}")
        st.experimental_rerun()
    else:
        st.error("⚠️ Completa todos los campos correctamente.")

# **Botón para refrescar datos manualmente**
if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()

