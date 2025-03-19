#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog ustawień aplikacji.
"""

import os
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QFontComboBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QFont

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class SettingsDialog(QDialog):
    """
    Dialog umożliwiający konfigurację ustawień aplikacji.
    """
    
    def __init__(self, parent=None):
        """
        Inicjalizacja dialogu ustawień.
        
        Args:
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.setWindowTitle("Ustawienia")
        self.resize(600, 400)
        
        # Inicjalizacja ustawień
        self.settings = QSettings("TireDepositManager", "Settings")
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie aktualnych ustawień
        self.load_settings()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        main_layout = QVBoxLayout(self)
        
        # Zakładki ustawień
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Zakładka ustawień ogólnych
        general_tab = QWidget()
        self.init_general_tab(general_tab)
        self.tabs.addTab(general_tab, QIcon(os.path.join(ICONS_DIR, "settings.png")), "Ogólne")
        
        # Zakładka ustawień wyglądu
        appearance_tab = QWidget()
        self.init_appearance_tab(appearance_tab)
        self.tabs.addTab(appearance_tab, QIcon(os.path.join(ICONS_DIR, "ui.png")), "Wygląd")
        
        # Zakładka ustawień firmowych
        company_tab = QWidget()
        self.init_company_tab(company_tab)
        self.tabs.addTab(company_tab, QIcon(os.path.join(ICONS_DIR, "company.png")), "Dane firmy")
        
        # Zakładka ustawień kopii zapasowych
        backup_tab = QWidget()
        self.init_backup_tab(backup_tab)
        self.tabs.addTab(backup_tab, QIcon(os.path.join(ICONS_DIR, "backup.png")), "Kopie zapasowe")
        
        # Zakładka ustawień komunikacji
        communication_tab = QWidget()
        self.init_communication_tab(communication_tab)
        self.tabs.addTab(communication_tab, QIcon(os.path.join(ICONS_DIR, "email.png")), "Komunikacja")
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def init_general_tab(self, tab):
        """
        Inicjalizacja zakładki ustawień ogólnych.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Katalog danych
        data_layout = QHBoxLayout()
        self.data_dir_input = QLineEdit()
        self.data_dir_input.setReadOnly(True)
        data_layout.addWidget(self.data_dir_input, 1)
        
        browse_data_dir_button = QPushButton("Przeglądaj...")
        browse_data_dir_button.clicked.connect(self.browse_data_dir)
        data_layout.addWidget(browse_data_dir_button)
        
        layout.addRow("Katalog danych:", data_layout)
        
        # Język
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Polski", "English"])
        layout.addRow("Język:", self.language_combo)
        
        # Automatyczne logowanie
        self.auto_login_checkbox = QCheckBox("Automatycznie loguj przy starcie")
        layout.addRow("", self.auto_login_checkbox)
        
        # Automatyczne aktualizacje
        self.auto_update_checkbox = QCheckBox("Sprawdzaj aktualizacje przy starcie")
        layout.addRow("", self.auto_update_checkbox)
        
        # Domyślny czas wizyty
        self.default_visit_duration = QSpinBox()
        self.default_visit_duration.setRange(15, 240)
        self.default_visit_duration.setSingleStep(15)
        self.default_visit_duration.setValue(60)
        self.default_visit_duration.setSuffix(" min")
        layout.addRow("Domyślny czas trwania wizyty:", self.default_visit_duration)
        
        # Domyślna stawka VAT
        self.default_vat_rate = QComboBox()
        self.default_vat_rate.addItems(["23%", "8%", "5%", "0%"])
        layout.addRow("Domyślna stawka VAT:", self.default_vat_rate)
    
    def init_appearance_tab(self, tab):
        """
        Inicjalizacja zakładki ustawień wyglądu.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Motyw
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        layout.addRow("Motyw:", self.theme_combo)
        
        # Czcionka
        self.font_combo = QFontComboBox()
        layout.addRow("Czcionka:", self.font_combo)
        
        # Rozmiar czcionki
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setSingleStep(1)
        self.font_size_spin.setValue(10)
        layout.addRow("Rozmiar czcionki:", self.font_size_spin)
        
        # Podgląd czcionki
        self.font_preview = QLabel("Podgląd czcionki")
        self.font_preview.setStyleSheet("""
            background-color: white;
            border: 1px solid #bdc3c7;
            padding: 10px;
        """)
        self.font_preview.setAlignment(Qt.AlignCenter)
        layout.addRow("Podgląd:", self.font_preview)
        
        # Podłączenie zmiany czcionki do podglądu
        self.font_combo.currentFontChanged.connect(self.update_font_preview)
        self.font_size_spin.valueChanged.connect(self.update_font_preview)
        
        # Pokazywanie statusu w nagłówku
        self.show_status_checkbox = QCheckBox("Pokazuj status w nagłówku")
        layout.addRow("", self.show_status_checkbox)
        
        # Kolorowe etykiety statusu
        self.colored_status_checkbox = QCheckBox("Użyj kolorowych etykiet statusu")
        layout.addRow("", self.colored_status_checkbox)
    
    def init_company_tab(self, tab):
        """
        Inicjalizacja zakładki ustawień firmowych.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Nazwa firmy
        self.company_name_input = QLineEdit()
        layout.addRow("Nazwa firmy:", self.company_name_input)
        
        # Adres
        self.company_address_input = QLineEdit()
        layout.addRow("Adres:", self.company_address_input)
        
        # Miasto i kod pocztowy
        self.company_city_input = QLineEdit()
        layout.addRow("Miasto i kod pocztowy:", self.company_city_input)
        
        # NIP
        self.company_tax_id_input = QLineEdit()
        layout.addRow("NIP:", self.company_tax_id_input)
        
        # Telefon
        self.company_phone_input = QLineEdit()
        layout.addRow("Telefon:", self.company_phone_input)
        
        # E-mail
        self.company_email_input = QLineEdit()
        layout.addRow("E-mail:", self.company_email_input)
        
        # Strona www
        self.company_website_input = QLineEdit()
        layout.addRow("Strona www:", self.company_website_input)
        
        # Informacje dodatkowe (stopka faktur)
        self.company_footer_input = QLineEdit()
        layout.addRow("Stopka dokumentów:", self.company_footer_input)
    
    def init_backup_tab(self, tab):
        """
        Inicjalizacja zakładki ustawień kopii zapasowych.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Automatyczne kopie zapasowe
        self.auto_backup_checkbox = QCheckBox("Automatycznie twórz kopie zapasowe")
        layout.addRow("", self.auto_backup_checkbox)
        
        # Interwał kopii zapasowych
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setSingleStep(1)
        self.backup_interval_spin.setValue(7)
        self.backup_interval_spin.setSuffix(" dni")
        layout.addRow("Interwał kopii zapasowych:", self.backup_interval_spin)
        
        # Katalog kopii zapasowych
        backup_dir_layout = QHBoxLayout()
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setReadOnly(True)
        backup_dir_layout.addWidget(self.backup_dir_input, 1)
        
        browse_backup_dir_button = QPushButton("Przeglądaj...")
        browse_backup_dir_button.clicked.connect(self.browse_backup_dir)
        backup_dir_layout.addWidget(browse_backup_dir_button)
        
        layout.addRow("Katalog kopii zapasowych:", backup_dir_layout)
        
        # Ilość kopii do przechowywania
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        self.backup_count_spin.setSingleStep(1)
        self.backup_count_spin.setValue(10)
        layout.addRow("Ilość kopii do przechowywania:", self.backup_count_spin)
        
        # Kompresja kopii zapasowych
        self.compress_backup_checkbox = QCheckBox("Kompresuj kopie zapasowe")
        layout.addRow("", self.compress_backup_checkbox)
        
        # Przycisk do ręcznego wykonania kopii
        manual_backup_button = QPushButton("Wykonaj kopię teraz")
        manual_backup_button.clicked.connect(self.create_manual_backup)
        layout.addRow("", manual_backup_button)
    
    def init_communication_tab(self, tab):
        """
        Inicjalizacja zakładki ustawień komunikacji.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Ustawienia e-mail
        email_section = QLabel("Ustawienia e-mail")
        email_section.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addRow(email_section)
        
        # Adres e-mail
        self.email_address_input = QLineEdit()
        layout.addRow("Adres e-mail:", self.email_address_input)
        
        # Hasło (w praktyce powinno być zabezpieczone)
        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Hasło:", self.email_password_input)
        
        # Serwer SMTP
        self.smtp_server_input = QLineEdit()
        layout.addRow("Serwer SMTP:", self.smtp_server_input)
        
        # Port SMTP
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        layout.addRow("Port SMTP:", self.smtp_port_spin)
        
        # Użyj SSL
        self.use_ssl_checkbox = QCheckBox("Użyj SSL/TLS")
        layout.addRow("", self.use_ssl_checkbox)
        
        # Ustawienia SMS
        sms_section = QLabel("Ustawienia SMS")
        sms_section.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addRow(sms_section)
        
        # API SMS
        self.sms_api_combo = QComboBox()
        self.sms_api_combo.addItems(["SerwerSMS.pl", "SMSAPI.pl", "SMSCenter.pl", "Inne"])
        layout.addRow("Usługa SMS:", self.sms_api_combo)
        
        # Klucz API
        self.sms_api_key_input = QLineEdit()
        layout.addRow("Klucz API:", self.sms_api_key_input)
        
        # Nazwa nadawcy
        self.sms_sender_input = QLineEdit()
        layout.addRow("Nazwa nadawcy:", self.sms_sender_input)
        
        # Testowy SMS
        test_sms_button = QPushButton("Wyślij testowy SMS")
        test_sms_button.clicked.connect(self.send_test_sms)
        layout.addRow("", test_sms_button)
    
    def update_font_preview(self):
        """Aktualizuje podgląd czcionki na podstawie wybranych ustawień."""
        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_spin.value())
        self.font_preview.setFont(font)
    
    def browse_data_dir(self):
        """Otwiera okno wyboru katalogu danych."""
        from PySide6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog danych", self.data_dir_input.text()
        )
        if directory:
            self.data_dir_input.setText(directory)
    
    def browse_backup_dir(self):
        """Otwiera okno wyboru katalogu kopii zapasowych."""
        from PySide6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog kopii zapasowych", self.backup_dir_input.text()
        )
        if directory:
            self.backup_dir_input.setText(directory)
    
    def create_manual_backup(self):
        """Wykonuje ręczną kopię zapasową bazy danych."""
        try:
            from utils.database import backup_database
            from utils.paths import BACKUP_DIR
            import os
            from datetime import datetime
            
            # Tworzenie ścieżki do pliku kopii zapasowej
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"manual_backup_{timestamp}.db")
            
            # Tworzenie kopii zapasowej
            parent = self.parent()
            result = backup_database(parent.conn if parent else None, backup_path)
            
            if result:
                QMessageBox.information(
                    self, 
                    "Kopia zapasowa", 
                    f"Pomyślnie utworzono kopię zapasową:\n{backup_path}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Kopia zapasowa", 
                    "Nie udało się utworzyć kopii zapasowej."
                )
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia ręcznej kopii zapasowej: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas tworzenia kopii zapasowej:\n{str(e)}"
            )
    
    def send_test_sms(self):
        """Wysyła testowy SMS do sprawdzenia konfiguracji."""
        try:
            # W rzeczywistej implementacji należałoby wykorzystać odpowiednie API
            QMessageBox.information(
                self, 
                "Test SMS", 
                "Funkcja wysyłania testowego SMS jest niedostępna w tej wersji."
            )
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania testowego SMS: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas wysyłania testowego SMS:\n{str(e)}"
            )
    
    def load_settings(self):
        """Ładuje zapisane ustawienia do formularza."""
        # Ogólne
        from utils.paths import APP_DATA_DIR, BACKUP_DIR
        
        self.data_dir_input.setText(self.settings.value("data_dir", APP_DATA_DIR))
        self.language_combo.setCurrentText(self.settings.value("language", "Polski"))
        self.auto_login_checkbox.setChecked(self.settings.value("auto_login", False, type=bool))
        self.auto_update_checkbox.setChecked(self.settings.value("auto_update", True, type=bool))
        self.default_visit_duration.setValue(self.settings.value("default_visit_duration", 60, type=int))
        self.default_vat_rate.setCurrentText(self.settings.value("default_vat_rate", "23%"))
        
        # Wygląd
        self.theme_combo.setCurrentText(self.settings.value("theme", "Light"))
        
        font_family = self.settings.value("font_family", "Segoe UI")
        font = QFont(font_family)
        self.font_combo.setCurrentFont(font)
        
        self.font_size_spin.setValue(self.settings.value("font_size", 10, type=int))
        self.show_status_checkbox.setChecked(self.settings.value("show_status", True, type=bool))
        self.colored_status_checkbox.setChecked(self.settings.value("colored_status", True, type=bool))
        
        # Ustawienia firmy
        self.company_name_input.setText(self.settings.value("company_name", "Serwis Opon MATEO"))
        self.company_address_input.setText(self.settings.value("company_address", "ul. Przykładowa 123"))
        self.company_city_input.setText(self.settings.value("company_city", "00-000 Miasto"))
        self.company_tax_id_input.setText(self.settings.value("company_tax_id", "123-456-78-90"))
        self.company_phone_input.setText(self.settings.value("company_phone", "+48 123 456 789"))
        self.company_email_input.setText(self.settings.value("company_email", "kontakt@serwisopony.pl"))
        self.company_website_input.setText(self.settings.value("company_website", "www.serwisopony.pl"))
        self.company_footer_input.setText(self.settings.value("company_footer", "Dziękujemy za skorzystanie z naszych usług!"))
        
        # Kopie zapasowe
        self.auto_backup_checkbox.setChecked(self.settings.value("auto_backup", True, type=bool))
        self.backup_interval_spin.setValue(self.settings.value("backup_interval", 7, type=int))
        self.backup_dir_input.setText(self.settings.value("backup_dir", BACKUP_DIR))
        self.backup_count_spin.setValue(self.settings.value("backup_count", 10, type=int))
        self.compress_backup_checkbox.setChecked(self.settings.value("compress_backup", False, type=bool))
        
        # Komunikacja
        self.email_address_input.setText(self.settings.value("email_address", ""))
        self.email_password_input.setText(self.settings.value("email_password", ""))
        self.smtp_server_input.setText(self.settings.value("smtp_server", "smtp.gmail.com"))
        self.smtp_port_spin.setValue(self.settings.value("smtp_port", 587, type=int))
        self.use_ssl_checkbox.setChecked(self.settings.value("use_ssl", True, type=bool))
        
        self.sms_api_combo.setCurrentText(self.settings.value("sms_api", "SerwerSMS.pl"))
        self.sms_api_key_input.setText(self.settings.value("sms_api_key", ""))
        self.sms_sender_input.setText(self.settings.value("sms_sender", "SERWIS"))
        
        # Aktualizacja podglądu czcionki
        self.update_font_preview()
    
    def save_settings(self):
        """Zapisuje ustawienia z formularza."""
        try:
            # Ogólne
            self.settings.setValue("data_dir", self.data_dir_input.text())
            self.settings.setValue("language", self.language_combo.currentText())
            self.settings.setValue("auto_login", self.auto_login_checkbox.isChecked())
            self.settings.setValue("auto_update", self.auto_update_checkbox.isChecked())
            self.settings.setValue("default_visit_duration", self.default_visit_duration.value())
            self.settings.setValue("default_vat_rate", self.default_vat_rate.currentText())
            
            # Wygląd
            self.settings.setValue("theme", self.theme_combo.currentText())
            self.settings.setValue("font_family", self.font_combo.currentFont().family())
            self.settings.setValue("font_size", self.font_size_spin.value())
            self.settings.setValue("show_status", self.show_status_checkbox.isChecked())
            self.settings.setValue("colored_status", self.colored_status_checkbox.isChecked())
            
            # Ustawienia firmy
            self.settings.setValue("company_name", self.company_name_input.text())
            self.settings.setValue("company_address", self.company_address_input.text())
            self.settings.setValue("company_city", self.company_city_input.text())
            self.settings.setValue("company_tax_id", self.company_tax_id_input.text())
            self.settings.setValue("company_phone", self.company_phone_input.text())
            self.settings.setValue("company_email", self.company_email_input.text())
            self.settings.setValue("company_website", self.company_website_input.text())
            self.settings.setValue("company_footer", self.company_footer_input.text())
            
            # Kopie zapasowe
            self.settings.setValue("auto_backup", self.auto_backup_checkbox.isChecked())
            self.settings.setValue("backup_interval", self.backup_interval_spin.value())
            self.settings.setValue("backup_dir", self.backup_dir_input.text())
            self.settings.setValue("backup_count", self.backup_count_spin.value())
            self.settings.setValue("compress_backup", self.compress_backup_checkbox.isChecked())
            
            # Komunikacja
            self.settings.setValue("email_address", self.email_address_input.text())
            self.settings.setValue("email_password", self.email_password_input.text())
            self.settings.setValue("smtp_server", self.smtp_server_input.text())
            self.settings.setValue("smtp_port", self.smtp_port_spin.value())
            self.settings.setValue("use_ssl", self.use_ssl_checkbox.isChecked())
            
            self.settings.setValue("sms_api", self.sms_api_combo.currentText())
            self.settings.setValue("sms_api_key", self.sms_api_key_input.text())
            self.settings.setValue("sms_sender", self.sms_sender_input.text())
            
            logger.info("Ustawienia zostały zapisane")
            self.accept()
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania ustawień: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas zapisywania ustawień:\n{str(e)}"
            )