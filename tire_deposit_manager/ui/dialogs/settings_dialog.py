#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog ustawień aplikacji.
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QFontComboBox, QTextEdit, QGroupBox,
    QFileDialog, QFrame, QScrollArea, QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt, QSettings, QDir, QFile
from PySide6.QtGui import QIcon, QFont, QTextDocument, QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView

from utils.paths import ICONS_DIR, CONFIG_DIR, ensure_dir_exists
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireDepositManager")

# Domyślne szablony HTML
DEFAULT_EMAIL_TEMPLATES = {
    "active": {
        "subject": "Twój depozyt opon - informacja o przechowywaniu",
        "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Informacja o depozycie opon</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #4dabf7;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            font-size: 0.8em;
            color: #6c757d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #dee2e6;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #e9ecef;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{company_name}</h2>
        <p>Informacja o depozycie opon</p>
    </div>
    <div class="content">
        <p>Szanowny Kliencie,</p>
        <p>Twoje opony są bezpiecznie przechowywane w naszym magazynie.</p>
        
        <table>
            <tr>
                <th colspan="2">Szczegóły depozytu</th>
            </tr>
            <tr>
                <td>Numer depozytu:</td>
                <td><strong>{deposit_id}</strong></td>
            </tr>
            <tr>
                <td>Rozmiar opon:</td>
                <td>{tire_size}</td>
            </tr>
            <tr>
                <td>Typ opon:</td>
                <td>{tire_type}</td>
            </tr>
            <tr>
                <td>Ilość:</td>
                <td>{quantity} szt.</td>
            </tr>
            <tr>
                <td>Data przyjęcia:</td>
                <td>{deposit_date}</td>
            </tr>
            <tr>
                <td>Planowana data odbioru:</td>
                <td>{pickup_date}</td>
            </tr>
        </table>
        
        <p>W razie pytań prosimy o kontakt z naszym serwisem.</p>
        <p>Z poważaniem,<br>{company_name}</p>
    </div>
    <div class="footer">
        <p>{company_address}, {company_phone}<br>
        {company_email}, {company_website}</p>
    </div>
</body>
</html>"""
    },
    "pickup": {
        "subject": "Twoje opony są gotowe do odbioru",
        "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Gotowe do odbioru</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #fd7e14;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            font-size: 0.8em;
            color: #6c757d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #dee2e6;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #e9ecef;
        }
        .highlight {
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #fd7e14;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{company_name}</h2>
        <p>Gotowe do odbioru</p>
    </div>
    <div class="content">
        <p>Szanowny Kliencie,</p>
        <p>Twoje opony są gotowe do odbioru z naszego magazynu.</p>
        
        <div class="highlight">
            <p>Prosimy o odbiór opon do dnia: <strong>{pickup_date}</strong></p>
        </div>
        
        <table>
            <tr>
                <th colspan="2">Szczegóły depozytu</th>
            </tr>
            <tr>
                <td>Numer depozytu:</td>
                <td><strong>{deposit_id}</strong></td>
            </tr>
            <tr>
                <td>Rozmiar opon:</td>
                <td>{tire_size}</td>
            </tr>
            <tr>
                <td>Typ opon:</td>
                <td>{tire_type}</td>
            </tr>
            <tr>
                <td>Ilość:</td>
                <td>{quantity} szt.</td>
            </tr>
            <tr>
                <td>Data przyjęcia:</td>
                <td>{deposit_date}</td>
            </tr>
        </table>
        
        <p>Zapraszamy w godzinach pracy naszego serwisu.</p>
        <p>Z poważaniem,<br>{company_name}</p>
    </div>
    <div class="footer">
        <p>{company_address}, {company_phone}<br>
        {company_email}, {company_website}</p>
    </div>
</body>
</html>"""
    },
    "overdue": {
        "subject": "Pilne - Zaległy depozyt opon",
        "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Zaległy depozyt</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #fa5252;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            font-size: 0.8em;
            color: #6c757d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #dee2e6;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #e9ecef;
        }
        .warning {
            background-color: #f8d7da;
            border-left: 4px solid #fa5252;
            padding: 15px;
            margin: 20px 0;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{company_name}</h2>
        <p>Zaległy depozyt opon</p>
    </div>
    <div class="content">
        <p>Szanowny Kliencie,</p>
        
        <div class="warning">
            <p><strong>Przypominamy o zaległym depozycie opon w naszym magazynie.</strong></p>
            <p>Termin odbioru minął: <strong>{pickup_date}</strong></p>
        </div>
        
        <table>
            <tr>
                <th colspan="2">Szczegóły depozytu</th>
            </tr>
            <tr>
                <td>Numer depozytu:</td>
                <td><strong>{deposit_id}</strong></td>
            </tr>
            <tr>
                <td>Rozmiar opon:</td>
                <td>{tire_size}</td>
            </tr>
            <tr>
                <td>Typ opon:</td>
                <td>{tire_type}</td>
            </tr>
            <tr>
                <td>Ilość:</td>
                <td>{quantity} szt.</td>
            </tr>
            <tr>
                <td>Data przyjęcia:</td>
                <td>{deposit_date}</td>
            </tr>
        </table>
        
        <p>Prosimy o pilny kontakt w sprawie dalszego przechowywania lub odbioru opon.</p>
        <p>Z poważaniem,<br>{company_name}</p>
    </div>
    <div class="footer">
        <p>{company_address}, {company_phone}<br>
        {company_email}, {company_website}</p>
    </div>
</body>
</html>"""
    },
    "general": {
        "subject": "Informacja o depozycie opon",
        "body": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Informacja o depozycie opon</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #6c757d;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            font-size: 0.8em;
            color: #6c757d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #dee2e6;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #e9ecef;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{company_name}</h2>
        <p>Informacja o depozycie opon</p>
    </div>
    <div class="content">
        <p>Szanowny Kliencie,</p>
        <p>Przesyłamy informację o Twoim depozycie opon:</p>
        
        <table>
            <tr>
                <th colspan="2">Szczegóły depozytu</th>
            </tr>
            <tr>
                <td>Numer depozytu:</td>
                <td><strong>{deposit_id}</strong></td>
            </tr>
            <tr>
                <td>Status:</td>
                <td>{status}</td>
            </tr>
            <tr>
                <td>Rozmiar opon:</td>
                <td>{tire_size}</td>
            </tr>
            <tr>
                <td>Typ opon:</td>
                <td>{tire_type}</td>
            </tr>
            <tr>
                <td>Ilość:</td>
                <td>{quantity} szt.</td>
            </tr>
            <tr>
                <td>Data przyjęcia:</td>
                <td>{deposit_date}</td>
            </tr>
            <tr>
                <td>Planowana data odbioru:</td>
                <td>{pickup_date}</td>
            </tr>
        </table>
        
        <p>W razie pytań prosimy o kontakt z naszym serwisem.</p>
        <p>Z poważaniem,<br>{company_name}</p>
    </div>
    <div class="footer">
        <p>{company_address}, {company_phone}<br>
        {company_email}, {company_website}</p>
    </div>
</body>
</html>"""
    }
}

