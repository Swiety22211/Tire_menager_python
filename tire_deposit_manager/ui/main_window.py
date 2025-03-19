#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Główne okno aplikacji Menadżer Depozytów Opon.
Ujednolicona i rozszerzona wersja łącząca najlepsze elementy z dotychczasowych implementacji.
"""

import os
import sys
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QPushButton, QLineEdit, QMenu, QDialog, 
    QMessageBox, QFileDialog, QStatusBar, QFrame, QSplashScreen,
    QComboBox
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QAction
from PySide6.QtCore import Qt, QSize, QTimer, QSettings, Signal, Slot

# Import własnych modułów aplikacji
from ui.tabs.dashboard_tab import DashboardTab
from ui.dialogs.settings_dialog import SettingsDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR, APP_DATA_DIR, DATABASE_PATH, BACKUP_DIR, resource_path
from utils.database import backup_database, restore_database, initialize_test_data
from utils.exporter import export_data_to_excel, export_data_to_pdf, export_data_to_csv
from utils.styles import STYLE_SHEET

# Logger
logger = logging.getLogger("TireDepositManager")

class MainWindow(QMainWindow):
    """Główne okno aplikacji z zakładkami i paskiem menu."""
    
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
        
        # Ustawienie globalnego arkusza stylów
        self.setStyleSheet(STYLE_SHEET)
        
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
        
        # Inicjalizacja timera do aktualizacji czasu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Aktualizacja co sekundę
        
        # Pokaż okno
        self.setup_window()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        # Ustawienia głównego okna
        self.setWindowTitle("Menadżer Depozytów Opon")
        self.setGeometry(100, 100, 1280, 800)
        
        # Główny widget i układ
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Pasek narzędzi
        self.create_toolbar()
        
        # Główne zakładki
        self.create_tabs()
        
        # Pasek statusu
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Aplikacja gotowa")
        
        # Pasek menu
        self.create_menu()
        
        # Stopka aplikacji
        self.create_footer()
        
    def create_toolbar(self):
        """Tworzy pasek narzędzi z wyszukiwarką i przyciskami akcji."""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo aplikacji
        logo_label = QLabel()
        logo_path = os.path.join(ICONS_DIR, "logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        toolbar_layout.addWidget(logo_label)
        
        # Tytuł aplikacji
        title_label = QLabel("Menadżer Depozytów Opon")
        title_label.setObjectName("headerLabel")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addSpacing(20)
        
        # Globalne pole wyszukiwania
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Szukaj (klienci, depozyty, opony...)")
        self.search_input.textChanged.connect(self.global_search)
        self.search_input.setMinimumWidth(300)
        toolbar_layout.addWidget(self.search_input, 1)  # 1 to stretch factor
        
        # Typ wyszukiwania
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Wszystko", "Klienci", "Depozyty", "Opony", "Zamówienia"])
        toolbar_layout.addWidget(self.search_type_combo)
        
        # Przyciski narzędziowe
        self.add_button = QPushButton("Nowy")
        self.add_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add.png")))
        self.add_button.clicked.connect(self.show_add_menu)
        toolbar_layout.addWidget(self.add_button)
        
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.png")))
        self.refresh_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.settings_button = QPushButton("Ustawienia")
        self.settings_button.setIcon(QIcon(os.path.join(ICONS_DIR, "settings.png")))
        self.settings_button.clicked.connect(self.show_settings)
        toolbar_layout.addWidget(self.settings_button)
        
        self.main_layout.addWidget(toolbar_widget)
        
        # Dodaj separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #bdc3c7;")
        self.main_layout.addWidget(separator)
    
    def create_tabs(self):
        """Tworzy główne zakładki aplikacji."""
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Zakładka pulpitu
        self.dashboard_tab = DashboardTab(self.conn)
        self.tabs.addTab(self.dashboard_tab, QIcon(os.path.join(ICONS_DIR, "dashboard.png")), "Pulpit")
        
        # Tymczasowe zakładki-zaślepki (należy je zaimplementować w rzeczywistej aplikacji)
        # W pełnej implementacji należy zastąpić te placeholdery prawdziwymi klasami
        
        # Zakładka depozytów
        self.deposits_tab = QWidget()  # Placeholder - powinno być DepositsTab(self.conn)
        self.tabs.addTab(self.deposits_tab, QIcon(os.path.join(ICONS_DIR, "tire.png")), "Depozyty")
        
        # Zakładka klientów
        self.clients_tab = QWidget()  # Placeholder - powinno być ClientsTab(self.conn)
        self.tabs.addTab(self.clients_tab, QIcon(os.path.join(ICONS_DIR, "client.png")), "Klienci")
        
        # Zakładka zamówień
        self.orders_tab = QWidget()  # Placeholder - powinno być OrdersTab(self.conn)
        self.tabs.addTab(self.orders_tab, QIcon(os.path.join(ICONS_DIR, "order.png")), "Zamówienia")
        
        # Zakładka magazynu
        self.inventory_tab = QWidget()  # Placeholder - powinno być InventoryTab(self.conn)
        self.tabs.addTab(self.inventory_tab, QIcon(os.path.join(ICONS_DIR, "inventory.png")), "Opony na stanie")
        
        # Zakładka części/akcesoriów
        self.parts_tab = QWidget()  # Placeholder - powinno być PartsTab(self.conn)
        self.tabs.addTab(self.parts_tab, QIcon(os.path.join(ICONS_DIR, "parts.png")), "Części i akcesoria")
        
        # Zakładka harmonogramu
        self.schedule_tab = QWidget()  # Placeholder - powinno być ScheduleTab(self.conn)
        self.tabs.addTab(self.schedule_tab, QIcon(os.path.join(ICONS_DIR, "calendar.png")), "Harmonogram")
        
        # Zakładka statystyk
        self.statistics_tab = QWidget()  # Placeholder - powinno być StatisticsTab(self.conn)
        self.tabs.addTab(self.statistics_tab, QIcon(os.path.join(ICONS_DIR, "chart.png")), "Statystyki")
        
        # Połączenie sygnału zmiany zakładki
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.main_layout.addWidget(self.tabs)
    
    def create_menu(self):
        """Tworzy menu główne aplikacji."""
        menubar = self.menuBar()
        
        # Menu Plik
        file_menu = menubar.addMenu("&Plik")
        
        # Podmenu Nowy
        new_menu = QMenu("Nowy", self)
        new_deposit_action = QAction(QIcon(os.path.join(ICONS_DIR, "add.png")), "Depozyt", self)
        new_deposit_action.triggered.connect(self.add_deposit)
        new_menu.addAction(new_deposit_action)
        
        new_client_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-client.png")), "Klient", self)
        new_client_action.triggered.connect(self.add_client)
        new_menu.addAction(new_client_action)
        
        new_order_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-order.png")), "Zamówienie", self)
        new_order_action.triggered.connect(self.add_order)
        new_menu.addAction(new_order_action)
        
        new_inventory_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-tire.png")), "Opona na stanie", self)
        new_inventory_action.triggered.connect(self.add_inventory_item)
        new_menu.addAction(new_inventory_action)
        
        new_part_action = QAction(QIcon(os.path.join(ICONS_DIR, "parts.png")), "Część/akcesorium", self)
        new_part_action.triggered.connect(self.add_part)
        new_menu.addAction(new_part_action)
        
        new_appointment_action = QAction(QIcon(os.path.join(ICONS_DIR, "calendar.png")), "Wizyta", self)
        new_appointment_action.triggered.connect(self.add_appointment)
        new_menu.addAction(new_appointment_action)
        
        file_menu.addMenu(new_menu)
        
        file_menu.addSeparator()
        
        # Import i eksport
        import_menu = QMenu("Importuj dane", self)
        
        import_excel_action = QAction(QIcon(os.path.join(ICONS_DIR, "excel.png")), "Z pliku Excel", self)
        import_excel_action.triggered.connect(self.import_from_excel)
        import_menu.addAction(import_excel_action)
        
        import_csv_action = QAction(QIcon(os.path.join(ICONS_DIR, "csv.png")), "Z pliku CSV", self)
        import_csv_action.triggered.connect(self.import_from_csv)
        import_menu.addAction(import_csv_action)
        
        file_menu.addMenu(import_menu)
        
        export_menu = QMenu("Eksportuj dane", self)
        
        export_excel_action = QAction(QIcon(os.path.join(ICONS_DIR, "excel.png")), "Do pliku Excel", self)
        export_excel_action.triggered.connect(self.export_to_excel)
        export_menu.addAction(export_excel_action)
        
        export_csv_action = QAction(QIcon(os.path.join(ICONS_DIR, "csv.png")), "Do pliku CSV", self)
        export_csv_action.triggered.connect(self.export_to_csv)
        export_menu.addAction(export_csv_action)
        
        export_pdf_action = QAction(QIcon(os.path.join(ICONS_DIR, "pdf.png")), "Do pliku PDF", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        export_menu.addAction(export_pdf_action)
        
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        # Kopia zapasowa
        backup_action = QAction(QIcon(os.path.join(ICONS_DIR, "backup.png")), "Utwórz kopię zapasową", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        restore_action = QAction(QIcon(os.path.join(ICONS_DIR, "restore.png")), "Przywróć z kopii", self)
        restore_action.triggered.connect(self.restore_from_backup)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        # Wyjście
        exit_action = QAction(QIcon(os.path.join(ICONS_DIR, "exit.png")), "Zakończ", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Edycja
        edit_menu = menubar.addMenu("&Edycja")
        
        refresh_action = QAction(QIcon(os.path.join(ICONS_DIR, "refresh.png")), "Odśwież wszystko", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        edit_menu.addAction(refresh_action)
        
        edit_menu.addSeparator()
        
        # Menu Narzędzia
        tools_menu = menubar.addMenu("&Narzędzia")
        
        settings_action = QAction(QIcon(os.path.join(ICONS_DIR, "settings.png")), "Ustawienia", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        locations_action = QAction("Zarządzaj lokalizacjami", self)
        locations_action.triggered.connect(self.manage_locations)
        tools_menu.addAction(locations_action)
        
        templates_action = QAction("Zarządzaj szablonami", self)
        templates_action.triggered.connect(self.manage_templates)
        tools_menu.addAction(templates_action)
        
        tools_menu.addSeparator()
        
        notifications_action = QAction("Zarządzaj powiadomieniami", self)
        notifications_action.triggered.connect(self.manage_notifications)
        tools_menu.addAction(notifications_action)
        
        barcode_action = QAction("Generator kodów kreskowych", self)
        barcode_action.triggered.connect(self.show_barcode_generator)
        tools_menu.addAction(barcode_action)
        
        tools_menu.addSeparator()
        
        view_logs_action = QAction("Pokaż logi aplikacji", self)
        view_logs_action.triggered.connect(self.view_logs)
        tools_menu.addAction(view_logs_action)
        
        # Menu Pomoc
        help_menu = menubar.addMenu("Pomo&c")
        
        help_action = QAction(QIcon(os.path.join(ICONS_DIR, "help.png")), "Pomoc", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_footer(self):
        """Tworzy stopkę aplikacji z datą i czasem."""
        footer_widget = QFrame()
        footer_widget.setObjectName("footer")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        # Informacje po lewej
        version_label = QLabel("Wersja 2.1")
        footer_layout.addWidget(version_label)
        
        # Elastyczne wypełnienie
        footer_layout.addStretch(1)
        
        # Liczba rekordów
        self.records_label = QLabel("Depozyty: 0 | Klienci: 0 | Opony na stanie: 0")
        footer_layout.addWidget(self.records_label)
        
        # Czas i data
        self.time_label = QLabel()
        footer_layout.addWidget(self.time_label)
        
        # Aktualizacja czasu
        self.update_time()
        
        # Dodanie stopki do głównego układu
        self.main_layout.addWidget(footer_widget)
    
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

# Pobierz dodatkowe liczniki dla nowych modułów
            try:
                cursor.execute("SELECT COUNT(*) FROM parts")
                parts = cursor.fetchone()[0]
            except Exception:
                parts = 0

            try:
                cursor.execute("SELECT COUNT(*) FROM appointments WHERE status != 'Anulowana'")
                appointments = cursor.fetchone()[0]
            except Exception:
                appointments = 0
            
            # Aktualizuj etykietę
            self.records_label.setText(
                f"Depozyty: {active_deposits} | "
                f"Klienci: {clients} | "
                f"Opony: {inventory} | "
                f"Części: {parts} | "
                f"Wizyty: {appointments}"
            )
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji liczby rekordów: {e}")
    
    def on_tab_changed(self, index):
        """Obsługuje zmianę aktywnej zakładki."""
        # Aktualizacja danych w aktywnej zakładce
        current_tab = self.tabs.widget(index)
        if hasattr(current_tab, 'refresh_data'):
            current_tab.refresh_data()
    
    def global_search(self, text):
        """Obsługuje globalne wyszukiwanie w aplikacji."""
        if len(text) >= 3:  # Rozpocznij wyszukiwanie po wpisaniu co najmniej 3 znaków
            search_type = self.search_type_combo.currentText()
            
            # W rzeczywistej aplikacji powinny być zaimplementowane wszystkie zakładki
            # i metody wyszukiwania
            # Tutaj obsługujemy tylko pulpit jako przykład
            if search_type == "Wszystko" or search_type == "Klienci":
                self.statusBar.showMessage(f"Wyszukiwanie '{text}' w zakładce: {search_type}")
                
                # W rzeczywistości należałoby aktywować odpowiednią zakładkę
                # i wywołać metodę wyszukiwania
                # Przykład dla pulpitu:
                if hasattr(self.dashboard_tab, 'refresh_data'):
                    self.dashboard_tab.refresh_data()
    
    def show_add_menu(self):
        """Wyświetla menu umożliwiające dodawanie nowych elementów."""
        menu = QMenu(self)
        
        add_deposit_action = QAction(QIcon(os.path.join(ICONS_DIR, "add.png")), "Nowy depozyt", self)
        add_deposit_action.triggered.connect(self.add_deposit)
        menu.addAction(add_deposit_action)
        
        add_client_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-client.png")), "Nowy klient", self)
        add_client_action.triggered.connect(self.add_client)
        menu.addAction(add_client_action)
        
        add_order_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-order.png")), "Nowe zamówienie", self)
        add_order_action.triggered.connect(self.add_order)
        menu.addAction(add_order_action)
        
        add_inventory_action = QAction(QIcon(os.path.join(ICONS_DIR, "add-tire.png")), "Nowa opona na stanie", self)
        add_inventory_action.triggered.connect(self.add_inventory_item)
        menu.addAction(add_inventory_action)
        
        add_part_action = QAction(QIcon(os.path.join(ICONS_DIR, "parts.png")), "Dodaj część/akcesorium", self)
        add_part_action.triggered.connect(self.add_part)
        menu.addAction(add_part_action)
        
        add_appointment_action = QAction(QIcon(os.path.join(ICONS_DIR, "calendar.png")), "Nowa wizyta", self)
        add_appointment_action.triggered.connect(self.add_appointment)
        menu.addAction(add_appointment_action)
        
        # Wyświetlenie menu pod przyciskiem
        menu.exec(self.add_button.mapToGlobal(self.add_button.rect().bottomLeft()))
    
    def refresh_data(self):
        """Odświeża dane we wszystkich zakładkach."""
        # Informacja o rozpoczęciu odświeżania
        self.statusBar.showMessage("Odświeżanie danych...")
        
        # Odświeżenie danych w każdej zakładce
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'refresh_data'):
                tab.refresh_data()
        
        # Aktualizacja liczby rekordów
        self.update_record_counts()
        
        # Informacja o zakończeniu odświeżania
        self.statusBar.showMessage("Dane zostały odświeżone", 3000)
        
        # Powiadomienie
        NotificationManager.get_instance().show_notification(
            "Wszystkie dane zostały odświeżone.",
            NotificationTypes.SUCCESS,
            duration=3000
        )
    
    def show_settings(self):
        """Pokazuje okno dialogowe ustawień."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Zastosuj nowe ustawienia
            self.load_settings()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                "Ustawienia zostały zapisane.",
                NotificationTypes.SUCCESS,
                duration=3000
            )

    # Metody obsługi elementów menu i przycisków
    
    def add_deposit(self):
        """Obsługa dodawania nowego depozytu."""
        # W rzeczywistej aplikacji należałoby zaimplementować zakładkę depozytów
        # i wywołać odpowiednią metodę
        self.statusBar.showMessage("Dodawanie nowego depozytu...", 3000)
        
        # Przykładowe powiadomienie
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
            # Odświeżenie danych
            self.refresh_data()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Dodano nowego klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS,
                duration=3000
            )
    
    def add_order(self):
        """Obsługa dodawania nowego zamówienia."""
        self.statusBar.showMessage("Dodawanie nowego zamówienia...", 3000)
        
        # Przykładowe powiadomienie
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania zamówień nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_inventory_item(self):
        """Obsługa dodawania nowej opony do magazynu."""
        self.statusBar.showMessage("Dodawanie nowej opony do magazynu...", 3000)
        
        # Przykładowe powiadomienie
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania opon do magazynu nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_part(self):
        """Obsługa dodawania nowej części/akcesorium."""
        self.statusBar.showMessage("Dodawanie nowej części/akcesorium...", 3000)
        
        # Przykładowe powiadomienie
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania części/akcesoriów nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def add_appointment(self):
        """Obsługa dodawania nowej wizyty."""
        self.statusBar.showMessage("Dodawanie nowej wizyty...", 3000)
        
        # Przykładowe powiadomienie
        NotificationManager.get_instance().show_notification(
            "Funkcja dodawania wizyt nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def import_from_excel(self):
        """Importuje dane z pliku Excel."""
        try:
            # Wybór pliku
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Wybierz plik Excel",
                "",
                "Pliki Excel (*.xlsx *.xls)"
            )
            
            if file_path:
                # Przykładowe powiadomienie (bez faktycznej implementacji importu)
                NotificationManager.get_instance().show_notification(
                    "Funkcja importu z Excela nie jest jeszcze w pełni zaimplementowana.",
                    NotificationTypes.WARNING,
                    duration=3000
                )
                
                # W rzeczywistej aplikacji
                # Należałoby dodać dialog wyboru typu danych i zaimplementować import
                
        except Exception as e:
            logger.error(f"Błąd podczas importu danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd importu",
                f"Wystąpił błąd podczas importowania danych:\n{str(e)}"
            )
    
    def import_from_csv(self):
        """Importuje dane z pliku CSV."""
        try:
            # Wybór pliku
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Wybierz plik CSV",
                "",
                "Pliki CSV (*.csv)"
            )
            
            if file_path:
                # Przykładowe powiadomienie (bez faktycznej implementacji importu)
                NotificationManager.get_instance().show_notification(
                    "Funkcja importu z CSV nie jest jeszcze w pełni zaimplementowana.",
                    NotificationTypes.WARNING,
                    duration=3000
                )
                
                # W rzeczywistej aplikacji
                # Należałoby dodać dialog wyboru typu danych i zaimplementować import
                
        except Exception as e:
            logger.error(f"Błąd podczas importu danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd importu",
                f"Wystąpił błąd podczas importowania danych:\n{str(e)}"
            )
    
    def export_to_excel(self):
        """Eksportuje dane do pliku Excel."""
        try:
            # Przykładowe powiadomienie (bez faktycznej implementacji eksportu)
            NotificationManager.get_instance().show_notification(
                "Funkcja eksportu do Excela nie jest jeszcze w pełni zaimplementowana.",
                NotificationTypes.WARNING,
                duration=3000
            )
            
            # W rzeczywistej aplikacji
            # Należałoby dodać dialog wyboru typu danych i zaimplementować eksport
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd eksportu",
                f"Wystąpił błąd podczas eksportowania danych:\n{str(e)}"
            )
    
    def export_to_csv(self):
        """Eksportuje dane do pliku CSV."""
        try:
            # Przykładowe powiadomienie (bez faktycznej implementacji eksportu)
            NotificationManager.get_instance().show_notification(
                "Funkcja eksportu do CSV nie jest jeszcze w pełni zaimplementowana.",
                NotificationTypes.WARNING,
                duration=3000
            )
            
            # W rzeczywistej aplikacji
            # Należałoby dodać dialog wyboru typu danych i zaimplementować eksport
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd eksportu",
                f"Wystąpił błąd podczas eksportowania danych:\n{str(e)}"
            )
    
    def export_to_pdf(self):
        """Eksportuje dane do pliku PDF."""
        try:
            # Przykładowe powiadomienie (bez faktycznej implementacji eksportu)
            NotificationManager.get_instance().show_notification(
                "Funkcja eksportu do PDF nie jest jeszcze w pełni zaimplementowana.",
                NotificationTypes.WARNING,
                duration=3000
            )
            
            # W rzeczywistej aplikacji
            # Należałoby dodać dialog wyboru typu danych i zaimplementować eksport
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd eksportu",
                f"Wystąpił błąd podczas eksportowania danych:\n{str(e)}"
            )
    
    def create_backup(self):
        """Tworzy kopię zapasową bazy danych."""
        try:
            # Tworzenie katalogu kopii zapasowych, jeśli nie istnieje
            os.makedirs(BACKUP_DIR, exist_ok=True)
            
            # Standardowa nazwa pliku z datą i czasem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"backup_{timestamp}.db"
            
            # Okno wyboru pliku
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz kopię zapasową",
                os.path.join(BACKUP_DIR, default_filename),
                "Bazy danych (*.db)"
            )
            
            if file_path:
                # Tworzenie kopii zapasowej
                result = backup_database(self.conn, file_path)
                
                if result:
                    # Powiadomienie o sukcesie
                    NotificationManager.get_instance().show_notification(
                        f"Kopia zapasowa została utworzona: {os.path.basename(file_path)}",
                        NotificationTypes.SUCCESS,
                        duration=5000
                    )
                else:
                    # Powiadomienie o błędzie
                    NotificationManager.get_instance().show_notification(
                        "Nie udało się utworzyć kopii zapasowej.",
                        NotificationTypes.ERROR,
                        duration=5000
                    )
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia kopii zapasowej: {e}")
            QMessageBox.critical(
                self,
                "Błąd kopii zapasowej",
                f"Wystąpił błąd podczas tworzenia kopii zapasowej:\n{str(e)}"
            )
    
    def restore_from_backup(self):
        """Przywraca bazę danych z kopii zapasowej."""
        try:
            # Okno wyboru pliku
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Wybierz kopię zapasową",
                BACKUP_DIR,
                "Bazy danych (*.db)"
            )
            
            if file_path:
                # Potwierdzenie operacji
                reply = QMessageBox.warning(
                    self,
                    "Przywracanie bazy danych",
                    "Ta operacja zastąpi aktualną bazę danych. Wszystkie niezapisane zmiany zostaną utracone. Kontynuować?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Zamknięcie połączenia z bazą danych
                    self.conn.close()
                    
                    # Przywrócenie bazy danych
                    result = restore_database(file_path)
                    
                    if result:
                        # Ponowne połączenie z bazą danych
                        from utils.database import create_connection
                        self.conn = create_connection()
                        
                        # Odświeżenie danych
                        self.refresh_data()
                        
                        # Emitowanie sygnału o aktualizacji bazy danych
                        self.database_updated.emit()
                        
                        # Powiadomienie o sukcesie
                        NotificationManager.get_instance().show_notification(
                            "Baza danych została przywrócona pomyślnie.",
                            NotificationTypes.SUCCESS,
                            duration=5000
                        )
                    else:
                        # Powiadomienie o błędzie
                        NotificationManager.get_instance().show_notification(
                            "Nie udało się przywrócić bazy danych.",
                            NotificationTypes.ERROR,
                            duration=5000
                        )
        except Exception as e:
            logger.error(f"Błąd podczas przywracania bazy danych: {e}")
            QMessageBox.critical(
                self,
                "Błąd przywracania",
                f"Wystąpił błąd podczas przywracania bazy danych:\n{str(e)}"
            )
    
    def manage_locations(self):
        """Otwiera okno zarządzania lokalizacjami."""
        # Przykładowe powiadomienie (bez faktycznej implementacji)
        NotificationManager.get_instance().show_notification(
            "Funkcja zarządzania lokalizacjami nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def manage_templates(self):
        """Otwiera okno zarządzania szablonami."""
        # Przykładowe powiadomienie (bez faktycznej implementacji)
        NotificationManager.get_instance().show_notification(
            "Funkcja zarządzania szablonami nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def manage_notifications(self):
        """Otwiera okno zarządzania powiadomieniami."""
        # Przykładowe powiadomienie (bez faktycznej implementacji)
        NotificationManager.get_instance().show_notification(
            "Funkcja zarządzania powiadomieniami nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def show_barcode_generator(self):
        """Otwiera okno generatora kodów kreskowych."""
        # Przykładowe powiadomienie (bez faktycznej implementacji)
        NotificationManager.get_instance().show_notification(
            "Generator kodów kreskowych nie jest jeszcze zaimplementowany.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def view_logs(self):
        """Wyświetla logi aplikacji."""
        # Przykładowe powiadomienie (bez faktycznej implementacji)
        NotificationManager.get_instance().show_notification(
            "Przeglądarka logów nie jest jeszcze zaimplementowana.",
            NotificationTypes.WARNING,
            duration=3000
        )
    
    def show_help(self):
        """Wyświetla pomoc aplikacji."""
        QMessageBox.information(
            self,
            "Pomoc",
            "Pomoc aplikacji Menadżer Depozytów Opon.\n\n"
            "Skróty klawiaturowe:\n"
            "- F1: Pomoc\n"
            "- F5: Odśwież dane\n"
            "- Ctrl+Q: Zakończ aplikację\n\n"
            "Aby uzyskać więcej informacji, skontaktuj się z administratorem systemu "
            "lub skorzystaj z dokumentacji użytkownika."
        )
    
    def show_about(self):
        """Wyświetla informacje o aplikacji."""
        QMessageBox.about(
            self,
            "O programie",
            f"<h3>Menadżer Depozytów Opon</h3>"
            f"<p>Wersja 2.1</p>"
            f"<p>Aplikacja do zarządzania depozytami opon oraz stanami magazynowymi.</p>"
            f"<p>Umożliwia przechowywanie informacji o klientach, oponach na stanie, "
            f"zamówieniach oraz generowanie raportów i drukowanie etykiet.</p>"
            f"<p>System posiada również funkcje zarządzania częściami i harmonogramem wizyt.</p>"
            f"<p>©2023-2025 Serwis Opon MATEO</p>"
        )
    
    def load_settings(self):
        """Ładuje ustawienia aplikacji."""
        # Ustawienia wyglądu
        theme = self.settings.value("theme", "Light")
        if theme == "Dark":
            # Zastosowanie ciemnego motywu
            from utils.styles import DARK_STYLE_SHEET
            self.setStyleSheet(DARK_STYLE_SHEET)
        else:
            # Zastosowanie jasnego motywu
            from utils.styles import STYLE_SHEET
            self.setStyleSheet(STYLE_SHEET)
        
        # Ustawienia czcionki
        font_family = self.settings.value("font_family", "Segoe UI")
        font_size = int(self.settings.value("font_size", 10))
        font = QFont(font_family, font_size)
        self.setFont(font)
        
        # Zapisanie ustawień
        self.settings.setValue("theme", theme)
        self.settings.setValue("font_family", font_family)
        self.settings.setValue("font_size", font_size)
    
    def closeEvent(self, event):
        """Obsługuje zdarzenie zamknięcia okna."""
        # Zapisanie stanu aplikacji
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        
        # Zamykanie połączenia z bazą danych
        if self.conn:
            self.conn.close()
            logger.info("Połączenie z bazą danych zostało zamknięte")
        
        # Standardowa obsługa zamknięcia
        super().closeEvent(event)