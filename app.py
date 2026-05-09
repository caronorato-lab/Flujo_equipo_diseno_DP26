import streamlit as st
import pandas as pd

# Configuración de la página (para que ocupe toda la pantalla y tenga un emoji de métricas)
st.set_page_config(page_title="Sistema de Gestión DP 2026", page_icon="📊", layout="wide")

# --- DISEÑO MINIMALISTA Y COLORES DEFENSORÍA ---
st.markdown("""
    <style>
    /* Color Institucional Azul Defensoría: #003876 */
    h1, h2, h3, h4 {
        color: #003876 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stButton>button {
        background-color: #003876;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #002244;
        color: white;
    }
    .stAlert {
        background-color: #f4f8fc;
        border-left: 5px solid #003876;
        color: #333333;
    }
    .css-1d391kg, .css-1n76uvr {
        /* Estilos generales para inputs y selectores */
        border-radius: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Logo de la Defensoría del Pueblo (URL pública oficial de Wikipedia)
st.image("logo_defensoria.png", width=300)


# Caché de Streamlit: La clave del éxito. 
# Esto evita que el servidor explote recargando el Excel cada vez que das un clic.
@st.cache_data
def cargar_datos(archivo_excel):
    try:
        # sheet_name=None obliga a Pandas a leer TODAS las pestañas automáticamente.
        diccionario_hojas = pd.read_excel(archivo_excel, sheet_name=None)
        
        lista_dfs = []
        
        # Iteramos sobre cada pestaña (sin importar cuántas nuevas agreguen a futuro)
        for nombre_pestaña, df_temp in diccionario_hojas.items():
            # Inyectamos el mes basado en el nombre de la pestaña
            df_temp.insert(0, 'Mes', nombre_pestaña)
            lista_dfs.append(df_temp)
                
        # Unimos todas las tablas en una sola
        df_completo = pd.concat(lista_dfs, ignore_index=True)
        
        # Limpiamos los nombres de las columnas de espacios en blanco ocultos
        df_completo.columns = df_completo.columns.str.strip()
        
        # Llenamos vacíos
        df_completo.fillna("NO REGISTRA", inplace=True)
        
        return df_completo
        
    except Exception as e:
        # Si algo sale mal, se lo informamos al usuario
        st.error(f"Error al procesar el archivo Excel. Detalles técnicos: {e}")
        st.stop() # Detiene la ejecución de la app aquí mismo


# --- INTERFAZ DE USUARIO ---

st.title("Flujo de trabajo equipo de diseño DP 2026")
st.markdown("Plataforma unificada para el seguimiento de solicitudes de diseño gráfico.")

# Mensaje para subir el archivo
st.info("📌 **Nota:** Por favor, carga el archivo de Excel unificado para iniciar la consulta.")

# Widget para subir el archivo
archivo_subido = st.file_uploader("Carga el archivo Excel aquí (.xlsx)", type=["xlsx"])

# Si no hay archivo, detenemos el proceso suavemente
if archivo_subido is None:
    st.stop()  # Esto detiene todo. No renderiza nada más abajo hasta que suban algo.


# --- ZONA DE PROCESAMIENTO (Solo si el archivo fue subido) ---

# Mostramos un spinner mientras lee todo
with st.spinner("Procesando datos y consolidando pestañas..."):
    df = cargar_datos(archivo_subido)

st.success("✅ Archivo cargado y procesado exitosamente.")

st.markdown("---")
st.header("Filtros de Búsqueda")

# Creamos columnas para el menú
col1, col2 = st.columns([1, 2])

with col1:
    # Selector principal con términos formales
    opcion_busqueda = st.selectbox(
        "¿Qué parámetro deseas consultar?",
        options=[
            "Solicitud (Qué pidieron)", 
            "Solicitante (Quién solicitó)", 
            "Diseñador (Quién lo realizó)"
        ]
    )

# Mapeamos la opción visual a la columna real del DataFrame
mapa_columnas = {
    "Solicitud (Qué pidieron)": "solicitud",
    "Solicitante (Quién solicitó)": "solicitante",
    "Diseñador (Quién lo realizó)": "diseñador"
}
columna_real = mapa_columnas[opcion_busqueda]


with col2:
    # Lógica inteligente: Text Input para Solicitudes, Selectbox para Nombres
    if opcion_busqueda == "Solicitud (Qué pidieron)":
        termino_busqueda = st.text_input(f"Escribe tu término de búsqueda para '{columna_real}':")
    else:
        # Obtenemos los nombres únicos de la columna (Solicitante o Diseñador)
        nombres_unicos = df[columna_real].dropna().unique().tolist()
        # Limpiamos los datos: quitamos vacíos, convertimos a texto y quitamos espacios en los extremos
        nombres_unicos = [str(n).strip() for n in nombres_unicos if str(n).strip() not in ["", "NO REGISTRA", "nan"]]
        # Eliminamos duplicados y ordenamos alfabéticamente
        nombres_unicos = sorted(list(set(nombres_unicos)))
        # Añadimos una opción en blanco al inicio para que no filtre por defecto al primer nombre
        nombres_unicos.insert(0, "") 
        
        termino_busqueda = st.selectbox(f"Selecciona el nombre del {columna_real}:", options=nombres_unicos)


# Si el usuario seleccionó o escribió algo, filtramos
if termino_busqueda:
    
    if opcion_busqueda == "Solicitud (Qué pidieron)":
        # Búsqueda por texto parcial (ej: si busca "logo", le sale "logo campaña" o "diseño logo")
        resultados = df[df[columna_real].astype(str).str.contains(termino_busqueda, case=False, na=False)]
    else:
        # Búsqueda exacta por nombre desde la lista desplegable
        resultados = df[df[columna_real].astype(str).str.strip() == termino_busqueda]
    
    if resultados.empty:
        st.warning(f"No se encontraron registros para '{termino_busqueda}' en la categoría seleccionada.")
    else:
        # Definimos qué columnas se van a mostrar en la tabla final
        columnas_a_mostrar = [
            'Mes', 
            'solicitud', 
            'solicitante', 
            'diseñador', 
            'fecha recepción solicitud', 
            'fecha solicitada de entrega', 
            'fecha entrega final'
        ]
        
        # Nos aseguramos de que las columnas existan en el excel cargado para no generar errores
        columnas_disponibles = [col for col in columnas_a_mostrar if col in df.columns]
        df_final = resultados[columnas_disponibles]
        
        st.markdown(f"### 🎯 Resultados Encontrados ({len(df_final)} registros)")
        
        # Renderizamos la tabla (st.dataframe permite scroll y ordenar por columnas)
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
        # Botón para descargar el resultado de la búsqueda como CSV
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar reporte (CSV)",
            data=csv,
            file_name=f"reporte_{termino_busqueda}.csv",
            mime="text/csv",
        )
