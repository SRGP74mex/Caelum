import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from config import CARPETA_DATOS, CARPETA_DATOS_ANTIGUA, directorio_datos_usuario


@unittest.skipIf(os.name == "nt", "Las rutas XDG solo aplican a Linux/Unix")
class TestMigracionCarpetaDatos(unittest.TestCase):
    """La carpeta del nombre antiguo ("weather_linux") se migra a "caelum"
    sin perder los ajustes de instalaciones previas."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        entorno = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.base)})
        entorno.start()
        self.addCleanup(entorno.stop)

    def test_migra_carpeta_antigua_conservando_archivos(self):
        antigua = self.base / CARPETA_DATOS_ANTIGUA
        antigua.mkdir()
        (antigua / "config.json").write_text('{"idioma": "pt"}', encoding="utf-8")

        ruta = directorio_datos_usuario("config")

        self.assertEqual(ruta, self.base / CARPETA_DATOS)
        self.assertEqual((ruta / "config.json").read_text(encoding="utf-8"), '{"idioma": "pt"}')
        self.assertFalse(antigua.exists())

    def test_instalacion_nueva_usa_carpeta_caelum(self):
        self.assertEqual(directorio_datos_usuario("config"), self.base / CARPETA_DATOS)
        self.assertFalse((self.base / CARPETA_DATOS_ANTIGUA).exists())

    def test_si_ya_existen_ambas_no_toca_nada(self):
        (self.base / CARPETA_DATOS).mkdir()
        (self.base / CARPETA_DATOS_ANTIGUA).mkdir()
        self.assertEqual(directorio_datos_usuario("config"), self.base / CARPETA_DATOS)
        self.assertTrue((self.base / CARPETA_DATOS_ANTIGUA).exists())

    def test_si_no_se_puede_mover_sigue_usando_la_antigua(self):
        antigua = self.base / CARPETA_DATOS_ANTIGUA
        antigua.mkdir()
        with mock.patch.object(Path, "rename", side_effect=PermissionError):
            self.assertEqual(directorio_datos_usuario("config"), antigua)


if __name__ == "__main__":
    unittest.main()
