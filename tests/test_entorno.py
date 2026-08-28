import os
import unittest
from unittest.mock import patch

from src.utils.entorno_sistema import EntornoSistema


class TestEntornoSistema(unittest.TestCase):
    def test_deteccion_wayland_por_xdg_session_type(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland", "WAYLAND_DISPLAY": "wayland-0"}, clear=False):
            self.assertTrue(EntornoSistema.es_wayland())
            self.assertEqual(EntornoSistema.obtener_servidor_grafico(), "Wayland")

    def test_deteccion_x11_por_xdg_session_type(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"}, clear=True):
            self.assertTrue(EntornoSistema.es_x11())
            self.assertFalse(EntornoSistema.es_wayland())
            self.assertEqual(EntornoSistema.obtener_servidor_grafico(), "X11 (XCB)")

    def test_deteccion_entornos_escritorio(self):
        casos = [
            ("ubuntu:GNOME", "GNOME"),
            ("GNOME", "GNOME"),
            ("KDE", "KDE Plasma"),
            ("KDE:Plasma", "KDE Plasma"),
            ("XFCE", "XFCE"),
            ("X-Cinnamon", "Cinnamon"),
            ("MATE", "MATE"),
            ("LXQt", "LXQt"),
            ("Hyprland", "Hyprland"),
            ("sway", "Sway"),
            ("i3", "i3"),
            ("COSMIC", "COSMIC")
        ]

        for env_val, esperado in casos:
            with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": env_val}, clear=False):
                self.assertEqual(
                    EntornoSistema.obtener_entorno_escritorio(),
                    esperado,
                    f"Fallo detectando {env_val} -> esperado {esperado}"
                )

    def test_obtener_info_completa(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "KDE"}, clear=False):
            info = EntornoSistema.obtener_info_completa()
            self.assertIn("servidor_grafico", info)
            self.assertIn("escritorio", info)
            self.assertIn("es_wayland", info)
            self.assertIn("es_x11", info)
            self.assertIn("soporte_bandeja", info)
            self.assertEqual(info["escritorio"], "KDE Plasma")

    def test_configurar_optimizaciones_wayland(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            EntornoSistema.configurar_optimizaciones_wayland()
            self.assertEqual(os.environ.get("QT_QPA_PLATFORM"), "wayland;xcb")


if __name__ == "__main__":
    unittest.main()