DEFAULT_LABEL_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Etykieta depozytu</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 10px;
        }
        .label {
            border: 1px solid #000;
            padding: 5px;
            width: 60mm;
            height: 28mm;
        }
        .deposit-id {
            font-size: 14pt;
            font-weight: bold;
        }
        .client {
            font-size: 12pt;
        }
        .info {
            font-size: 10pt;
        }
        .location {
            font-size: 14pt;
            font-weight: bold;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="label">
        <div class="deposit-id">{deposit_id}</div>
        <div class="client">{client_name}</div>
        <div class="info">{tire_size} ({tire_type}) - {quantity} szt.</div>
        <div class="info">Przyjęto: {deposit_date}</div>
        <div class="location">{location}</div>
    </div>
</body>
</html>"""

DEFAULT_RECEIPT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Potwierdzenie przyjęcia depozytu opon</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .title {
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .company {
            font-size: 14pt;
            margin-bottom: 5px;
        }
        .document-number {
            font-size: 12pt;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 15px;
        }
        .section-title {
            font-weight: bold;
            border-bottom: 1px solid #000;
            margin-bottom: 5px;
        }
        .client-info, .deposit-info {
            display: table;
            width: 100%;
        }
        .row {
            display: table-row;
        }
        .cell {
            display: table-cell;
            padding: 3px 10px 3px 0;
        }
        .label {
            font-weight: bold;
            width: 150px;
        }
        .signatures {
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
        }
        .signature {
            width: 45%;
            border-top: 1px solid #000;
            padding-top: 5px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">POTWIERDZENIE PRZYJĘCIA DEPOZYTU OPON</div>
        <div class="company">{company_name}</div>
        <div class="document-number">Numer depozytu: {deposit_id}</div>
        <div>Data wystawienia: {current_date}</div>
    </div>
    
    <div class="section">
        <div class="section-title">Dane klienta</div>
        <div class="client-info">
            <div class="row">
                <div class="cell label">Imię i nazwisko:</div>
                <div class="cell">{client_name}</div>
            </div>
            <div class="row">
                <div class="cell label">Telefon:</div>
                <div class="cell">{phone_number}</div>
            </div>
            <div class="row">
                <div class="cell label">Email:</div>
                <div class="cell">{email}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Dane depozytu</div>
        <div class="deposit-info">
            <div class="row">
                <div class="cell label">Rozmiar opon:</div>
                <div class="cell">{tire_size}</div>
            </div>
            <div class="row">
                <div class="cell label">Typ opon:</div>
                <div class="cell">{tire_type}</div>
            </div>
            <div class="row">
                <div class="cell label">Ilość:</div>
                <div class="cell">{quantity} szt.</div>
            </div>
            <div class="row">
                <div class="cell label">Lokalizacja:</div>
                <div class="cell">{location}</div>
            </div>
            <div class="row">
                <div class="cell label">Data przyjęcia:</div>
                <div class="cell">{deposit_date}</div>
            </div>
            <div class="row">
                <div class="cell label">Planowana data odbioru:</div>
                <div class="cell">{pickup_date}</div>
            </div>
            <div class="row">
                <div class="cell label">Uwagi:</div>
                <div class="cell">{notes}</div>
            </div>
        </div>
    </div>
    
    <div class="signatures">
        <div class="signature">Potwierdzenie wydał</div>
        <div class="signature">Podpis klienta</div>
    </div>
</body>
</html>"""


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
        self.resize(800, 600)
        
        # Inicjalizacja ustawień
        self.settings = QSettings("TireDepositManager", "Settings")
        
        # Ścieżka do pliku z szablonami
        self.templates_file = os.path.join(CONFIG_DIR, "templates.json")
        ensure_dir_exists(CONFIG_DIR)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie aktualnych ustawień
        self.load_settings()
        
        # Załadowanie szablonów
        self.load_templates()
    
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
        
        # Zakładka szablonów
        templates_tab = QWidget()
        self.init_templates_tab(templates_tab)
        self.tabs.addTab(templates_tab, QIcon(os.path.join(ICONS_DIR, "template.png")), "Szablony")
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
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

            # Zaakceptuj dialog
            self.accept()

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania ustawień: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania ustawień:\n{str(e)}"
            )

    def load_settings(self):
        """Ładuje ustawienia do formularza."""
        try:

            # Domyślna ścieżka danych z utils.paths
            from utils.paths import APP_DATA_DIR

            # Pobierz ścieżkę katalogu danych z ustawień, używając domyślnej wartości APP_DATA_DIR
            data_directory = self.settings.value("data_directory", APP_DATA_DIR)
            
            # Upewnij się, że katalog istnieje
            os.makedirs(data_directory, exist_ok=True)
            
            # Ustaw ścieżkę w polu input
            self.data_dir_input.setText(data_directory)

            # Ustawienia ogólne
            self.data_dir_input.setText(self.settings.value("data_directory", ""))
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
            self.backup_dir_input.setText(self.settings.value("backup_directory", ""))
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
        
        # Testowy e-mail
        test_email_button = QPushButton("Wyślij testowy email")
        test_email_button.clicked.connect(self.send_test_email)
        layout.addRow("", test_email_button)

    def init_templates_tab(self, tab):
        """
        Inicjalizacja zakładki szablonów.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        # Główny layout
        main_layout = QVBoxLayout(tab)
        
        # Zakładki dla różnych typów szablonów
        templates_tabs = QTabWidget()
        templates_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2c3034;
            }
            QTabBar::tab {
                background-color: #343a40;
                color: white;
                padding: 8px 12px;
                margin-right: 5px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4dabf7;
                font-weight: bold;
            }
        """)
        
        # Zakładka szablonów email
        self.email_tab = QWidget()
        templates_tabs.addTab(self.email_tab, "Szablony Email")
        
        # Zakładka szablonów etykiet
        self.label_tab = QWidget()
        templates_tabs.addTab(self.label_tab, "Szablony Etykiet")
        
        # Zakładka szablonów potwierdzeń
        self.receipt_tab = QWidget()
        templates_tabs.addTab(self.receipt_tab, "Szablony Potwierdzeń")
        
        main_layout.addWidget(templates_tabs)
        
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
        self.email_template_combo.addItems([
            "Aktywny depozyt", 
            "Do odbioru", 
            "Zaległy depozyt", 
            "Ogólny"
        ])
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
        
        # Pola edycji szablonu
        form_layout = QFormLayout()
        
        # Temat
        form_layout.addRow("Temat:", QLabel())
        self.email_subject_edit = QLineEdit()
        form_layout.addRow("", self.email_subject_edit)
        
        # Treść
        form_layout.addRow("Treść HTML:", QLabel())
        
        # Edytor HTML + podgląd
        html_layout = QHBoxLayout()
        
        # Edytor HTML
        self.email_body_edit = QTextEdit()
        self.email_body_edit.setMinimumHeight(300)
        self.email_body_edit.textChanged.connect(self.update_email_preview)
        html_layout.addWidget(self.email_body_edit, 1)
        
        # Podgląd HTML
        preview_group = QGroupBox("Podgląd")
        preview_layout = QVBoxLayout(preview_group)
        
        self.email_preview = QWebEngineView()
        self.email_preview.setMinimumWidth(300)
        self.email_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.email_preview)
        
        html_layout.addWidget(preview_group, 1)
        
        form_layout.addRow("", html_layout)
        
        layout.addLayout(form_layout)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{location} - Lokalizacja w magazynie\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru\n"
            "{status} - Status depozytu\n"
            "{notes} - Uwagi\n"
            "{phone_number} - Numer telefonu klienta\n"
            "{email} - Adres email klienta\n"
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
        
        layout.addLayout(select_layout)
        
        # HTML Editor + Preview
        editor_preview_layout = QHBoxLayout()
        
        # HTML Editor
        self.label_content_edit = QTextEdit()
        self.label_content_edit.setMinimumHeight(300)
        self.label_content_edit.textChanged.connect(self.update_label_preview)
        editor_preview_layout.addWidget(self.label_content_edit, 1)
        
        # Podgląd HTML
        preview_group = QGroupBox("Podgląd etykiety")
        preview_layout = QVBoxLayout(preview_group)
        
        self.label_preview = QWebEngineView()
        self.label_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.label_preview)
        
        editor_preview_layout.addWidget(preview_group, 1)
        
        layout.addLayout(editor_preview_layout)
        
        # Ustawienia drukowania etykiet
        printer_group = QGroupBox("Ustawienia drukowania etykiet")
        printer_layout = QFormLayout(printer_group)
        
        # Wybór drukarki
        self.label_printer_combo = QComboBox()
        printer_layout.addRow("Drukarka etykiet:", self.label_printer_combo)
        
        # Rozmiar etykiety
        size_layout = QHBoxLayout()
        
        self.label_width_spin = QSpinBox()
        self.label_width_spin.setRange(10, 200)
        self.label_width_spin.setValue(62)
        self.label_width_spin.setSuffix(" mm")
        size_layout.addWidget(self.label_width_spin)
        
        size_layout.addWidget(QLabel("x"))
        
        self.label_height_spin = QSpinBox()
        self.label_height_spin.setRange(10, 200)
        self.label_height_spin.setValue(29)
        self.label_height_spin.setSuffix(" mm")
        size_layout.addWidget(self.label_height_spin)
        
        printer_layout.addRow("Rozmiar etykiety:", size_layout)
        
        # Margines
        self.label_margin_spin = QSpinBox()
        self.label_margin_spin.setRange(0, 20)
        self.label_margin_spin.setValue(2)
        self.label_margin_spin.setSuffix(" mm")
        printer_layout.addRow("Margines:", self.label_margin_spin)
        
        # Test drukowania
        test_print_btn = QPushButton("Wydrukuj testową etykietę")
        test_print_btn.clicked.connect(self.print_test_label)
        printer_layout.addRow("", test_print_btn)
        
        layout.addWidget(printer_group)
        
        # Lista dostępnych zmiennych
        variables_group = QGroupBox("Dostępne zmienne")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_label = QLabel(
            "Możesz użyć następujących zmiennych w szablonie HTML:\n"
            "{deposit_id} - ID depozytu\n"
            "{client_name} - Nazwa klienta\n"
            "{tire_size} - Rozmiar opon\n"
            "{tire_type} - Typ opon\n"
            "{quantity} - Ilość opon\n"
            "{location} - Lokalizacja w magazynie\n"
            "{deposit_date} - Data przyjęcia\n"
            "{pickup_date} - Planowana data odbioru"
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
        
        # HTML Editor + Preview
        editor_preview_layout = QHBoxLayout()
        
        # HTML Editor
        self.receipt_content_edit = QTextEdit()
        self.receipt_content_edit.setMinimumHeight(300)
        self.receipt_content_edit.textChanged.connect(self.update_receipt_preview)
        editor_preview_layout.addWidget(self.receipt_content_edit, 1)
        
        # Podgląd HTML
        preview_group = QGroupBox("Podgląd potwierdzenia")
        preview_layout = QVBoxLayout(preview_group)
        
        self.receipt_preview = QWebEngineView()
        self.receipt_preview.setMinimumHeight(300)
        preview_layout.addWidget(self.receipt_preview)
        
        editor_preview_layout.addWidget(preview_group, 1)
        
        layout.addLayout(editor_preview_layout)
        
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
        """Aktualizuje podgląd czcionki na podstawie wybranych ustawień."""
        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_spin.value())
        self.font_preview.setFont(font)

    def browse_data_dir(self):
        """Otwiera okno wyboru katalogu danych."""
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog danych", self.data_dir_input.text()
        )
        if directory:
            self.data_dir_input.setText(directory)

    def browse_backup_dir(self):
        """Otwiera okno wyboru katalogu kopii zapasowych."""
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

    def send_test_email(self):
        """Wysyła testowy email do sprawdzenia konfiguracji."""
        try:
            # W rzeczywistej implementacji należałoby wykorzystać odpowiednie API
            QMessageBox.information(
                self, 
                "Test email", 
                "Funkcja wysyłania testowego emaila jest niedostępna w tej wersji."
            )
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania testowego emaila: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas wysyłania testowego emaila:\n{str(e)}"
            )
            
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
                if template_name in self.templates.get("email", {}):
                    del self.templates["email"][template_name]
                
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
            if "email" not in self.templates:
                self.templates["email"] = {}
            
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
                if template_name in self.templates.get("label", {}):
                    del self.templates["label"][template_name]
                
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
            if "label" not in self.templates:
                self.templates["label"] = {}
            
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
            
            # Opcjonalnie - zapisz jako bieżący szablon
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
                "phone_number": "123 456 789",
                "email": "jan.kowalski@example.com",
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
                if template_name in self.templates.get("receipt", {}):
                    del self.templates["receipt"][template_name]
                
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
            if "receipt" not in self.templates:
                self.templates["receipt"] = {}
            
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
            
            # Opcjonalnie - zapisz jako bieżący szablon
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

    def load_templates(self):
        """Ładuje szablony z pliku."""
        try:
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
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania szablonów: {e}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas zapisywania szablonów:\n{str(e)}"
            )

    def on_email_template_changed(self, index):
        """Obsługuje zmianę szablonu email."""
        try:
            template_key = self.email_template_mapping.get(index)
            if not template_key:
                return
                
            template = self.templates.get("email", {}).get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            self.email_subject_edit.setText(template.get("subject", ""))
            self.email_body_edit.setPlainText(template.get("body", ""))
            self.update_email_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu email: {e}")

    def on_label_template_changed(self, index):
        """Obsługuje zmianę szablonu etykiety."""
        try:
            template_name = self.label_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = self.templates.get("label", {}).get(template_name, DEFAULT_LABEL_TEMPLATE)
            
            self.label_content_edit.setPlainText(template)
            self.update_label_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu etykiety: {e}")

    def on_receipt_template_changed(self, index):
        """Obsługuje zmianę szablonu potwierdzenia."""
        try:
            template_name = self.receipt_template_combo.itemData(index)
            if not template_name:
                template_name = "default"
                
            template = self.templates.get("receipt", {}).get(template_name, DEFAULT_RECEIPT_TEMPLATE)
            
            self.receipt_content_edit.setPlainText(template)
            self.update_receipt_preview()
        except Exception as e:
            logger.error(f"Błąd podczas zmiany szablonu potwierdzenia: {e}")


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