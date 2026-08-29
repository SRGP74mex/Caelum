"""
Script de construcción de instalador Windows MSI para Caelum.
Uso (en Windows o mediante GitHub Actions):
    python setup_msi.py bdist_msi
"""

import sys

from cx_Freeze import Executable, setup

# -----------------------------------------------------------------------------
# 1. Configuración de Paquetes y Archivos Incluidos
# -----------------------------------------------------------------------------
build_exe_options = {
    "packages": [
        "src",
        "src.componentes",
        "src.modelos",
        "src.servicios",
        "src.utils",
        "src.vistas",
        "requests",
        "hijri_converter",
        "dateutil",
        "urllib3",
    ],
    "include_files": [
        ("assets", "assets"),
        ("config.py", "config.py"),
    ],
    "include_msvcr": True,
}

bdist_msi_options = {
    "summary_data": {
        "author": "Salvador RG (SRGP74mex)",
        "comments": "Caelum - A Fluid, Fast & Visually Immersive Weather Experience",
    },
    "upgrade_code": "{D3E7B219-5481-54E3-8E57-2B5C9130D7B2}",
    "install_icon": "assets/icons/app_icon.ico",
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        "main.py",
        target_name="Caelum.exe",
        base=base,
        icon="assets/icons/app_icon.ico",
        shortcut_name="Caelum",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="Caelum",
    version="1.5.0",
    author="Salvador RG",
    description="Caelum - A Fluid, Fast and Visually Immersive Weather App",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)

