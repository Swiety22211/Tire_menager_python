#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka ustawień aplikacji w ciemnym motywie z pełną funkcjonalnością.
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from PySide6.QtCore import Qt, QSize, QSettings, QDir, QFile, Signal
    from PySide6.QtGui import QIcon, QFont, QTextDocument, QTextCursor, QPixmap, QColor
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QSpinBox,
        QMessageBox, QFontComboBox, QTextEdit, QGroupBox,
        QFileDialog, QFrame, QScrollArea, QSizePolicy, QInputDialog,
        QListWidget, QListWidgetItem, QStackedWidget, QSplitter, QTabWidget,
        QDialogButtonBox
                )
            
    def init_templates_page(self, layout):
        """
        Inicjalizacja strony szablonów.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Zakładki dla różnych typów szablonów
        templates_tabs = QTabWidget()
        
        # Zakładka szablonów email
        self.email_tab = QWidget()
        templates_tabs.addTab(self.email_tab, "Szablony Email")
        
        # Zakładka szablonów etykiet
        self.label_tab = QWidget()
        templates_tabs.addTab(self.label_tab, "Szablony Etykiet")
        
        # Zakładka szablonów potwierdzeń
        self.receipt_tab = QWidget()
        templates_tabs.addTab(self.receipt_tab, "Szablony Potwierdzeń")
        
        layout.addWidget(templates_tabs)
        
        # Konfiguracja zakładek
        self.setup_email_tab()
        self.setup_label_tab()
        self.setup_receipt_tab()
            
    def init_communication_page(self, layout):
        """
        Inicjalizacja strony ustawień komunikacji.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Ustawienia e-mail
        email_group = QGroupBox("Ustawienia e-mail")
        email_layout = QFormLayout(email_group)
        email_layout.setSpacing(10)
        
        # Adres e-mail
        self.email_address_input = QLineEdit()
        email_layout.addRow("Adres e-mail:", self.email_address_input)
        
        # Hasło (w praktyce powinno być zabezpieczone)
        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        email_layout.addRow("Hasło:", self.email_password_input)
        
        # Serwer SMTP
        self.smtp_server_input = QLineEdit()
        email_layout.addRow("Serwer SMTP:", self.smtp_server_input)
        
        # Port SMTP
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        email_layout.addRow("Port SMTP:", self.smtp_port_spin)
        
        # Użyj SSL
        self.use_ssl_checkbox = QCheckBox("Użyj SSL/TLS")
        email_layout.addRow("", self.use_ssl_checkbox)
        
        # Testowy e-mail
        test_email_button = QPushButton("Wyślij testowy email")
        test_email_button.clicked.connect(self.send_test_email)
        email_layout.addRow("", test_email_button)
        
        layout.addWidget(email_group)

    def send_test_email(self):
        """Wysyła testowy email."""
        try:
            # Sprawdź czy wszystkie wymagane pola są wypełnione
            email = self.email_address_input.text().strip()
            password = self.email_password_input.text()
            server = self.smtp_server_input.text().strip()
            port = self.smtp_port_spin.value()
            
            if not all([email, password, server, port]):
                QMessageBox.warning(
                    self,
                    "Brak danych",
                    "Proszę wypełnić wszystkie wymagane pola (adres email, hasło, serwer, port)."
                )
                return
                
            # Zapytaj o adres docelowy
            recipient, ok = QInputDialog.getText(
                self,
                "Testowy email",
                "Podaj adres email, na który chcesz wysłać test:",
                QLineEdit.Normal,
                email
            )
            
            if not ok or not recipient:
                return
                
            # Spróbuj zaimportować moduły SMTP
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
            except ImportError as e:
                logger.error(f"Nie można zaimportować modułów email: {e}")
                QMessageBox.critical(
                    self,
                    "Błąd importu",
                    f"Nie można zaimportować wymaganych modułów: {str(e)}"
                )
                return
                
            # Pokazujemy komunikat, że wysyłamy email
            QMessageBox.information(
                self,
                "Wysyłanie...",
                "Próba wysłania testowej wiadomości. To może potrwać chwilę.\n\n"
                "Pojawi się komunikat o wyniku operacji."
            )
            
            # Przygotuj wiadomość
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = recipient
            msg['Subject'] = "Test konfiguracji SMTP"
            
            body = """
            To jest testowa wiadomość wysłana z aplikacji TireDepositManager.
            
            Jeśli widzisz tę wiadomość, oznacza to, że konfiguracja SMTP działa poprawnie.
            
            Pozdrawiamy,
            TireDepositManager
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Wysyłka emaila
            try:
                # Utworzenie sesji SMTP
                session = smtplib.SMTP(server, port)
                
                # Dla większości serwerów konieczne jest rozpoczęcie sesji TLS
                if self.use_ssl_checkbox.isChecked():
                    session.starttls()
                
                # Logowanie do serwera SMTP
                session.login(email, password)
                
                # Wysłanie wiadomości
                session.sendmail(email, recipient, msg.as_string())
                
                # Zakończenie sesji
                session.quit()
                
                # Powiadomienie o sukcesie
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Testowa wiadomość została pomyślnie wysłana na adres {recipient}."
                )
                
            except Exception as e:
                logger.error(f"Błąd podczas wysyłania testowego emaila: {e}")
                QMessageBox.critical(
                    self,
                    "Błąd wysyłania",
                    f"Nie udało się wysłać testowej wiadomości:\n\n{str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania testowego emaila: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd: {str(e)}"
            )
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError as e:
    logging.error(f"Błąd importu: {e}")
    raise

# Bezpieczny import modułów aplikacji
try:
    from utils.paths import ICONS_DIR, CONFIG_DIR, ensure_dir_exists
    from ui.notifications import NotificationManager, NotificationTypes
    from utils.i18n import _  # Funkcja do obsługi lokalizacji
    from ui.dialogs.settings_dialog import (
        DEFAULT_EMAIL_TEMPLATES, DEFAULT_LABEL_TEMPLATE, DEFAULT_RECEIPT_TEMPLATE
    )
except ImportError as e:
    logging.warning(f"Nie udało się zaimportować modułu aplikacji: {e}")

# Logger
logger = logging.getLogger("TireDepositManager")

# Paleta kolorów dla ciemnego motywu
DARK_BG = "#1E1E1E"
DARK_WIDGET_BG = "#2D2D30"
DARK_HEADER = "#252526"
SIDEBAR_BG = "#2c3e50"
HIGHLIGHT_COLOR = "#4dabf7"
TEXT_COLOR = "#FFFFFF"
TEXT_SECONDARY = "#AAAAAA"
SUCCESS_COLOR = "#28a745"
BORDER_COLOR = "#444444"

# Style CSS dla ciemnego motywu
DARK_STYLE = """
QWidget {
    background-color: #1E1E1E;
    color: #FFFFFF;
    font-size: 10pt;
}

QGroupBox {
    border: 1px solid #444444;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #FFFFFF;
}

QLabel {
    color: #FFFFFF;
}

QLineEdit, QComboBox, QSpinBox, QDateEdit, QFontComboBox, QTextEdit {
    background-color: #2D2D30;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px;
    color: #FFFFFF;
    selection-background-color: #4dabf7;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #4dabf7;
}

QPushButton {
    background-color: #2D2D30;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 12px;
    color: #FFFFFF;
}

QPushButton:hover {
    background-color: #3E3E42;
}

QPushButton:pressed {
    background-color: #4d4d50;
}

QPushButton#success {
    background-color: #28a745;
    border: none;
    color: white;
}

QPushButton#success:hover {
    background-color: #218838;
}

QListWidget {
    background-color: #2c3e50;
    border: none;
    border-right: 1px solid #444444;
    color: #FFFFFF;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border: none;
}

QListWidget::item:selected {
    background-color: #4dabf7;
    color: white;
}

QListWidget::item:hover {
    background-color: #3c546c;
}

QScrollArea {
    border: none;
}

QTabWidget::pane {
    border: 1px solid #444444;
    background-color: #2D2D30;
}

QTabBar::tab {
    background-color: #1E1E1E;
    color: #FFFFFF;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #4dabf7;
}

QTabBar::tab:hover:!selected {
    background-color: #3E3E42;
}

QCheckBox {
    color: #FFFFFF;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background-color: #2D2D30;
    border: 1px solid #444444;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #4dabf7;
    border-color: #4dabf7;
}

