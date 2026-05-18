import os
import streamlit as st
from supertonic import TTS
import pypdf

# Configuración de la interfaz gráfica local
st.set_page_config(page_title="Sintetizador Supertonic", page_icon="🎙️", layout="centered")

st.title("🎙️ Lector Multiformato Local (TXT y PDF)")
st.write("Arrastra tus documentos o capítulos de novelas para convertirlos a voz sin usar internet.")

# Inicializar el motor TTS con caché para evitar recargas lentas
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
    "Voz Masculina Estándar (M1)": "M1",
    "Voz Masculina Grave (M2)": "M2",
    "Voz Masculina Enérgica (M3)": "M3",
}
voz_seleccionada = st.sidebar.selectbox("Selecciona el Estilo de Voz:", list(diccionario_voces.keys()))
codigo_voz = diccionario_voces[voz_seleccionada]

# 3. Control de Velocidad
velocidad = st.sidebar.slider("Velocidad de Lectura:", min_value=0.7, max_value=1.5, value=1.05, step=0.05)


# --- CUERPO PRINCIPAL: COMPONENTE ARRASTRAR Y SOLTAR ---
st.subheader("1. Carga tu archivo")

# Componente nativo de arrastrar y soltar
archivo_subido = st.file_uploader(
    "Suelta tu archivo aquí (formatos aceptados: .txt y .pdf)", 
    type=["txt", "pdf"]
)

if archivo_subido is not None:
    st.success(f"📦 Archivo '{archivo_subido.name}' cargado con éxito.")
    contenido_texto = ""

    # Procesar el archivo según su extensión
    try:
        if archivo_subido.name.endswith(".txt"):
            # Leer archivo de texto plano
            contenido_texto = archivo_subido.read().decode("utf-8", errors="ignore")
            
        elif archivo_subido.name.endswith(".pdf"):
            # Leer y extraer texto del PDF página por página
            lector_pdf = pypdf.PdfReader(archivo_subido)
            paginas_texto = []
            
            for num_pag, pagina in enumerate(lector_pdf.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    paginas_texto.append(texto_pagina)
            
            contenido_texto = "\n".join(paginas_texto)

        # Validar si el archivo contiene texto procesable
        if not contenido_texto.strip():
            st.warning("⚠️ No se pudo extraer texto del archivo. Verifica que no sea un PDF escaneado (que actúe como imagen).")
        else:
            # Mostrar una pequeña muestra del texto para confirmar la lectura
            with st.expander("📄 Ver fragmento del texto a procesar (Primeros 2000 caracteres)"):
                st.text_area("Contenido:", contenido_texto[:2000] + ("..." if len(contenido_texto) > 2000 else ""), height=150, disabled=True)
            
            # Botón de ejecución
            st.subheader("2. Procesar")
            if st.button("🚀 Convertir Texto a Voz", type="primary"):
                with st.spinner("Sintetizando audio localmente... Por favor espera."):
                    
                    # Configurar estilo y ejecutar síntesis
                    estilo = engine.get_voice_style(codigo_voz)
                    resultado = engine.synthesize(
                        text=contenido_texto,
                        voice_style=estilo,
                        lang=codigo_idioma,
                        speed=velocidad
                    )
                    
                    # Generar nombre del archivo de salida en la carpeta del proyecto
                    nombre_base, _ = os.path.splitext(archivo_subido.name)
                    ruta_audio_salida = f"{nombre_base}.wav"
                    
                    # Guardar el audio generado
                    wav_data = resultado[0] if isinstance(resultado, tuple) else resultado
                    engine.save_audio(wav=wav_data, output_path=ruta_audio_salida)
                    
                    if os.path.exists(ruta_audio_salida):
                        st.success("🎉 ¡Audio generado con éxito de forma automática!")
                        st.info(f"💾 Guardado en la carpeta de tu proyecto como: `{ruta_audio_salida}`")
                        
                        # Reproductor de audio integrado
                        st.audio(ruta_audio_salida, format="audio/wav")
                        
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")