from abc import ABC, abstractmethod
from src.modelos.clima_datos import Ubicacion, ReporteClimaCompleto

class IWeatherProvider(ABC):
    """Interfaz abstracta para proveedores de datos meteorológicos."""

    @abstractmethod
    def obtener_reporte_completo(self, ubicacion: Ubicacion) -> ReporteClimaCompleto:
        """Obtiene y construye el reporte meteorológico completo para una ubicación."""
        pass

