# POCKET MINI BOT — macOS

Mini aplicación flotante de 350 × 500 px para observar visualmente un gráfico abierto en Pocket Option.

## Qué hace
- Permite seleccionar manualmente el rectángulo del gráfico.
- Captura esa zona periódicamente.
- Intenta detectar cuerpos rojos/verdes y calcula métricas visuales aproximadas.
- Muestra CALL / PUT / ESPERAR como resultado heurístico.
- Ventana siempre visible.

## Limitaciones importantes
- No recibe cotizaciones oficiales ni datos OHLC de Pocket Option.
- La detección depende del tema, colores, zoom, resolución y escala del gráfico.
- El valor de "confianza" es una puntuación heurística, NO una probabilidad estadística calibrada.
- No ejecuta operaciones, no inicia sesión y no almacena credenciales.
- No garantiza resultados ni debe usarse como única base para invertir.
- Comprueba los términos de Pocket Option antes de usar captura automatizada; utiliza solo funciones permitidas.

## Requisitos
- macOS y Python 3.10 o superior.
- Permiso de Grabación de pantalla para Terminal o Python.
- Conexión a internet solo para instalar dependencias.

## Instalación
1. Descomprime `POCKET_MINI_BOT.zip`.
2. Abre Terminal y entra en la carpeta:
   `cd ~/Downloads/POCKET_MINI_BOT`
   (ajusta la ruta si la descomprimiste en otro lugar).
3. Ejecuta:
   `chmod +x install_mac.sh run_mac.sh`
   `./install_mac.sh`
4. Ejecuta:
   `./run_mac.sh`
5. Si macOS pide permiso de grabación de pantalla: Ajustes del Sistema → Privacidad y seguridad → Grabación de pantalla. Autoriza Terminal (o la app desde la que ejecutas Python) y vuelve a abrirla.

## Uso
1. Abre Pocket Option y deja visible el gráfico.
2. Abre POCKET MINI BOT.
3. Pulsa **Seleccionar gráfico**.
4. Arrastra un rectángulo que incluya solo la zona de velas, sin paneles ni menús.
5. Pulsa **Iniciar análisis**. La ventana queda siempre encima.
6. Usa **Pausar análisis** para detenerlo.

## Solución de problemas
- Si la captura aparece negra, concede el permiso de Grabación de pantalla a Terminal/Python y reinicia Terminal.
- Si no detecta velas, selecciona un área más ajustada y asegúrate de que los cuerpos sean rojos/verdes saturados.
- En pantallas Retina, algunas configuraciones pueden usar escalado de coordenadas; si el rectángulo no coincide, ejecuta la app en la pantalla principal y vuelve a seleccionar.
- No selecciones la ventana del mini bot como área de gráfico.
