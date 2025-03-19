#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka pulpitu - główny ekran aplikacji z podsumowaniem kluczowych informacji.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QSpacerItem
)
from PySide6.QtCore import Qt, QSize, QDate, QTime
from PySide6.QtGui import QIcon, QColor, QFont, QPainter, QPixmap

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class DashboardWidget(QFrame):
    """Widget do wyświetlania statystyk na pulpicie."""
    
    def __init__(self, title, value, icon_path=None, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu statystyk.
        
        Args:
            title (str): Tytuł widgetu
            value (str): Wartość do wyświetlenia
            icon_path (str, optional): Ścieżka do ikony. Domyślnie None.
            color (str, optional): Kolor tła w formacie HEX. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("dashboardWidget")
        self.setStyleSheet(f"""
            QFrame#dashboardWidget {{
                background-color: {color};
                border-radius: 8px;
                color: white;
                padding: 15px;
            }}
        """)
        
        # Ustawienie minimalnej wysokości
        self.setMinimumHeight(120)
        
        # Układ widgetu
        layout = QHBoxLayout(self)
        
        # Ikona jeśli podano
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label)
        
        # Dane
        data_layout = QVBoxLayout()
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setObjectName("dashboardTitle")
        title_label.setFont(QFont("Segoe UI", 10))
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        data_layout.addWidget(title_label)
        
        # Wartość
        value_label = QLabel(value)
        value_label.setObjectName("dashboardValue")
        value_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        value_label.setStyleSheet("color: white;")
        data_layout.addWidget(value_label)
        
        layout.addLayout(data_layout)
        layout.addStretch(1)

class DashboardTab(QWidget):
    """
    Zakładka pulpitu wyświetlająca podsumowanie kluczowych informacji.
    """
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki pulpitu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Odświeżenie danych
        self.refresh_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Powitanie
        welcome_layout = QHBoxLayout()
        
        welcome_label = QLabel("Witaj w Menadżerze Depozytów Opon!")
        welcome_label.setObjectName("welcomeLabel")