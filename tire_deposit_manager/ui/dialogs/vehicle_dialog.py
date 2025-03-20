#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do dodawania i edycji pojazdów klientów.
"""

import os
import logging
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QCheckBox, QSpinBox, QDateEdit, QDialogButtonBox, 
    QMessageBox
)
from PySide6.QtCore import Qt, QRegularExpression, QDate
from PySide6.QtGui import QRegularExpressionValidator, QFont

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class VehicleDialog(QDialog):
    """
    Dialog do dodawania i edycji danych pojazdu klienta.
    """
    
    def __init__(self, db_connection, vehicle_id=None, client_id=None, parent=None):
        """
        Inicjalizacja dialogu pojazdu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            vehicle_id (int, optional): ID pojazdu do edycji. Domyślnie None (nowy pojazd).
            client_id (int, optional): ID klienta, do którego przypisany jest pojazd. 
                                      Wymagane dla nowego pojazdu.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.vehicle_id = vehicle_id
        self.client_id = client_id
        
        if not client_id and not vehicle_id:
            raise ValueError("Należy podać client_id dla nowego pojazdu")
        
        self.setWindowTitle("Dodaj nowy pojazd" if vehicle_id is None else "Edytuj pojazd")
        self.setMinimumWidth(500)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Jeśli edycja, załaduj dane pojazdu
        if vehicle_id is not None:
            self.load_vehicle_data()
        
        # Jeśli nowy pojazd dla istniejącego klienta, załaduj dane klienta
        elif client_id is not None:
            self.load_client_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        main_layout = QVBoxLayout(self)
        
        # Formularz danych pojazdu
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Dane klienta (tylko wyświetlanie)
        self.client_info_label = QLabel("Klient: ")
        self.client_info_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(self.client_info_label)
        
        # Marka pojazdu
        self.make_input = QLineEdit()
        self.make_input.setPlaceholderText("np. Toyota, Volkswagen, Audi")
        form_layout.addRow("Marka*:", self.make_input)
        
        # Model pojazdu
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("np. Corolla, Golf, A4")
        form_layout.addRow("Model*:", self.model_input)
        
        # Rok produkcji
        self.year_spin = QSpinBox()
        current_year = QDate.currentDate().year()
        self.year_spin.setRange(1980, current_year)
        self.year_spin.setValue(current_year)
        form_layout.addRow("Rok produkcji:", self.year_spin)
        
        # Numer rejestracyjny
        self.registration_input = QLineEdit()
        self.registration_input.setPlaceholderText("np. WA12345")
        # Walidator numeru rejestracyjnego
        reg_regex = QRegularExpression("^[A-Z]{2,3}[0-9A-Z]{3,5}$")
        self.registration_input.setValidator(QRegularExpressionValidator(reg_regex))
        form_layout.addRow("Nr rejestracyjny*:", self.registration_input)
        
        # VIN
        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText("np. WVWZZZ1JZXW000001")
        # Walidator numeru VIN
        vin_regex = QRegularExpression("^[A-HJ-NPR-Z0-9]{17}$")
        self.vin_input.setValidator(QRegularExpressionValidator(vin_regex))
        form_layout.addRow("VIN:", self.vin_input)
        
        # Rozmiar opon
        self.tire_size_combo = QComboBox()
        self.tire_size_combo.setEditable(True)
        self.tire_size_combo.addItems([
            "195/65 R15", "205/55 R16", "225/45 R17", "225/40 R18",
            "235/35 R19", "245/35 R20", "175/70 R14", "185/60 R15"
        ])
        form_layout.addRow("Rozmiar opon:", self.tire_size_combo)
        
        # Typ pojazdu
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems([
            "Osobowy", "SUV", "Dostawczy", "Terenowy", "Ciężarowy", "Motocykl", "Inny"
        ])
        form_layout.addRow("Typ pojazdu:", self.vehicle_type_combo)
        
        # Dodatkowe informacje
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Wprowadź dodatkowe informacje o pojeździe...")
        form_layout.addRow("Uwagi:", self.notes_input)
        
        main_layout.addLayout(form_layout)
        
        # Dodanie pola informacji o polach wymaganych
        required_info = QLabel("* - pola wymagane")
        required_info.setStyleSheet("color: #e74c3c;")
        main_layout.addWidget(required_info)
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_vehicle)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def load_client_data(self):
        """Ładuje dane klienta dla nowego pojazdu."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane klienta
            cursor.execute(
                "SELECT name FROM clients WHERE id = ?",
                (self.client_id,)
            )
            
            client = cursor.fetchone()
            if client:
                client_name = client[0]
                self.client_info_label.setText(f"Klient: {client_name}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania danych klienta:\n{str(e)}"
            )
    
    def load_vehicle_data(self):
        """Ładuje dane pojazdu do formularza."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane pojazdu
            cursor.execute("""
                SELECT v.make, v.model, v.year, v.registration_number, v.vin, 
                       v.tire_size, v.vehicle_type, v.notes, v.client_id, c.name
                FROM vehicles v
                JOIN clients c ON v.client_id = c.id
                WHERE v.id = ?
            """, (self.vehicle_id,))
            
            vehicle = cursor.fetchone()
            if not vehicle:
                logger.error(f"Nie znaleziono pojazdu o ID: {self.vehicle_id}")
                QMessageBox.critical(
                    self, 
                    "Błąd", 
                    f"Nie znaleziono pojazdu o ID: {self.vehicle_id}"
                )
                self.reject()
                return
            
            # Rozpakowanie danych
            make, model, year, reg_number, vin, tire_size, vehicle_type, notes, client_id, client_name = vehicle
            
            # Ustawienie danych w formularzu
            self.client_info_label.setText(f"Klient: {client_name}")
            self.make_input.setText(make or "")
            self.model_input.setText(model or "")
            self.year_spin.setValue(year or QDate.currentDate().year())
            self.registration_input.setText(reg_number or "")
            self.vin_input.setText(vin or "")
            
            # Ustawienie rozmiaru opon
            if tire_size:
                if self.tire_size_combo.findText(tire_size) == -1:
                    self.tire_size_combo.addItem(tire_size)
                self.tire_size_combo.setCurrentText(tire_size)
            
            # Ustawienie typu pojazdu
            if vehicle_type:
                index = self.vehicle_type_combo.findText(vehicle_type)
                if index >= 0:
                    self.vehicle_type_combo.setCurrentIndex(index)
                else:
                    self.vehicle_type_combo.setCurrentIndex(0)
            
            self.notes_input.setText(notes or "")
            
            # Zapisanie ID klienta
            self.client_id = client_id
            
            logger.debug(f"Załadowano dane pojazdu o ID: {self.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania danych pojazdu:\n{str(e)}"
            )
    
    def validate_form(self):
        """
        Sprawdza poprawność danych w formularzu.
        
        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym razie
        """
        # Sprawdzenie marki
        if not self.make_input.text().strip():
            QMessageBox.critical(
                self, 
                "Błąd", 
                "Marka pojazdu jest wymagana."
            )
            self.make_input.setFocus()
            return False
        
        # Sprawdzenie modelu
        if not self.model_input.text().strip():
            QMessageBox.critical(
                self, 
                "Błąd", 
                "Model pojazdu jest wymagany."
            )
            self.model_input.setFocus()
            return False
        
        # Sprawdzenie numeru rejestracyjnego
        reg_number = self.registration_input.text().strip()
        if not reg_number:
            QMessageBox.critical(
                self, 
                "Błąd", 
                "Numer rejestracyjny jest wymagany."
            )
            self.registration_input.setFocus()
            return False
        elif not self.registration_input.hasAcceptableInput():
            QMessageBox.warning(
                self, 
                "Nieprawidłowy numer rejestracyjny", 
                "Podany numer rejestracyjny ma nieprawidłowy format."
            )
            self.registration_input.setFocus()
            return False
        
        # Sprawdzenie VIN
        vin = self.vin_input.text().strip()
        if vin and not self.vin_input.hasAcceptableInput():
            QMessageBox.warning(
                self, 
                "Nieprawidłowy numer VIN", 
                "Podany numer VIN ma nieprawidłowy format."
            )
            self.vin_input.setFocus()
            return False
        
        # Sprawdzenie, czy numer rejestracyjny nie jest już używany przez inny pojazd
        cursor = self.conn.cursor()
        if self.vehicle_id:
            # Edycja - sprawdź, czy numer nie jest używany przez inny pojazd
            cursor.execute(
                "SELECT id FROM vehicles WHERE registration_number = ? AND id != ?",
                (reg_number, self.vehicle_id)
            )
        else:
            # Nowy pojazd - sprawdź, czy numer nie jest już używany
            cursor.execute(
                "SELECT id FROM vehicles WHERE registration_number = ?",
                (reg_number,)
            )
        
        existing = cursor.fetchone()
        if existing:
            QMessageBox.critical(
                self, 
                "Błąd", 
                "Ten numer rejestracyjny jest już przypisany do innego pojazdu."
            )
            self.registration_input.setFocus()
            return False
        
        return True
    
    def save_vehicle(self):
        """Zapisuje dane pojazdu do bazy danych."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie danych
            make = self.make_input.text().strip()
            model = self.model_input.text().strip()
            year = self.year_spin.value()
            registration_number = self.registration_input.text().strip().upper()
            vin = self.vin_input.text().strip().upper()
            tire_size = self.tire_size_combo.currentText().strip()
            vehicle_type = self.vehicle_type_combo.currentText()
            notes = self.notes_input.text().strip()
            
            # Zapis do bazy danych
            if self.vehicle_id:  # Edycja istniejącego pojazdu
                cursor.execute(
                    """
                    UPDATE vehicles
                    SET make = ?, model = ?, year = ?, registration_number = ?, 
                        vin = ?, tire_size = ?, vehicle_type = ?, notes = ?
                    WHERE id = ?
                    """,
                    (make, model, year, registration_number, vin, tire_size, 
                     vehicle_type, notes, self.vehicle_id)
                )
                
                logger.info(f"Zaktualizowano pojazd o ID: {self.vehicle_id}")
                
            else:  # Nowy pojazd
                cursor.execute(
                    """
                    INSERT INTO vehicles
                    (client_id, make, model, year, registration_number, vin, 
                     tire_size, vehicle_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (self.client_id, make, model, year, registration_number, vin, 
                     tire_size, vehicle_type, notes)
                )
                
                # Pobranie ID nowego pojazdu
                self.vehicle_id = cursor.lastrowid
                
                logger.info(f"Utworzono nowy pojazd o ID: {self.vehicle_id}")
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Zamknij dialog z sukcesem
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania danych pojazdu:\n{str(e)}"
            )