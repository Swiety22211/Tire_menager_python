import os
import datetime
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QTextEdit,
    QGridLayout, QFrame, QMessageBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QSplitter
)#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ulepszony dialog wydawania depozytu opon w aplikacji Menadżer Serwisu Opon.
"""

import os
import datetime
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QTextEdit,
    QGridLayout, QFrame, QMessageBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont

from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireDepositManager")


class DepositReleaseDialog(QDialog):
    """Dialog do wydawania depozytu opon klientowi."""
    
    def __init__(self, db_connection, deposit_id=None, parent=None):
        """
        Inicjalizacja dialogu wydawania depozytu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            deposit_id (int, optional): ID depozytu do wydania. Jeśli None, to trzeba wybrać z listy.
            parent: Rodzic widgetu
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.deposit_id = deposit_id
        self.selected_deposit_id = None  # Będzie ustawione jeśli wybrano depozyt z listy
        
        # Wartości początkowe
        self.client_id = None
        self.client_name = ""
        self.deposit_details = {}
        
        # Jeśli podano ID depozytu, pobierz dane
        if self.deposit_id:
            self.load_deposit_data()
        
        # Ustawienie tytułu okna
        self.setWindowTitle(_("Wydanie depozytu"))
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Wypełnienie formularza danymi (jeśli podano deposit_id)
        if self.deposit_id:
            self.fill_form()
    
    def load_deposit_data(self):
        """Ładuje dane depozytu z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT 
                d.client_id,
                c.name AS client_name,
                d.id,
                d.deposit_date,
                d.pickup_date,
                d.tire_size,
                d.tire_type,
                d.quantity,
                d.location,
                d.status,
                d.notes
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                d.id = ? AND d.status != 'Wydany'
            """
            
            cursor.execute(query, (self.deposit_id,))
            result = cursor.fetchone()
            
            if result:
                self.client_id = result['client_id']
                self.client_name = result['client_name']
                self.deposit_details = dict(result)
                logger.info(f"Załadowano dane depozytu ID {self.deposit_id}: {self.deposit_details}")
            else:
                logger.warning(f"Nie znaleziono aktywnego depozytu o ID {self.deposit_id}")
                raise ValueError(f"No active deposit found with ID {self.deposit_id}")
                
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania danych depozytu: {e}",
                NotificationTypes.ERROR
            )
            self.reject()  # Zamknij dialog w przypadku błędu
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        # Stylizacja dialog podobnie do dialogu depozytu
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QLabel {
                background-color: transparent;  
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit, QTextEdit, QDateEdit, QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus {
                border: 1px solid #4dabf7;
            }
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #505050;
                border-left-style: solid;
                background-color: #3a3a3a;
            }
            QComboBox::after {
                content: "▼";
                color: white;
                padding-right: 6px;
            }
            QTableWidget {
                background-color: #2c3034;
                color: #fff;
                border: none;
                gridline-color: #3a3f44;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3a3f44;
            }
            QTableWidget::item:selected {
                background-color: #4dabf7;
                color: white;
            }
            QHeaderView::section {
                background-color: #1a1d21;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #505050;
                border-radius: 3px;
                background-color: #3a3a3a;
            }
            QCheckBox::indicator:checked {
                background-color: #4dabf7;
            }
            QFrame { 
                background-color: #2a2a2a;  
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Jeśli nie podano ID depozytu, pokaż listę do wyboru
        if not self.deposit_id:
            self.setup_client_selection_section(main_layout)
        
        # Szczegóły depozytu (widoczne zawsze)
        details_frame = QFrame()
        
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(10)
        
        # Nagłówek sekcji
        details_header = QLabel(_("Szczegóły depozytu do wydania"))
        details_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        details_layout.addWidget(details_header)
        
        # Grid dla szczegółów depozytu
        details_grid = QGridLayout()
        details_grid.setSpacing(10)
        
        # ID depozytu
        details_grid.addWidget(QLabel(_("ID depozytu:")), 0, 0)
        self.id_label = QLabel("-")
        self.id_label.setStyleSheet("font-weight: bold; color: #4dabf7;")
        details_grid.addWidget(self.id_label, 0, 1)
        
        # Klient
        details_grid.addWidget(QLabel(_("Klient:")), 0, 2)
        self.client_label = QLabel("-")
        self.client_label.setStyleSheet("font-weight: bold; color: #4dabf7;")
        details_grid.addWidget(self.client_label, 0, 3)
        
        # Rozmiar opon
        details_grid.addWidget(QLabel(_("Rozmiar opon:")), 1, 0)
        self.tire_size_label = QLabel("-")
        details_grid.addWidget(self.tire_size_label, 1, 1)
        
        # Typ opon
        details_grid.addWidget(QLabel(_("Typ opon:")), 1, 2)
        self.tire_type_label = QLabel("-")
        details_grid.addWidget(self.tire_type_label, 1, 3)
        
        # Ilość
        details_grid.addWidget(QLabel(_("Ilość:")), 2, 0)
        self.quantity_label = QLabel("-")
        details_grid.addWidget(self.quantity_label, 2, 1)
        
        # Lokalizacja
        details_grid.addWidget(QLabel(_("Lokalizacja:")), 2, 2)
        self.location_label = QLabel("-")
        details_grid.addWidget(self.location_label, 2, 3)
        
        # Data przyjęcia
        details_grid.addWidget(QLabel(_("Data przyjęcia:")), 3, 0)
        self.deposit_date_label = QLabel("-")
        details_grid.addWidget(self.deposit_date_label, 3, 1)
        
        # Data planowanego odbioru
        details_grid.addWidget(QLabel(_("Planowana data odbioru:")), 3, 2)
        self.pickup_date_label = QLabel("-")
        details_grid.addWidget(self.pickup_date_label, 3, 3)
        
        # Status
        details_grid.addWidget(QLabel(_("Aktualny status:")), 4, 0)
        self.status_label = QLabel("-")
        self.status_label.setStyleSheet("font-weight: bold;")
        details_grid.addWidget(self.status_label, 4, 1)
        
        # Dodanie grid layout do głównego layout'u sekcji
        details_layout.addLayout(details_grid)
        
        main_layout.addWidget(details_frame)
        
        # Upewnienie się, że szczegóły są zawsze widoczne
        details_frame.setMinimumHeight(200)
        
        # Sekcja wydania
        release_frame = QFrame()
        
        release_layout = QVBoxLayout(release_frame)
        release_layout.setContentsMargins(15, 15, 15, 15)
        release_layout.setSpacing(10)
        
        # Nagłówek sekcji
        release_header = QLabel(_("Informacje o wydaniu"))
        release_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        release_layout.addWidget(release_header)
        
        # Grid layout dla informacji o wydaniu
        release_grid = QGridLayout()
        release_grid.setSpacing(10)
        
        # Data faktycznego wydania
        release_grid.addWidget(QLabel(_("Data wydania:")), 0, 0)
        
        self.release_date_edit = QDateEdit()
        self.release_date_edit.setCalendarPopup(True)
        self.release_date_edit.setDate(QDate.currentDate())
        self.release_date_edit.setFixedHeight(30)
        release_grid.addWidget(self.release_date_edit, 0, 1)
        
        # Osoba odbierająca
        release_grid.addWidget(QLabel(_("Osoba odbierająca:")), 0, 2)
        
        self.receiver_edit = QLineEdit()
        self.receiver_edit.setPlaceholderText(_("Imię i nazwisko osoby odbierającej"))
        self.receiver_edit.setFixedHeight(30)
        release_grid.addWidget(self.receiver_edit, 0, 3)
        
        release_layout.addLayout(release_grid)
        
        # Uwagi dot. wydania
        release_layout.addWidget(QLabel(_("Uwagi do wydania:")))
        
        self.release_notes_edit = QTextEdit()
        self.release_notes_edit.setPlaceholderText(_("Dodatkowe informacje o wydaniu depozytu..."))
        self.release_notes_edit.setMaximumHeight(100)
        release_layout.addWidget(self.release_notes_edit)
        
        # Checkbox do potwierdzenia
        self.confirm_checkbox = QCheckBox(_("Potwierdzam wydanie kompletu opon klientowi"))
        self.confirm_checkbox.setStyleSheet("font-weight: bold;")
        release_layout.addWidget(self.confirm_checkbox)
        
        main_layout.addWidget(release_frame)
        
        # Przyciski OK i Anuluj
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton(_("Anuluj"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.release_btn = QPushButton(_("Wydaj depozyt"))
        self.release_btn.setEnabled(False)  # Domyślnie wyłączony do czasu potwierdzenia
        self.release_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #f8f9fa;
            }
        """)
        self.release_btn.clicked.connect(self.release_deposit)
        button_layout.addWidget(self.release_btn)
        
        main_layout.addLayout(button_layout)
        
        # Połączenie sygnału checkboxa z aktywacją przycisku
        self.confirm_checkbox.stateChanged.connect(self.toggle_release_button)
        
        # Ustawienie rozmiaru dialogu i maksymalizacja
        self.resize(900, 700)
        
        # Zastosowanie stylu strzałek dla wszystkich comboboxów
        dropdown_style = """
            QComboBox {
                padding-right: 15px; /* Miejsce na strzałkę */
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #505050;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
            }
            /* Dodanie trójkąta jako strzałki */
            QComboBox::after {
                content: "▼";
                color: white;
                font-size: 10px;
                position: absolute;
                top: 7px;
                right: 7px;
            }
        """
        
        # Zastosowanie stylu do comboboxów jeśli są dostępne
        if hasattr(self, 'client_combo'):
            self.client_combo.setStyleSheet(dropdown_style)
    
    def setup_client_selection_section(self, main_layout):
        """Konfiguruje sekcję wyboru klienta i depozytu."""
        # Sekcja wyboru klienta
        client_frame = QFrame()
        
        client_layout = QVBoxLayout(client_frame)
        client_layout.setContentsMargins(15, 15, 15, 15)
        client_layout.setSpacing(10)
        
        # Nagłówek sekcji
        client_header = QLabel(_("Wybierz klienta i depozyt"))
        client_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        client_layout.addWidget(client_header)
        
        # Wybór klienta
        client_search_layout = QHBoxLayout()
        client_search_layout.addWidget(QLabel(_("Klient:")))
        
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        self.client_combo.setMinimumWidth(300)
        self.client_combo.setFixedHeight(30)
        client_search_layout.addWidget(self.client_combo, 1)
        
        self.search_btn = QPushButton(_("Szukaj"))
        self.search_btn.clicked.connect(self.search_deposits)
        client_search_layout.addWidget(self.search_btn)
        
        client_layout.addLayout(client_search_layout)
        
        # Tabela depozytów do wyboru
        client_layout.addWidget(QLabel(_("Depozyty klienta:")))
        
        self.deposits_table = QTableWidget()
        self.deposits_table.setColumnCount(7)
        self.deposits_table.setHorizontalHeaderLabels([
            _("ID"), _("Klient"), _("Rozmiar"), _("Typ"), 
            _("Data przyjęcia"), _("Lokalizacja"), _("Status")
        ])
        
        # Dostosowanie szerokości kolumn
        self.deposits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.deposits_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Klient
        self.deposits_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Rozmiar
        self.deposits_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Typ
        self.deposits_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Data przyjęcia
        self.deposits_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Lokalizacja
        self.deposits_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Status
        
        self.deposits_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.deposits_table.setSelectionMode(QTableWidget.SingleSelection)
        self.deposits_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.deposits_table.setMinimumHeight(200)  # Zapewnienie minimalnej wysokości tabeli
        
        client_layout.addWidget(self.deposits_table)
        
        main_layout.addWidget(client_frame)
        
        # Ładuj listę klientów
        self.load_clients()
        
        # Połącz sygnał wyboru depozytu
        self.deposits_table.itemSelectionChanged.connect(self.on_deposit_selected)
    
    def load_clients(self):
        """Ładuje listę klientów do comboboxa."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz klientów, którzy mają aktywne depozyty
            cursor.execute("""
                SELECT DISTINCT c.id, c.name 
                FROM clients c
                JOIN deposits d ON c.id = d.client_id
                WHERE d.status != 'Wydany'
                ORDER BY c.name
            """)
            clients = cursor.fetchall()
            
            # Wypełnij combobox
            self.client_combo.clear()
            self.client_combo.addItem(_("-- Wybierz klienta --"), None)
            
            for client in clients:
                self.client_combo.addItem(client['name'], client['id'])
            
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania listy klientów: {e}",
                NotificationTypes.ERROR
            )
    
    def search_deposits(self):
        """Wyszukuje depozyty dla wybranego klienta."""
        try:
            # Pobierz ID wybranego klienta
            index = self.client_combo.currentIndex()
            client_id = self.client_combo.itemData(index)
            
            if not client_id:
                QMessageBox.warning(self, _("Uwaga"), _("Wybierz klienta z listy."))
                return
            
            # Zapytanie o depozyty klienta
            cursor = self.conn.cursor()
            
            query = """
            SELECT 
                d.id,
                c.name AS client_name,
                d.tire_size,
                d.tire_type,
                d.deposit_date,
                d.location,
                d.status
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                d.client_id = ? AND d.status != 'Wydany'
            ORDER BY 
                d.id DESC
            """
            
            cursor.execute(query, (client_id,))
            deposits = cursor.fetchall()
            
            # Wyczyść tabelę
            self.deposits_table.setRowCount(0)
            
            # Wypełnij tabelę
            for deposit in deposits:
                row_position = self.deposits_table.rowCount()
                self.deposits_table.insertRow(row_position)
                
                # Formatowanie ID (D001, D002, itp.)
                deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
                
                # Formatowanie daty
                deposit_date = datetime.datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                # Dodanie danych do komórek
                self.deposits_table.setItem(row_position, 0, QTableWidgetItem(deposit_id_str))
                self.deposits_table.setItem(row_position, 1, QTableWidgetItem(deposit['client_name']))
                self.deposits_table.setItem(row_position, 2, QTableWidgetItem(deposit['tire_size']))
                self.deposits_table.setItem(row_position, 3, QTableWidgetItem(deposit['tire_type']))
                self.deposits_table.setItem(row_position, 4, QTableWidgetItem(deposit_date))
                self.deposits_table.setItem(row_position, 5, QTableWidgetItem(deposit['location']))
                self.deposits_table.setItem(row_position, 6, QTableWidgetItem(deposit['status']))
            
            # Informacja o liczbie znalezionych depozytów
            if not deposits:
                QMessageBox.information(
                    self, 
                    _("Informacja"), 
                    _("Nie znaleziono aktywnych depozytów dla wybranego klienta.")
                )
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyszukiwania depozytów: {e}",
                NotificationTypes.ERROR
            )
    
    def on_deposit_selected(self):
        """Obsługuje wybór depozytu z tabeli."""
        selected_items = self.deposits_table.selectedItems()
        if not selected_items:
            return
        
        # Pobierz ID wybranego depozytu
        row = selected_items[0].row()
        deposit_id_str = self.deposits_table.item(row, 0).text()
        self.selected_deposit_id = int(deposit_id_str.replace('D', ''))
        
        # Załaduj szczegóły wybranego depozytu
        self.deposit_id = self.selected_deposit_id
        
        logger.info(f"Wybrano depozyt ID: {self.deposit_id}")
        
        try:
            self.load_deposit_data()
            self.fill_form()
            
            # Przewiń widok do szczegółów depozytu
            QApplication.processEvents()
            self.release_btn.setFocus()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania wybranego depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def fill_form(self):
        """Wypełnia formularz danymi depozytu."""
        if not self.deposit_details:
            return
        
        # Formatowanie ID
        deposit_id = f"D{str(self.deposit_details['id']).zfill(3)}"
        
        # Formatowanie dat
        deposit_date = datetime.datetime.strptime(self.deposit_details['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
        pickup_date = datetime.datetime.strptime(self.deposit_details['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
        
        # Uzupełnienie etykiet
        self.id_label.setText(deposit_id)
        self.client_label.setText(self.client_name)
        self.tire_size_label.setText(self.deposit_details['tire_size'])
        self.tire_type_label.setText(self.deposit_details['tire_type'])
        self.quantity_label.setText(str(self.deposit_details['quantity']))
        self.location_label.setText(self.deposit_details.get('location', '-'))
        self.deposit_date_label.setText(deposit_date)
        self.pickup_date_label.setText(pickup_date)
        self.status_label.setText(self.deposit_details['status'])
        
        # Uzupełnienie pola osoby odbierającej
        if not self.receiver_edit.text():
            self.receiver_edit.setText(self.client_name)
            
        # Wyraźne powiadomienie o załadowaniu szczegółów
        NotificationManager.get_instance().show_notification(
            f"Załadowano szczegóły depozytu {deposit_id}",
            NotificationTypes.INFO
        )
    
    def toggle_release_button(self, state):
        """Włącza/wyłącza przycisk wydania w zależności od stanu checkboxa."""
        self.release_btn.setEnabled(state == Qt.Checked and (self.deposit_id or self.selected_deposit_id))
    
    def validate_form(self):
        """Sprawdza poprawność danych formularza."""
        # Sprawdź, czy wybrano depozyt
        if not self.deposit_id and not self.selected_deposit_id:
            QMessageBox.warning(self, _("Błąd walidacji"), _("Wybierz depozyt do wydania."))
            return False
        
        # Sprawdź, czy podano osobę odbierającą
        if not self.receiver_edit.text().strip():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Podaj imię i nazwisko osoby odbierającej."))
            return False
        
        # Sprawdź, czy zaznaczono checkbox potwierdzenia
        if not self.confirm_checkbox.isChecked():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Zaznacz potwierdzenie wydania depozytu."))
            return False
        
        # Sprawdź datę wydania
        release_date = self.release_date_edit.date().toPython()
        current_date = datetime.datetime.now().date()
        
        if release_date > current_date:
            response = QMessageBox.question(
                self, 
                _("Uwaga"), 
                _("Data wydania jest przyszła. Czy na pewno chcesz kontynuować?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if response == QMessageBox.No:
                return False
        
        return True
    
    def release_deposit(self):
        """Wydaje depozyt - zmienia jego status na 'Wydany'."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy tabela deposits ma wymagane kolumny
            cursor.execute("PRAGMA table_info(deposits)")
            columns = [column[1] for column in cursor.fetchall()]
            
            has_release_date = "release_date" in columns
            has_release_person = "release_person" in columns
            has_release_notes = "release_notes" in columns
            
            # Jeśli brakuje kolumn, dodaj je
            if not has_release_date:
                cursor.execute("ALTER TABLE deposits ADD COLUMN release_date TEXT")
            
            if not has_release_person:
                cursor.execute("ALTER TABLE deposits ADD COLUMN release_person TEXT")
            
            if not has_release_notes:
                cursor.execute("ALTER TABLE deposits ADD COLUMN release_notes TEXT")
            
            # Użyj wybranego ID depozytu (z tabeli lub przekazanego w konstruktorze)
            deposit_id = self.selected_deposit_id if self.selected_deposit_id else self.deposit_id
            
            # Pobierz dane z formularza
            release_date = self.release_date_edit.date().toString("yyyy-MM-dd")
            receiver = self.receiver_edit.text().strip()
            notes = self.release_notes_edit.toPlainText()
            
            # Aktualizacja statusu depozytu
            cursor.execute(
                """
                UPDATE deposits SET 
                    status = 'Wydany', 
                    release_date = ?,
                    release_person = ?,
                    release_notes = ?
                WHERE id = ?
                """,
                (release_date, receiver, notes, deposit_id)
            )
            
            self.conn.commit()
            
            # Zapamiętaj ID wydanego depozytu
            self.deposit_id = deposit_id
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Depozyt został pomyślnie wydany klientowi",
                NotificationTypes.SUCCESS
            )
            
            # Zamknij dialog z akceptacją
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wydawania depozytu: {e}",
                NotificationTypes.ERROR
            )