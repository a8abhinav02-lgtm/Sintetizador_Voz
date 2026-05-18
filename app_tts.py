import os
import streamlit as st
import numpy as np
from supertonic import TTS
import pypdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
import warnings

# Desactivar advertencias molestas de terceras librerías en la consola
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configuración de la interfaz gráfica local
st.set_page_config(page_title="Lector de Novelas Supertonic", page_icon="📖", layout="centered")

st.title("⚡ Lector de Novelas con Inferencia por Lotes")
st.write("Convierte tus libros a voz a alta velocidad aprovechando el procesamiento optimizado de tu procesador.")

# Inicializar el motor TTS con caché
@st.cache_resource
def inicializar_motor():
    return TTS()

with st.spinner("Cargando el motor de Supertonic..."):
    engine = inicializar_motor()

# --- BARRA LATERAL: CONFIGURACIÓN MULTI-VOZ Y RENDIMIENTO ---
st.sidebar.header("⚙️ Configuración del Elenco")

# 1. Selección de Idioma
diccionario_idiomas = {
    "Español": "es", "Inglés": "en", "Francés": "fr", "Alemán": "de", "Italiano": "it", "Portugués": "pt"
}
idioma_seleccionado = st.sidebar.selectbox("Idioma del texto:", list(diccionario_idiomas.keys()))
codigo_idioma = diccionario_idiomas[idioma_seleccionado]

# Catálogo de voces
diccionario_voces = {
    "Voz Masculina Grave (M2)": "M2",
    "Voz Femenina Joven (F2)": "F2",
    "Voz Masculina Estándar (M1)": "M1",
    "Voz Femenina Estándar (F1)": "F1",
    "Voz Masculina Enérgica (M3)": "M3",
    "Voz Femenina Madura (F3)": "F3",
}

# 2. Asignación de Roles
voz_narrador = st.sidebar.selectbox("🎙️ Voz del Narrador:", list(diccionario_voces.keys()), index=0)
voz_personaje = st.sidebar.selectbox("💬 Voz del Personaje:", list(diccionario_voces.keys()), index=1)

codigo_narrador = diccionario_voces[voz_narrador]
codigo_personaje = diccionario_voces[voz_personaje]

# 3. Ajustes de Audio
velocidad = st.sidebar.slider("Velocidad de Lectura:", min_value=0.7, max_value=1.5, value=1.05, step=0.05)

# 4. OPTIMIZACIÓN: Tamaño del Lote (Batch Size)
st.sidebar.markdown("---")
st.sidebar.header("🚀 Optimización de CPU")
tamano_lote = st.sidebar.slider(
    "Tamaño del Lote (Batch Size):", 
    min_value=1, 
    max_value=10, 
    value=4, 
    help="Cuántas oraciones se consolidan en un único bloque de procesamiento continuo."
)


# --- CUERPO PRINCIPAL: COMPONENTE ARRASTRAR Y SOLTAR ---
st.subheader("1. Carga tu archivo")
archivo_subido = st.file_uploader(
    "Suelte su archivo aquí (.txt, .pdf, .epub, .docx)", 
    type=["txt", "pdf", "epub", "docx"]
)

