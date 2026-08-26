import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modelos.clima_datos import Ubicacion
from src.servicios.cache_manager import CacheManager
from src.servicios.geocoding_service import GeocodingService
from src.servicios.open_meteo_service import OpenMeteoService
from src.utils.fecha_utils import FechaHelper


def main():
    ciudad_busqueda = sys.argv[1] if len(sys.argv) > 1 else "Bogotá"
    print("\n🌤️  =======================================================")
    print("   WEATHERAPP LINUX - DEMOSTRACIÓN DEL MOTOR (SPRINT 1)")
    print("=======================================================\n")

    geo = GeocodingService()
    print(f"🔍 Buscando ubicación: '{ciudad_busqueda}'...")
    ciudades = geo.buscar_ciudades(ciudad_busqueda, limite=1)

    if not ciudades:
        print(f"⚠️  No se encontró '{ciudad_busqueda}', usando ubicación por defecto...")
        ubicacion = Ubicacion("Bogotá", "Colombia", 4.6097, -74.0817, "America/Bogota")
    else:
        ubicacion = ciudades[0]

    print(f"📍 Ubicación detectada: {ubicacion.ciudad}, {ubicacion.pais} (Lat: {ubicacion.latitud}, Lon: {ubicacion.longitud})")

    cache = CacheManager()
    service = OpenMeteoService()

    # Verificar caché
    reporte = cache.obtener_reporte(ubicacion.latitud, ubicacion.longitud)
    if reporte:
        print("⚡ Datos cargados desde CACHÉ local (0 ms de latencia)")
    else:
        print("🌐 Consultando Open-Meteo API en vivo...")
        reporte = service.obtener_reporte_completo(ubicacion)
        cache.guardar_reporte(reporte)
        print("💾 Respuesta guardada en caché local")

    greg, hijri = FechaHelper.fecha_dual_completa()
    act = reporte.actual

    print("\n" + "═"*55)
    print(f"  🏙️  {ubicacion.ciudad.upper()}, {ubicacion.pais.upper()}")
    print(f"  📅  {greg}")
    print(f"  🌙  {hijri}")
    print("═"*55)
    print(f"  🌡️   TEMPERATURA:     {act.temperatura:.1f} °C  (Sensación: {act.sensacion_termica:.1f} °C)")
    print(f"  ☁️   CONDICIÓN:       {act.condicion.descripcion} [Icono: {act.condicion.icon_name}]")
    print(f"  📈  RANGO HOY:       Mín: {act.temp_min_hoy:.1f} °C  •  Máx: {act.temp_max_hoy:.1f} °C")
    print(f"  💧  HUMEDAD:         {act.humedad_relativa}% (Punto Rocío: {act.punto_rocio} °C)")
    print(f"  💨  VIENTO:          {act.viento_velocidad:.1f} km/h {act.viento_direccion_cardinal} ({act.viento_direccion}°)")
    print(f"  ☀️   ÍNDICE UV:       {act.indice_uv:.1f} ({act.uv_categoria})")
    print(f"  👁️   VISIBILIDAD:     {act.visibilidad_km} km")
    print(f"  📊  PRESIÓN:         {act.presion_hpa:.1f} hPa")
    if act.amanecer_iso and act.ocaso_iso:
        am_hora = FechaHelper.formato_hora_corta(act.amanecer_iso)
        oc_hora = FechaHelper.formato_hora_corta(act.ocaso_iso)
        print(f"  🌅  SOL:             Amanecer: {am_hora}  •  Ocaso: {oc_hora}")
    print("─"*55)

    print("\n⏱️  PRONÓSTICO PRÓXIMAS 12 HORAS:")
    print("┌────────┬─────────────┬─────────────┬──────────────┬─────────────┐")
    print("│  HORA  │ TEMPERATURA │ SENSACIÓN   │ LLUVIA (%)   │ CONDICIÓN   │")
    print("├────────┼─────────────┼─────────────┼──────────────┼─────────────┤")
    for h in reporte.horas_24h[:12]:
        print(f"│ {h.hora_etiqueta:<6} │ {h.temperatura:>6.1f} °C   │ {h.sensacion:>6.1f} °C   │ {h.probabilidad_lluvia:>6}%      │ {h.condicion.descripcion[:11]:<11} │")
    print("└────────┴─────────────┴─────────────┴──────────────┴─────────────┘")

    print("\n📅  PRONÓSTICO 7 DÍAS (BARRAS DE RANGO TÉRMICO):")
    min_global = min(d.temp_min for d in reporte.dias_7d)
    max_global = max(d.temp_max for d in reporte.dias_7d)
    rango_total = max(max_global - min_global, 1.0)

    for d in reporte.dias_7d:
        barra_ancho = 18
        pos_min = int(((d.temp_min - min_global) / rango_total) * barra_ancho)
        pos_max = int(((d.temp_max - min_global) / rango_total) * barra_ancho)
        barra = list("─" * barra_ancho)
        for i in range(pos_min, min(pos_max + 1, barra_ancho)):
            barra[i] = "█"
        barra_str = "".join(barra)

        prob_str = f"🌧️ {d.probabilidad_lluvia}%" if d.probabilidad_lluvia > 15 else "      "
        print(f"  {d.nombre_dia:<4}  {d.condicion.descripcion[:12]:<12} {prob_str:<8} {d.temp_min:>4.1f}° [{barra_str}] {d.temp_max:>4.1f}°")

    print("\n✅ Demostración finalizada exitosamente.\n")

if __name__ == "__main__":
    main()

