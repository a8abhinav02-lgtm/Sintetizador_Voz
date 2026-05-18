import os
import streamlit as st
from supertonic import TTS

# Configuración de la página web local
st.set_page_config(page_title="Sintetizador Supertonic", page_icon="🎙️", layout="centered")

st.title("🎙️ Mi Sintetizador de Voz Local")
st.write("Convierte tus archivos de texto en audio de alta fidelidad sin usar internet.")

# Inicializar el motor TTS (usamos cache para que cargue rápido y no se reinicie en cada clic)
@st.cache_resource
def inicializar_motor():
    return TTS()

with st.spinner("Cargando el motor de Supertonic..."):
    engine = inicializar_motor()

# --- BARRA LATERAL: CONFIGURACIÓN DE VOZ ---
st.sidebar.header("⚙️ Configuración de Audio")

# 1. Selección de Idioma
diccionario_idiomas = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt",
    "Japonés": "ja"
}
idioma_seleccionado = st.sidebar.selectbox("Selecciona el Idioma:", list(diccionario_idiomas.keys()))
codigo_idioma = diccionario_idiomas[idioma_seleccionado]

# 2. Selección de Voces con Nombres Amigables
diccionario_voces = {
    "Voz Femenina Estándar (F1)": "F1",
    "Voz Femenina Joven (F2)": "F2",
    "Voz Femenina Madura (F3)": "F3",
    "Voz Femenina Estilo 4 (F4)": "F4",
    "Voz Femenina Estilo 5 (F5)": "F5",
    "Voz Masculina Estándar (M1)": "M1",
    "Voz Masculina Grave (M2)": "M2",
    "Voz Masculina Enérgica (M3)": "M3",
    "Voz Masculina Estilo 4 (M4)": "M4",
    "Voz Masculina Estilo 5 (M5)": "M5",
}
voz_seleccionada = st.sidebar.selectbox("Selecciona el Estilo de Voz:", list(diccionario_voces.keys()))
codigo_voz = diccionario_voces[voz_seleccionada]

# 3. Control de Velocidad
velocidad = st.sidebar.slider("Velocidad de Lectura:", min_value=0.7, max_value=1.5, value=1.05, step=0.05)


# --- CUERPO PRINCIPAL: SELECCIÓN DE ARCHIVO ---
st.subheader("1. Ubicación del archivo de texto")

# Entrada de texto para la ruta del archivo
ruta_archivo = st.text_input(
    "Pega aquí la ruta completa de tu archivo .txt:",
    placeholder="Ejemplo: C:\\Usuarios\\angel\\Documentos\\mi_texto.txt"
)

# Limpiar comillas si el usuario copia la ruta con ellas
if ruta_archivo:
    ruta_archivo = ruta_archivo.strip('"').strip("'")

if ruta_archivo:
    if os.path.exists(ruta_archivo) and ruta_archivo.endswith('.txt'):
        st.success("✅ Archivo encontrado correctamente.")
        
        # Leer y mostrar una previsualización del texto
        try:
            with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                contenido_texto = f.read()
            
            with st.expander("📄 Ver contenido del texto a procesar"):
                st.text_area("Contenido:", contenido_texto, height=150, disabled=True)
            
            # Botón para procesar
            st.subheader("2. Procesar")
            if st.button("🚀 Convertir Texto a Voz", type="primary"):
                with st.spinner("Sintetizando audio localmente... Por favor espera."):
                    
                    # Obtener el estilo y sintetizar
                    estilo = engine.get_voice_style(codigo_voz)
                    resultado = engine.synthesize(
                        text=contenido_texto,
                        voice_style=estilo,
                        lang=codigo_idioma,
                        speed=velocidad
                    )
                    
                    # Generar automáticamente la ruta de salida (.wav) en la misma carpeta
                    ruta_base, _ = os.path.splitext(ruta_archivo)
                    ruta_audio_salida = f"{ruta_base}.wav"
                    
                    # Guardar el audio
                    wav_data = resultado[0] if isinstance(resultado, tuple) else resultado
                    engine.save_audio(wav=wav_data, output_path=ruta_audio_salida)
                    
                    if os.path.exists(ruta_audio_salida):
                        st.success("🎉 ¡Audio generado con éxito de forma automática!")
                        st.info(f"💾 Guardado en: `{ruta_audio_salida}`")
                        
                        # Reproductor de audio integrado en la interfaz web
                        st.audio(ruta_audio_salida, format="audio/wav")
                        
        except Exception as e:
            st.error(f"Error al leer o procesar el archivo: {e}")
    else:
        st.error("❌ La ruta no es válida o el archivo no es un formato .txt. Verifica la ubicación.")