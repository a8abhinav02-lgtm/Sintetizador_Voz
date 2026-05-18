import os
import streamlit as st
import numpy as np
from supertonic import TTS
import pypdf

# Configuración de la interfaz gráfica local
st.set_page_config(page_title="Lector de Novelas Supertonic", page_icon="📖", layout="centered")

st.title("📖 Lector de Novelas y Audiolibros")
st.write("Convierte tus textos en audiolibros dramatizados cambiando de voz automáticamente en los diálogos.")

# Inicializar el motor TTS con caché
@st.cache_resource
def inicializar_motor():
    return TTS()

with st.spinner("Cargando el motor de Supertonic..."):
    engine = inicializar_motor()

# --- BARRA LATERAL: CONFIGURACIÓN MULTI-VOZ ---
st.sidebar.header("⚙️ Configuración del Elenco")

# 1. Selección de Idioma
diccionario_idiomas = {
    "Español": "es", 
    "Inglés": "en", 
    "Francés": "fr", 
    "Alemán": "de", 
    "Italiano": "it", 
    "Portugués": "pt"
}
idioma_seleccionado = st.sidebar.selectbox("Idioma del texto:", list(diccionario_idiomas.keys()))
codigo_idioma = diccionario_idiomas[idioma_seleccionado]

# Catálogo de voces amigables
diccionario_voces = {
    "Voz Masculina Grave (M2)": "M2",
    "Voz Femenina Joven (F2)": "F2",
    "Voz Masculina Estándar (M1)": "M1",
    "Voz Femenina Estándar (F1)": "F1",
    "Voz Masculina Enérgica (M3)": "M3",
    "Voz Femenina Madura (F3)": "F3",
}

# 2. Asignación de Roles
voz_narrador = st.sidebar.selectbox("🎙️ Voz del Narrador (Historias/Descripciones):", list(diccionario_voces.keys()), index=0)
voz_personaje = st.sidebar.selectbox("💬 Voz del Personaje (Diálogos/Guiones):", list(diccionario_voces.keys()), index=1)

codigo_narrador = diccionario_voces[voz_narrador]
codigo_personaje = diccionario_voces[voz_personaje]

# 3. Control de Velocidad
velocidad = st.sidebar.slider("Velocidad de Lectura:", min_value=0.7, max_value=1.5, value=1.05, step=0.05)


# --- CUERPO PRINCIPAL: COMPONENTE ARRASTRAR Y SOLTAR ---
st.subheader("1. Carga tu capítulo o fragmento")
archivo_subido = st.file_uploader("Suelte su archivo .txt o .pdf aquí", type=["txt", "pdf"])

if archivo_subido is not None:
    st.success(f"📦 Documento '{archivo_subido.name}' cargado.")
    contenido_texto = ""

    try:
        # Extracción de texto según el formato cargado
        if archivo_subido.name.endswith(".txt"):
            contenido_texto = archivo_subido.read().decode("utf-8", errors="ignore")
        elif archivo_subido.name.endswith(".pdf"):
            lector_pdf = pypdf.PdfReader(archivo_subido)
            contenido_texto = "\n".join([p.extract_text() for p in lector_pdf.pages if p.extract_text()])

        if not contenido_texto.strip():
            st.warning("⚠️ No se detectó texto procesable en el archivo.")
        else:
            with st.expander("📄 Ver fragmento del texto extraído"):
                st.text_area("Texto detectado:", contenido_texto[:2000] + "\n...", height=150, disabled=True)
            
            # Botón de ejecución principal
            st.subheader("2. Generar Audiolibro")
            if st.button("🎭 Comenzar Lectura Dramatizada", type="primary"):
                
                # Preparamos los estilos de voz nativos
                estilo_narrador = engine.get_voice_style(codigo_narrador)
                estilo_personaje = engine.get_voice_style(codigo_personaje)
                
                # Separamos el texto por líneas limpiando espacios vacíos
                lineas = [l.strip() for l in contenido_texto.split('\n') if l.strip()]
                
                audios_generados = []
                progreso = st.progress(0)
                status_text = st.empty()
                
                # Procesamos fragmento por fragmento
                for idx, linea in enumerate(lineas):
                    # Actualizar barra de progreso visual
                    porcentaje = int((idx + 1) / len(lineas) * 100)
                    progreso.progress(porcentaje)
                    status_text.text(f"Procesando fragmento {idx + 1} de {len(lineas)}...")
                    
                    # Detección de Diálogos (Guiones largos, cortos, comillas inglesas o latinas)
                    es_dialogo = linea.startswith('—') or linea.startswith('-') or linea.startswith('"') or linea.startswith('«')
                    estilo_actual = estilo_personaje if es_dialogo else estilo_narrador
                    
                    # Sintetizar la línea actual en memoria
                    resultado = engine.synthesize(
                        text=linea,
                        voice_style=estilo_actual,
                        lang=codigo_idioma,
                        speed=velocidad
                    )
                    
                    # Extraer el arreglo de audio (NumPy array) de la tupla
                    wav_chunk = resultado[0] if isinstance(resultado, tuple) else resultado
                    audios_generados.append(wav_chunk)
                
                status_text.text("💾 Uniendo fragmentos y estructurando archivo continuo...")
                
                if audios_generados:
                    # Corrección de Dimensiones: Aplastamos las matrices 2D a arreglos planos 1D
                    audios_planos = [chunk.flatten() for chunk in audios_generados]
                    
                    # Concatenamos de forma segura a lo largo del eje del tiempo
                    audio_final = np.concatenate(audios_planos)
                    
                    # Generar automáticamente la ruta de salida en la carpeta del proyecto
                    nombre_base, _ = os.path.splitext(archivo_subido.name)
                    ruta_audio_salida = f"{nombre_base}_dramatizado.wav"
                    
                    # Guardar el archivo final utilizando el método nativo del motor
                    engine.save_audio(wav=audio_final, output_path=ruta_audio_salida)
                    
                    # Limpieza visual de estado y despliegue del reproductor
                    status_text.empty()
                    st.success("🎉 ¡Audiolibro dramatizado generado con éxito!")
                    st.info(f"💾 Guardado de forma local como: `{ruta_audio_salida}`")
                    st.audio(ruta_audio_salida, format="audio/wav")
                        
    except Exception as e:
        st.error(f"Error en la producción del audiolibro: {e}")