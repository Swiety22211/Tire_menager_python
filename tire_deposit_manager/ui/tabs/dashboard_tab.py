#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka pulpitu - główny ekran aplikacji z podsumowaniem kluczowych informacji.
Wyświetla statystyki, wykresy i zapewnia szybki dostęp do najważniejszych funkcji.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QSpacerItem, QGraphicsDropShadowEffect, QScrollArea, QCalendarWidget,
    QComboBox, QStackedWidget, QLineEdit, QToolButton, QMenu
)
from PySide6.QtCore import (
    Qt, QSize, QDate, Signal, QTimer, QPropertyAnimation, 
    QEasingCurve, Property, QRect, QPoint
)
from PySide6.QtGui import (
    QIcon, QColor, QFont, QPainter, QPixmap, QPalette, QBrush, 
    QLinearGradient, QPen, QCursor, QAction,
)
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

#Definicja kolorów
DARK_COLORS = {
    'background': '#121212',       # Główne tło
    'card_background': '#1E1E1E',  # Tło ramek i kontenerów
    'text_primary': '#E0E0E0',     # Główny kolor tekstu
    'text_secondary': '#A0A0A0',   # Drugorzędny kolor tekstu
    'accent_blue': '#4A6CF7',      # Niebieski akcentowy
    'accent_green': '#3CA576',     # Zielony akcentowy
    'accent_red': '#DB7093',       # Czerwony/różowy akcentowy
    'border': '#333333',           # Kolor obramowań
    'hover': '#2C2C2C'             # Kolor przy najechaniu
}

