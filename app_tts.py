import os
import re
import streamlit as st
import numpy as np
from supertonic import TTS
import pypdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
import warnings

# Desactivar advertencias molestas
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configuración de la interfaz gráfica local
st.set_page_config(page_title="Lector de Novelas Supertonic", page_icon="📖", layout="centered")

st.title("⚡ Lector de Novelas con Normalización Avanzada")
st.write("Convierte tus libros a voz limpiando artefactos de texto y añadiendo pausas dramáticas automáticas.")

# Inicializar el motor TTS con caché
@st.cache_resource
def inicializar_motor():
    return TTS()

with st.spinner("Cargando el motor de Supertonic..."):
    engine = inicializar_motor()

# --- BARRA LATERAL: CONFIGURACIÓN MULTI-VOZ Y RENDIMIENTO ---
st.sidebar.header("⚙️ Configuración del Elenco")

diccionario_idiomas = {
    "Español": "es", "Inglés": "en", "Francés": "fr", "Alemán": "de", "Italiano": "it", "Portugués": "pt", "Multi-idioma (Neutral)": "na"
}
idioma_seleccionado = st.sidebar.selectbox("Idioma del texto:", list(diccionario_idiomas.keys()))
codigo_idioma = diccionario_idiomas[idioma_seleccionado]

diccionario_voces = {
    "Voz Masculina Grave (M2)": "M2",
    "Voz Femenina Joven (F2)": "F2",
    "Voz Masculina Estándar (M1)": "M1",
    "Voz Femenina Estándar (F1)": "F1",
    "Voz Masculina Enérgica (M3)": "M3",
    "Voz Femenina Madura (F3)": "F3",
}

voz_narrador = st.sidebar.selectbox("🎙️ Voz del Narrador:", list(diccionario_voces.keys()), index=0)
voz_personaje = st.sidebar.selectbox("💬 Voz del Personaje:", list(diccionario_voces.keys()), index=1)

codigo_narrador = diccionario_voces[voz_narrador]
codigo_personaje = diccionario_voces[voz_personaje]

