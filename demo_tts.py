import os
from supertonic import TTS

def ejecutar_sintesis_definitiva():
    print("--- 1. Inicializando el motor de Supertonic ---")
    engine = TTS()
    
    # Seleccionamos la primera voz femenina disponible
    voz_seleccionada = 'F1'
    print(f"Seleccionando la voz de referencia: '{voz_seleccionada}'")
    estilo = engine.get_voice_style(voz_seleccionada)
    
    texto = (
        "Hola. Esta es la prueba definitiva utilizando las voces nativas "
        "y los métodos de guardado integrados en la librería."
    )
    
    print("\n--- 2. Sintetizando texto a audio ---")
    resultado = engine.synthesize(
        text=texto,
        voice_style=estilo,
        lang="es"
    )
    
    print("\n--- 3. Guardando el archivo de audio ---")
    archivo_salida = "audio_local_supertonic.wav"
    
    # Extraemos únicamente el arreglo 'wav' (el primer elemento de la tupla)
    wav_data = resultado[0] if isinstance(resultado, tuple) else resultado
    
    try:
        # Usamos los nombres de argumentos exactos que pide el método nativo
        engine.save_audio(wav=wav_data, output_path=archivo_salida)
        
        if os.path.exists(archivo_salida):
            print(f"\n¡Éxito total! El archivo se generó correctamente en:\n{os.path.abspath(archivo_salida)}")
            
    except Exception as e:
        print(f"Fallo el método nativo: {e}")
        print("Ejecutando guardado de respaldo con soundfile...")
        import soundfile as sf
        
        # Si falla el nativo, extraemos el sample_rate directamente de la propiedad del motor
        sr = engine.sample_rate if hasattr(engine, 'sample_rate') else 24000
        sf.write(archivo_salida, wav_data, sr)
        print(f"¡Guardado con soundfile en: {os.path.abspath(archivo_salida)}")

if __name__ == "__main__":
    ejecutar_sintesis_definitiva()