class StatWidget(QFrame):
    """Widget do wyświetlania statystyk z animacją licznika."""
    
    clicked = Signal()  # Sygnał emitowany przy kliknięciu
    
    def __init__(self, title, value="0", icon_path=None, color="#4A6CF7", parent=None):
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
        self.setObjectName("statWidget")
        self.setStyleSheet(f"""
            QFrame#statWidget {{
                background-color: {color};
                border-radius: 12px;
                color: white;
                padding: 18px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            
            QFrame#statWidget QLabel {{
                background-color: rgba(0, 0, 0, 0);
                border-radius: 0px;
                padding: 0px;
            }}
            
            QFrame#statWidget:hover {{
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self._lighten_color(color, 40)}
                );
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
                transform: translateY(-5px);
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnej wysokości
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Nagłówek (ikona + tytuł)
        header_layout = QHBoxLayout()
        
        # Ikona jeśli podano
        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Opcjonalnie: lekko przyciemnij ikonę
            image = pixmap.toImage()
            for x in range(image.width()):
                for y in range(image.height()):
                    color = image.pixelColor(x, y)
                    if color.alpha() > 0:  # Jeśli piksel nie jest przezroczysty
                        color.setRgb(
                            max(0, color.red() - 50),
                            max(0, color.green() - 50), 
                            max(0, color.blue() - 50)
                        )
                        image.setPixelColor(x, y, color)
            
            pixmap = QPixmap.fromImage(image)
            self.icon_label.setPixmap(pixmap)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            background-color: rgba(0, 0, 0, 30);
            border-radius: 6px;
            padding: 5px;
        """)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Wartość
        self._current_value = 0
        self._target_value = int(value)
        self.value_label = QLabel("0")
        self.value_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.value_label.setStyleSheet("""
            color: white;
            margin-top: 5px;
            background-color: rgba(0, 0, 0, 30);
            border-radius: 6px;
            padding: 5px;
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Dodatkowy tekst informacyjny
        self.info_label = QLabel("Kliknij, aby zobaczyć szczegóły")
        self.info_label.setFont(QFont("Segoe UI", 9))
        self.info_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            background-color: rgba(0, 0, 0, 30);
            border-radius: 6px;
            padding: 5px;
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Ustawienie wskazówki
        self.setToolTip(f"Kliknij, aby zobaczyć szczegółowe informacje o {title.lower()}")
        
        # Animacja licznika
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_counter)
        self.timer.start(30)
        
        # Podłączenie zdarzenia kliknięcia
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _update_counter(self):
        """Aktualizuje animowany licznik."""
        if self._current_value < self._target_value:
            # Przyrost wartości (szybciej na początku, wolniej przy końcu)
            increment = max(1, int((self._target_value - self._current_value) / 10))
            self._current_value += increment
            if self._current_value > self._target_value:
                self._current_value = self._target_value
            
            # Aktualizacja wyświetlanej wartości
            self.value_label.setText(str(self._current_value))
        else:
            self.timer.stop()
            
    def set_value(self, new_value):
        """Ustawia nową wartość z animacją."""
        try:
            # Konwersja na int
            self._target_value = int(new_value)
            # Zresetuj timer jeśli został zatrzymany
            if not self.timer.isActive():
                self.timer.start(30)
        except (ValueError, TypeError):
            self.value_label.setText(str(new_value))
            
    def set_trend(self, percentage_change):
        """Ustawia informację o trendzie zmian."""
        if percentage_change > 0:
            trend_text = f"↑ +{percentage_change:.1f}% wzrost"
            trend_color = "rgba(46, 204, 113, 0.8)"
        elif percentage_change < 0:
            trend_text = f"↓ {percentage_change:.1f}% spadek"
            trend_color = "rgba(231, 76, 60, 0.8)"
        else:
            trend_text = "→ Bez zmian"
            trend_color = "rgba(255, 255, 255, 0.7)"
            
        self.info_label.setText(trend_text)
        self.info_label.setStyleSheet(f"color: {trend_color};")
    
    def set_info_text(self, text, color="rgba(255, 255, 255, 0.7)"):
        """Ustawia tekst informacyjny."""
        self.info_label.setText(text)
        self.info_label.setStyleSheet(f"color: {color};")
        
    def _lighten_color(self, color, amount=20):
        """Rozjaśnia kolor HEX o podaną wartość."""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def mousePressEvent(self, event):
        """Obsługa kliknięcia w widget."""
        super().mousePressEvent(event)
        # Emitujemy sygnał kliknięcia
        self.clicked.emit()

class ActionButton(QFrame):
    """Przycisk szybkiej akcji z ikoną."""
    
    clicked = Signal()  # Sygnał emitowany przy kliknięciu
    
    def __init__(self, title, icon_path, color="#3498db", parent=None):
        """
        Inicjalizacja przycisku akcji.
        
        Args:
            title (str): Tytuł przycisku
            icon_path (str): Ścieżka do ikony
            color (str, optional): Kolor tła w formacie HEX. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("actionButton")
        self.setStyleSheet(f"""
            QFrame#actionButton {{
                background-color: {color};
                border-radius: 10px;
                color: white;
                padding: 10px;
            }}
            
            QFrame#actionButton:hover {{
                background-color: {self._lighten_color(color)};
                border: 1px solid white;
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Układ widgetu
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Ikona
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title_label, 1)
        
        # Ustawienie wskazówki
        self.setToolTip(f"Kliknij, aby {title.lower()}")
        
        # Podłączenie zdarzenia kliknięcia
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _lighten_color(self, color, amount=20):
        """Rozjaśnia kolor HEX o podaną wartość."""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def mousePressEvent(self, event):
        """Obsługa kliknięcia w widget."""
        super().mousePressEvent(event)
        # Emitujemy sygnał kliknięcia
        self.clicked.emit()

class DashboardTab(QWidget):
    """
    Zakładka pulpitu wyświetlająca podsumowanie kluczowych informacji.
    """
    
    tab_change_requested = Signal(str)  # Sygnał do zmiany zakładki
    action_requested = Signal(str, object)  # Sygnał do wykonania akcji z opcjonalnym parametrem
    
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
        
        # Timer do automatycznego odświeżania danych co 5 minut
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # 5 minut = 300000 ms
        
        # Odświeżenie danych początkowych
        self.refresh_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        # Główny układ z marginesami
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 1. GÓRNA SEKCJA - powitanie, wyszukiwarka, data
        self.create_top_section(main_layout)
        
        # 2. ŚRODKOWA SEKCJA - statystyki i szybkie akcje
        self.create_middle_section(main_layout)
        
        # 3. DOLNA SEKCJA - wizyty i ostatnie działania
        self.create_bottom_section(main_layout)

        # Ustaw tło całego widgetu na ciemny kolor
        self.setStyleSheet(f"""
            DashboardTab {{
                background-color: {DARK_COLORS['background']};
                color: {DARK_COLORS['text_primary']};
            }}
        """)
    

    
    def create_frame(self):
        """Tworzy ramkę z cieniem."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {DARK_COLORS['card_background']};
                border-radius: 10px;
                padding: 10px;
                color: {DARK_COLORS['text_primary']};
                border: 1px solid {DARK_COLORS['border']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        frame.setGraphicsEffect(shadow)
        
        return frame
    
    def create_top_section(self, parent_layout):
        """Tworzy górną sekcję z powitaniem, wyszukiwarką i datą."""
        top_bar_layout = QHBoxLayout()
        
        # Panel powitalny
        welcome_frame = self.create_frame()
        welcome_layout = QHBoxLayout(welcome_frame)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(ICONS_DIR, "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        welcome_layout.addWidget(logo_label)
        
        # Tekst powitania
        greeting_layout = QVBoxLayout()
        
        # Dynamiczne powitanie zależne od pory dnia
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Dzień dobry!"
        elif hour < 18:
            greeting = "Witaj ponownie!"
        else:
            greeting = "Dobry wieczór!"
            
        welcome_label = QLabel(f"{greeting} Serwis Opon MATEO")
        welcome_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        welcome_label.setStyleSheet("color: #2c3e50;")
        greeting_layout.addWidget(welcome_label)
        
        # Dodajemy informację o dzisiejszych wizytach
        self.today_appointments_label = QLabel("Ładowanie danych...")
        self.today_appointments_label.setFont(QFont("Segoe UI", 10))
        self.today_appointments_label.setStyleSheet("color: #7f8c8d;")
        greeting_layout.addWidget(self.today_appointments_label)
        
        welcome_layout.addLayout(greeting_layout)
        top_bar_layout.addWidget(welcome_frame)
        
        # Wyszukiwarka
        search_frame = self.create_frame()
        search_layout = QHBoxLayout(search_frame)
        
        search_icon = QLabel()
        search_icon_path = os.path.join(ICONS_DIR, "search.png")
        if os.path.exists(search_icon_path):
            pixmap = QPixmap(search_icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            search_icon.setPixmap(pixmap)
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj klientów, opon, depozytów...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 5px;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        top_bar_layout.addWidget(search_frame)
        
        # Dzisiejsza data
        date_frame = self.create_frame()
        date_layout = QVBoxLayout(date_frame)
        date_layout.setAlignment(Qt.AlignCenter)
        
        now = datetime.now()
        
        # Dzień miesiąca (duży)
        day_label = QLabel(now.strftime("%d"))
        day_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        day_label.setStyleSheet("color: #e74c3c;")
        day_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(day_label)
        
        # Miesiąc i rok
        month_year_label = QLabel(now.strftime("%b %Y"))
        month_year_label.setFont(QFont("Segoe UI", 12))
        month_year_label.setStyleSheet("color: #7f8c8d;")
        month_year_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(month_year_label)
        
        # Dzień tygodnia (polskie nazwy)
        weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        weekday = weekdays[now.weekday()]
        weekday_label = QLabel(weekday)
        weekday_label.setFont(QFont("Segoe UI", 10))
        weekday_label.setStyleSheet("color: #7f8c8d;")
        weekday_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(weekday_label)
        
        top_bar_layout.addWidget(date_frame)
        
        # Dodanie układu do głównego layoutu
        parent_layout.addLayout(top_bar_layout)
    
    def create_middle_section(self, parent_layout):
        """Tworzy środkową sekcję z kafelkami statystyk i szybkimi akcjami."""
        middle_section_layout = QHBoxLayout()
        
        # 1. Kafelki statystyk (lewa strona)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        # Kafelek - Klienci
        self.clients_stat = StatWidget(
            "Klienci", "0",
            os.path.join(ICONS_DIR, "client.png"),
            "#3498db"
        )
        self.clients_stat.clicked.connect(lambda: self.tab_change_requested.emit("clients"))
        stats_grid.addWidget(self.clients_stat, 0, 0)
        
        # Kafelek - Depozyty
        self.deposits_stat = StatWidget(
            "Aktywne depozyty", "0",
            os.path.join(ICONS_DIR, "tire.png"),
            "#2ecc71"
        )
        self.deposits_stat.clicked.connect(lambda: self.tab_change_requested.emit("deposits"))
        stats_grid.addWidget(self.deposits_stat, 0, 1)
        
        # Kafelek - Opony na stanie
        self.inventory_stat = StatWidget(
            "Opony na stanie", "0",
            os.path.join(ICONS_DIR, "inventory.png"),
            "#f39c12"
        )
        self.inventory_stat.clicked.connect(lambda: self.tab_change_requested.emit("inventory"))
        stats_grid.addWidget(self.inventory_stat, 1, 0)
        
        # Kafelek - Nadchodzące wizyty
        self.appointments_stat = StatWidget(
            "Zaplanowane wizyty", "0",
            os.path.join(ICONS_DIR, "calendar.png"),
            "#e74c3c"
        )
        self.appointments_stat.clicked.connect(lambda: self.tab_change_requested.emit("schedule"))
        stats_grid.addWidget(self.appointments_stat, 1, 1)
        
        # Kafelek - Części/akcesoria
        self.parts_stat = StatWidget(
            "Części i akcesoria", "0",
            os.path.join(ICONS_DIR, "parts.png"),
            "#9b59b6"
        )
        self.parts_stat.clicked.connect(lambda: self.tab_change_requested.emit("parts"))
        stats_grid.addWidget(self.parts_stat, 2, 0, 1, 2)  # Zajmuje 2 kolumny
        
        middle_section_layout.addLayout(stats_grid, 3)  # Proporcja 3
        
        # 2. Przyciski szybkich akcji i wykresy (prawa strona)
        right_panel_layout = QVBoxLayout()
        
        # Przyciski szybkich akcji
        action_buttons_frame = self.create_frame()
        action_buttons_frame.setMinimumHeight(180)
        action_buttons_layout = QVBoxLayout(action_buttons_frame)
        
        # Tytuł sekcji
        actions_title = QLabel("Szybkie akcje")
        actions_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        actions_title.setStyleSheet("color: #2c3e50;")
        action_buttons_layout.addWidget(actions_title)
        
        # Siatka przycisków
        actions_grid = QGridLayout()
        actions_grid.setSpacing(10)
        
        # Przyciski
        add_client_btn = ActionButton("Dodaj klienta", os.path.join(ICONS_DIR, "add-client.png"), "#3498db")
        add_client_btn.clicked.connect(self.add_client)
        actions_grid.addWidget(add_client_btn, 0, 0)
        
        add_deposit_btn = ActionButton("Nowy depozyt", os.path.join(ICONS_DIR, "add.png"), "#2ecc71")
        add_deposit_btn.clicked.connect(self.add_deposit)
        actions_grid.addWidget(add_deposit_btn, 0, 1)
        
        add_appointment_btn = ActionButton("Zaplanuj wizytę", os.path.join(ICONS_DIR, "calendar.png"), "#e74c3c")
        add_appointment_btn.clicked.connect(self.add_appointment)
        actions_grid.addWidget(add_appointment_btn, 1, 0)
        
        generate_report_btn = ActionButton("Generuj raport", os.path.join(ICONS_DIR, "chart.png"), "#9b59b6")
        generate_report_btn.clicked.connect(self.generate_report)
        actions_grid.addWidget(generate_report_btn, 1, 1)
        
        action_buttons_layout.addLayout(actions_grid)
        right_panel_layout.addWidget(action_buttons_frame)
        
        # Wykres - Zajętość magazynu
        storage_chart_frame = self.create_frame()
        storage_chart_layout = QVBoxLayout(storage_chart_frame)
        
        storage_title = QLabel("Zajętość magazynu")
        storage_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        storage_title.setStyleSheet("color: #2c3e50;")
        storage_chart_layout.addWidget(storage_title)
        
        # Kontener na wykres
        self.storage_chart_container = QWidget()
        self.storage_chart_container.setMinimumHeight(150)
        self.storage_chart_layout = QVBoxLayout(self.storage_chart_container)
        storage_chart_layout.addWidget(self.storage_chart_container)
        
        right_panel_layout.addWidget(storage_chart_frame)
        
        middle_section_layout.addLayout(right_panel_layout, 2)  # Proporcja 2
        
        # Dodanie układu do głównego layoutu
        parent_layout.addLayout(middle_section_layout)
    
    def create_bottom_section(self, parent_layout):
        """Tworzy dolną sekcję z nadchodzącymi wizytami i ostatnimi działaniami."""
        bottom_section_layout = QHBoxLayout()
        
        # 1. Nadchodzące wizyty (lewa strona)
        appointments_frame = self.create_frame()
        appointments_layout = QVBoxLayout(appointments_frame)
        
        # Tytuł z przyciskiem "Zobacz wszystkie"
        appointments_header = QHBoxLayout()
        
        appointments_title = QLabel("Nadchodzące wizyty")
        appointments_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        appointments_title.setStyleSheet("color: #2c3e50;")
        appointments_header.addWidget(appointments_title)
        
        view_all_btn = QPushButton("Zobacz wszystkie")
        view_all_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3498db;
                border: none;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        view_all_btn.setCursor(QCursor(Qt.PointingHandCursor))
        view_all_btn.clicked.connect(lambda: self.tab_change_requested.emit("schedule"))
        appointments_header.addWidget(view_all_btn, alignment=Qt.AlignRight)
        
        appointments_layout.addLayout(appointments_header)
        
        # Tabela nadchodzących wizyt
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(4)
        self.appointments_table.setHorizontalHeaderLabels(["Klient", "Usługa", "Data i godzina", "Status"])
        self.appointments_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #3498db;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        # Ustawienia tabeli
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setShowGrid(False)
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointments_table.setAlternatingRowColors(True)
        
        self.appointments_table.doubleClicked.connect(self.view_appointment_details)
        
        appointments_layout.addWidget(self.appointments_table)
        
        bottom_section_layout.addWidget(appointments_frame)
        
        # 2. Ostatnie działania (prawa strona)
        activities_frame = self.create_frame()
        activities_layout = QVBoxLayout(activities_frame)
        
        # Tytuł z filtrem
        activities_header = QHBoxLayout()
        
        activities_title = QLabel("Ostatnie działania")
        activities_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        activities_title.setStyleSheet("color: #2c3e50;")
        activities_header.addWidget(activities_title)
        
        # Filtr typów działań
        self.activities_filter = QComboBox()
        self.activities_filter.addItems(["Wszystkie", "Klienci", "Depozyty", "Wizyty"])
        self.activities_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px 8px;
                min-width: 120px;
            }
        """)
        self.activities_filter.currentIndexChanged.connect(self.filter_activities)
        activities_header.addWidget(self.activities_filter, alignment=Qt.AlignRight)
        
        activities_layout.addLayout(activities_header)
        
        # Tabela ostatnich działań
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(4)
        self.activities_table.setHorizontalHeaderLabels(["Data", "Typ", "Opis", "Status"])
        self.activities_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3498db;
                padding: 5px;
                border: none;
                font-weight: bold;
                color: white;
            }
        """)
        
        # Ustawienia tabeli
        self.activities_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activities_table.setShowGrid(False)
        self.activities_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Data
        self.activities_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Typ
        self.activities_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Opis
        self.activities_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        self.activities_table.setAlternatingRowColors(True)
        
        self.activities_table.doubleClicked.connect(self.view_activity_details)
        
        activities_layout.addWidget(self.activities_table)
        
        bottom_section_layout.addWidget(activities_frame)
        
        # Dodanie układu do głównego layoutu
        parent_layout.addLayout(bottom_section_layout)
    
    def create_pie_chart(self, data, colors=None):
        """
        Tworzy wykres kołowy.
        
        Args:
            data (dict): Dane w formacie {etykieta: wartość}
            colors (list, optional): Lista kolorów. Domyślnie None.
            
        Returns:
            QChartView: Widget z wykresem
        """
        # Przygotowanie wykresu
        chart = QChart()
        chart.setTitle("")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Seria danych
        series = QPieSeries()
        
        # Domyślne kolory
        if colors is None:
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        
        # Suma wartości dla procentów
        total = sum(data.values())
        
        # Dodaj elementy do serii
        for i, (label, value) in enumerate(data.items()):
            slice = series.append(label, value)
            slice.setLabelVisible(True)
            
            # Oblicz procent
            if total > 0:
                percent = (value / total) * 100
                slice.setLabel(f"{label}: {percent:.1f}%")
            else:
                slice.setLabel(f"{label}: 0%")
                
            # Ustaw kolor
            slice.setBrush(QColor(colors[i % len(colors)]))
        
        chart.addSeries(series)
        
        # Utwórz widok wykresu
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    def refresh_data(self):
        """Odświeża dane na pulpicie."""
        try:
            cursor = self.conn.cursor()
            
            # ------------------------
            # 1. Aktualizacja statystyk
            # ------------------------
            
            # Liczba klientów
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]
            self.clients_stat.set_value(str(clients_count))
            
            # Sprawdź wzrost/spadek liczby klientów w ostatnim miesiącu
            try:
                # Pobierz datę ostatniej aktualizacji (zakładając, że mamy tabelę z historią)
                one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                # W prawdziwej implementacji powinniśmy sprawdzić historię
                # Na potrzeby przykładu używamy stałej wartości
                clients_growth = 5.2
                self.clients_stat.set_trend(clients_growth)
            except Exception as e:
                logger.warning(f"Błąd podczas obliczania trendu klientów: {e}")
                self.clients_stat.set_info_text("Kliknij, aby zobaczyć szczegóły")
            
            # Liczba aktywnych depozytów
            cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
            deposits_count = cursor.fetchone()[0]
            self.deposits_stat.set_value(str(deposits_count))
            
            # Przykładowy trend
            self.deposits_stat.set_trend(2.8)
            
            # Liczba opon na stanie
            try:
                cursor.execute("SELECT SUM(quantity) FROM inventory")
                inventory_count = cursor.fetchone()[0] or 0
                self.inventory_stat.set_value(str(inventory_count))
                
                # Przykładowy trend (spadek)
                self.inventory_stat.set_trend(-1.5)
            except Exception as e:
                logger.warning(f"Błąd podczas obliczania opon na stanie: {e}")
                self.inventory_stat.set_value("0")
                self.inventory_stat.set_info_text("Brak danych")
            
            # Liczba zaplanowanych wizyt
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_date >= ? AND status != 'Anulowana'
            """, (today.strftime("%Y-%m-%d"),))
            appointments_count = cursor.fetchone()[0]
            self.appointments_stat.set_value(str(appointments_count))
            
            # Przykładowy trend
            self.appointments_stat.set_trend(10.0)
            
            # Części i akcesoria
            try:
                cursor.execute("SELECT SUM(quantity) FROM parts")
                parts_count = cursor.fetchone()[0] or 0
                self.parts_stat.set_value(str(parts_count))
                
                # Sprawdź ile produktów ma stan poniżej minimum
                cursor.execute("SELECT COUNT(*) FROM parts WHERE quantity < minimum_quantity")
                low_stock_count = cursor.fetchone()[0]
                
                if low_stock_count > 0:
                    self.parts_stat.set_info_text(
                        f"{low_stock_count} produkt{'y' if 2 <= low_stock_count <= 4 else 'ów' if low_stock_count >= 5 else ''} poniżej minimalnego stanu",
                        "rgba(231, 76, 60, 0.8)"
                    )
                else:
                    self.parts_stat.set_info_text("Wszystkie stany magazynowe są optymalne", "rgba(46, 204, 113, 0.8)")
            except Exception as e:
                logger.warning(f"Błąd podczas obliczania części na stanie: {e}")
                self.parts_stat.set_value("0")
                self.parts_stat.set_info_text("Brak danych")
            
            # ------------------------
            # 2. Aktualizacja informacji o dzisiejszych wizytach
            # ------------------------
            today_str = today.strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_date = ? AND status != 'Anulowana'
            """, (today_str,))
            today_appointments = cursor.fetchone()[0]
            
            if today_appointments > 0:
                self.today_appointments_label.setText(
                    f"Masz {today_appointments} wizyt{'y' if 2 <= today_appointments <= 4 else '' if today_appointments == 1 else 'ę'} zaplanowanych na dzisiaj"
                )
            else:
                self.today_appointments_label.setText("Brak wizyt zaplanowanych na dzisiaj")
            
            # ------------------------
            # 3. Aktualizacja wykresu zajętości magazynu
            # ------------------------
            # Najpierw wyczyść układ wykresu
            for i in reversed(range(self.storage_chart_layout.count())): 
                self.storage_chart_layout.itemAt(i).widget().setParent(None)
            
            # Pobierz dane o zajętości magazynu
            try:
                cursor.execute("SELECT SUM(used) as used, SUM(capacity) as capacity FROM locations")
                storage_data = cursor.fetchone()
                
                if storage_data and storage_data[1]:
                    used = storage_data[0] or 0
                    capacity = storage_data[1]
                    free = max(0, capacity - used)
                    
                    # Tworzenie wykresu
                    chart_data = {"Zajęte": used, "Wolne": free}
                    chart = self.create_pie_chart(chart_data, ["#3498db", "#ecf0f1"])
                    self.storage_chart_layout.addWidget(chart)
                else:
                    # Brak danych - pusty wykres lub informacja
                    empty_label = QLabel("Brak danych o lokalizacjach magazynowych")
                    empty_label.setAlignment(Qt.AlignCenter)
                    empty_label.setStyleSheet("color: #7f8c8d;")
                    self.storage_chart_layout.addWidget(empty_label)
            except Exception as e:
                logger.warning(f"Błąd podczas obliczania zajętości magazynu: {e}")
                empty_label = QLabel("Wystąpił błąd podczas ładowania danych magazynowych")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("color: #e74c3c;")
                self.storage_chart_layout.addWidget(empty_label)
            
            # ------------------------
            # 4. Aktualizacja tabeli nadchodzących wizyt
            # ------------------------
            # Wyczyść tabelę
            self.appointments_table.setRowCount(0)
            
            # Pobierz najbliższe wizyty (dziś + jutro, maksymalnie 10)
            tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT a.id, c.name, a.service_type, a.appointment_date, a.appointment_time, a.status
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.appointment_date BETWEEN ? AND ? AND a.status != 'Anulowana'
                ORDER BY a.appointment_date ASC, a.appointment_time ASC
                LIMIT 10
            """, (today_str, tomorrow))
            
            appointments = cursor.fetchall()
            
            for row, (appointment_id, client_name, service_type, date, time, status) in enumerate(appointments):
                self.appointments_table.insertRow(row)
                
                # Formatowanie daty
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    if date_obj.date() == today:
                        date_str = f"Dzisiaj, {time}"
                    else:
                        date_str = f"Jutro, {time}"
                except ValueError:
                    date_str = f"{date}, {time}"
                
                # Dodaj dane do tabeli
                self.appointments_table.setItem(row, 0, QTableWidgetItem(client_name))
                self.appointments_table.setItem(row, 1, QTableWidgetItem(service_type))
                self.appointments_table.setItem(row, 2, QTableWidgetItem(date_str))
                
                # Status z kolorowym tłem
                status_item = QTableWidgetItem(status)
                
                if status == "Zaplanowana":
                    status_item.setBackground(QColor("#3498db"))
                    status_item.setForeground(QColor("white"))
                elif status == "W trakcie":
                    status_item.setBackground(QColor("#f39c12"))
                    status_item.setForeground(QColor("white"))
                elif status == "Zakończona":
                    status_item.setBackground(QColor("#2ecc71"))
                    status_item.setForeground(QColor("white"))
                
                self.appointments_table.setItem(row, 3, status_item)
                
                # Dodaj ID wizyty jako dane w wierszu
                self.appointments_table.setItem(row, 0, QTableWidgetItem(client_name)).setData(Qt.UserRole, appointment_id)
            
            # ------------------------
            # 5. Aktualizacja tabeli ostatnich działań
            # ------------------------
            self.load_recent_activities()
            
            logger.debug("Odświeżono dane na pulpicie")
            
        except Exception as e:
            logger.error(f"Błąd podczas odświeżania danych na pulpicie: {e}")
            NotificationManager.get_instance().show_notification(
                f"Wystąpił błąd podczas odświeżania danych: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def load_recent_activities(self):
        """Ładuje ostatnie działania z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Wyczyść tabelę
            self.activities_table.setRowCount(0)
            
            # Kategoria filtra
            filter_type = self.activities_filter.currentText()
            
            # Budowanie zapytania w zależności od filtra
            query_parts = []
            params = []
            
            # Pobranie ostatnich klientów
            if filter_type in ["Wszystkie", "Klienci"]:
                query_parts.append("""
                    SELECT 'Klient' as type, name as description, 'Dodano' as status, 
                           '2025-03-19' as date, id
                    FROM clients 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
            
            # Pobranie ostatnich wizyt
            if filter_type in ["Wszystkie", "Wizyty"]:
                query_parts.append("""
                    SELECT 'Wizyta' as type, service_type as description, status, 
                           appointment_date as date, id
                    FROM appointments
                    ORDER BY id DESC 
                    LIMIT 5
                """)
            
            # Pobranie ostatnich depozytów
            if filter_type in ["Wszystkie", "Depozyty"]:
                query_parts.append("""
                    SELECT 'Depozyt' as type, (tire_brand || ' ' || tire_size) as description, 
                           status, deposit_date as date, id
                    FROM deposits 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
            
            # Połączenie zapytań
            if query_parts:
                full_query = " UNION ALL ".join(query_parts) + " ORDER BY date DESC LIMIT 10"
                
                cursor.execute(full_query)
                activities = cursor.fetchall()
                
                for row, (type_action, description, status, date, item_id) in enumerate(activities):
                    self.activities_table.insertRow(row)
                    
                    # Formatowanie daty
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        date_str = date_obj.strftime("%d.%m.%Y")
                    except (ValueError, TypeError):
                        date_str = date
                    
                    # Dodaj dane do tabeli
                    self.activities_table.setItem(row, 0, QTableWidgetItem(date_str))
                    self.activities_table.setItem(row, 1, QTableWidgetItem(type_action))
                    self.activities_table.setItem(row, 2, QTableWidgetItem(description))
                    
                    # Status z kolorowym tłem
                    status_item = QTableWidgetItem(status)
                    
                    if status in ["Zakończona", "Aktywny", "Dodano"]:
                        status_item.setBackground(QColor("#e6f7ed"))  # Jasny zielony
                        status_item.setForeground(QColor("#2ecc71"))  # Zielony
                    elif status == "W trakcie":
                        status_item.setBackground(QColor("#fff8e6"))  # Jasny pomarańczowy
                        status_item.setForeground(QColor("#f39c12"))  # Pomarańczowy
                    elif status in ["Anulowana", "Przeterminowany"]:
                        status_item.setBackground(QColor("#fde9e9"))  # Jasny czerwony
                        status_item.setForeground(QColor("#e74c3c"))  # Czerwony
                    
                    self.activities_table.setItem(row, 3, status_item)
                    
                    # Zapisz typ i ID jako dane
                    self.activities_table.setItem(row, 0, QTableWidgetItem(date_str)).setData(Qt.UserRole, (type_action, item_id))
        
        except Exception as e:
            logger.error(f"Błąd podczas ładowania ostatnich działań: {e}")
            # Możemy wyświetlić komunikat błędu w tabeli
            self.activities_table.setRowCount(1)
            self.activities_table.setSpan(0, 0, 1, 4)
            error_item = QTableWidgetItem(f"Wystąpił błąd podczas ładowania danych: {str(e)}")
            error_item.setForeground(QColor("#e74c3c"))
            self.activities_table.setItem(0, 0, error_item)
    
    def filter_activities(self, index):
        """Filtruje ostatnie działania według wybranego typu."""
        self.load_recent_activities()
    
    def perform_search(self):
        """Obsługuje wyszukiwanie globalne."""
        search_text = self.search_input.text().strip()
        if not search_text:
            return
        
        # Wyświetlamy powiadomienie o wyszukiwaniu
        NotificationManager.get_instance().show_notification(
            f"Wyszukiwanie: {search_text}",
            NotificationTypes.INFO
        )
        
        # Przekierowujemy do odpowiedniej zakładki z parametrami wyszukiwania
        # W rzeczywistej implementacji powinno to być obsługiwane przez główne okno
        self.action_requested.emit("search", search_text)
    
    def add_client(self):
        """Obsługuje dodawanie nowego klienta."""
        self.action_requested.emit("add_client", None)
    
    def add_deposit(self):
        """Obsługuje dodawanie nowego depozytu."""
        self.action_requested.emit("add_deposit", None)
    
    def add_appointment(self):
        """Obsługuje dodawanie nowej wizyty."""
        self.action_requested.emit("add_appointment", None)
    
    def generate_report(self):
        """Obsługuje generowanie raportu."""
        # Tutaj można wyświetlić menu z wyborem typu raportu
        menu = QMenu(self)
        
        clients_report_action = QAction("Raport klientów", self)
        clients_report_action.triggered.connect(lambda: self.action_requested.emit("generate_report", "clients"))
        menu.addAction(clients_report_action)
        
        deposits_report_action = QAction("Raport depozytów", self)
        deposits_report_action.triggered.connect(lambda: self.action_requested.emit("generate_report", "deposits"))
        menu.addAction(deposits_report_action)
        
        inventory_report_action = QAction("Raport stanu magazynowego", self)
        inventory_report_action.triggered.connect(lambda: self.action_requested.emit("generate_report", "inventory"))
        menu.addAction(inventory_report_action)
        
        menu.exec(QCursor.pos())
    
    def view_appointment_details(self, index):
        """Obsługuje podgląd szczegółów wizyty."""
        row = index.row()
        item = self.appointments_table.item(row, 0)
        if item:
            appointment_id = item.data(Qt.UserRole)
            if appointment_id:
                self.action_requested.emit("view_appointment", appointment_id)
    
    def view_activity_details(self, index):
        """Obsługuje podgląd szczegółów działania."""
        row = index.row()
        item = self.activities_table.item(row, 0)
        if item:
            data = item.data(Qt.UserRole)
            if data:
                activity_type, item_id = data
                self.action_requested.emit("view_activity", (activity_type, item_id))