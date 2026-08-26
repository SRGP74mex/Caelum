import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def _crear_sesion_http() -> requests.Session:
    """Sesión HTTP compartida con reintentos automáticos (backoff exponencial)
    ante errores transitorios de red o del servidor."""
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    sesion = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    sesion.mount("https://", adapter)
    sesion.mount("http://", adapter)
    return sesion


sesion_http = _crear_sesion_http()
