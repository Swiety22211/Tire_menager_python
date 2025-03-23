#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł definiujący ścieżki używane w aplikacji.
"""

import os
import sys
import platform
from pathlib import Path

def resource_path(relative_path):
    """
    Zwraca ścieżkę do zasobu, działającą zarówno w trybie deweloperskim, jak i po skompilowaniu.
    
    Args:
        relative_path (str): Ścieżka względna do zasobu.
        
    Returns:
        str: Pełna ścieżka do zasobu.
    """
    try:
        # PyInstaller tworzy folder tymczasowy i przechowuje tam ścieżkę w _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        return os.path.join(base_path, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)

# Ustalenie ścieżki katalogu danych aplikacji w zależności od systemu operacyjnego
if platform.system() == "Windows":
    # Windows - %APPDATA%\TireDepositManager
    APP_DATA_DIR = os.path.join(os.environ['APPDATA'], "TireDepositManager")
elif platform.system() == "Darwin":
    # macOS - ~/Library/Application Support/TireDepositManager
    APP_DATA_DIR = os.path.expanduser("~/Library/Application Support/TireDepositManager")
else:
    # Linux i inne - ~/.config/TireDepositManager
    APP_DATA_DIR = os.path.expanduser("~/.config/TireDepositManager")

# Ścieżki do katalogów w projekcie
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = resource_path(os.path.join(ROOT_DIR, "resources"))
ICONS_DIR = resource_path(os.path.join(RESOURCES_DIR, "icons"))
TEMPLATES_DIR = resource_path(os.path.join(RESOURCES_DIR, "templates"))
FONTS_DIR = resource_path(os.path.join(RESOURCES_DIR, "fonts"))
IMAGES_DIR = resource_path(os.path.join(RESOURCES_DIR, "images"))
CONFIG_DIR = os.path.join(APP_DATA_DIR, "config")

# Ścieżki do katalogów danych aplikacji
DATA_DIR = os.path.join(APP_DATA_DIR, "data")
LOGS_DIR = os.path.join(APP_DATA_DIR, "logs")
BACKUP_DIR = os.path.join(APP_DATA_DIR, "backup")
TEMP_DIR = os.path.join(APP_DATA_DIR, "temp")

# Ścieżka do pliku bazy danych
DATABASE_PATH = os.path.join(DATA_DIR, "database.db")

def ensure_dir_exists(directory=None):
    """Tworzy wymagane katalogi, jeśli nie istnieją."""
    if directory:
        os.makedirs(directory, exist_ok=True)
    else:
        for directory in [APP_DATA_DIR, DATA_DIR, LOGS_DIR, BACKUP_DIR, TEMP_DIR, CONFIG_DIR]:
            os.makedirs(directory, exist_ok=True)

ensure_directories_exist = ensure_dir_exists  # Alias funkcji

