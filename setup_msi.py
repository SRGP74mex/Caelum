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
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtSvg",
    ],
    "include_files": [
        ("assets", "assets"),
        ("config.py", "config.py"),
    ],
    "include_msvcr": True,
}

# -----------------------------------------------------------------------------
# 2. Configuración de Accesos Directos (Escritorio y Menú Inicio de Windows)
# -----------------------------------------------------------------------------
shortcut_table = [
    (
        "DesktopShortcut",          # Shortcut
        "DesktopFolder",            # Directory_
        "Caelum",                   # Name
        "TARGETDIR",                # Component_
        "[TARGETDIR]Caelum.exe",    # Target
        None,                       # Arguments
        "Caelum - Clima y Astronomía", # Description
        None,                       # Hotkey
        None,                       # Icon
        None,                       # IconIndex
        None,                       # ShowCmd
        "TARGETDIR",                # WkDir
    ),
    (
        "ProgramMenuShortcut",      # Shortcut
        "ProgramMenuFolder",        # Directory_
        "Caelum",                   # Name
        "TARGETDIR",                # Component_
        "[TARGETDIR]Caelum.exe",    # Target
        None,                       # Arguments
        "Caelum - Clima y Astronomía", # Description
        None,                       # Hotkey
        None,                       # Icon
        None,                       # IconIndex
        None,                       # ShowCmd
        "TARGETDIR",                # WkDir
    ),
]

msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {
    "data": msi_data,
    "summary_data": {
        "author": "Salvador RG (SRGP74mex)",
        "comments": "Caelum - A Fluid, Fast & Visually Immersive Weather Experience",
    },
    "upgrade_code": "{95C54926-C4DE-4942-88E2-CAELUM001500}",
    "install_icon": "assets/icons/app_icon.ico",
}

# En Windows ocultar consola con Win32GUI
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
