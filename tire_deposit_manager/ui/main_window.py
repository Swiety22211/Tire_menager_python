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
        
        # Inicjalizacja paska statusu - WAŻNE: najpierw utworzyć pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Aplikacja gotowa")
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Inicjalizacja ustawień
        self.settings = QSettings("TireDepositManager", "Settings")
        self.load_settings()
        
        # Inicjalizacja notyfikacji
        self.init_notification_system()
        
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
    
    def create_sidebar(self):
        """Tworzy boczny panel nawigacyjny."""
        # Ramka bocznego panelu - POSZERZONA
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebarFrame")
        self.sidebar_frame.setFixedWidth(240)  # Zwiększono szerokość z 200px na 240px
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 10)  # Dodano margines na dole
        sidebar_layout.setSpacing(10)  # Zwiększono odstęp między elementami
        
        # Logo i nazwa aplikacji - USUNIĘTO NIEBIESKIE TŁO
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setContentsMargins(20, 25, 20, 15)  # Większe marginesy
        
        # Logo - zmiana na logo.png z katalogu images
        logo_label = QLabel()
        logo_label.setObjectName("logoLabel")
        # Zmiana ścieżki do pliku logo
        logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        
        # Nazwa aplikacji - WIĘKSZA CZCIONKA
        app_title_label = QLabel("MENADŻER\nSERWISU OPON")
        app_title_label.setObjectName("appTitleLabel")
        app_title_label.setAlignment(Qt.AlignCenter)
        app_title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-top: 10px;")
        
        logo_layout.addWidget(logo_label, 0, Qt.AlignCenter)
        logo_layout.addWidget(app_title_label, 0, Qt.AlignCenter)
        
        sidebar_layout.addWidget(logo_widget)
        
        # Separator pod logo
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #34495e; max-height: 1px;")
        sidebar_layout.addWidget(separator)
        sidebar_layout.addSpacing(10)  # Odstęp po separatorze
        
        # Przyciski menu - WIĘKSZE I LEPIEJ WIDOCZNE
        menu_items = [
            {"icon": "🏠", "text": "Pulpit", "module": "dashboard"},
            {"icon": "📋", "text": "Zamówienia", "module": "orders"},
            {"icon": "👥", "text": "Klienci", "module": "clients"},
            {"icon": "🏢", "text": "Depozyty", "module": "deposits"},
            {"icon": "📦", "text": "Magazyn", "module": "inventory"},
            {"icon": "💰", "text": "Finanse", "module": "finances"},
            {"icon": "📊", "text": "Raporty", "module": "reports"},
            {"icon": "⚙️", "text": "Ustawienia", "module": "settings"}
        ]
        
        self.menu_buttons = {}
        
        for item in menu_items:
            btn = QPushButton(f"{item['icon']}  {item['text']}")  # Dodano dodatkową spację po ikonie
            btn.setObjectName("menuButton")
            btn.setProperty("module", item["module"])
            btn.setMinimumHeight(45)  # Zwiększono wysokość z 40 na 45
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
                    background-color: #34495e;
                }
                QPushButton[active="true"] {
                    background-color: #3498db;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(self.switch_module)
            sidebar_layout.addWidget(btn)
            self.menu_buttons[item["module"]] = btn
        
        sidebar_layout.addStretch()
        
        # Separator przed informacją o wersji
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #34495e; max-height: 1px;")
        sidebar_layout.addWidget(separator)
        sidebar_layout.addSpacing(5)  # Odstęp po separatorze
        
        # Informacje w stopce - WIĘKSZA CZCIONKA, bez dodatkowego tła
        version_label = QLabel("Wersja 2.1")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #95a5a6; margin: 10px 0; font-size: 13px; background-color: transparent;")
        sidebar_layout.addWidget(version_label)
        
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
        modules = ["deposits", "inventory", "finances", "reports"]
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
        header_frame.setMinimumHeight(70)  # Zwiększono wysokość z 60 na 70
        header_frame.setMaximumHeight(70)
        # Usunięcie tła pod nazwą zakładki
        header_frame.setStyleSheet("background: transparent;")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Tytuł - WIĘKSZA CZCIONKA
        self.title_label = QLabel("Pulpit")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: transparent;")  # Dodany transparent background
        
        # Wyszukiwarka - WIĘKSZA
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)  # Zwiększono odstęp
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("🔍 Szukaj")
        self.search_input.setMinimumWidth(300)  # Zwiększono szerokość z 250 na 300
        self.search_input.setMinimumHeight(35)  # Dodano minimalną wysokość
        
        # Przycisk szukaj
        self.search_button = QPushButton("Szukaj")
        self.search_button.setObjectName("searchButton")
        self.search_button.setMinimumHeight(35)
        self.search_button.clicked.connect(self.perform_search)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Wszystko", "Klienci", "Depozyty", "Opony", "Zamówienia"])
        self.search_type_combo.setMinimumHeight(35)  # Dodano minimalną wysokość
        self.search_type_combo.setMinimumWidth(120)  # Dodano minimalną szerokość
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)  # Dodanie przycisku "Szukaj"
        search_layout.addWidget(self.search_type_combo)
        
        # Przyciski akcji - WIĘKSZE
        self.add_button = QPushButton("+ Nowy")
        self.add_button.setObjectName("addButton")
        self.add_button.setMinimumHeight(35)  # Dodano minimalną wysokość
        self.add_button.setMinimumWidth(100)  # Dodano minimalną szerokość
        self.add_button.clicked.connect(self.show_add_menu)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setFixedSize(40, 35)  # Ustawiono stały rozmiar
        self.refresh_button.clicked.connect(self.refresh_data)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addLayout(search_layout)
        header_layout.addSpacing(10)  # Dodano odstęp między wyszukiwarką a przyciskami
        header_layout.addWidget(self.add_button)
        header_layout.addSpacing(5)  # Dodano odstęp między przyciskami
        header_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(header_frame)
    
    def create_footer(self, parent_layout):
        """Tworzy stopkę aplikacji."""
        footer_frame = QFrame()
        footer_frame.setObjectName("footer")
        footer_frame.setMinimumHeight(35)  # Zwiększono wysokość z 30 na 35
        footer_frame.setMaximumHeight(35)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(15, 0, 15, 0)  # Zwiększono marginesy boczne
        
        # Informacje w stopce - WIĘKSZA CZCIONKA
        self.records_label = QLabel("Depozyty: 0 | Klienci: 0 | Opony: 0")
        self.records_label.setStyleSheet("font-size: 13px;")  # Bezpośrednie ustawienie stylu
        
        # Elastyczne wypełnienie
        footer_layout.addWidget(self.records_label)
        footer_layout.addStretch(1)
        
        # Czas i data - WIĘKSZA CZCIONKA
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 13px;")  # Bezpośrednie ustawienie stylu
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
            "reports": 6,
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
            "reports": "Raporty",
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
            btn.setStyleSheet("")  # Wymusza odświeżenie stylu
        
        # Aktualizacja paska statusu
        self.status_bar.showMessage(f"Moduł: {module_title.get(module, module.capitalize())}")
    
    def perform_search(self):
        """Obsługuje wyszukiwanie po kliknięciu przycisku Szukaj."""
        search_text = self.search_input.text()
        self.global_search(search_text)
    
    def global_search(self, text):
        """Obsługuje globalne wyszukiwanie w aplikacji."""
        if len(text) >= 3:  # Rozpocznij wyszukiwanie po wpisaniu co najmniej 3 znaków
            search_type = self.search_type_combo.currentText()
            self.status_bar.showMessage(f"Wyszukiwanie '{text}' w zakładce: {search_type}")
            
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
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 15px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #3498db;
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
        self.status_bar.showMessage("Odświeżanie danych...")
        
        # Odświeżenie danych w aktywnej zakładce
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh_data') and callable(current_widget.refresh_data):
            current_widget.refresh_data()
        
        # Aktualizacja liczby rekordów
        self.update_record_counts()
        
        self.status_bar.showMessage("Dane zostały odświeżone", 3000)
        
        NotificationManager.get_instance().show_notification(
            "Dane zostały odświeżone.",
            NotificationTypes.SUCCESS,
            duration=3000
        )
    
    # Metody obsługi akcji
    def add_deposit(self):
        """Obsługa dodawania nowego depozytu."""
        self.status_bar.showMessage("Dodawanie nowego depozytu...", 3000)
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
        self.status_bar.showMessage("Dodawanie nowego zamówienia...", 3000)
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania zamówień nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_inventory_item(self):
        """Obsługa dodawania nowej opony do magazynu."""
        self.status_bar.showMessage("Dodawanie nowej opony do magazynu...", 3000)
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
        
        # Nadpisujemy niektóre style, aby pozbyć się niebieskiego tła pod logo i dodatkowych teł
        custom_style = get_style_sheet("Dark") + """
        QLabel#logoLabel {
            background-color: transparent;
            border-radius: 30px;
            min-width: 70px;
            max-width: 70px;
            min-height: 70px;
            max-height: 70px;
            margin: 15px auto;
        }
        
        QFrame#headerFrame {
            background: transparent;
            border-bottom: 1px solid #0c1419;
            min-height: 70px;
            max-height: 70px;
        }
        
        QLabel#titleLabel {
            font-size: 22px;
            font-weight: bold;
            color: #ecf0f1;
            background-color: transparent;
        }
        
        QFrame#footer {
            background-color: transparent;
            color: #95a5a6;
            min-height: 35px;
            max-height: 35px;
            border-top: 1px solid #0c1419;
            font-size: 13px;
        }
        
        QStatusBar {
            background-color: transparent;
            color: #95a5a6;
            min-height: 35px;
            font-size: 13px;
        }
        """
        
        self.setStyleSheet(custom_style)
        
        # Ustawienia czcionki
        font_family = self.settings.value("font_family", "Segoe UI")
        font_size = int(self.settings.value("font_size", 10))
        font = QFont(font_family, font_size)
        self.setFont(font)