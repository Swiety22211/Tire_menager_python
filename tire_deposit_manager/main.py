#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Menadżer Depozytów Opon - główny plik uruchomieniowy aplikacji.
Obsługuje inicjalizację logowania, połączenie z bazą danych oraz uruchomienie interfejsu użytkownika.
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer

from ui.main_window import MainWindow
from utils.database import create_connection, initialize_database
from utils.paths import APP_DATA_DIR, LOGS_DIR, ICONS_DIR, ensure_directories_exist

# Konfiguracja logowania
def setup_logging():
    """Konfiguruje system logowania aplikacji."""
    # Upewnij się, że katalog na logi istnieje
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Nazwa pliku logu z datą
    log_file = os.path.join(LOGS_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Konfiguracja loggera
    logger = logging.getLogger("TireDepositManager")
    logger.setLevel(logging.DEBUG)
    
    # Obsługa logowania do pliku
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Obsługa logowania do konsoli
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Dodanie handlerów do loggera
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def exception_hook(exctype, value, traceback):
    """Przechwytuje nieobsłużone wyjątki i loguje je."""
    logger = logging.getLogger("TireDepositManager")
    logger.critical("Nieobsłużony wyjątek:", exc_info=(exctype, value, traceback))
    # Przekazanie wyjątku do oryginalnego handlera
    sys.__excepthook__(exctype, value, traceback)

def main():
    """Funkcja główna aplikacji."""
    # Ustawienie obsługi nieobsłużonych wyjątków
    sys.excepthook = exception_hook
    
    # Konfiguracja logowania
    logger = setup_logging()
    logger.info("Uruchamianie aplikacji Menadżer Depozytów Opon")
    
    # Upewnij się, że wszystkie wymagane katalogi istnieją
    ensure_directories_exist()
    
    # Inicjalizacja aplikacji Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Menadżer Depozytów Opon")
    app.setWindowIcon(QIcon(os.path.join(ICONS_DIR, "app-icon.png")))
    
    # Wyświetlenie ekranu powitalnego
    splash_path = os.path.join(ICONS_DIR, "logo.png")
    if os.path.exists(splash_path):
        splash_pixmap = QPixmap(splash_path)
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()
    else:
        splash = None
    
    # Wyświetlenie informacji o inicjalizacji na ekranie powitalnym
    if splash:
        splash.showMessage("Inicjalizacja bazy danych...", Qt.AlignBottom | Qt.AlignHCenter, Qt.white)
    
    # Nawiązanie połączenia z bazą danych
    conn = create_connection()
    if not conn:
        if splash:
            splash.close()
        QMessageBox.critical(None, "Błąd", "Nie można połączyć się z bazą danych!")
        logger.critical("Nie można połączyć się z bazą danych!")
        return 1
    
    # Inicjalizacja struktury bazy danych
    initialize_database(conn)
    
    # Aktualizacja ekranu powitalnego
    if splash:
        splash.showMessage("Ładowanie interfejsu użytkownika...", Qt.AlignBottom | Qt.AlignHCenter, Qt.white)
    
    # Utworzenie głównego okna aplikacji
    mainWindow = MainWindow(conn)
    
    # Zamknięcie ekranu powitalnego i wyświetlenie głównego okna
    if splash:
        splash.finish(mainWindow)
    
    mainWindow.show()
    
    # Uruchomienie pętli zdarzeń aplikacji
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())