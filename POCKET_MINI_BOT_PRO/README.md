# 🤖 POCKET MINI BOT PRO — EDICIÓN PROFESIONAL MAC

Asistente privado de análisis técnico visual para **Pocket Option** en macOS (Apple Silicon M1/M2/M3 e Intel).

---

## 📌 CARACTERÍSTICAS PRINCIPALES

- **Dimensiones Compactas**: Ventana flotante de 350 px × 500 px.
- **Siempre al Frente**: Permanece visible sobre tu navegador sin interrumpir la operativa.
- **100% Visual y Seguro**: No requiere credenciales, cookies de sesión ni acceso a contraseñas. Funciona mediante captura visual de pantalla nativa (`mss` + `OpenCV`).
- **Estrategia Cuantitativa de 6 Filtros**: Requiere al menos 5 de 6 confirmaciones para emitir una señal (**CALL** o **PUT**).
- **Gestión de Riesgo Integrada**: Límite estricto de pérdidas consecutivas, pérdida diaria máxima y regla Anti-Martingale.
- **Base de Datos SQLite**: Registro histórico local de señales, resultados (Win/Loss) y estadísticas de rendimiento.
- **Soporte Retina Display**: Ajuste automático de escala de píxeles para pantallas MacBook Retina.

---

## 🏛️ LOS SEIS FILTROS CUANTITATIVOS

Para generar una señal ejecutable (**CALL** o **PUT**), el motor exige la coincidencia de al menos **5 de los siguientes 6 filtros**:

1. **Tendencia (EMA 9 / EMA 21 / EMA 50)**:
   - **CALL**: $\text{EMA}_9 > \text{EMA}_{21}$ con pendiente positiva.
   - **PUT**: $\text{EMA}_9 < \text{EMA}_{21}$ con pendiente negativa.
2. **Momentum RSI (14)**:
   - **CALL**: RSI entre 50 y 68.
   - **PUT**: RSI entre 32 y 50.
   - Filtra extremos de sobrecompra (>70) y sobreventa (<30).
3. **MACD (12, 26, 9)**:
   - **CALL**: Histograma positivo en expansión.
   - **PUT**: Histograma negativo en expansión.
4. **Patrón de Vela Cerrada (Price Action)**:
   - Confirmación por velas cerradas: *Hammer, Shooting Star, Pinbar elástico, Envolventes o Marubozus*.
5. **Soporte y Resistencia**:
   - Evita compras inmediatamente debajo de resistencias.
   - Evita ventas inmediatamente encima de soportes.
6. **Volatilidad y Escudo Anti-Spike (ATR 14)**:
   - Bloquea velas con mechas anormales ($>68\%$) y dojis planos sin volumen institucional.

---

## 🚀 INSTALACIÓN RÁPIDA EN MACOS

Abre la terminal en esta carpeta y ejecuta:

```bash
# 1. Dar permisos de ejecución
chmod +x install_mac.sh run_mac.sh build_mac.sh

# 2. Instalar entorno y dependencias
./install_mac.sh

# 3. Iniciar la aplicación
./run_mac.sh
```

---

## 🔐 PERMISOS DE MACOS

Para que el bot pueda capturar la ventana del gráfico:
1. Abre **Ajustes del Sistema** en tu Mac.
2. Ve a **Privacidad y Seguridad** $\rightarrow$ **Grabación de Pantalla**.
3. Asegúrate de que **Terminal**, **iTerm** o **Python** tengan el permiso activado.

---

## 📦 COMPILACIÓN A .APP NATIVO

Para empaquetar la aplicación como un ejecutable independiente de macOS:

```bash
./build_mac.sh
```
El archivo `PocketMiniBotPro.app` se generará en la carpeta `dist/`.

---

## 🛡️ AVISO LEGAL Y DE RIESGO

- **Pocket Mini Bot Pro** es una herramienta analítica visual y no ofrece asesoramiento financiero ni garantiza ganancias.
- La aplicación **nunca ejecuta órdenes de forma automática**. Todas las decisiones de inversión son tomadas exclusivamente por el usuario.
