#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Główne okno aplikacji Menadżer Serwisu Opon.
Zmodernizowana wersja interfejsu z nowoczesnym wyglądem.
"""

import os
import sys
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QPushButton, QLineEdit, QMenu, QDialog, 
    QMessageBox, QFileDialog, QStatusBar, QFrame, QSplashScreen,
    QComboBox, QStackedWidget, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QAction
from PySide6.QtCore import Qt, QSize, QTimer, QSettings, Signal, Slot

# Import własnych modułów aplikacji
from ui.tabs.dashboard_tab import DashboardTab
from ui.dialogs.settings_dialog import SettingsDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR, APP_DATA_DIR, DATABASE_PATH, BACKUP_DIR, resource_path

# Dodaj nową stałą dla katalogu images
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "images")

from utils.database import backup_database, restore_database, initialize_test_data
from utils.exporter import export_data_to_excel, export_data_to_pdf, export_data_to_csv
from ui.tabs.clients_tab import ClientsTab

# Logger
logger = logging.getLogger("TireDepositManager")

class MainWindow(QMainWindow):
    """Główne okno aplikacji Menadżer Serwisu Opon"""
    
    # Sygnały
    database_updated = Signal()  # Emitowany po aktualizacji bazy danych
    
    def __init__(self, db_connection):
        """
        Inicjalizacja głównego okna aplikacji.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Ustawienie czcionki
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Inicjalizacja ustawień
        self.settings = QSettings("TireDepositManager", "Settings")
        self.load_settings()
        
        # Inicjalizacja notyfikacji
        self.init_notification_system()

        # Test powiadomienia - DODAJ TE DWIE LINIE
        QTimer.singleShot(1000, lambda: NotificationManager.get_instance().show_notification(
            "Testowe powiadomienie - aplikacja uruchomiona!", NotificationTypes.SUCCESS, 5000))
        
        # Inicjalizacja timera do aktualizacji czasu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Aktualizacja co sekundę
        
        # Pokaż okno
        self.setup_window()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        # Ustawienia głównego okna
        self.setWindowTitle("Menadżer Serwisu Opon")
        self.setGeometry(100, 100, 1280, 800)
        self.setMinimumSize(1000, 700)  # Ustaw minimalny rozmiar okna
        
        # Główny widget i układ
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Główny układ poziomy
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Tworzenie panelu bocznego
        self.create_sidebar()
        
        # Tworzenie prawego panelu z zawartością
        self.create_content_panel()

    def showStatusMessage(self, message, timeout=0):
        """
        Wyświetla komunikat w stopce aplikacji.
        
        Args:
            message (str): Treść komunikatu
            timeout (int, optional): Czas wyświetlania w milisekundach. 
                                Domyślnie 0 (stały komunikat)
        """
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
            
            # Opcjonalne wyczyszczenie komunikatu po określonym czasie
            if timeout > 0:
                QTimer.singleShot(timeout, lambda: self.status_label.setText("Aplikacja gotowa"))

    def create_sidebar(self):
        """Tworzy boczny panel nawigacyjny."""
        # Ramka bocznego panelu
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebarFrame")
        self.sidebar_frame.setFixedWidth(240)  # Szerokość zgodna ze zrzutem ekranu
        # Dodajemy jednolite tło dla całego lewego paska
        self.sidebar_frame.setStyleSheet("background-color: #1a1d21;")
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)  # Usuwamy marginesy
        sidebar_layout.setSpacing(0)  # Usuwamy odstępy między elementami
        
        # Logo i nazwa aplikacji
        logo_widget = QWidget()
        
        # Użyj QHBoxLayout zamiast QVBoxLayout dla lepszego centrowania poziomego
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 25, 0, 15)  # Marginesy górny i dolny
        
        # Kontener na logo i tekst (układ pionowy)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)  # Wyrównanie zawartości do środka
        center_layout.setSpacing(10)  # Odstęp między logo a tekstem
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(Qt.AlignCenter)  # Wyrównanie zawartości etykiety
        
        # Ustawienie rozmiaru logo
        logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "logo.png"))
        if not logo_pixmap.isNull():
            # Zachowaj oryginalne proporcje obrazu
            logo_pixmap = logo_pixmap.scaled(320, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        
        # Nazwa aplikacji
        app_title_label = QLabel("MENADŻER\nSERWISU OPON")
        app_title_label.setObjectName("appTitleLabel")
        app_title_label.setAlignment(Qt.AlignCenter)
        app_title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        # Dodaj logo i etykietę do centralnego układu pionowego
        center_layout.addWidget(self.logo_label)
        center_layout.addWidget(app_title_label)
        
        # Dodaj centralny widget do poziomego layoutu, który automatycznie wycentruje zawartość
        logo_layout.addWidget(center_widget, 1, Qt.AlignCenter)
        
        # Dodaj widget logo do głównego layoutu sidebar
        sidebar_layout.addWidget(logo_widget)
        
        # Separator pod logo
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #2c3034; max-height: 1px;")
        sidebar_layout.addWidget(separator)
        
        # Menu - kontener
        menu_widget = QWidget()
        menu_widget.setObjectName("menuContainer")
        menu_widget.setStyleSheet("background-color: #1a1d21;") # To samo tło
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 10, 0, 10)
        menu_layout.setSpacing(0)
        
        # Przyciski menu
        menu_items = [
            {"icon": "🏠", "text": "Pulpit", "module": "dashboard"},
            {"icon": "📋", "text": "Zamówienia", "module": "orders"},
            {"icon": "👥", "text": "Klienci", "module": "clients"},
            {"icon": "🏢", "text": "Depozyty", "module": "deposits"},
            {"icon": "📦", "text": "Magazyn", "module": "inventory"},
            {"icon": "💰", "text": "Finanse", "module": "finances"},
            {"icon": "💲", "text": "Cennik", "module": "pricelist"},
            {"icon": "⚙️", "text": "Ustawienia", "module": "settings"}
        ]
        
        self.menu_buttons = {}
        
        for item in menu_items:
            btn = QPushButton(f"{item['icon']}  {item['text']}")
            btn.setObjectName("menuButton")
            btn.setProperty("module", item["module"])
            btn.setMinimumHeight(45)
            btn.setCursor(Qt.PointingHandCursor) # Dodanie kursora wskazującego
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 30px;
                    font-size: 15px;
                    border: none;
                    color: white;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #2c3034;
                }
                QPushButton[active="true"] {
                    background-color: #4dabf7;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(self.switch_module)
            menu_layout.addWidget(btn)
            self.menu_buttons[item["module"]] = btn
        
        menu_layout.addStretch()
        sidebar_layout.addWidget(menu_widget, 1)  # 1 = rozciąganie
        
        # Separator przed informacją o wersji
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #2c3034; max-height: 1px;")
        sidebar_layout.addWidget(separator)
        
        # Stopka w sidebar
        footer_widget = QWidget()
        footer_widget.setObjectName("sidebarFooter")
        footer_widget.setStyleSheet("background-color: #1a1d21;") # To samo tło
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 5, 0, 10)
        
        # Informacje w stopce
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(15, 0, 15, 0)
        
        version_label = QLabel("Serwis Opon MATEO © wersja 2.1")
        version_label.setAlignment(Qt.AlignRight)
        version_label.setStyleSheet("color: #95a5a6; font-size: 13px;")
        info_layout.addWidget(version_label, 1)  # 1 = stretch factor, aby wypełnić całą szerokość
        
        footer_layout.addWidget(info_widget)
        sidebar_layout.addWidget(footer_widget)
        
        # Dodanie panelu bocznego do głównego układu
        self.main_layout.addWidget(self.sidebar_frame)
    
    def create_content_panel(self):
        """Tworzy panel z główną zawartością aplikacji."""
        # Kontener na zawartość
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Pasek tytułowy/header
        self.create_header(content_layout)
        
        # Stos widgetów z modułami
        self.content_stack = QStackedWidget()
        
        # Dodanie modułów do stosu
        # Moduł Pulpit
        self.dashboard_tab = DashboardTab(self.conn)
        self.content_stack.addWidget(self.dashboard_tab)
        
        # Moduł Zamówienia (placeholder)
        orders_placeholder = QWidget()
        orders_layout = QVBoxLayout(orders_placeholder)
        orders_label = QLabel("Moduł Zamówienia - w budowie")
        orders_label.setAlignment(Qt.AlignCenter)
        orders_layout.addWidget(orders_label)
        self.content_stack.addWidget(orders_placeholder)
        
        # Moduł Klienci
        self.clients_tab = ClientsTab(self.conn)
        self.content_stack.addWidget(self.clients_tab)
        
        # Pozostałe moduły - placeholdery
        modules = ["deposits", "inventory", "finances", "pricelist"]
        for module in modules:
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel(f"Moduł {module.capitalize()} - w budowie")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            self.content_stack.addWidget(placeholder)
        
        # Moduł Ustawienia
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        self.content_stack.addWidget(settings_tab)
        
        content_layout.addWidget(self.content_stack)
        
        # Stopka
        self.create_footer(content_layout)
        
        # Dodanie kontenera zawartości do głównego układu
        self.main_layout.addWidget(content_container)
        
        # Ustawienie domyślnego modułu
        self.set_active_module("dashboard")
    
    def create_header(self, parent_layout):
        """Tworzy pasek nagłówkowy aplikacji."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setMinimumHeight(70)
        header_frame.setMaximumHeight(70)
        header_frame.setStyleSheet("background: transparent; border-bottom: 1px solid #2c3034;")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Tytuł
        self.title_label = QLabel("Pulpit")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ecf0f1;")
        
        # Wyszukiwarka
        search_container = QWidget()
        search_container.setFixedWidth(600)  # Stała szerokość dla lepszego wyrównania
        search_container.setStyleSheet("background: transparent;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        
        # Ikona lupy i pole wyszukiwania w jednym komponencie
        search_box = QFrame()
        search_box.setObjectName("searchBox")
        search_box.setFixedHeight(30)  # Zmniejszona wysokość z 35px na 30px
        search_box.setStyleSheet("""
            QFrame#searchBox {
                background-color: #2c3034;
                border-radius: 5px;
                min-height: 35px;
            }
        """)
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 10, 0)
        search_box_layout.setSpacing(5)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #bdc3c7; background: transparent;")
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Szukaj")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: white;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        
        search_box_layout.addWidget(search_icon)
        search_box_layout.addWidget(self.search_input)
        
        # Combobox filtrowania
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Wszystko", "Klienci", "Depozyty", "Opony", "Zamówienia"])
        self.search_type_combo.setMinimumHeight(30)
        self.search_type_combo.setFixedWidth(120)
        self.search_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2c3034;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 30px;
                max-height: 30px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            /* Style dla rozwiniętej listy */
            QComboBox QAbstractItemView {
                background-color: #2c3034;
                color: white;
                border: 1px solid #0c1419;
                selection-background-color: #4dabf7;
                selection-color: white;
                outline: 0px;  /* Usuwa niebieskie obramowanie po wybraniu */
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #34495e;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4dabf7;
            }
        """)
        
        search_layout.addWidget(search_box, 1)  # 1 = rozciąganie
        search_layout.addWidget(self.search_type_combo)
        
        # Przyciski akcji
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background: transparent;")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        # Przycisk dodawania
        self.add_button = QPushButton("+ Nowy")
        self.add_button.setObjectName("addButton")
        self.add_button.setFixedSize(100, 35)
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setStyleSheet("""
            QPushButton#addButton {
                background-color: #51cf66;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                min-height: 35px;
            }
            QPushButton#addButton:hover {
                background-color: #40c057;
            }
        """)
        self.add_button.clicked.connect(self.show_add_menu)
        
        # Przycisk odświeżania
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setFixedSize(40, 35)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.setStyleSheet("""
            QPushButton#refreshButton {
                background-color: #4dabf7;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                min-height: 35px;
            }
            QPushButton#refreshButton:hover {
                background-color: #339af0;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_data)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.refresh_button)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(search_container)
        header_layout.addWidget(buttons_container)
        
        parent_layout.addWidget(header_frame)
    
    # W metodzie create_footer()
    def create_footer(self, parent_layout):
        """Tworzy stopkę aplikacji."""
        footer_frame = QFrame()
        footer_frame.setObjectName("footer")
        footer_frame.setMinimumHeight(35)
        footer_frame.setMaximumHeight(35)
        footer_frame.setStyleSheet("background-color: transparent; border-top: 1px solid #2c3034;")
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(15, 0, 15, 0)
        
        # Informacje o rekordach
        self.records_label = QLabel("Depozyty: 124 | Klienci: 87 | Opony: 256")
        self.records_label.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        
        # Status - przeniesiemy tu komunikaty ze statusbara
        self.status_label = QLabel("Aplikacja gotowa")
        self.status_label.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        
        # Data i czas
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        
        # Dodanie wszystkich elementów do stopki
        footer_layout.addWidget(self.records_label)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.status_label)  # Nowy element
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.time_label)
        
        # Aktualizacja czasu
        self.update_time()
        
        parent_layout.addWidget(footer_frame)
    
    def init_notification_system(self):
        """Inicjalizacja systemu powiadomień."""
        self.notification_manager = NotificationManager.get_instance()
        self.notification_manager.set_parent(self)
    
    def setup_window(self):
        """Konfiguracja okna głównego."""
        # Ustawienie ikony aplikacji
        icon_path = os.path.join(ICONS_DIR, "app-icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Załadowanie rozmiaru i pozycji okna z ustawień
        if self.settings.contains("window/geometry"):
            self.restoreGeometry(self.settings.value("window/geometry"))
        
        if self.settings.contains("window/state"):
            self.restoreState(self.settings.value("window/state"))
    
    def update_time(self):
        """Aktualizuje czas w pasku statusu."""
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.time_label.setText(current_time)
        
        # Co minutę aktualizujemy statystyki
        if datetime.now().second == 0:
            self.update_record_counts()
    
    def update_record_counts(self):
        """Aktualizuje liczby rekordów w bazie danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz liczby rekordów
            try:
                cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
                active_deposits = cursor.fetchone()[0]
            except Exception:
                try:
                    cursor.execute("SELECT COUNT(*) FROM deposits")
                    active_deposits = cursor.fetchone()[0]
                except Exception:
                    active_deposits = 0
            
            try:
                cursor.execute("SELECT COUNT(*) FROM clients")
                clients = cursor.fetchone()[0]
            except Exception:
                clients = 0
            
            try:
                cursor.execute("SELECT COUNT(*) FROM inventory")
                inventory = cursor.fetchone()[0]
            except Exception:
                inventory = 0
            
            # Aktualizuj etykietę
            self.records_label.setText(
                f"Depozyty: {active_deposits} | "
                f"Klienci: {clients} | "
                f"Opony: {inventory}"
            )
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji liczby rekordów: {e}")
    
    def switch_module(self):
        """Przełącza aktywny moduł."""
        sender = self.sender()
        module = sender.property("module")
        self.set_active_module(module)
    
    def set_active_module(self, module):
        """Ustawia aktywny moduł."""
        # Mapowanie nazw modułów na indeksy w QStackedWidget
        module_index = {
            "dashboard": 0,
            "orders": 1,
            "clients": 2,
            "deposits": 3,
            "inventory": 4,
            "finances": 5,
            "pricelist": 6,
            "settings": 7
        }
        
        # Aktualizacja tytułu
        module_title = {
            "dashboard": "Pulpit",
            "orders": "Zamówienia",
            "clients": "Klienci",
            "deposits": "Depozyty",
            "inventory": "Magazyn",
            "finances": "Finanse",
            "pricelist": "Cennik",
            "settings": "Ustawienia"
        }
        
        if module in module_index:
            # Przełączenie widoku
            self.content_stack.setCurrentIndex(module_index[module])
            
            # Aktualizacja tytułu
            self.title_label.setText(module_title.get(module, ""))
            
            
            # Specjalne obsługa dla modułu ustawień
            if module == "settings":
                self.show_settings()
        
        # Aktualizacja wyglądu przycisków menu
        for m, btn in self.menu_buttons.items():
            btn.setProperty("active", m == module)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
        
        # Aktualizacja paska statusu
        self.showStatusMessage(f"Moduł: {module_title.get(module, module.capitalize())}")
    
    def perform_search(self):
        """Obsługuje wyszukiwanie po wpisaniu tekstu."""
        search_text = self.search_input.text()
        if len(search_text) >= 3:  # Rozpocznij wyszukiwanie po wpisaniu co najmniej 3 znaków
            self.global_search(search_text)
    
    def global_search(self, text):
        """Obsługuje globalne wyszukiwanie w aplikacji."""
        if len(text) >= 3:  # Rozpocznij wyszukiwanie po wpisaniu co najmniej 3 znaków
            search_type = self.search_type_combo.currentText()
            self.showStatusMessage(f"Wyszukiwanie '{text}' w zakładce: {search_type}")
            
            # Logowanie informacji o wyszukiwaniu
            logger.info(f"Wyszukiwanie: '{text}' w kategorii: {search_type}")
            
            # Identyfikacja aktywnego modułu
            current_module = None
            for module, btn in self.menu_buttons.items():
                if btn.property("active"):
                    current_module = module
                    break
            
            # Wykonanie wyszukiwania w zależności od typu
            if search_type == "Klienci" or (search_type == "Wszystko" and current_module == "clients"):
                # Przełącz na zakładkę klientów
                self.set_active_module("clients")
                # Wywołaj metodę wyszukiwania w module klientów
                if hasattr(self.clients_tab, 'search'):
                    self.clients_tab.search(text)
                    return
            
            # Wywołanie metody wyszukiwania w aktywnym module
            current_widget = self.content_stack.currentWidget()
            if hasattr(current_widget, 'search') and callable(current_widget.search):
                current_widget.search(text)
            else:
                # Jeśli bieżący moduł nie obsługuje wyszukiwania, pokaż komunikat
                NotificationManager.get_instance().show_notification(
                    f"Wyszukiwanie '{text}' w module {current_module} nie jest obsługiwane.",
                    NotificationTypes.WARNING,
                    duration=3000
                )
        else:
            # Komunikat o minimalnej długości tekstu
            NotificationManager.get_instance().show_notification(
                "Wprowadź co najmniej 3 znaki, aby rozpocząć wyszukiwanie.",
                NotificationTypes.INFO,
                duration=3000
            )
    
    def show_add_menu(self):
        """Wyświetla menu umożliwiające dodawanie nowych elementów."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c3034;
                color: white;
                border: 1px solid #1a1d21;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 15px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #4dabf7;
            }
        """)
        
        # Utworzenie akcji menu
        actions = [
            {"text": "Nowy depozyt", "icon": "add.png", "slot": self.add_deposit},
            {"text": "Nowy klient", "icon": "add-client.png", "slot": self.add_client},
            {"text": "Nowe zamówienie", "icon": "add-order.png", "slot": self.add_order},
            {"text": "Nowa opona na stanie", "icon": "add-tire.png", "slot": self.add_inventory_item}
        ]
        
        for action_info in actions:
            icon_path = os.path.join(ICONS_DIR, action_info["icon"])
            action = QAction(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), 
                            action_info["text"], self)
            action.triggered.connect(action_info["slot"])
            menu.addAction(action)
        
        # Wyświetlenie menu pod przyciskiem
        menu.exec(self.add_button.mapToGlobal(self.add_button.rect().bottomLeft()))
    
    def refresh_data(self):
            """Odświeża dane we wszystkich zakładkach."""
            self.showStatusMessage("Odświeżanie danych...")
            
            # Odświeżenie danych w aktywnej zakładce
            current_widget = self.content_stack.currentWidget()
            if hasattr(current_widget, 'refresh_data') and callable(current_widget.refresh_data):
                current_widget.refresh_data()
            
            # Aktualizacja liczby rekordów
            self.update_record_counts()
            
            self.showStatusMessage("Dane zostały odświeżone", 3000)
            
            NotificationManager.get_instance().show_notification(
                "Dane zostały odświeżone.",
                NotificationTypes.SUCCESS,
                duration=3000
            )
    
    # Metody obsługi akcji
    def add_deposit(self):
        """Obsługa dodawania nowego depozytu."""
        self.showStatusMessage("Dodawanie nowego depozytu...", 3000)
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania depozytów nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_client(self):
        """Obsługa dodawania nowego klienta."""
        from ui.dialogs.client_dialog import ClientDialog
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()
            NotificationManager.get_instance().show_notification(
                f"Dodano nowego klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS,
                duration=3000
            )
    
    def add_order(self):
        """Obsługa dodawania nowego zamówienia."""
        self.showStatusMessage("Dodawanie nowego zamówienia...", 3000)
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania zamówień nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_inventory_item(self):
        """Obsługa dodawania nowej opony do magazynu."""
        self.showStatusMessage("Dodawanie nowej opony do magazynu...", 3000)
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania opon do magazynu nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def show_settings(self):
        """Pokazuje okno dialogowe ustawień."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Zastosuj nowe ustawienia
            self.load_settings()
            NotificationManager.get_instance().show_notification(
                "Ustawienia zostały zapisane.",
                NotificationTypes.SUCCESS,
                duration=3000
            )
    
    def load_settings(self):
        """Ładuje ustawienia aplikacji."""
        # Ustawienia wyglądu
        theme = self.settings.value("theme", "Dark")
        
        # Niezależnie od wcześniejszego ustawienia, używamy ciemnego motywu
        self.settings.setValue("theme", "Dark")
        
        # Załaduj style z pliku styli
        from utils.styles import get_style_sheet
        
        # Aplikujemy globalne style
        self.setStyleSheet(get_style_sheet("Dark"))
        
        # Odświeżenie stylów poszczególnych komponentów
        self.update_component_styles()
        
        # Ustawienia czcionki
        font_family = self.settings.value("font_family", "Segoe UI")
        font_size = int(self.settings.value("font_size", 10))
        font = QFont(font_family, font_size)
        self.setFont(font)
    
    def update_component_styles(self):
        """Aktualizuje style poszczególnych komponentów interfejsu."""
        # Menu boczne - jednolite ciemne tło
        self.sidebar_frame.setStyleSheet("background-color: #1a1d21;")
        
        # Przyciski menu
        for module, btn in self.menu_buttons.items():
            # Odświeżenie stanu aktywności
            is_active = btn.property("active")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 30px;
                    font-size: 15px;
                    border: none;
                    color: white;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #2c3034;
                }
                QPushButton[active="true"] {
                    background-color: #4dabf7;
                    font-weight: bold;
                }
            """)
        
        # Pole wyszukiwania i przyciski
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: white;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        
        # Przyciski w górnym pasku
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
    
    # Metody do regulacji wielkości i pozycji logo
    def set_logo_size(self, size):
        """
        Pozwala na zmianę rozmiaru logo.
        
        Args:
            width (int): Szerokość logo w pikselach
            height (int, optional): Wysokość logo w pikselach. Jeśli nie podana, używana jest ta sama wartość co szerokość
        """
        if height is None:
            height = width
        #Zapamiętanie nowego rozmiaru
        self.logo_size = size

        # Aktualizacja stylów etykiety logo
        self.logo_label.setStyleSheet(f"""
            background-color: transparent;
            border-radius: 30px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
            margin: 15px auto;
        """) 

        #aktualizacja pixmapy
        logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(self.logo_size, self.logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        
    def set_logo_position(self, alignment):
        """
        Pozwala na zmianę pozycji logo.
        
        Args:
            alignment (Qt.AlignmentFlag): Flaga wyrównania Qt, np. Qt.AlignCenter, Qt.AlignLeft
        """
        if hasattr(self, 'logo_label'):
            logo_layout = self.logo_label.parent().layout()
            logo_layout.removeWidget(self.logo_label)
            logo_layout.addWidget(self.logo_label, 0, alignment)
    
    def closeEvent(self, event):
        """Obsługuje zdarzenie zamknięcia okna."""
        # Zapisanie rozmiaru i pozycji okna
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        
        # Zapytanie o potwierdzenie zamknięcia aplikacji
        reply = QMessageBox.question(
            self, 'Zamykanie aplikacji',
            "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Zamknięcie połączenia z bazą danych
            if self.conn:
                try:
                    self.conn.close()
                    logger.info("Połączenie z bazą danych zostało zamknięte")
                except Exception as e:
                    logger.error(f"Błąd podczas zamykania połączenia z bazą danych: {e}")
            
            # Zamknięcie aplikacji
            event.accept()
        else:
            event.ignore()