# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
Este proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [1.3.0] - 2026-08-26

### Añadido
- Pantalla de ajustes (⚙️) para elegir unidades de temperatura (°C/°F) y
  viento (km/h, m/s, mph), y comportamiento de la bandeja del sistema.
- `cerrar_a_bandeja` ahora tiene efecto real: la ventana se minimiza a la
  bandeja al cerrarla en vez de terminar la aplicación (antes la
  preferencia existía en el modelo de configuración pero no hacía nada).

### Corregido
- Sufijos de unidad ("km/h", "°C") que estaban hardcodeados en varios
  widgets ahora reflejan la unidad realmente seleccionada.
- El cálculo del punto de rocío horario en `bento_grid.py` (fórmula válida
  solo en Celsius) ahora opera siempre en Celsius internamente antes de
  convertir el resultado a la unidad de visualización.

## [1.2.0] - 2026-08-26

### Añadido
- `pyproject.toml`: metadata del paquete y entry point (`weather-linux`),
  instalable con `pip install -e .` o `pipx install .`.

## [1.1.0] - 2026-08-26

### Añadido
- Logging estructurado (archivo rotativo en `~/.cache/weather_linux/weatherapp.log`).
- Reintentos automáticos con backoff en las llamadas HTTP (sesión `requests` compartida).
- Tests deterministas con `unittest.mock` para los servicios de red (`tests/test_servicios_mock.py`).
- Lint (`ruff`) y type-checking (`mypy`) configurados en `pyproject.toml`.
- CI en GitHub Actions (lint + tests headless en cada push/PR).

### Cambiado
- Mejor feedback de error en la ventana principal (referencia explícita al botón de reintentar).

## [1.0.1] - 2026-08-26

### Corregido
- Permisos world-writable en `venv/` corregidos.
- Proveedor de respaldo de geolocalización por IP migrado de HTTP plano
  (`ip-api.com`, sin soporte HTTPS gratuito) a HTTPS (`ipwho.is`).
- `.desktop` generado dinámicamente con la ruta real del equipo en vez de
  tener una ruta fija hardcodeada (`install_desktop.sh`).
- Dependencias fijadas a versiones exactas en `requirements.txt`.
- Caché de fondo escalado en la ventana principal para evitar recalcular
  un `SmoothTransformation` costoso en cada repintado.
- Agrupación de horas por día optimizada de O(días×horas) a O(horas).

## [1.0.0] - 2026-08-25

### Añadido
- Primera versión funcional: pronóstico actual, 24 horas y 7 días vía
  Open-Meteo, búsqueda de ciudades, caché local, bandeja de sistema y
  fondos animados según condición climática.
