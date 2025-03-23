#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ulepszony dialog dodawania/edycji depozytu opon w aplikacji Menadżer Serwisu Opon.
"""

import os
import datetime
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QSpinBox, QTextEdit,
    QGridLayout, QFrame, QMessageBox, QCheckBox, QCompleter,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate, Signal, QStringListModel
from PySide6.QtGui import QIcon, QPixmap, QFont

from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.vehicle_dialog import VehicleDialog

# Logger
logger = logging.getLogger("TireDepositManager")


class DepositDialog(QDialog):
    """Dialog do dodawania nowego depozytu opon lub edycji istniejącego."""
    
    def __init__(self, db_connection, deposit_id=None, parent=None):
        """
        Inicjalizacja dialogu depozytu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            deposit_id (int, optional): ID depozytu do edycji. Jeśli None, to dodawanie nowego.
            parent: Rodzic widgetu
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.deposit_id = deposit_id
        self.is_edit_mode = deposit_id is not None
        
        # Wartości początkowe dla nowego depozytu
        self.client_id = None
        self.client_name = ""
        self.vehicle_id = None
        self.deposit_date = datetime.datetime.now().date()
        self.pickup_date = self.deposit_date + datetime.timedelta(days=180)  # Domyślnie 6 miesięcy przechowywania
        self.tire_size = ""
        self.tire_type = _("Zimowe")
        self.quantity = 4  # Domyślnie 4 opony
        self.location = ""
        self.status = _("Aktywny")
        self.notes = ""
        
        # Lista klientów - wypełniana w init_ui
        self.clients_list = []
        self.vehicles_list = []
        
        # Jeśli to edycja, pobierz dane depozytu
        if self.is_edit_mode:
            self.load_deposit_data()
        
        # Ustawienie tytułu okna
        self.setWindowTitle(_("Dodaj nowy depozyt") if not self.is_edit_mode else _("Edytuj depozyt"))
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Wypełnienie formularza danymi (jeśli edycja)
        if self.is_edit_mode:
            self.fill_form()
    
    def load_deposit_data(self):
        """Ładuje dane depozytu z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT 
                d.client_id,
                c.name AS client_name,
                d.vehicle_id,
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
                d.id = ?
            """
            
            cursor.execute(query, (self.deposit_id,))
            result = cursor.fetchone()
            
            if result:
                self.client_id = result['client_id']
                self.client_name = result['client_name']
                self.vehicle_id = result.get('vehicle_id')
                self.deposit_date = datetime.datetime.strptime(result['deposit_date'], "%Y-%m-%d").date()
                self.pickup_date = datetime.datetime.strptime(result['pickup_date'], "%Y-%m-%d").date()
                self.tire_size = result['tire_size']
                self.tire_type = result['tire_type']
                self.quantity = result['quantity']
                self.location = result['location']
                self.status = result['status']
                self.notes = result['notes']
            else:
                raise ValueError(f"No deposit found with ID {self.deposit_id}")
                
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania danych depozytu: {e}",
                NotificationTypes.ERROR
            )
            self.reject()  # Zamknij dialog w przypadku błędu
    
    def ensure_database_schema(self):
        """Upewnia się, że schemat bazy danych zawiera wymagane kolumny."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź czy tabela deposits ma kolumnę notes i vehicle_id
            cursor.execute("PRAGMA table_info(deposits)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Dodaj kolumnę vehicle_id jeśli nie istnieje
            if "vehicle_id" not in columns:
                try:
                    cursor.execute("ALTER TABLE deposits ADD COLUMN vehicle_id INTEGER")
                    self.conn.commit()
                    logger.info("Dodano kolumnę vehicle_id do tabeli deposits")
                except Exception as e:
                    logger.error(f"Błąd podczas dodawania kolumny vehicle_id: {e}")
            
            # Dodaj kolumnę notes jeśli nie istnieje
            if "notes" not in columns:
                try:
                    cursor.execute("ALTER TABLE deposits ADD COLUMN notes TEXT")
                    self.conn.commit()
                    logger.info("Dodano kolumnę notes do tabeli deposits")
                except Exception as e:
                    logger.error(f"Błąd podczas dodawania kolumny notes: {e}")
                    
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania schematu bazy danych: {e}")
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        # Najpierw upewnij się, że mamy odpowiednią strukturę bazy danych
        self.ensure_database_schema()
        
        # Stwórz lub pobierz obraz strzałki dla komboboxów
        arrow_image_path = os.path.join(ICONS_DIR, "down_arrow.png")
        if not os.path.exists(arrow_image_path):
            try:
                # Jeśli obraz nie istnieje, użyj domyślnego stylu
                self.setStyleSheet("""
                    QComboBox::down-arrow {
                        color: white;
                        /* Znak unicode dla strzałki w dół */
                        font-size: 14px;
                    }
                """)
            except Exception as e:
                logger.warning(f"Nie można ustawić domyślnej strzałki dla ComboBox: {e}")
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
            QLineEdit, QTextEdit, QDateEdit, QComboBox, QSpinBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 14px;
                height: 14px;
            }
            /* Fallback style jeśli obraz strzałki nie jest dostępny */
            QComboBox:after {
                content: "▼";
                color: white;
                padding-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ffffff;
                selection-background-color: #4dabf7;
                border: 1px solid #505050;
                outline: 0px;
            }
            QListWidget {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #4dabf7;
                color: #ffffff;
            }
        """)

        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Sekcja klienta
        client_frame = QFrame()
        client_frame.setStyleSheet("""
            QFrame { 
                background-color: #2a2a2a;  
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        client_layout = QVBoxLayout(client_frame)
        client_layout.setContentsMargins(15, 15, 15, 15)
        client_layout.setSpacing(10)
        
        # Nagłówek sekcji
        client_header = QLabel(_("Dane klienta"))
        client_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        client_layout.addWidget(client_header)
        
        # Subsekcja wyszukiwania klienta
        client_search_layout = QHBoxLayout()
        client_search_layout.setSpacing(10)
        
        # Pole wyszukiwania klienta z autouzupełnianiem
        client_search_layout.addWidget(QLabel(_("Klient:")))
        
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText(_("Wpisz nazwę klienta..."))
        self.client_input.setMinimumWidth(300)
        
        # Ładowanie listy klientów
        self.load_clients_list()
        
        # Dodanie autocomplete do pola wyszukiwania klienta
        completer = QCompleter(self.clients_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.client_input.setCompleter(completer)
        
        self.client_input.textChanged.connect(self.on_client_text_changed)
        client_search_layout.addWidget(self.client_input)
        
        # Przycisk dodawania nowego klienta
        self.add_client_btn = QPushButton(_("Dodaj nowego klienta"))
        self.add_client_btn.clicked.connect(self.add_new_client)
        client_search_layout.addWidget(self.add_client_btn)
        
        client_layout.addLayout(client_search_layout)
        
        # Subsekcja wyboru pojazdu klienta
        vehicle_layout = QHBoxLayout()
        vehicle_layout.setSpacing(10)
        
        vehicle_layout.addWidget(QLabel(_("Pojazd:")))
        
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setMinimumWidth(300)
        self.vehicle_combo.setPlaceholderText(_("Wybierz pojazd klienta..."))
        self.vehicle_combo.setEnabled(False)  # Domyślnie wyłączone do czasu wyboru klienta
        self.vehicle_combo.currentIndexChanged.connect(self.on_vehicle_selected)
        vehicle_layout.addWidget(self.vehicle_combo)
        
        # Przycisk dodawania nowego pojazdu
        self.add_vehicle_btn = QPushButton(_("Dodaj nowy pojazd"))
        self.add_vehicle_btn.setEnabled(False)  # Domyślnie wyłączone do czasu wyboru klienta
        self.add_vehicle_btn.clicked.connect(self.add_new_vehicle)
        vehicle_layout.addWidget(self.add_vehicle_btn)
        
        client_layout.addLayout(vehicle_layout)
        
        main_layout.addWidget(client_frame)
        
        # Sekcja informacji o oponach
        tire_frame = QFrame()
        tire_frame.setStyleSheet("""
            QFrame { 
                background-color: #2a2a2a;  
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        tire_layout = QVBoxLayout(tire_frame)
        tire_layout.setContentsMargins(15, 15, 15, 15)
        tire_layout.setSpacing(10)
        
        # Nagłówek sekcji
        tire_header = QLabel(_("Informacje o oponach"))
        tire_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        tire_layout.addWidget(tire_header)
        
        # Grid layout dla pól opon
        tire_grid = QGridLayout()
        tire_grid.setSpacing(10)
        
        # Rozmiar opon
        tire_grid.addWidget(QLabel(_("Rozmiar opon:")), 0, 0)
        
        self.tire_size_combo = QComboBox()
        self.tire_size_combo.setEditable(True)
        
        # Popularne rozmiary opon
        standard_sizes = [
            "185/65 R15", "195/65 R15", "205/55 R16", "205/60 R16", 
            "215/55 R16", "215/60 R16", "225/45 R17", "225/50 R17",
            "225/55 R17", "235/45 R17", "235/55 R17", "245/45 R18"
        ]
        self.tire_size_combo.addItems(standard_sizes)
        
        if self.is_edit_mode and self.tire_size:
            if self.tire_size not in standard_sizes:
                self.tire_size_combo.addItem(self.tire_size)
            self.tire_size_combo.setCurrentText(self.tire_size)
        
        tire_grid.addWidget(self.tire_size_combo, 0, 1)
        
        # Typ opon
        tire_grid.addWidget(QLabel(_("Typ opon:")), 0, 2)
        
        self.tire_type_combo = QComboBox()
        self.tire_type_combo.addItems([_("Zimowe"), _("Letnie"), _("Całoroczne")])
        
        if self.is_edit_mode:
            index = self.tire_type_combo.findText(self.tire_type)
            if index >= 0:
                self.tire_type_combo.setCurrentIndex(index)
        
        tire_grid.addWidget(self.tire_type_combo, 0, 3)
        
        # Ilość opon
        tire_grid.addWidget(QLabel(_("Ilość opon:")), 1, 0)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 20)  # Zazwyczaj od 1 do 20 opon
        self.quantity_spin.setValue(self.quantity if self.is_edit_mode else 4)  # Domyślnie 4 opony
        
        tire_grid.addWidget(self.quantity_spin, 1, 1)
        
        # Lokalizacja w magazynie
        tire_grid.addWidget(QLabel(_("Lokalizacja:")), 1, 2)
        
        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        
        # Przykładowe lokalizacje
        standard_locations = [
            "Regał A-1", "Regał A-2", "Regał A-3", "Regał B-1", 
            "Regał B-2", "Regał B-3", "Regał C-1", "Regał C-2", 
            "Regał C-3", "Regał D-1", "Regał D-2", "Regał D-3"
        ]
        self.location_combo.addItems(standard_locations)
        
        if self.is_edit_mode and self.location:
            if self.location not in standard_locations:
                self.location_combo.addItem(self.location)
            self.location_combo.setCurrentText(self.location)
        
        tire_grid.addWidget(self.location_combo, 1, 3)
        
        # Dodanie grid layout do głównego layout'u sekcji
        tire_layout.addLayout(tire_grid)
        
        main_layout.addWidget(tire_frame)
        
        # Sekcja dat
        date_frame = QFrame()
        date_frame.setStyleSheet("""
            QFrame { 
                background-color: #2a2a2a;  
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        date_layout = QVBoxLayout(date_frame)
        date_layout.setContentsMargins(15, 15, 15, 15)
        date_layout.setSpacing(10)
        
        # Nagłówek sekcji
        date_header = QLabel(_("Daty i status"))
        date_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        date_layout.addWidget(date_header)
        
        # Grid layout dla dat
        date_grid = QGridLayout()
        date_grid.setSpacing(10)
        
        # Data przyjęcia
        date_grid.addWidget(QLabel(_("Data przyjęcia:")), 0, 0)
        
        self.deposit_date_edit = QDateEdit()
        self.deposit_date_edit.setCalendarPopup(True)
        self.deposit_date_edit.setDate(
            QDate(self.deposit_date.year, self.deposit_date.month, self.deposit_date.day)
        )
        
        date_grid.addWidget(self.deposit_date_edit, 0, 1)
        
        # Data odbioru
        date_grid.addWidget(QLabel(_("Data odbioru:")), 0, 2)
        
        self.pickup_date_edit = QDateEdit()
        self.pickup_date_edit.setCalendarPopup(True)
        self.pickup_date_edit.setDate(
            QDate(self.pickup_date.year, self.pickup_date.month, self.pickup_date.day)
        )
        
        date_grid.addWidget(self.pickup_date_edit, 0, 3)
        
        # Status depozytu
        date_grid.addWidget(QLabel(_("Status:")), 1, 0)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            _("Aktywny"), 
            _("Do odbioru"), 
            _("Zaległy"), 
            _("Rezerwacja")
        ])
        
        if self.is_edit_mode:
            index = self.status_combo.findText(self.status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        
        date_grid.addWidget(self.status_combo, 1, 1)
        
        # Dodanie grid layout do głównego layout'u sekcji
        date_layout.addLayout(date_grid)
        
        main_layout.addWidget(date_frame)
        
        # Uwagi
        notes_frame = QFrame()
        notes_frame.setStyleSheet("""
            QFrame { 
                background-color: #2a2a2a;  
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(15, 15, 15, 15)
        notes_layout.setSpacing(10)
        
        # Nagłówek sekcji
        notes_header = QLabel(_("Uwagi"))
        notes_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        notes_layout.addWidget(notes_header)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(_("Dodatkowe informacje o depozycie..."))
        self.notes_edit.setMaximumHeight(100)
        if self.is_edit_mode and self.notes:
            self.notes_edit.setText(self.notes)
        
        notes_layout.addWidget(self.notes_edit)
        
        main_layout.addWidget(notes_frame)
        
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
        
        self.save_btn = QPushButton(_("Zapisz"))
        self.save_btn.setStyleSheet("""
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
        """)
        self.save_btn.clicked.connect(self.save_deposit)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        # Ustawienie rozmiaru dialogu
        self.resize(800, 650)
        
        # Jeśli w trybie edycji, wypełnij pola
        if self.is_edit_mode and self.client_id:
            self.client_input.setText(self.client_name)
            self.load_vehicles_for_client(self.client_id)
            if self.vehicle_id:
                # Znajdź i ustaw wybrany pojazd
                for i in range(self.vehicle_combo.count()):
                    if self.vehicle_combo.itemData(i) == self.vehicle_id:
                        self.vehicle_combo.setCurrentIndex(i)
                        break
        
        # Zastosowanie stylu strzałek dla wszystkich comboboxów
        # Ta sekcja musi być na końcu init_ui, po utworzeniu wszystkich kontrolek
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
        
        # Zastosowanie stylu do wszystkich comboboxów
        self.tire_size_combo.setStyleSheet(dropdown_style)
        self.tire_type_combo.setStyleSheet(dropdown_style)
        self.vehicle_combo.setStyleSheet(dropdown_style)
        self.location_combo.setStyleSheet(dropdown_style)
        self.status_combo.setStyleSheet(dropdown_style)
    
    def load_clients_list(self):
        """Ładuje pełną listę klientów do autocomplete."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz wszystkich klientów
            cursor.execute("""
                SELECT id, name, phone_number, email 
                FROM clients 
                ORDER BY name
            """)
            
            clients = cursor.fetchall()
            
            # Zapisz listę klientów i utwórz listę nazw do autocomplete
            self.clients_data = clients
            self.clients_list = [client['name'] for client in clients]
            
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania listy klientów: {e}",
                NotificationTypes.ERROR
            )
    
    def on_client_text_changed(self, text):
        """Obsługuje zmianę tekstu w polu klienta."""
        if not text:
            self.client_id = None
            self.vehicle_combo.clear()
            self.vehicle_combo.setEnabled(False)
            self.add_vehicle_btn.setEnabled(False)
            return
        
        # Sprawdź czy wpisany tekst odpowiada dokładnie jakiemuś klientowi
        found = False
        for client in self.clients_data:
            if client['name'].lower() == text.lower():
                self.client_id = client['id']
                self.client_name = client['name']
                self.load_vehicles_for_client(self.client_id)
                found = True
                break
        
        # Jeśli nie znaleziono klienta, wyczyść ID
        if not found:
            self.client_id = None
            self.vehicle_combo.clear()
            self.vehicle_combo.setEnabled(False)
            self.add_vehicle_btn.setEnabled(False)
    
    def load_vehicles_for_client(self, client_id):
        """Ładuje pojazdy dla wybranego klienta."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz pojazdy klienta
            cursor.execute("""
                SELECT id, make, model, registration_number, tire_size 
                FROM vehicles 
                WHERE client_id = ? 
                ORDER BY make, model
            """, (client_id,))
            
            vehicles = cursor.fetchall()
            
            # Wyczyść i wypełnij combobox
            self.vehicle_combo.clear()
            self.vehicle_combo.addItem(_("-- Wybierz pojazd --"), None)
            
            for vehicle in vehicles:
                display_text = f"{vehicle['make']} {vehicle['model']} ({vehicle['registration_number']})"
                self.vehicle_combo.addItem(display_text, vehicle['id'])
                
                # Zapisz rozmiar opon pojazdu do późniejszego użycia
                if 'tire_size' in vehicle and vehicle['tire_size']:
                    self.vehicles_list.append((vehicle['id'], vehicle['tire_size']))
            
            # Włącz combo i przycisk dodawania pojazdu
            self.vehicle_combo.setEnabled(True)
            self.add_vehicle_btn.setEnabled(True)
            
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania pojazdów klienta: {e}",
                NotificationTypes.ERROR
            )
    
    def on_vehicle_selected(self, index):
        """Obsługuje wybór pojazdu z comboboxa."""
        if index <= 0:  # Pierwszy element to placeholder
            self.vehicle_id = None
            return
        
        self.vehicle_id = self.vehicle_combo.itemData(index)
        
        # Znajdź rozmiar opon wybranego pojazdu
        for vehicle_id, tire_size in self.vehicles_list:
            if vehicle_id == self.vehicle_id and tire_size:
                # Ustaw rozmiar opon z pojazdu
                self.tire_size_combo.setCurrentText(tire_size)
                break
    
    def add_new_client(self):
        """Otwiera dialog dodawania nowego klienta."""
        try:
            dialog = ClientDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Aktualizuj listę klientów
                self.load_clients_list()
                
                # Ustaw nowo dodanego klienta jako wybranego
                self.client_id = dialog.client_id
                self.client_name = dialog.client_name
                self.client_input.setText(dialog.client_name)
                
                # Załaduj pojazdy tego klienta (nie powinno ich być, ale dla spójności)
                self.load_vehicles_for_client(self.client_id)
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"Dodano nowego klienta: {dialog.client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania nowego klienta: {e}",
                NotificationTypes.ERROR
            )
    
    def add_new_vehicle(self):
        """Otwiera dialog dodawania nowego pojazdu dla wybranego klienta."""
        if not self.client_id:
            QMessageBox.warning(
                self, 
                _("Uwaga"), 
                _("Najpierw wybierz klienta.")
            )
            return
            
        try:
            dialog = VehicleDialog(self.conn, client_id=self.client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę pojazdów klienta
                self.load_vehicles_for_client(self.client_id)
                
                # Ustaw nowo dodany pojazd jako wybrany
                for i in range(self.vehicle_combo.count()):
                    if self.vehicle_combo.itemData(i) == dialog.vehicle_id:
                        self.vehicle_combo.setCurrentIndex(i)
                        break
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"Dodano nowy pojazd dla klienta: {self.client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania nowego pojazdu: {e}",
                NotificationTypes.ERROR
            )
    
    def fill_form(self):
        """Wypełnia formularz danymi depozytu."""
        # Większość pól już została wypełniona w init_ui()
        pass
    
    def validate_form(self):
        """Sprawdza poprawność danych formularza."""
        # Sprawdź, czy wybrano klienta
        if not self.client_id:
            QMessageBox.warning(self, _("Błąd walidacji"), _("Wybierz klienta dla depozytu."))
            return False
        
        # Sprawdź, czy podano rozmiar opon
        if not self.tire_size_combo.currentText().strip():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Podaj rozmiar opon."))
            return False
        
        # Sprawdź daty
        deposit_date = self.deposit_date_edit.date().toPython()
        pickup_date = self.pickup_date_edit.date().toPython()
        
        if deposit_date > pickup_date:
            QMessageBox.warning(
                self, 
                _("Błąd walidacji"), 
                _("Data odbioru nie może być wcześniejsza niż data przyjęcia.")
            )
            return False
        
        return True
    
    def save_deposit(self):
        """Zapisuje depozyt do bazy danych."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Pobierz wartości z pól formularza
            client_id = self.client_id
            vehicle_id = self.vehicle_id  # Może być None jeśli nie wybrano pojazdu
            deposit_date = self.deposit_date_edit.date().toString("yyyy-MM-dd")
            pickup_date = self.pickup_date_edit.date().toString("yyyy-MM-dd")
            tire_size = self.tire_size_combo.currentText().strip()
            tire_type = self.tire_type_combo.currentText()
            quantity = self.quantity_spin.value()
            location = self.location_combo.currentText().strip()
            status = self.status_combo.currentText()
            notes = self.notes_edit.toPlainText()
            
            # Sprawdźmy czy tabela deposits ma kolumnę notes
            cursor.execute("PRAGMA table_info(deposits)")
            columns = [column[1] for column in cursor.fetchall()]
            has_notes_column = "notes" in columns
            has_vehicle_id_column = "vehicle_id" in columns
            
            if self.is_edit_mode:
                # Aktualizacja istniejącego depozytu
                if has_vehicle_id_column and has_notes_column:
                    # Pełna wersja z vehicle_id i notes
                    cursor.execute(
                        """
                        UPDATE deposits SET 
                            client_id = ?, 
                            vehicle_id = ?,
                            deposit_date = ?, 
                            pickup_date = ?, 
                            tire_size = ?, 
                            tire_type = ?, 
                            quantity = ?, 
                            location = ?, 
                            status = ?, 
                            notes = ?
                        WHERE id = ?
                        """,
                        (client_id, vehicle_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, notes, self.deposit_id)
                    )
                elif has_vehicle_id_column:
                    # Wersja z vehicle_id, bez notes
                    cursor.execute(
                        """
                        UPDATE deposits SET 
                            client_id = ?, 
                            vehicle_id = ?,
                            deposit_date = ?, 
                            pickup_date = ?, 
                            tire_size = ?, 
                            tire_type = ?, 
                            quantity = ?, 
                            location = ?, 
                            status = ?
                        WHERE id = ?
                        """,
                        (client_id, vehicle_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, self.deposit_id)
                    )
                elif has_notes_column:
                    # Wersja bez vehicle_id, z notes
                    cursor.execute(
                        """
                        UPDATE deposits SET 
                            client_id = ?, 
                            deposit_date = ?, 
                            pickup_date = ?, 
                            tire_size = ?, 
                            tire_type = ?, 
                            quantity = ?, 
                            location = ?, 
                            status = ?, 
                            notes = ?
                        WHERE id = ?
                        """,
                        (client_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, notes, self.deposit_id)
                    )
                else:
                    # Wersja bez vehicle_id i bez notes
                    cursor.execute(
                        """
                        UPDATE deposits SET 
                            client_id = ?, 
                            deposit_date = ?, 
                            pickup_date = ?, 
                            tire_size = ?, 
                            tire_type = ?, 
                            quantity = ?, 
                            location = ?, 
                            status = ?
                        WHERE id = ?
                        """,
                        (client_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, self.deposit_id)
                    )
            else:
                # Dodanie nowego depozytu
                if has_vehicle_id_column and has_notes_column:
                    # Pełna wersja z vehicle_id i notes
                    cursor.execute(
                        """
                        INSERT INTO deposits (
                            client_id, vehicle_id, deposit_date, pickup_date, tire_size, 
                            tire_type, quantity, location, status, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (client_id, vehicle_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, notes)
                    )
                elif has_vehicle_id_column:
                    # Wersja z vehicle_id, bez notes
                    cursor.execute(
                        """
                        INSERT INTO deposits (
                            client_id, vehicle_id, deposit_date, pickup_date, tire_size, 
                            tire_type, quantity, location, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (client_id, vehicle_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status)
                    )
                elif has_notes_column:
                    # Wersja bez vehicle_id, z notes
                    cursor.execute(
                        """
                        INSERT INTO deposits (
                            client_id, deposit_date, pickup_date, tire_size, 
                            tire_type, quantity, location, status, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (client_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status, notes)
                    )
                else:
                    # Wersja bez vehicle_id i bez notes
                    cursor.execute(
                        """
                        INSERT INTO deposits (
                            client_id, deposit_date, pickup_date, tire_size, 
                            tire_type, quantity, location, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (client_id, deposit_date, pickup_date, tire_size, tire_type, 
                         quantity, location, status)
                    )
                
                # Zapisz ID nowego depozytu
                self.deposit_id = cursor.lastrowid
            
            self.conn.commit()
            
            # Powiadomienie o sukcesie
            action = _("zaktualizowano") if self.is_edit_mode else _("dodano")
            NotificationManager.get_instance().show_notification(
                f"Depozyt pomyślnie {action}",
                NotificationTypes.SUCCESS
            )
            
            self.accept()  # Zamknij dialog z akceptacją
            
        except Exception as e:
            self.conn.rollback()
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zapisywania depozytu: {e}",
                NotificationTypes.ERROR
            )