velocidad = st.sidebar.slider("Velocidad de Lectura:", min_value=0.7, max_value=1.5, value=1.05, step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("🚀 Optimización de CPU")
tamano_lote = st.sidebar.slider("Tamaño del Lote (Batch Size):", min_value=1, max_value=10, value=4)


# --- FUNCIÓN COMPLEMENTARIA: LIMPIEZA Y NORMALIZACIÓN DE TEXTO ---
def normalizar_texto_novela(texto_crudo, simular_pausas, eliminar_numeros, diccionario_personalizado):
    lines = texto_crudo.split('\n')
    texto_filtrado = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # 1. Filtro de Cortes de Escena (ej: ***, ---, ___ o * * *)
        if simular_pausas and re.match(r'^[\s*#\-_~=\.]{3,}$', line_clean):
            # Transformamos el corte visual en un comando de pausa nativo de Supertonic
            texto_filtrado.append("[pause:2.0]")
            continue

        # 2. Filtro de Números de Página huérfanos (Evita leer "Página 45" o un "12" suelto al final del párrafo)
        if eliminar_numeros and (line_clean.isdigit() or re.match(r'^(pág\.|pagina|pag\.)\s*\d+$', line_clean, re.IGNORECASE)):
            continue

        # 3. Diccionario de Reemplazos Personalizados (Abreviaturas o Trazas de nombres)
        if diccionario_personalizado:
            for busqueda, reemplazo in diccionario_personalizado.items():
                if busqueda.strip():
                    line_clean = re.sub(r'\b' + re.escape(busqueda.strip()) + r'\b', reemplazo.strip(), line_clean, flags=re.IGNORECASE)

        texto_filtrado.append(line_clean)
        
    return "\n".join(texto_filtrado)


# --- CUERPO PRINCIPAL: COMPONENTE ARRASTRAR Y SOLTAR ---
st.subheader("1. Carga tu archivo")
archivo_subido = st.file_uploader("Suelte su archivo aquí (.txt, .pdf, .epub, .docx)", type=["txt", "pdf", "epub", "docx"])

if archivo_subido is not None:
    st.success(f"📦 Documento '{archivo_subido.name}' cargado con éxito.")
    contenido_texto_original = ""

    try:
        # Extracción multiformato
        if archivo_subido.name.endswith(".txt"):
            contenido_texto_original = archivo_subido.read().decode("utf-8", errors="ignore")
        elif archivo_subido.name.endswith(".pdf"):
            lector_pdf = pypdf.PdfReader(archivo_subido)
            contenido_texto_original = "\n".join([p.extract_text() for p in lector_pdf.pages if p.extract_text()])
        elif archivo_subido.name.endswith(".epub"):
            libro = epub.read_epub(archivo_subido)
            paginas_epub = []
            for item in libro.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    sopa = BeautifulSoup(item.get_content(), 'html.parser')
                    texto_limpio = sopa.get_text()
                    if texto_limpio.strip():
                        paginas_epub.append(texto_limpio.strip())
            contenido_texto_original = "\n".join(paginas_epub)
        elif archivo_subido.name.endswith(".docx"):
            doc = Document(archivo_subido)
            contenido_texto_original = "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

        if not contenido_texto_original.strip():
            st.warning("⚠️ No se detectó texto procesable.")
        else:
            # --- NUEVA SECCIÓN: INTERFAZ DE NORMALIZACIÓN ---
            st.subheader("2. Filtros de Normalización y Limpieza")
            with st.expander("🔧 Configurar Reglas de Limpieza Textual", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    activa_pausas = st.checkbox("Convertir cortes de escena (***, ---) en silencios [pause:2.0]", value=True)
                with col2:
                    activa_num_paginas = st.checkbox("Detectar y eliminar números de página sueltos", value=True)
                
                st.markdown("**Diccionario de correcciones personalizadas (Opcional):**")
                st.caption("Útil para expandir abreviaturas manuales. Formato: `abreviatura = reemplazo` (una por línea). Ej: `Sr. = Señor`")
                lineas_diccionario = st.text_area("Correcciones:", placeholder="Ejemplo:\nSr. = Señor\nDra. = Doctora\ncap. = capítulo", height=100)
                
                # Procesar el diccionario ingresado por el usuario
                dict_reglas = {}
                if lineas_diccionario.strip():
                    for l in lineas_diccionario.split('\n'):
                        if '=' in l:
                            k, v = l.split('=', 1)
                            dict_reglas[k.strip()] = v.strip()

            # Aplicar filtros de normalización antes de mostrar o procesar el texto
            contenido_texto_normalizado = normalizar_texto_novela(
                contenido_texto_original, activa_pausas, activa_num_paginas, dict_reglas
            )

            with st.expander("📄 Ver fragmento del texto Normalizado (Pre-visualización)"):
                st.text_area("Texto listo para sintetizar:", contenido_texto_normalizado[:2000] + "\n...", height=150, disabled=True)
            
            # Botón de ejecución principal
            st.subheader("3. Generar Audiolibro")
            if st.button("🎭 Comenzar Lectura Normalizada", type="primary"):
                
                estilo_narrador = engine.get_voice_style(codigo_narrador)
                estilo_personaje = engine.get_voice_style(codigo_personaje)
                
                # Obtener todas las líneas ya filtradas
                lineas = [l.strip() for l in contenido_texto_normalizado.split('\n') if l.strip()]
                
                audios_generados = []
                progreso = st.progress(0)
                status_text = st.empty()
                
                # LÓGICA DE PROCESAMIENTO POR LOTES DINÁMICOS
                lotes = []
                lote_actual = []
                estilo_lote_actual = None
                
                for linea in lineas:
                    # Si es una etiqueta de pausa pura, hereda el estilo del lote actual para no romper la agrupación
                    if linea.startswith("[pause:"):
                        if estilo_lote_actual is None:
                            estilo_lote_actual = estilo_narrador
                        lote_actual.append(linea)
                        continue

                    es_dialogo = linea.startswith('—') or linea.startswith('-') or linea.startswith('"') or linea.startswith('«')
                    estilo_linea = estilo_personaje if es_dialogo else estilo_narrador
                    
                    if estilo_lote_actual is None:
                        estilo_lote_actual = estilo_linea
                    
                    if estilo_linea == estilo_lote_actual and len(lote_actual) < tamano_lote:
                        lote_actual.append(linea)
                    else:
                        lotes.append((lote_actual, estilo_lote_actual))
                        lote_actual = [linea]
                        estilo_lote_actual = estilo_linea
                
                if lote_actual:
                    lotes.append((lote_actual, estilo_lote_actual))
                
                # EJECUCIÓN DE LOS LOTES CONSOLIDADOS
                total_lotes = len(lotes)
                for idx, (textos_lote, estilo_lote) in enumerate(lotes):
                    porcentaje = int((idx + 1) / total_lotes * 100)
                    progreso.progress(porcentaje)
                    status_text.text(f"Procesando bloque {idx + 1} de {total_lotes}...")
                    
                    texto_unificado = "\n".join(textos_lote)
                    
                    resultado = engine.synthesize(
                        text=texto_unificado,  
                        voice_style=estilo_lote,
                        lang=codigo_idioma,
                        speed=velocidad
                    )
                    
                    wav_chunk = resultado[0] if isinstance(resultado, tuple) else resultado
                    audios_generados.append(wav_chunk)
                
                status_text.text("💾 Uniendo fragmentos limpios...")
                
                if audios_generados:
                    audios_planos = [chunk.flatten() for chunk in audios_generados]
                    audio_final = np.concatenate(audios_planos)
                    
                    nombre_base, _ = os.path.splitext(archivo_subido.name)
                    ruta_audio_salida = f"{nombre_base}_normalizado.wav"
                    
                    engine.save_audio(wav=audio_final, output_path=ruta_audio_salida)
                    
                    status_text.empty()
                    st.success("🎉 ¡Audiolibro normalizado generado con éxito!")
                    st.info(f"💾 Guardado localmente como: `{ruta_audio_salida}`")
                    st.audio(ruta_audio_salida, format="audio/wav")
                        
    except Exception as e:
        st.error(f"Error en el procesamiento de normalización: {e}")