if archivo_subido is not None:
    st.success(f"📦 Documento '{archivo_subido.name}' cargado con éxito.")
    contenido_texto = ""

    try:
        # Extracción multiformato
        if archivo_subido.name.endswith(".txt"):
            contenido_texto = archivo_subido.read().decode("utf-8", errors="ignore")
        elif archivo_subido.name.endswith(".pdf"):
            lector_pdf = pypdf.PdfReader(archivo_subido)
            contenido_texto = "\n".join([p.extract_text() for p in lector_pdf.pages if p.extract_text()])
        elif archivo_subido.name.endswith(".epub"):
            libro = epub.read_epub(archivo_subido)
            paginas_epub = []
            for item in libro.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    sopa = BeautifulSoup(item.get_content(), 'html.parser')
                    texto_limpio = sopa.get_text()
                    if texto_limpio.strip():
                        paginas_epub.append(texto_limpio.strip())
            contenido_texto = "\n".join(paginas_epub)
        elif archivo_subido.name.endswith(".docx"):
            doc = Document(archivo_subido)
            contenido_texto = "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

        if not contenido_texto.strip():
            st.warning("⚠️ No se detectó texto procesable.")
        else:
            with st.expander("📄 Ver fragmento del texto extraído"):
                st.text_area("Texto detectado:", contenido_texto[:2000] + "\n...", height=150, disabled=True)
            
            st.subheader("2. Generar Audiolibro")
            if st.button("🎭 Comenzar Lectura Avanzada", type="primary"):
                
                estilo_narrador = engine.get_voice_style(codigo_narrador)
                estilo_personaje = engine.get_voice_style(codigo_personaje)
                
                # Obtener todas las líneas válidas
                lineas = [l.strip() for l in contenido_texto.split('\n') if l.strip()]
                
                audios_generados = []
                progreso = st.progress(0)
                status_text = st.empty()
                
                # --- LÓGICA DE PROCESAMIENTO POR LOTES DINÁMICOS ---
                lotes = []
                lote_actual = []
                estilo_lote_actual = None
                
                for linea in lineas:
                    es_dialogo = linea.startswith('—') or linea.startswith('-') or linea.startswith('"') or linea.startswith('«')
                    estilo_linea = estilo_personaje if es_dialogo else estilo_narrador
                    
                    if estilo_lote_actual is None:
                        estilo_lote_actual = estilo_linea
                    
                    # Si la línea comparte el mismo estilo y el lote no está lleno, la acumulamos
                    if estilo_linea == estilo_lote_actual and len(lote_actual) < tamano_lote:
                        lote_actual.append(linea)
                    else:
                        # Guardamos el lote completo anterior y abrimos uno nuevo
                        lotes.append((lote_actual, estilo_lote_actual))
                        lote_actual = [linea]
                        estilo_lote_actual = estilo_linea
                
                # No olvidar añadir el último lote rezagado
                if lote_actual:
                    lotes.append((lote_actual, estilo_lote_actual))
                
                # --- EJECUCIÓN DE LOS LOTES CONSOLIDADOS ---
                total_lotes = len(lotes)
                for idx, (textos_lote, estilo_lote) in enumerate(lotes):
                    porcentaje = int((idx + 1) / total_lotes * 100)
                    progreso.progress(porcentaje)
                    status_text.text(f"Procesando bloque {idx + 1} de {total_lotes} (Consolidando {len(textos_lote)} líneas)...")
                    
                    # CORRECCIÓN CLAVE: Convertimos la lista de strings en un único string multilínea válido
                    texto_unificado = "\n".join(textos_lote)
                    
                    # Enviar el bloque de texto continuo al motor
                    resultado = engine.synthesize(
                        text=texto_unificado,  
                        voice_style=estilo_lote,
                        lang=codigo_idioma,
                        speed=velocidad
                    )
                    
                    # Extraer el arreglo de audio (NumPy array) de la respuesta
                    wav_chunk = resultado[0] if isinstance(resultado, tuple) else resultado
                    audios_generados.append(wav_chunk)
                
                status_text.text("💾 Uniendo fragmentos optimizados...")
                
                if audios_generados:
                    audios_planos = [chunk.flatten() for chunk in audios_generados]
                    audio_final = np.concatenate(audios_planos)
                    
                    nombre_base, _ = os.path.splitext(archivo_subido.name)
                    ruta_audio_salida = f"{nombre_base}_batch.wav"
                    
                    engine.save_audio(wav=audio_final, output_path=ruta_audio_salida)
                    
                    status_text.empty()
                    st.success("🎉 ¡Audiolibro de alta velocidad generado con éxito!")
                    st.info(f"💾 Archivo optimizado guardado como: `{ruta_audio_salida}`")
                    st.audio(ruta_audio_salida, format="audio/wav")
                        
    except Exception as e:
        st.error(f"Error en el procesamiento por lotes: {e}")