QWebEngineView {
    background-color: #FFFFFF;
}
"""


class SettingsTab(QWidget):
    """
    Zakładka umożliwiająca konfigurację ustawień aplikacji w nowym interfejsie.
    """
    
    # Sygnał emitowany po zapisaniu ustawień
    settingsSaved = Signal()
    
    def __init__(self, parent=None):
        """
        Inicjalizacja zakładki ustawień.
        
        Args:
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Inicjalizacja ustawień
        self.settings = QSettings("TireDepositManager", "Settings")
        
        # Ścieżka do pliku z szablonami
        self.templates_file = os.path.join(CONFIG_DIR, "templates.json")
        ensure_dir_exists(CONFIG_DIR)
        
        # Inicjalizacja templates
        self.templates = {}
        self.email_template_mapping = {}
        
        # Ustawienie stylu ciemnego motywu
        self.setStyleSheet(DARK_STYLE)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie aktualnych ustawień
        self.load_settings()
        
        # Załadowanie szablonów
        self.load_templates()

    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel boczny (lista kategorii)
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(200)
        self.categories_list.setIconSize(QSize(24, 24))
        self.categories_list.currentRowChanged.connect(self.change_settings_page)
        main_layout.addWidget(self.categories_list)
        
        # Kontener na zawartość ustawień
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Tytuł sekcji
        self.section_title = QLabel("Ustawienia systemu")
        self.section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        content_layout.addWidget(self.section_title)
        
        # Linia separatora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #444444;")
        content_layout.addWidget(separator)
        
        # Stos stron (zawartość każdej kategorii)
        self.settings_stack = QStackedWidget()
        content_layout.addWidget(self.settings_stack)
        
        # Przyciski zapisz/anuluj
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        save_button = QPushButton("Zapisz zmiany")
        save_button.setProperty("id", "success")
        save_button.clicked.connect(self.save_settings)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        
        content_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(content_container, 1)
        
        # Dodanie kategorii i ich stron
        self.add_categories()

    def add_categories(self):
        """Dodaje kategorie ustawień do listy."""
        categories = [
            {"name": "Ogólne", "icon": "settings.png"},
            {"name": "Wygląd", "icon": "ui.png"},
            {"name": "Dane firmy", "icon": "company.png"},
            {"name": "Kopie zapasowe", "icon": "backup.png"},
            {"name": "Komunikacja", "icon": "email.png"},
            {"name": "Szablony", "icon": "template.png"}
        ]
        
        for category in categories:
            item = QListWidgetItem(category["name"])
            icon_path = os.path.join(ICONS_DIR, category["icon"])
            if os.path.exists(icon_path):
                item.setIcon(QIcon(icon_path))
            self.categories_list.addItem(item)
            
            # Dodaj odpowiednią stronę ustawień dla kategorii
            page = self.create_settings_page(category["name"])
            self.settings_stack.addWidget(page)
        
        # Ustawienie pierwszej kategorii jako aktywnej
        if self.categories_list.count() > 0:
            self.categories_list.setCurrentRow(0)

    def change_settings_page(self, index):
        self.settings_stack.setCurrentIndex(index)
        
        # Aktualizacja tytułu sekcji na podstawie wybranej kategorii
        if 0 <= index < self.categories_list.count():
            category_name = self.categories_list.item(index).text()
            self.section_title.setText(f"Ustawienia - {category_name}")


    def create_settings_page(self, category_name):
        """
        Tworzy stronę ustawień dla danej kategorii.
        
        Args:
            category_name (str): Nazwa kategorii
            
        Returns:
            QWidget: Widget z zawartością ustawień
        """
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        if category_name == "Ogólne":
            self.init_general_page(layout)
        elif category_name == "Wygląd":
            self.init_appearance_page(layout)
        elif category_name == "Dane firmy":
            self.init_company_page(layout)
        elif category_name == "Kopie zapasowe":
            self.init_backup_page(layout)
        elif category_name == "Komunikacja":
            self.init_communication_page(layout)
        elif category_name == "Szablony":
            self.init_templates_page(layout)
        
        layout.addStretch()
        page.setWidget(content)
        return page

    def init_general_page(self, layout):
        """
        Inicjalizacja strony ustawień ogólnych.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Ustawienia ogólne
        general_group = QGroupBox("Ustawienia ogólne")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)
        
        # Katalog danych
        data_layout = QHBoxLayout()
        self.data_dir_input = QLineEdit()
        self.data_dir_input.setReadOnly(True)
        data_layout.addWidget(self.data_dir_input, 1)
        
        browse_data_dir_button = QPushButton("Przeglądaj...")
        browse_data_dir_button.clicked.connect(self.browse_data_dir)
        data_layout.addWidget(browse_data_dir_button)
        
        general_layout.addRow("Katalog danych:", data_layout)
        
        # Język
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Polski", "English"])
        general_layout.addRow("Język:", self.language_combo)
        
        # Automatyczne logowanie
        self.auto_login_checkbox = QCheckBox("Automatycznie loguj przy starcie")
        general_layout.addRow("", self.auto_login_checkbox)
        
        # Automatyczne aktualizacje
        self.auto_update_checkbox = QCheckBox("Sprawdzaj aktualizacje przy starcie")
        general_layout.addRow("", self.auto_update_checkbox)
        
        # Domyślny czas wizyty
        self.default_visit_duration = QSpinBox()
        self.default_visit_duration.setRange(15, 240)
        self.default_visit_duration.setSingleStep(15)
        self.default_visit_duration.setValue(60)
        self.default_visit_duration.setSuffix(" min")
        general_layout.addRow("Domyślny czas trwania wizyty:", self.default_visit_duration)
        
        # Domyślna stawka VAT
        self.default_vat_rate = QComboBox()
        self.default_vat_rate.addItems(["23%", "8%", "5%", "0%"])
        general_layout.addRow("Domyślna stawka VAT:", self.default_vat_rate)
        
        layout.addWidget(general_group)

    def init_appearance_page(self, layout):
        """
        Inicjalizacja strony ustawień wyglądu.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Ustawienia wyglądu
        appearance_group = QGroupBox("Ustawienia wyglądu")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setSpacing(10)
        
        # Motyw
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        appearance_layout.addRow("Motyw:", self.theme_combo)
        
        # Czcionka
        font_layout = QHBoxLayout()
        self.font_combo = QFontComboBox()
        font_layout.addWidget(self.font_combo, 3)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        font_layout.addWidget(self.font_size_spin, 1)
        
        appearance_layout.addRow("Czcionka:", font_layout)
        
        # Podgląd czcionki
        self.font_preview = QLabel("Podgląd czcionki")
        self.font_preview.setStyleSheet("padding: 10px; background-color: #2D2D30; border: 1px solid #444444; border-radius: 4px;")
        self.font_preview.setAlignment(Qt.AlignCenter)
        appearance_layout.addRow("", self.font_preview)
        
        # Aktualizacja podglądu czcionki przy zmianie
        self.font_combo.currentFontChanged.connect(self.update_font_preview)
        self.font_size_spin.valueChanged.connect(self.update_font_preview)
        
        # Pozostałe opcje
        self.show_status_checkbox = QCheckBox("Pokazuj status w nagłówku")
        appearance_layout.addRow("", self.show_status_checkbox)
        
        self.colored_status_checkbox = QCheckBox("Kolorowe etykiety statusów")
        appearance_layout.addRow("", self.colored_status_checkbox)
        
        layout.addWidget(appearance_group)
        
        # Ustaw początkowy podgląd czcionki
        self.update_font_preview()

    def init_company_page(self, layout):
        """
        Inicjalizacja strony ustawień firmy.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Dane firmy
        company_group = QGroupBox("Dane firmy")
        company_layout = QFormLayout(company_group)
        company_layout.setSpacing(10)
        
        # Nazwa firmy
        self.company_name_input = QLineEdit()
        company_layout.addRow("Nazwa firmy:", self.company_name_input)
        
        # Adres
        self.company_address_input = QLineEdit()
        company_layout.addRow("Adres:", self.company_address_input)
        
        # Miasto
        self.company_city_input = QLineEdit()
        company_layout.addRow("Miasto:", self.company_city_input)
        
        # NIP
        self.company_tax_id_input = QLineEdit()
        company_layout.addRow("NIP:", self.company_tax_id_input)
        
        # Telefon
        self.company_phone_input = QLineEdit()
        company_layout.addRow("Telefon:", self.company_phone_input)
        
        # Email
        self.company_email_input = QLineEdit()
        company_layout.addRow("Email:", self.company_email_input)
        
        # Strona www
        self.company_website_input = QLineEdit()
        company_layout.addRow("Strona www:", self.company_website_input)
        
        # Stopka dokumentów
        self.company_footer_input = QLineEdit()
        company_layout.addRow("Stopka dokumentów:", self.company_footer_input)
        
        layout.addWidget(company_group)

    def init_backup_page(self, layout):
        """
        Inicjalizacja strony ustawień kopii zapasowych.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Kopie zapasowe
        backup_group = QGroupBox("Kopie zapasowe")
        backup_layout = QFormLayout(backup_group)
        backup_layout.setSpacing(10)
        
        # Automatyczne kopie
        self.auto_backup_checkbox = QCheckBox("Twórz automatyczne kopie zapasowe")
        backup_layout.addRow("", self.auto_backup_checkbox)
        
        # Interwał kopii
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setValue(7)
        self.backup_interval_spin.setSuffix(" dni")
        backup_layout.addRow("Interwał kopii:", self.backup_interval_spin)
        
        # Katalog kopii
        backup_dir_layout = QHBoxLayout()
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setReadOnly(True)
        backup_dir_layout.addWidget(self.backup_dir_input, 1)
        
        browse_backup_dir_button = QPushButton("Przeglądaj...")
        browse_backup_dir_button.clicked.connect(self.browse_backup_dir)
        backup_dir_layout.addWidget(browse_backup_dir_button)
        
        backup_layout.addRow("Katalog kopii:", backup_dir_layout)
        
        # Liczba przechowywanych kopii
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 50)
        self.backup_count_spin.setValue(10)
        backup_layout.addRow("Liczba kopii:", self.backup_count_spin)
        
        # Kompresja kopii
        self.compress_backup_checkbox = QCheckBox("Kompresuj kopie zapasowe")
        backup_layout.addRow("", self.compress_backup_checkbox)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        create_backup_button = QPushButton("Utwórz kopię teraz")
        create_backup_button.clicked.connect(self.create_backup_now)
        buttons_layout.addWidget(create_backup_button)
        
        restore_backup_button = QPushButton("Przywróć z kopii")
        restore_backup_button.clicked.connect(self.restore_from_backup)
        buttons_layout.addWidget(restore_backup_button)
        
        backup_layout.addRow("", buttons_layout)
        
        layout.addWidget(backup_group)

    def browse_backup_dir(self):
        """Otwiera okno wyboru katalogu kopii zapasowych."""
        directory = QFileDialog.getExistingDirectory(self, "Wybierz katalog kopii zapasowych", self.backup_dir_input.text())
        if directory:
            self.backup_dir_input.setText(directory)
            
    def create_backup_now(self):
        """Tworzy kopię zapasową na żądanie."""
        try:
            QMessageBox.information(
                self,
                "Kopia zapasowa",
                "Funkcja tworzenia kopii zapasowej będzie dostępna po implementacji mechanizmu kopii zapasowych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia kopii zapasowej: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas tworzenia kopii zapasowej:\n{str(e)}"
            )

    def restore_from_backup(self):
        """Przywraca dane z kopii zapasowej."""
        try:
            QMessageBox.information(
                self,
                "Przywracanie kopii",
                "Funkcja przywracania z kopii zapasowej będzie dostępna po implementacji mechanizmu kopii zapasowych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas przywracania kopii zapasowej: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas przywracania z kopii zapasowej:\n{str(e)}"
            )

    def init_communication_page(self, layout):
        """
        Inicjalizacja strony ustawień komunikacji.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Ustawienia e-mail
        email_group = QGroupBox("Ustawienia e-mail")
        email_layout = QFormLayout(email_group)
        email_layout.setSpacing(10)
        
        # Adres e-mail
        self.email_address_input = QLineEdit()
        email_layout.addRow("Adres e-mail:", self.email_address_input)
        
        # Hasło (w praktyce powinno być zabezpieczone)
        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        email_layout.addRow("Hasło:", self.email_password_input)
        
        # Serwer SMTP
        self.smtp_server_input = QLineEdit()
        email_layout.addRow("Serwer SMTP:", self.smtp_server_input)
        
        # Port SMTP
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        email_layout.addRow("Port SMTP:", self.smtp_port_spin)
        
        # Użyj SSL
        self.use_ssl_checkbox = QCheckBox("Użyj SSL/TLS")
        email_layout.addRow("", self.use_ssl_checkbox)
        
        # Testowy e-mail
        test_email_button = QPushButton("Wyślij testowy email")
        test_email_button.clicked.connect(self.send_test_email)
        email_layout.addRow("", test_email_button)
        
        layout.addWidget(email_group)

    def send_test_email(self):
        """Wysyła testowy email."""
        try:
            # Sprawdź czy wszystkie wymagane pola są wypełnione
            email = self.email_address_input.text().strip()
            password = self.email_password_input.text()
            server = self.smtp_server_input.text().strip()
            port = self.smtp_port_spin.value()
            
            if not all([email, password, server, port]):
                QMessageBox.warning(
                    self,
                    "Brak danych",
                    "Proszę wypełnić wszystkie wymagane pola (adres email, hasło, serwer, port)."
                )
                return
                
            # Zapytaj o adres docelowy
            recipient, ok = QInputDialog.getText(
                self,
                "Testowy email",
                "Podaj adres email, na który chcesz wysłać test:",
                QLineEdit.Normal,
                email
            )
            
            if not ok or not recipient:
                return
                
            # Spróbuj zaimportować moduły SMTP
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
            except ImportError as e:
                logger.error(f"Nie można zaimportować modułów email: {e}")
                QMessageBox.critical(
                    self,
                    "Błąd importu",
                    f"Nie można zaimportować wymaganych modułów: {str(e)}"
                )
                return
                
            # Pokazujemy komunikat, że wysyłamy email
            QMessageBox.information(
                self,
                "Wysyłanie...",
                "Próba wysłania testowej wiadomości. To może potrwać chwilę.\n\n"
                "Pojawi się komunikat o wyniku operacji."
            )
            
            # Przygotuj wiadomość
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = recipient
            msg['Subject'] = "Test konfiguracji SMTP"
            
            body = """
            To jest testowa wiadomość wysłana z aplikacji TireDepositManager.
            
            Jeśli widzisz tę wiadomość, oznacza to, że konfiguracja SMTP działa poprawnie.
            
            Pozdrawiamy,
            TireDepositManager
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Wysyłka emaila
            try:
                # Utworzenie sesji SMTP
                session = smtplib.SMTP(server, port)
                
                # Dla większości serwerów konieczne jest rozpoczęcie sesji TLS
                if self.use_ssl_checkbox.isChecked():
                    session.starttls()
                
                # Logowanie do serwera SMTP
                session.login(email, password)
                
                # Wysłanie wiadomości
                session.sendmail(email, recipient, msg.as_string())
                
                # Zakończenie sesji
                session.quit()
                
                # Powiadomienie o sukcesie
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Testowa wiadomość została pomyślnie wysłana na adres {recipient}."
                )
                
            except Exception as e:
                logger.error(f"Błąd podczas wysyłania testowego emaila: {e}")
                QMessageBox.critical(
                    self,
                    "Błąd wysyłania",
                    f"Nie udało się wysłać testowej wiadomości:\n\n{str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania testowego emaila: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd: {str(e)}"
            )

    def browse_data_dir(self):
        """Otwiera okno wyboru katalogu danych."""
        directory = QFileDialog.getExistingDirectory(self, "Wybierz katalog danych", self.data_dir_input.text())
        if directory:
            self.data_dir_input.setText(directory)

    def on_email_template_changed(self, index):
        """Obsługuje zmianę szablonu email."""
        try:
            template_key = self.email_template_mapping.get(index)
            if not template_key:
                # Jeśli nie znaleziono w mapowaniu, użyj nazwy z combobox
                template_key = self.email_template_combo.currentText()
                
            # Ustal, który szablon załadować
            if template_key == "Aktywny depozyt":
                template_key = "active"
            elif template_key == "Do odbioru":
                template_key = "pickup"
            elif template_key == "Zaległy depozyt":
                template_key = "overdue"
            elif template_key == "Ogólny":
                template_key = "general"
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "email" in self.templates and template_key in self.templates["email"]:
                template = self.templates["email"][template_key]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_EMAIL_TEMPLATES.get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Ustaw pola formularza
            self.email_subject_edit.setText(template.get("subject", ""))
            self.email_body_edit.setPlainText(template.get("body", ""))
            
            # Aktualizuj podgląd
            self.update_email_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu email: {e}")

    def on_label_template_changed(self, index):
        """Obsługuje zmianę szablonu etykiety."""
        try:
            template_name = self.label_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "label" in self.templates and template_name in self.templates["label"]:
                template = self.templates["label"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_LABEL_TEMPLATE
            
            # Ustaw pola formularza
            self.label_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_label_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu etykiety: {e}")

    def on_receipt_template_changed(self, index):
        """Obsługuje zmianę szablonu potwierdzenia."""
        try:
            template_name = self.receipt_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "receipt" in self.templates and template_name in self.templates["receipt"]:
                template = self.templates["receipt"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_RECEIPT_TEMPLATE
            
            # Ustaw pola formularza
            self.receipt_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_receipt_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu potwierdzenia: {e}")
            
    def load_templates(self):
        """Ładuje szablony z pliku."""
        try:
            # Sprawdź, czy plik z szablonami istnieje
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                # Plik nie istnieje, utwórz z domyślnymi szablonami
                self.templates = {
                    "email": DEFAULT_EMAIL_TEMPLATES,
                    "label": {"default": DEFAULT_LABEL_TEMPLATE},
                    "receipt": {"default": DEFAULT_RECEIPT_TEMPLATE}
                }
                self.save_templates()
                
            # Wypełnienie combo boxów z nazwami szablonów
            self.email_template_mapping = {
                0: "active",
                1: "pickup",
                2: "overdue",
                3: "general"
            }
            
            # Ładowanie niestandardowych szablonów email
            for template_name in self.templates.get("email", {}):
                if template_name not in ["active", "pickup", "overdue", "general"]:
                    self.email_template_combo.addItem(template_name)
                    index = self.email_template_combo.count() - 1
                    self.email_template_mapping[index] = template_name
            
            # Ładowanie szablonów etykiet
            self.label_template_combo.clear()
            self.label_template_combo.addItem("Domyślny", "default")
            
            label_templates = self.templates.get("label", {})
            for template_name in label_templates:
                if template_name != "default":
                    self.label_template_combo.addItem(template_name, template_name)
            
            # Ładowanie szablonów potwierdzeń
            self.receipt_template_combo.clear()
            self.receipt_template_combo.addItem("Domyślny", "default")
            
            receipt_templates = self.templates.get("receipt", {})
            for template_name in receipt_templates:
                if template_name != "default":
                    self.receipt_template_combo.addItem(template_name, template_name)
            
            # Ustawienie domyślnych szablonów
            self.on_email_template_changed(0)
            self.on_label_template_changed(0)
            self.on_receipt_template_changed(0)
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas ładowania szablonów:\n{str(e)}"
            )

    def save_templates(self):
        """Zapisuje szablony do pliku."""
        try:
            # Upewnij się, że katalog istnieje
            ensure_dir_exists(os.path.dirname(self.templates_file))
            
            # Zapisz szablony do pliku JSON
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas zapisywania szablonów:\n{str(e)}"
            )
            
    def load_settings(self):
        """Ładuje ustawienia do formularza."""
        try:
            # Domyślna ścieżka danych z utils.paths
            try:
                from utils.paths import APP_DATA_DIR
                default_data_dir = APP_DATA_DIR
            except ImportError:
                default_data_dir = os.path.join(os.path.expanduser("~"), "TireDepositManager")
                
            # Pobierz ścieżkę katalogu danych z ustawień, używając domyślnej wartości
            data_directory = self.settings.value("data_directory", default_data_dir)
            
            # Upewnij się, że katalog istnieje
            os.makedirs(data_directory, exist_ok=True)
            
            # Ustaw ścieżkę w polu input
            self.data_dir_input.setText(data_directory)

            # Ustawienia ogólne
            lang_index = self.language_combo.findText(self.settings.value("language", "Polski"))
            if lang_index != -1:
                self.language_combo.setCurrentIndex(lang_index)
            
            self.auto_login_checkbox.setChecked(self.settings.value("auto_login", False, type=bool))
            self.auto_update_checkbox.setChecked(self.settings.value("auto_update", False, type=bool))
            
            self.default_visit_duration.setValue(self.settings.value("default_visit_duration", 60, type=int))
            
            vat_index = self.default_vat_rate.findText(self.settings.value("default_vat_rate", "23%"))
            if vat_index != -1:
                self.default_vat_rate.setCurrentIndex(vat_index)

            # Ustawienia wyglądu
            theme_index = self.theme_combo.findText(self.settings.value("theme", "Dark"))
            if theme_index != -1:
                self.theme_combo.setCurrentIndex(theme_index)
            
            font_family = self.settings.value("font", "Arial")
            font_index = self.font_combo.findText(font_family)
            if font_index != -1:
                self.font_combo.setCurrentIndex(font_index)
            
            self.font_size_spin.setValue(self.settings.value("font_size", 10, type=int))
            self.show_status_checkbox.setChecked(self.settings.value("show_status_in_header", False, type=bool))
            self.colored_status_checkbox.setChecked(self.settings.value("colored_status_labels", False, type=bool))

            # Ustawienia firmowe
            self.company_name_input.setText(self.settings.value("company_name", ""))
            self.company_address_input.setText(self.settings.value("company_address", ""))
            self.company_city_input.setText(self.settings.value("company_city", ""))
            self.company_tax_id_input.setText(self.settings.value("company_tax_id", ""))
            self.company_phone_input.setText(self.settings.value("company_phone", ""))
            self.company_email_input.setText(self.settings.value("company_email", ""))
            self.company_website_input.setText(self.settings.value("company_website", ""))
            self.company_footer_input.setText(self.settings.value("company_footer", ""))

            # Ustawienia kopii zapasowych
            self.auto_backup_checkbox.setChecked(self.settings.value("auto_backup", False, type=bool))
            self.backup_interval_spin.setValue(self.settings.value("backup_interval", 7, type=int))
            
            # Pobierz ścieżkę katalogu kopii
            try:
                from utils.paths import BACKUP_DIR
                default_backup_dir = BACKUP_DIR
            except ImportError:
                default_backup_dir = os.path.join(data_directory, "backups")
                
            self.backup_dir_input.setText(self.settings.value("backup_directory", default_backup_dir))
            self.backup_count_spin.setValue(self.settings.value("backup_count", 10, type=int))
            self.compress_backup_checkbox.setChecked(self.settings.value("compress_backup", False, type=bool))

            # Ustawienia komunikacji
            self.email_address_input.setText(self.settings.value("email_address", ""))
            self.email_password_input.setText(self.settings.value("email_password", ""))
            self.smtp_server_input.setText(self.settings.value("smtp_server", ""))
            self.smtp_port_spin.setValue(self.settings.value("smtp_port", 587, type=int))
            self.use_ssl_checkbox.setChecked(self.settings.value("use_ssl", True, type=bool))

        except Exception as e:
            logger.error(f"Błąd podczas ładowania ustawień: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania ustawień:\n{str(e)}"
            )
            
    def save_settings(self):
        """Zapisuje ustawienia z wszystkich zakładek."""
        try:
            # Ustawienia ogólne
            self.settings.setValue("data_directory", self.data_dir_input.text())
            self.settings.setValue("language", self.language_combo.currentText())
            self.settings.setValue("auto_login", self.auto_login_checkbox.isChecked())
            self.settings.setValue("auto_update", self.auto_update_checkbox.isChecked())
            self.settings.setValue("default_visit_duration", self.default_visit_duration.value())
            self.settings.setValue("default_vat_rate", self.default_vat_rate.currentText())

            # Ustawienia wyglądu
            self.settings.setValue("theme", self.theme_combo.currentText())
            self.settings.setValue("font", self.font_combo.currentFont().family())
            self.settings.setValue("font_size", self.font_size_spin.value())
            self.settings.setValue("show_status_in_header", self.show_status_checkbox.isChecked())
            self.settings.setValue("colored_status_labels", self.colored_status_checkbox.isChecked())

            # Ustawienia firmowe
            self.settings.setValue("company_name", self.company_name_input.text())
            self.settings.setValue("company_address", self.company_address_input.text())
            self.settings.setValue("company_city", self.company_city_input.text())
            self.settings.setValue("company_tax_id", self.company_tax_id_input.text())
            self.settings.setValue("company_phone", self.company_phone_input.text())
            self.settings.setValue("company_email", self.company_email_input.text())
            self.settings.setValue("company_website", self.company_website_input.text())
            self.settings.setValue("company_footer", self.company_footer_input.text())

            # Ustawienia kopii zapasowych
            self.settings.setValue("auto_backup", self.auto_backup_checkbox.isChecked())
            self.settings.setValue("backup_interval", self.backup_interval_spin.value())
            self.settings.setValue("backup_directory", self.backup_dir_input.text())
            self.settings.setValue("backup_count", self.backup_count_spin.value())
            self.settings.setValue("compress_backup", self.compress_backup_checkbox.isChecked())

            # Ustawienia komunikacji
            self.settings.setValue("email_address", self.email_address_input.text())
            self.settings.setValue("email_password", self.email_password_input.text())
            self.settings.setValue("smtp_server", self.smtp_server_input.text())
            self.settings.setValue("smtp_port", self.smtp_port_spin.value())
            self.settings.setValue("use_ssl", self.use_ssl_checkbox.isChecked())

            # Zapisz szablony
            self.save_templates()
            
            # Powiadomienie o sukcesie
            QMessageBox.information(
                self, 
                "Ustawienia", 
                "Ustawienia zostały pomyślnie zapisane."
            )
            
            # Emituj sygnał o zapisaniu ustawień
            self.settingsSaved.emit()
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania ustawień: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania ustawień:\n{str(e)}"
            )    
            
    def on_email_template_changed(self, index):
        """Obsługuje zmianę szablonu email."""
        try:
            template_key = self.email_template_mapping.get(index)
            if not template_key:
                # Jeśli nie znaleziono w mapowaniu, użyj nazwy z combobox
                template_key = self.email_template_combo.currentText()
                
            # Ustal, który szablon załadować
            if template_key == "Aktywny depozyt":
                template_key = "active"
            elif template_key == "Do odbioru":
                template_key = "pickup"
            elif template_key == "Zaległy depozyt":
                template_key = "overdue"
            elif template_key == "Ogólny":
                template_key = "general"
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "email" in self.templates and template_key in self.templates["email"]:
                template = self.templates["email"][template_key]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_EMAIL_TEMPLATES.get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Ustaw pola formularza
            self.email_subject_edit.setText(template.get("subject", ""))
            self.email_body_edit.setPlainText(template.get("body", ""))
            
            # Aktualizuj podgląd
            self.update_email_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu email: {e}")

    def on_label_template_changed(self, index):
        """Obsługuje zmianę szablonu etykiety."""
        try:
            template_name = self.label_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "label" in self.templates and template_name in self.templates["label"]:
                template = self.templates["label"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_LABEL_TEMPLATE
            
            # Ustaw pola formularza
            self.label_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_label_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu etykiety: {e}")

    def on_receipt_template_changed(self, index):
        """Obsługuje zmianę szablonu potwierdzenia."""
        try:
            template_name = self.receipt_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "receipt" in self.templates and template_name in self.templates["receipt"]:
                template = self.templates["receipt"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_RECEIPT_TEMPLATE
            
            # Ustaw pola formularza
            self.receipt_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_receipt_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu potwierdzenia: {e}")
            
    def load_templates(self):
        """Ładuje szablony z pliku."""
        try:
            # Sprawdź, czy plik z szablonami istnieje
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                # Plik nie istnieje, utwórz z domyślnymi szablonami
                self.templates = {
                    "email": DEFAULT_EMAIL_TEMPLATES,
                    "label": {"default": DEFAULT_LABEL_TEMPLATE},
                    "receipt": {"default": DEFAULT_RECEIPT_TEMPLATE}
                }
                self.save_templates()
                
            # Wypełnienie combo boxów z nazwami szablonów
            self.email_template_mapping = {
                0: "active",
                1: "pickup",
                2: "overdue",
                3: "general"
            }
            
            # Ładowanie niestandardowych szablonów email
            for template_name in self.templates.get("email", {}):
                if template_name not in ["active", "pickup", "overdue", "general"]:
                    self.email_template_combo.addItem(template_name)
                    index = self.email_template_combo.count() - 1
                    self.email_template_mapping[index] = template_name
            
            # Ładowanie szablonów etykiet
            self.label_template_combo.clear()
            self.label_template_combo.addItem("Domyślny", "default")
            
            label_templates = self.templates.get("label", {})
            for template_name in label_templates:
                if template_name != "default":
                    self.label_template_combo.addItem(template_name, template_name)
            
            # Ładowanie szablonów potwierdzeń
            self.receipt_template_combo.clear()
            self.receipt_template_combo.addItem("Domyślny", "default")
            
            receipt_templates = self.templates.get("receipt", {})
            for template_name in receipt_templates:
                if template_name != "default":
                    self.receipt_template_combo.addItem(template_name, template_name)
            
            # Ustawienie domyślnych szablonów
            self.on_email_template_changed(0)
            self.on_label_template_changed(0)
            self.on_receipt_template_changed(0)
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas ładowania szablonów:\n{str(e)}"
            )

    def save_templates(self):
        """Zapisuje szablony do pliku."""
        try:
            # Upewnij się, że katalog istnieje
            ensure_dir_exists(os.path.dirname(self.templates_file))
            
            # Zapisz szablony do pliku JSON
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas zapisywania szablonów:\n{str(e)}"
            )
            
    def load_settings(self):
        """Ładuje ustawienia do formularza."""
        try:
            # Domyślna ścieżka danych z utils.paths
            try:
                from utils.paths import APP_DATA_DIR
                default_data_dir = APP_DATA_DIR
            except ImportError:
                default_data_dir = os.path.join(os.path.expanduser("~"), "TireDepositManager")
                
            # Pobierz ścieżkę katalogu danych z ustawień, używając domyślnej wartości
            data_directory = self.settings.value("data_directory", default_data_dir)
            
            # Upewnij się, że katalog istnieje
            os.makedirs(data_directory, exist_ok=True)
            
            # Ustaw ścieżkę w polu input
            self.data_dir_input.setText(data_directory)

            # Ustawienia ogólne
            lang_index = self.language_combo.findText(self.settings.value("language", "Polski"))
            if lang_index != -1:
                self.language_combo.setCurrentIndex(lang_index)
            
            self.auto_login_checkbox.setChecked(self.settings.value("auto_login", False, type=bool))
            self.auto_update_checkbox.setChecked(self.settings.value("auto_update", False, type=bool))
            
            self.default_visit_duration.setValue(self.settings.value("default_visit_duration", 60, type=int))
            
            vat_index = self.default_vat_rate.findText(self.settings.value("default_vat_rate", "23%"))
            if vat_index != -1:
                self.default_vat_rate.setCurrentIndex(vat_index)

            # Ustawienia wyglądu
            theme_index = self.theme_combo.findText(self.settings.value("theme", "Dark"))
            if theme_index != -1:
                self.theme_combo.setCurrentIndex(theme_index)
            
            font_family = self.settings.value("font", "Arial")
            font_index = self.font_combo.findText(font_family)
            if font_index != -1:
                self.font_combo.setCurrentIndex(font_index)
            
            self.font_size_spin.setValue(self.settings.value("font_size", 10, type=int))
            self.show_status_checkbox.setChecked(self.settings.value("show_status_in_header", False, type=bool))
            self.colored_status_checkbox.setChecked(self.settings.value("colored_status_labels", False, type=bool))

            # Ustawienia firmowe
            self.company_name_input.setText(self.settings.value("company_name", ""))
            self.company_address_input.setText(self.settings.value("company_address", ""))
            self.company_city_input.setText(self.settings.value("company_city", ""))
            self.company_tax_id_input.setText(self.settings.value("company_tax_id", ""))
            self.company_phone_input.setText(self.settings.value("company_phone", ""))
            self.company_email_input.setText(self.settings.value("company_email", ""))
            self.company_website_input.setText(self.settings.value("company_website", ""))
            self.company_footer_input.setText(self.settings.value("company_footer", ""))

            # Ustawienia kopii zapasowych
            self.auto_backup_checkbox.setChecked(self.settings.value("auto_backup", False, type=bool))
            self.backup_interval_spin.setValue(self.settings.value("backup_interval", 7, type=int))
            
            # Pobierz ścieżkę katalogu kopii
            try:
                from utils.paths import BACKUP_DIR
                default_backup_dir = BACKUP_DIR
            except ImportError:
                default_backup_dir = os.path.join(data_directory, "backups")
                
            self.backup_dir_input.setText(self.settings.value("backup_directory", default_backup_dir))
            self.backup_count_spin.setValue(self.settings.value("backup_count", 10, type=int))
            self.compress_backup_checkbox.setChecked(self.settings.value("compress_backup", False, type=bool))

            # Ustawienia komunikacji
            self.email_address_input.setText(self.settings.value("email_address", ""))
            self.email_password_input.setText(self.settings.value("email_password", ""))
            self.smtp_server_input.setText(self.settings.value("smtp_server", ""))
            self.smtp_port_spin.setValue(self.settings.value("smtp_port", 587, type=int))
            self.use_ssl_checkbox.setChecked(self.settings.value("use_ssl", True, type=bool))

        except Exception as e:
            logger.error(f"Błąd podczas ładowania ustawień: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania ustawień:\n{str(e)}"
            )
            
    def save_settings(self):
        """Zapisuje ustawienia z wszystkich zakładek."""
        try:
            # Ustawienia ogólne
            self.settings.setValue("data_directory", self.data_dir_input.text())
            self.settings.setValue("language", self.language_combo.currentText())
            self.settings.setValue("auto_login", self.auto_login_checkbox.isChecked())
            self.settings.setValue("auto_update", self.auto_update_checkbox.isChecked())
            self.settings.setValue("default_visit_duration", self.default_visit_duration.value())
            self.settings.setValue("default_vat_rate", self.default_vat_rate.currentText())

            # Ustawienia wyglądu
            self.settings.setValue("theme", self.theme_combo.currentText())
            self.settings.setValue("font", self.font_combo.currentFont().family())
            self.settings.setValue("font_size", self.font_size_spin.value())
            self.settings.setValue("show_status_in_header", self.show_status_checkbox.isChecked())
            self.settings.setValue("colored_status_labels", self.colored_status_checkbox.isChecked())

            # Ustawienia firmowe
            self.settings.setValue("company_name", self.company_name_input.text())
            self.settings.setValue("company_address", self.company_address_input.text())
            self.settings.setValue("company_city", self.company_city_input.text())
            self.settings.setValue("company_tax_id", self.company_tax_id_input.text())
            self.settings.setValue("company_phone", self.company_phone_input.text())
            self.settings.setValue("company_email", self.company_email_input.text())
            self.settings.setValue("company_website", self.company_website_input.text())
            self.settings.setValue("company_footer", self.company_footer_input.text())

            # Ustawienia kopii zapasowych
            self.settings.setValue("auto_backup", self.auto_backup_checkbox.isChecked())
            self.settings.setValue("backup_interval", self.backup_interval_spin.value())
            self.settings.setValue("backup_directory", self.backup_dir_input.text())
            self.settings.setValue("backup_count", self.backup_count_spin.value())
            self.settings.setValue("compress_backup", self.compress_backup_checkbox.isChecked())

            # Ustawienia komunikacji
            self.settings.setValue("email_address", self.email_address_input.text())
            self.settings.setValue("email_password", self.email_password_input.text())
            self.settings.setValue("smtp_server", self.smtp_server_input.text())
            self.settings.setValue("smtp_port", self.smtp_port_spin.value())
            self.settings.setValue("use_ssl", self.use_ssl_checkbox.isChecked())

            # Zapisz szablony
            self.save_templates()
            
            # Powiadomienie o sukcesie
            QMessageBox.information(
                self, 
                "Ustawienia", 
                "Ustawienia zostały pomyślnie zapisane."
            )
            
            # Emituj sygnał o zapisaniu ustawień
            self.settingsSaved.emit()
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania ustawień: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania ustawień:\n{str(e)}"
            ) 
            
    def setup_receipt_tab(self):
        """Konfiguracja zakładki szablonów potwierdzeń."""
        layout = QVBoxLayout(self.receipt_tab)
        layout.setSpacing(15)
        
        # Wybór szablonu
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Wybierz szablon:"))
        
        self.receipt_template_combo = QComboBox()
        self.receipt_template_combo.setMinimumWidth(250)
        self.receipt_template_combo.addItem("Domyślny", "default")
        self.receipt_template_combo.currentIndexChanged.connect(self.on_receipt_template_changed)
        select_layout.addWidget(self.receipt_template_combo)
        
        # Przyciski dodawania/usuwania szablonów
        self.add_receipt_template_btn = QPushButton("+")
        self.add_receipt_template_btn.setToolTip("Dodaj nowy szablon")
        self.add_receipt_template_btn.setFixedSize(30, 30)
        self.add_receipt_template_btn.clicked.connect(self.add_receipt_template)
        select_layout.addWidget(self.add_receipt_template_btn)
        
        self.remove_receipt_template_btn = QPushButton("-")
        self.remove_receipt_template_btn.setToolTip("Usuń wybrany szablon")
        self.remove_receipt_template_btn.setFixedSize(30, 30)
        self.remove_receipt_template_btn.clicked.connect(self.remove_receipt_template)
        select_layout.addWidget(self.remove_receipt_template_btn)
        
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Edytor treści potwierdzenia
        self.receipt_content_edit = QTextEdit()
        self.receipt_content_edit.setMinimumHeight(300)
        self.receipt_content_edit.textChanged.connect(self.update_receipt_preview)
        layout.addWidget(self.receipt_content_edit)
        
        # Podgląd potwierdzenia
        preview_group = QGroupBox("Podgląd")
        preview_layout = QVBoxLayout(preview_group)
        
        self.receipt_preview = QWebEngineView()
        self.receipt_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.receipt_preview)
        
        layout.addWidget(preview_group)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie HTML:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{phone_number} - Telefon klienta\n"
            "{email} - Email klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{location} - Lokalizacja w magazynie\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru\n"
            "{current_date} - Aktualna data\n"
            "{notes} - Uwagi\n"
            "{company_name} - Nazwa firmy\n"
            "{company_address} - Adres firmy\n"
            "{company_phone} - Telefon firmy\n"
            "{company_email} - Email firmy\n"
            "{company_website} - Strona firmy"
        )
        variables_label.setStyleSheet("font-family: monospace;")
        variables_layout.addWidget(variables_label)
        
        layout.addWidget(variables_group)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Resetuj do domyślnych")
        reset_btn.clicked.connect(self.reset_receipt_template)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("Zapisz zmiany")
        save_btn.clicked.connect(self.save_receipt_template)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)

    def update_font_preview(self):
        """Aktualizuje podgląd czcionki."""
        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_spin.value())
        
        self.font_preview.setFont(font)
        self.font_preview.setText(f"Podgląd czcionki {font.family()} {font.pointSize()}")

    def print_test_label(self):
        """Drukuje testową etykietę."""
        try:
            # Pokaż podgląd wydruku
            QMessageBox.information(
                self,
                "Drukowanie testowej etykiety",
                "Funkcja drukowania testowej etykiety będzie dostępna po implementacji obsługi drukarek."
            )
        except Exception as e:
            logger.error(f"Błąd podczas drukowania testowej etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas drukowania testowej etykiety:\n{str(e)}"
            )
            
    def get_company_data(self):
        """
        Pobiera aktualne dane firmy z ustawień.
        
        Returns:
            dict: Słownik z danymi firmy
        """
        return {
            "company_name": self.company_name_input.text() or "Serwis Opon",
            "company_address": self.company_address_input.text() or "",
            "company_city": self.company_city_input.text() or "",
            "company_tax_id": self.company_tax_id_input.text() or "",
            "company_phone": self.company_phone_input.text() or "",
            "company_email": self.company_email_input.text() or "",
            "company_website": self.company_website_input.text() or "",
            "company_footer": self.company_footer_input.text() or ""
        }   
            
    def add_email_template(self):
        """Dodaje nowy szablon email."""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "Nowy szablon email", 
                "Podaj nazwę nowego szablonu:"
            )
            
            if ok and name:
                # Sprawdź, czy szablon o tej nazwie już istnieje
                if name in self.templates.get("email", {}):
                    QMessageBox.warning(
                        self, 
                        "Błąd", 
                        f"Szablon o nazwie '{name}' już istnieje."
                    )
                    return
                
                # Dodaj nowy szablon na bazie domyślnego
                self.templates.setdefault("email", {})
                self.templates["email"][name] = DEFAULT_EMAIL_TEMPLATES["general"].copy()
                
                # Dodaj nowy szablon do listy
                self.email_template_combo.addItem(name)
                
                # Ustaw nowy szablon jako aktywny
                index = self.email_template_combo.count() - 1
                self.email_template_combo.setCurrentIndex(index)
                
                # Zapisz szablony
                self.save_templates()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania szablonu:\n{str(e)}"
            )

    def remove_email_template(self):
        """Usuwa wybrany szablon email."""
        try:
            # Pobierz bieżący indeks i nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_name = self.email_template_combo.currentText()
            
            # Nie pozwól usunąć domyślnych szablonów
            default_templates = ["Aktywny depozyt", "Do odbioru", "Zaległy depozyt", "Ogólny"]
            if template_name in default_templates:
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    "Nie można usunąć domyślnych szablonów."
                )
                return
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Usuń szablon", 
                f"Czy na pewno chcesz usunąć szablon '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Usuń szablon
                template_key = self.email_template_mapping.get(index, template_name)
                if template_key in self.templates.get("email", {}):
                    del self.templates["email"][template_key]
                
                # Usuń z listy
                self.email_template_combo.removeItem(index)
                
                # Zapisz zmiany
                self.save_templates()
                
                # Ustaw domyślny szablon
                self.email_template_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Błąd podczas usuwania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania szablonu:\n{str(e)}"
            )

    def save_email_template(self):
        """Zapisuje aktualny szablon email."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_name = self.email_template_mapping.get(index, self.email_template_combo.currentText())
            
            # Zaktualizuj szablon
            self.templates.setdefault("email", {})
            
            self.templates["email"][template_name] = {
                "subject": self.email_subject_edit.text(),
                "body": self.email_body_edit.toPlainText()
            }
            
            # Zapisz zmiany
            self.save_templates()
            
            # Powiadomienie
            QMessageBox.information(
                self, 
                "Szablon email", 
                f"Szablon '{template_name}' został zapisany."
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania szablonu:\n{str(e)}"
            )

    def reset_email_template(self):
        """Resetuje aktualny szablon do domyślnych ustawień."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_key = self.email_template_mapping.get(index)
            
            if not template_key:
                return
            
            # Przywróć domyślny szablon
            default_template = DEFAULT_EMAIL_TEMPLATES.get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Ustaw wartości
            self.email_subject_edit.setText(default_template.get("subject", ""))
            self.email_body_edit.setPlainText(default_template.get("body", ""))
            
            # Opcjonalnie - zapisz jako bieżący szablon
            self.templates.setdefault("email", {})
            self.templates["email"][template_key] = default_template
            self.save_templates()
            
            # Odśwież podgląd
            self.update_email_preview()
            
            QMessageBox.information(
                self, 
                "Reset szablonu", 
                f"Szablon '{template_key}' został zresetowany do ustawień domyślnych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas resetowania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas resetowania szablonu:\n{str(e)}"
            )

    def update_email_preview(self):
        """Aktualizuje podgląd szablonu email."""
        try:
            # Pobierz aktualną treść HTML
            html_content = self.email_body_edit.toPlainText()
            
            # Pobierz dane firmy
            company_data = self.get_company_data()
            
            # Przykładowe dane do podglądu
            preview_data = {
                "deposit_id": "D001",
                "client_name": "Jan Kowalski",
                "tire_size": "195/65 R15",
                "tire_type": "Letnie",
                "quantity": "4",
                "location": "Magazyn A",
                "deposit_date": "2024-03-22",
                "pickup_date": "2024-04-22",
                "status": "Aktywny",
                "notes": "Przegląd opon po sezonie",
                "phone_number": "123 456 789",
                "email": "jan.kowalski@example.com",
                "current_date": datetime.now().strftime("%d-%m-%Y"),
                **company_data  # Dodaj dane firmy
            }
            
            # Zastąp zmienne przykładowymi danymi
            for key, value in preview_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            self.email_preview.setHtml(html_content)
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji podglądu email: {e}")
            self.email_preview.setHtml(f"<p>Błąd podglądu: {str(e)}</p>")

    def add_label_template(self):
        """Dodaje nowy szablon etykiety."""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "Nowy szablon etykiety", 
                "Podaj nazwę nowego szablonu:"
            )
            
            if ok and name:
                # Sprawdź, czy szablon o tej nazwie już istnieje
                if name in self.templates.get("label", {}):
                    QMessageBox.warning(
                        self, 
                        "Błąd", 
                        f"Szablon o nazwie '{name}' już istnieje."
                    )
                    return
                
                # Dodaj nowy szablon na bazie domyślnego
                self.templates.setdefault("label", {})
                self.templates["label"][name] = DEFAULT_LABEL_TEMPLATE
                
                # Dodaj nowy szablon do listy
                self.label_template_combo.addItem(name, name)
                
                # Ustaw nowy szablon jako aktywny
                index = self.label_template_combo.count() - 1
                self.label_template_combo.setCurrentIndex(index)
                
                # Zapisz szablony
                self.save_templates()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania szablonu:\n{str(e)}"
            )

    def remove_label_template(self):
        """Usuwa wybrany szablon etykiety."""
        try:
            # Pobierz bieżący indeks i nazwę szablonu
            index = self.label_template_combo.currentIndex()
            template_name = self.label_template_combo.currentText()
            
            # Nie pozwól usunąć domyślnego szablonu
            if template_name == "Domyślny":
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    "Nie można usunąć domyślnego szablonu."
                )
                return
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Usuń szablon", 
                f"Czy na pewno chcesz usunąć szablon '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Usuń szablon
                template_key = self.label_template_combo.itemData(index) or template_name
                if template_key in self.templates.get("label", {}):
                    del self.templates["label"][template_key]
                
                # Usuń z listy
                self.label_template_combo.removeItem(index)
                
                # Zapisz zmiany
                self.save_templates()
                
                # Ustaw domyślny szablon
                self.label_template_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Błąd podczas usuwania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania szablonu:\n{str(e)}"
            )

    def save_label_template(self):
        """Zapisuje aktualny szablon etykiety."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.label_template_combo.currentIndex()
            template_name = self.label_template_combo.itemData(index) or "default"
            
            # Zaktualizuj szablon
            self.templates.setdefault("label", {})
            
            self.templates["label"][template_name] = self.label_content_edit.toPlainText()
            
            # Zapisz zmiany
            self.save_templates()
            
            # Powiadomienie
            QMessageBox.information(
                self, 
                "Szablon etykiety", 
                f"Szablon '{template_name}' został zapisany."
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania szablonu:\n{str(e)}"
            )

    def reset_label_template(self):
        """Resetuje aktualny szablon etykiety do domyślnych ustawień."""
        try:
            # Ustaw domyślny szablon
            self.label_content_edit.setPlainText(DEFAULT_LABEL_TEMPLATE)
            
            # Zapisz jako bieżący szablon
            self.templates.setdefault("label", {})
            self.templates["label"]["default"] = DEFAULT_LABEL_TEMPLATE
            self.save_templates()
            
            # Odśwież podgląd
            self.update_label_preview()
            
            QMessageBox.information(
                self, 
                "Reset szablonu", 
                "Szablon etykiety został zresetowany do ustawień domyślnych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas resetowania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas resetowania szablonu:\n{str(e)}"
            )

    def update_label_preview(self):
        """Aktualizuje podgląd szablonu etykiety."""
        try:
            # Pobierz aktualną treść HTML
            html_content = self.label_content_edit.toPlainText()
            
            # Pobierz dane firmy
            company_data = self.get_company_data()
            
            # Przykładowe dane do podglądu
            preview_data = {
                "deposit_id": "D001",
                "client_name": "Jan Kowalski",
                "tire_size": "195/65 R15",
                "tire_type": "Letnie",
                "quantity": "4",
                "location": "Magazyn A",
                "deposit_date": "2024-03-22",
                "pickup_date": "2024-04-22",
                "status": "Aktywny",
                "current_date": datetime.now().strftime("%d-%m-%Y"),
                **company_data  # Dodaj dane firmy
            }
            
            # Zastąp zmienne przykładowymi danymi
            for key, value in preview_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            self.label_preview.setHtml(html_content)
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji podglądu etykiety: {e}")
            self.label_preview.setHtml(f"<p>Błąd podglądu: {str(e)}</p>")
               
    def update_receipt_preview(self):
        """Aktualizuje podgląd szablonu potwierdzenia."""

    def init_templates_page(self, layout):
        """
        Inicjalizacja strony szablonów.
        
        Args:
            layout (QVBoxLayout): Layout strony
        """
        # Zakładki dla różnych typów szablonów
        templates_tabs = QTabWidget()
        
        # Zakładka szablonów email
        self.email_tab = QWidget()
        templates_tabs.addTab(self.email_tab, "Szablony Email")
        
        # Zakładka szablonów etykiet
        self.label_tab = QWidget()
        templates_tabs.addTab(self.label_tab, "Szablony Etykiet")
        
        # Zakładka szablonów potwierdzeń
        self.receipt_tab = QWidget()
        templates_tabs.addTab(self.receipt_tab, "Szablony Potwierdzeń")
        
        layout.addWidget(templates_tabs)
        
        # Konfiguracja zakładek
        self.setup_email_tab()
        self.setup_label_tab()
        self.setup_receipt_tab()
        
    def setup_email_tab(self):
        """Konfiguracja zakładki szablonów email."""
        layout = QVBoxLayout(self.email_tab)
        layout.setSpacing(15)
        
        # Wybór szablonu
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Wybierz szablon:"))
        
        self.email_template_combo = QComboBox()
        self.email_template_combo.setMinimumWidth(250)
        self.email_template_combo.addItems(["Aktywny depozyt", "Do odbioru", "Zaległy depozyt", "Ogólny"])
        self.email_template_combo.currentIndexChanged.connect(self.on_email_template_changed)
        select_layout.addWidget(self.email_template_combo)
        
        # Przyciski dodawania/usuwania szablonów
        self.add_email_template_btn = QPushButton("+")
        self.add_email_template_btn.setToolTip("Dodaj nowy szablon")
        self.add_email_template_btn.setFixedSize(30, 30)
        self.add_email_template_btn.clicked.connect(self.add_email_template)
        select_layout.addWidget(self.add_email_template_btn)
        
        self.remove_email_template_btn = QPushButton("-")
        self.remove_email_template_btn.setToolTip("Usuń wybrany szablon")
        self.remove_email_template_btn.setFixedSize(30, 30)
        self.remove_email_template_btn.clicked.connect(self.remove_email_template)
        select_layout.addWidget(self.remove_email_template_btn)
        
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Temat emaila
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Temat:"))
        
        self.email_subject_edit = QLineEdit()
        subject_layout.addWidget(self.email_subject_edit)
        
        layout.addLayout(subject_layout)
        
        # Edytor treści emaila
        self.email_body_edit = QTextEdit()
        self.email_body_edit.setMinimumHeight(200)
        self.email_body_edit.textChanged.connect(self.update_email_preview)
        layout.addWidget(self.email_body_edit)
        
        # Podgląd emaila
        preview_group = QGroupBox("Podgląd")
        preview_layout = QVBoxLayout(preview_group)
        
        self.email_preview = QWebEngineView()
        self.email_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.email_preview)
        
        layout.addWidget(preview_group)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie email:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{phone_number} - Telefon klienta\n"
            "{email} - Email klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru\n"
            "{status} - Status depozytu\n"
            "{current_date} - Aktualna data\n"
            "{company_name} - Nazwa firmy\n"
            "{company_address} - Adres firmy\n"
            "{company_phone} - Telefon firmy\n"
            "{company_email} - Email firmy\n"
            "{company_website} - Strona firmy"
        )
        variables_label.setStyleSheet("font-family: monospace;")
        variables_layout.addWidget(variables_label)
        
        layout.addWidget(variables_group)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Resetuj do domyślnych")
        reset_btn.clicked.connect(self.reset_email_template)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("Zapisz zmiany")
        save_btn.clicked.connect(self.save_email_template)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)

    def setup_label_tab(self):
        """Konfiguracja zakładki szablonów etykiet."""
        layout = QVBoxLayout(self.label_tab)
        layout.setSpacing(15)
        
        # Wybór szablonu
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Wybierz szablon:"))
        
        self.label_template_combo = QComboBox()
        self.label_template_combo.setMinimumWidth(250)
        self.label_template_combo.addItem("Domyślny", "default")
        self.label_template_combo.currentIndexChanged.connect(self.on_label_template_changed)
        select_layout.addWidget(self.label_template_combo)
        
        # Przyciski dodawania/usuwania szablonów
        self.add_label_template_btn = QPushButton("+")
        self.add_label_template_btn.setToolTip("Dodaj nowy szablon")
        self.add_label_template_btn.setFixedSize(30, 30)
        self.add_label_template_btn.clicked.connect(self.add_label_template)
        select_layout.addWidget(self.add_label_template_btn)
        
        self.remove_label_template_btn = QPushButton("-")
        self.remove_label_template_btn.setToolTip("Usuń wybrany szablon")
        self.remove_label_template_btn.setFixedSize(30, 30)
        self.remove_label_template_btn.clicked.connect(self.remove_label_template)
        select_layout.addWidget(self.remove_label_template_btn)
        
        select_layout.addStretch()
        
        # Przyciski drukowania
        self.print_test_label_btn = QPushButton("Wydrukuj próbną etykietę")
        self.print_test_label_btn.clicked.connect(self.print_test_label)
        select_layout.addWidget(self.print_test_label_btn)
        
        layout.addLayout(select_layout)
        
        # Edytor treści etykiety
        self.label_content_edit = QTextEdit()
        self.label_content_edit.setMinimumHeight(300)
        self.label_content_edit.textChanged.connect(self.update_label_preview)
        layout.addWidget(self.label_content_edit)
        
        # Podgląd etykiety
        preview_group = QGroupBox("Podgląd")
        preview_layout = QVBoxLayout(preview_group)
        
        self.label_preview = QWebEngineView()
        self.label_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.label_preview)
        
        layout.addWidget(preview_group)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie HTML:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{phone_number} - Telefon klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{location} - Lokalizacja w magazynie\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru\n"
            "{status} - Status depozytu\n"
            "{current_date} - Aktualna data\n"
            "{company_name} - Nazwa firmy\n"
            "{company_address} - Adres firmy\n"
            "{company_phone} - Telefon firmy"
        )
        variables_label.setStyleSheet("font-family: monospace;")
        variables_layout.addWidget(variables_label)
        
        layout.addWidget(variables_group)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Resetuj do domyślnych")
        reset_btn.clicked.connect(self.reset_label_template)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("Zapisz zmiany")
        save_btn.clicked.connect(self.save_label_template)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)

    def setup_receipt_tab(self):
        """Konfiguracja zakładki szablonów potwierdzeń."""
        layout = QVBoxLayout(self.receipt_tab)
        layout.setSpacing(15)
        
        # Wybór szablonu
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Wybierz szablon:"))
        
        self.receipt_template_combo = QComboBox()
        self.receipt_template_combo.setMinimumWidth(250)
        self.receipt_template_combo.addItem("Domyślny", "default")
        self.receipt_template_combo.currentIndexChanged.connect(self.on_receipt_template_changed)
        select_layout.addWidget(self.receipt_template_combo)
        
        # Przyciski dodawania/usuwania szablonów
        self.add_receipt_template_btn = QPushButton("+")
        self.add_receipt_template_btn.setToolTip("Dodaj nowy szablon")
        self.add_receipt_template_btn.setFixedSize(30, 30)
        self.add_receipt_template_btn.clicked.connect(self.add_receipt_template)
        select_layout.addWidget(self.add_receipt_template_btn)
        
        self.remove_receipt_template_btn = QPushButton("-")
        self.remove_receipt_template_btn.setToolTip("Usuń wybrany szablon")
        self.remove_receipt_template_btn.setFixedSize(30, 30)
        self.remove_receipt_template_btn.clicked.connect(self.remove_receipt_template)
        select_layout.addWidget(self.remove_receipt_template_btn)
        
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # Edytor treści potwierdzenia
        self.receipt_content_edit = QTextEdit()
        self.receipt_content_edit.setMinimumHeight(300)
        self.receipt_content_edit.textChanged.connect(self.update_receipt_preview)
        layout.addWidget(self.receipt_content_edit)
        
        # Podgląd potwierdzenia
        preview_group = QGroupBox("Podgląd")
        preview_layout = QVBoxLayout(preview_group)
        
        self.receipt_preview = QWebEngineView()
        self.receipt_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.receipt_preview)
        
        layout.addWidget(preview_group)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie HTML:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{phone_number} - Telefon klienta\n"
            "{email} - Email klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{location} - Lokalizacja w magazynie\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru\n"
            "{current_date} - Aktualna data\n"
            "{notes} - Uwagi\n"
            "{company_name} - Nazwa firmy\n"
            "{company_address} - Adres firmy\n"
            "{company_phone} - Telefon firmy\n"
            "{company_email} - Email firmy\n"
            "{company_website} - Strona firmy"
        )
        variables_label

    def on_email_template_changed(self, index):
        """Obsługuje zmianę szablonu email."""
        try:
            template_key = self.email_template_mapping.get(index)
            if not template_key:
                # Jeśli nie znaleziono w mapowaniu, użyj nazwy z combobox
                template_key = self.email_template_combo.currentText()
                
            # Ustal, który szablon załadować
            if template_key == "Aktywny depozyt":
                template_key = "active"
            elif template_key == "Do odbioru":
                template_key = "pickup"
            elif template_key == "Zaległy depozyt":
                template_key = "overdue"
            elif template_key == "Ogólny":
                template_key = "general"
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "email" in self.templates and template_key in self.templates["email"]:
                template = self.templates["email"][template_key]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_EMAIL_TEMPLATES.get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Ustaw pola formularza
            self.email_subject_edit.setText(template.get("subject", ""))
            self.email_body_edit.setPlainText(template.get("body", ""))
            
            # Aktualizuj podgląd
            self.update_email_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu email: {e}")

    def on_label_template_changed(self, index):
        """Obsługuje zmianę szablonu etykiety."""
        try:
            template_name = self.label_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "label" in self.templates and template_name in self.templates["label"]:
                template = self.templates["label"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_LABEL_TEMPLATE
            
            # Ustaw pola formularza
            self.label_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_label_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu etykiety: {e}")

    def on_receipt_template_changed(self, index):
        """Obsługuje zmianę szablonu potwierdzenia."""
        try:
            template_name = self.receipt_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = None
            
            # Sprawdź, czy szablon istnieje w wewnętrznej strukturze
            if "receipt" in self.templates and template_name in self.templates["receipt"]:
                template = self.templates["receipt"][template_name]
            else:
                # Jeśli nie istnieje, użyj domyślnego
                template = DEFAULT_RECEIPT_TEMPLATE
            
            # Ustaw pola formularza
            self.receipt_content_edit.setPlainText(template)
            
            # Aktualizuj podgląd
            self.update_receipt_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu potwierdzenia: {e}")

    def get_company_data(self):
        """
        Pobiera aktualne dane firmy z ustawień.
        
        Returns:
            dict: Słownik z danymi firmy
        """
        return {
            "company_name": self.company_name_input.text() or "Serwis Opon",
            "company_address": self.company_address_input.text() or "",
            "company_city": self.company_city_input.text() or "",
            "company_tax_id": self.company_tax_id_input.text() or "",
            "company_phone": self.company_phone_input.text() or "",
            "company_email": self.company_email_input.text() or "",
            "company_website": self.company_website_input.text() or "",
            "company_footer": self.company_footer_input.text() or ""
        }

    def print_test_label(self):
        """Drukuje testową etykietę."""
        try:
            # Pokaż podgląd wydruku
            QMessageBox.information(
                self,
                "Drukowanie testowej etykiety",
                "Funkcja drukowania testowej etykiety będzie dostępna po implementacji obsługi drukarek."
            )
        except Exception as e:
            logger.error(f"Błąd podczas drukowania testowej etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas drukowania testowej etykiety:\n{str(e)}"
            )

    def update_label_preview(self):
        """Aktualizuje podgląd szablonu etykiety."""
        try:
            # Pobierz aktualną treść HTML
            html_content = self.label_content_edit.toPlainText()
            
            # Pobierz dane firmy
            company_data = self.get_company_data()
            
            # Przykładowe dane do podglądu
            preview_data = {
                "deposit_id": "D001",
                "client_name": "Jan Kowalski",
                "tire_size": "195/65 R15",
                "tire_type": "Letnie",
                "quantity": "4",
                "location": "Magazyn A",
                "deposit_date": "2024-03-22",
                "pickup_date": "2024-04-22",
                "status": "Aktywny",
                "current_date": datetime.now().strftime("%d-%m-%Y"),
                **company_data  # Dodaj dane firmy
            }
            
            # Zastąp zmienne przykładowymi danymi
            for key, value in preview_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            self.label_preview.setHtml(html_content)
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji podglądu etykiety: {e}")
            self.label_preview.setHtml(f"<p>Błąd podglądu: {str(e)}</p>")

    def update_receipt_preview(self):
        """Aktualizuje podgląd szablonu potwierdzenia."""
        try:
            # Pobierz aktualną treść HTML
            html_content = self.receipt_content_edit.toPlainText()
            
            # Pobierz dane firmy
            company_data = self.get_company_data()
            
            # Przykładowe dane do podglądu
            preview_data = {
                "deposit_id": "D001",
                "client_name": "Jan Kowalski",
                "tire_size": "195/65 R15",
                "tire_type": "Letnie",
                "quantity": "4",
                "location": "Magazyn A",
                "deposit_date": "2024-03-22",
                "pickup_date": "2024-04-22",
                "status": "Aktywny",
                "notes": "Przegląd opon po sezonie",
                "phone_number": "123 456 789",
                "email": "jan.kowalski@example.com",
                "current_date": datetime.now().strftime("%d-%m-%Y"),
                **company_data  # Dodaj dane firmy
            }
            
            # Zastąp zmienne przykładowymi danymi
            for key, value in preview_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            self.receipt_preview.setHtml(html_content)
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji podglądu potwierdzenia: {e}")
            self.receipt_preview.setHtml(f"<p>Błąd podglądu: {str(e)}</p>")

    def update_email_preview(self):
        """Aktualizuje podgląd szablonu email."""
        try:
            # Pobierz aktualną treść HTML
            html_content = self.email_body_edit.toPlainText()
            
            # Pobierz dane firmy
            company_data = self.get_company_data()
            
            # Przykładowe dane do podglądu
            preview_data = {
                "deposit_id": "D001",
                "client_name": "Jan Kowalski",
                "tire_size": "195/65 R15",
                "tire_type": "Letnie",
                "quantity": "4",
                "location": "Magazyn A",
                "deposit_date": "2024-03-22",
                "pickup_date": "2024-04-22",
                "status": "Aktywny",
                "notes": "Przegląd opon po sezonie",
                "phone_number": "123 456 789",
                "email": "jan.kowalski@example.com",
                "current_date": datetime.now().strftime("%d-%m-%Y"),
                **company_data  # Dodaj dane firmy
            }
            
            # Zastąp zmienne przykładowymi danymi
            for key, value in preview_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            self.email_preview.setHtml(html_content)
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji podglądu email: {e}")
            self.email_preview.setHtml(f"<p>Błąd podglądu: {str(e)}</p>")

    def add_email_template(self):
        """Dodaje nowy szablon email."""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "Nowy szablon email", 
                "Podaj nazwę nowego szablonu:"
            )
            
            if ok and name:
                # Sprawdź, czy szablon o tej nazwie już istnieje
                if name in self.templates.get("email", {}):
                    QMessageBox.warning(
                        self, 
                        "Błąd", 
                        f"Szablon o nazwie '{name}' już istnieje."
                    )
                    return
                
                # Dodaj nowy szablon na bazie domyślnego
                self.templates.setdefault("email", {})
                self.templates["email"][name] = DEFAULT_EMAIL_TEMPLATES["general"].copy()
                
                # Dodaj nowy szablon do listy
                self.email_template_combo.addItem(name)
                
                # Ustaw nowy szablon jako aktywny
                index = self.email_template_combo.count() - 1
                self.email_template_combo.setCurrentIndex(index)
                
                # Zapisz szablony
                self.save_templates()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania szablonu:\n{str(e)}"
            )

    def remove_email_template(self):
        """Usuwa wybrany szablon email."""
        try:
            # Pobierz bieżący indeks i nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_name = self.email_template_combo.currentText()
            
            # Nie pozwól usunąć domyślnych szablonów
            default_templates = ["Aktywny depozyt", "Do odbioru", "Zaległy depozyt", "Ogólny"]
            if template_name in default_templates:
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    "Nie można usunąć domyślnych szablonów."
                )
                return
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Usuń szablon", 
                f"Czy na pewno chcesz usunąć szablon '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Usuń szablon
                template_key = self.email_template_mapping.get(index, template_name)
                if template_key in self.templates.get("email", {}):
                    del self.templates["email"][template_key]
                
                # Usuń z listy
                self.email_template_combo.removeItem(index)
                
                # Zapisz zmiany
                self.save_templates()
                
                # Ustaw domyślny szablon
                self.email_template_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Błąd podczas usuwania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania szablonu:\n{str(e)}"
            )

    def add_label_template(self):
        """Dodaje nowy szablon etykiety."""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "Nowy szablon etykiety", 
                "Podaj nazwę nowego szablonu:"
            )
            
            if ok and name:
                # Sprawdź, czy szablon o tej nazwie już istnieje
                if name in self.templates.get("label", {}):
                    QMessageBox.warning(
                        self, 
                        "Błąd", 
                        f"Szablon o nazwie '{name}' już istnieje."
                    )
                    return
                
                # Dodaj nowy szablon na bazie domyślnego
                self.templates.setdefault("label", {})
                self.templates["label"][name] = DEFAULT_LABEL_TEMPLATE
                
                # Dodaj nowy szablon do listy
                self.label_template_combo.addItem(name, name)
                
                # Ustaw nowy szablon jako aktywny
                index = self.label_template_combo.count() - 1
                self.label_template_combo.setCurrentIndex(index)
                
                # Zapisz szablony
                self.save_templates()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania szablonu:\n{str(e)}"
            )

    def remove_label_template(self):
        """Usuwa wybrany szablon etykiety."""
        try:
            # Pobierz bieżący indeks i nazwę szablonu
            index = self.label_template_combo.currentIndex()
            template_name = self.label_template_combo.currentText()
            
            # Nie pozwól usunąć domyślnego szablonu
            if template_name == "Domyślny":
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    "Nie można usunąć domyślnego szablonu."
                )
                return
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Usuń szablon", 
                f"Czy na pewno chcesz usunąć szablon '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Usuń szablon
                template_key = self.label_template_combo.itemData(index) or template_name
                if template_key in self.templates.get("label", {}):
                    del self.templates["label"][template_key]
                
                # Usuń z listy
                self.label_template_combo.removeItem(index)
                
                # Zapisz zmiany
                self.save_templates()
                
                # Ustaw domyślny szablon
                self.label_template_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Błąd podczas usuwania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania szablonu:\n{str(e)}"
            )

    def save_label_template(self):
        """Zapisuje aktualny szablon etykiety."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.label_template_combo.currentIndex()
            template_name = self.label_template_combo.itemData(index) or "default"
            
            # Zaktualizuj szablon
            self.templates.setdefault("label", {})
            
            self.templates["label"][template_name] = self.label_content_edit.toPlainText()
            
            # Zapisz zmiany
            self.save_templates()
            
            # Powiadomienie
            QMessageBox.information(
                self, 
                "Szablon etykiety", 
                f"Szablon '{template_name}' został zapisany."
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania szablonu:\n{str(e)}"
            )

    def reset_label_template(self):
        """Resetuje aktualny szablon etykiety do domyślnych ustawień."""
        try:
            # Ustaw domyślny szablon
            self.label_content_edit.setPlainText(DEFAULT_LABEL_TEMPLATE)
            
            # Zapisz jako bieżący szablon
            self.templates.setdefault("label", {})
            self.templates["label"]["default"] = DEFAULT_LABEL_TEMPLATE
            self.save_templates()
            
            # Odśwież podgląd
            self.update_label_preview()
            
            QMessageBox.information(
                self, 
                "Reset szablonu", 
                "Szablon etykiety został zresetowany do ustawień domyślnych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas resetowania szablonu etykiety: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas resetowania szablonu:\n{str(e)}"
            )

    def add_receipt_template(self):
        """Dodaje nowy szablon potwierdzenia."""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "Nowy szablon potwierdzenia", 
                "Podaj nazwę nowego szablonu:"
            )
            
            if ok and name:
                # Sprawdź, czy szablon o tej nazwie już istnieje
                if name in self.templates.get("receipt", {}):
                    QMessageBox.warning(
                        self, 
                        "Błąd", 
                        f"Szablon o nazwie '{name}' już istnieje."
                    )
                    return
                
                # Dodaj nowy szablon na bazie domyślnego
                self.templates.setdefault("receipt", {})
                self.templates["receipt"][name] = DEFAULT_RECEIPT_TEMPLATE
                
                # Dodaj nowy szablon do listy
                self.receipt_template_combo.addItem(name, name)
                
                # Ustaw nowy szablon jako aktywny
                index = self.receipt_template_combo.count() - 1
                self.receipt_template_combo.setCurrentIndex(index)
                
                # Zapisz szablony
                self.save_templates()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania szablonu potwierdzenia: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania szablonu:\n{str(e)}"
            )

    def remove_receipt_template(self):
        """Usuwa wybrany szablon potwierdzenia."""
        try:
            # Pobierz bieżący indeks i nazwę szablonu
            index = self.receipt_template_combo.currentIndex()
            template_name = self.receipt_template_combo.currentText()
            
            # Nie pozwól usunąć domyślnego szablonu
            if template_name == "Domyślny":
                QMessageBox.warning(
                    self, 
                    "Błąd", 
                    "Nie można usunąć domyślnego szablonu."
                )
                return
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Usuń szablon", 
                f"Czy na pewno chcesz usunąć szablon '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Usuń szablon
                template_key = self.receipt_template_combo.itemData(index) or template_name
                if template_key in self.templates.get("receipt", {}):
                    del self.templates["receipt"][template_key]
                
                # Usuń z listy
                self.receipt_template_combo.removeItem(index)
                
                # Zapisz zmiany
                self.save_templates()
                
                # Ustaw domyślny szablon
                self.receipt_template_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Błąd podczas usuwania szablonu potwierdzenia: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania szablonu:\n{str(e)}"
            )

    def save_receipt_template(self):
        """Zapisuje aktualny szablon potwierdzenia."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.receipt_template_combo.currentIndex()
            template_name = self.receipt_template_combo.itemData(index) or "default"
            
            # Zaktualizuj szablon
            self.templates.setdefault("receipt", {})
            
            self.templates["receipt"][template_name] = self.receipt_content_edit.toPlainText()
            
            # Zapisz zmiany
            self.save_templates()
            
            # Powiadomienie
            QMessageBox.information(
                self, 
                "Szablon potwierdzenia", 
                f"Szablon '{template_name}' został zapisany."
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonu potwierdzenia: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania szablonu:\n{str(e)}"
            )

    def reset_receipt_template(self):
        """Resetuje aktualny szablon potwierdzenia do domyślnych ustawień."""
        try:
            # Ustaw domyślny szablon
            self.receipt_content_edit.setPlainText(DEFAULT_RECEIPT_TEMPLATE)
            
            # Zapisz jako bieżący szablon
            self.templates.setdefault("receipt", {})
            self.templates["receipt"]["default"] = DEFAULT_RECEIPT_TEMPLATE
            self.save_templates()
            
            # Odśwież podgląd
            self.update_receipt_preview()
            
            QMessageBox.information(
                self, 
                "Reset szablonu", 
                "Szablon potwierdzenia został zresetowany do ustawień domyślnych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas resetowania szablonu potwierdzenia: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas resetowania szablonu:\n{str(e)}"
            )

    def save_email_template(self):
        """Zapisuje aktualny szablon email."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_name = self.email_template_mapping.get(index, self.email_template_combo.currentText())
            
            # Zaktualizuj szablon
            self.templates.setdefault("email", {})
            
            self.templates["email"][template_name] = {
                "subject": self.email_subject_edit.text(),
                "body": self.email_body_edit.toPlainText()
            }
            
            # Zapisz zmiany
            self.save_templates()
            
            # Powiadomienie
            QMessageBox.information(
                self, 
                "Szablon email", 
                f"Szablon '{template_name}' został zapisany."
            )
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania szablonu:\n{str(e)}"
            )

    def reset_email_template(self):
        """Resetuje aktualny szablon do domyślnych ustawień."""
        try:
            # Pobierz aktualną nazwę szablonu
            index = self.email_template_combo.currentIndex()
            template_key = self.email_template_mapping.get(index)
            
            if not template_key:
                return
            
            # Przywróć domyślny szablon
            default_template = DEFAULT_EMAIL_TEMPLATES.get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Ustaw wartości
            self.email_subject_edit.setText(default_template.get("subject", ""))
            self.email_body_edit.setPlainText(default_template.get("body", ""))
            
            # Opcjonalnie - zapisz jako bieżący szablon
            self.templates.setdefault("email", {})
            self.templates["email"][template_key] = default_template
            self.save_templates()
            
            # Odśwież podgląd
            self.update_email_preview()
            
            QMessageBox.information(
                self, 
                "Reset szablonu", 
                f"Szablon '{template_key}' został zresetowany do ustawień domyślnych."
            )
        except Exception as e:
            logger.error(f"Błąd podczas resetowania szablonu email: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas resetowania szablonu:\n{str(e)}"
            )

    def load_templates(self):
        """Ładuje szablony z pliku."""
        try:
            # Sprawdź, czy plik z szablonami istnieje
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                # Plik nie istnieje, utwórz z domyślnymi szablonami
                self.templates = {
                    "email": DEFAULT_EMAIL_TEMPLATES,
                    "label": {"default": DEFAULT_LABEL_TEMPLATE},
                    "receipt": {"default": DEFAULT_RECEIPT_TEMPLATE}
                }
                self.save_templates()
                
            # Wypełnienie combo boxów z nazwami szablonów
            self.email_template_mapping = {
                0: "active",
                1: "pickup",
                2: "overdue",
                3: "general"
            }
            
            # Ładowanie niestandardowych szablonów email
            for template_name in self.templates.get("email", {}):
                if template_name not in ["active", "pickup", "overdue", "general"]:
                    self.email_template_combo.addItem(template_name)
                    index = self.email_template_combo.count() - 1
                    self.email_template_mapping[index] = template_name
            
            # Ładowanie szablonów etykiet
            self.label_template_combo.clear()
            self.label_template_combo.addItem("Domyślny", "default")
            
            label_templates = self.templates.get("label", {})
            for template_name in label_templates:
                if template_name != "default":
                    self.label_template_combo.addItem(template_name, template_name)
            
            # Ładowanie szablonów potwierdzeń
            self.receipt_template_combo.clear()
            self.receipt_template_combo.addItem("Domyślny", "default")
            
            receipt_templates = self.templates.get("receipt", {})
            for template_name in receipt_templates:
                if template_name != "default":
                    self.receipt_template_combo.addItem(template_name, template_name)
            
            # Ustawienie domyślnych szablonów
            self.on_email_template_changed(0)
            self.on_label_template_changed(0)
            self.on_receipt_template_changed(0)
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas ładowania szablonów:\n{str(e)}"
            )

    def save_templates(self):
        """Zapisuje szablony do pliku."""
        try:
            # Upewnij się, że katalog istnieje
            ensure_dir_exists(os.path.dirname(self.templates_file))
            
            # Zapisz szablony do pliku JSON
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas zapisywania szablonów:\n{str(e)}"
            )