# Weather Linux

Aplicación de clima para escritorio Linux con estética glassmorphism, hecha en Python
con PySide6. Muestra el pronóstico actual, próximas 24 horas y 7 días, con fondos
fotográficos y partículas animadas (lluvia, nieve, estrellas) según la condición
climática real de la ubicación consultada.

Datos meteorológicos de [Open-Meteo](https://open-meteo.com/) (sin necesidad de API key).

## Requisitos

- Linux con soporte de escritorio (X11 o Wayland)
- Python 3.11+ con `python3-venv` disponible
- Conexión a internet (los datos de clima y geocodificación se consultan en vivo)

## Instalación y uso

```bash
git clone <url-del-repositorio>
cd "Weather Linux"
./run.sh
```

`run.sh` crea automáticamente un entorno virtual en `venv/` la primera vez, instala las
dependencias de `requirements.txt` y lanza la aplicación. Las siguientes ejecuciones
solo abren la app directamente.

### Icono de escritorio

Para tener un lanzador en el menú de aplicaciones del sistema:

```bash
./install_desktop.sh
```

Esto genera `weather-linux.desktop` con la ruta absoluta correcta de tu equipo y lo
instala en `~/.local/share/applications/`.

## Configuración y datos locales

La app no requiere configuración manual, pero guarda estado en:

- `~/.config/weather_linux/config.json` — última ciudad, ciudades recientes/favoritas y preferencias
- `~/.cache/weather_linux/` — caché de reportes de clima (TTL de 15 minutos) y archivo de log

## Tests

```bash
./venv/bin/python3 -m unittest discover -s tests -v
```

Los tests de UI (`tests/test_ui.py`) requieren correr con `QT_QPA_PLATFORM=offscreen`
si no hay un servidor gráfico disponible:

```bash
QT_QPA_PLATFORM=offscreen ./venv/bin/python3 -m unittest tests.test_ui -v
```

## Estructura del proyecto

```
config.py              # Constantes de la aplicación (rutas, valores por defecto, URLs de APIs)
main.py                # Punto de entrada
src/modelos/           # Dataclasses del dominio (Ubicacion, ClimaActual, PronosticoDia, ...)
src/servicios/         # Acceso a red, caché y configuración persistente del usuario
src/componentes/       # Widgets de UI reutilizables
src/vistas/            # Ventanas/orquestación de la aplicación
src/utils/             # Utilidades (fechas, mapeo de iconos de clima)
tests/                 # Suite de tests (unittest)
```

## Licencia

MIT — ver [LICENSE](LICENSE).
