#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do dodawania i edycji klientów.
"""

import os
import logging
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QCheckBox, QSpinBox, QTextEdit, QDialogButtonBox, 
    QMessageBox
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QFont

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class ClientDialog(QDialog):
    """
    Dialog do dodawania i edycji danych klienta.
    """
    
    def __init__(self, db_connection, client_id=None, parent=None):
        """
        Inicjalizacja dialogu klienta.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            client_id (int, optional): ID klienta do edycji. Domyślnie None (nowy klient).
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.client_id = client_id
        self.client_name = None  # Będzie ustawione po zapisaniu
        
        self.setWindowTitle("Dodaj nowego klienta" if client_id is None else "Edytuj klienta")
        self.setMinimumWidth(500)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Jeśli edycja, załaduj dane klienta
        if client_id is not None:
            self.load_client_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        main_layout = QVBoxLayout(self)
        
        # Ustawienie stylów - dodane style podobne do tych z order_dialog.py
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QLabel {
                background-color: transparent;  /* Przezroczyste tło etykiet */
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
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
            QDialogButtonBox QPushButton {
                min-height: 30px;
                min-width: 80px;
            }
        """)

        # Formularz danych klienta
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Nazwa klienta
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Wprowadź imię i nazwisko lub nazwę firmy")
        form_layout.addRow("Nazwa klienta*:", self.name_input)
        
        # Telefon
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("np. 123-456-789")
        # Walidator numeru telefonu
        phone_regex = QRegularExpression("^[0-9\\+\\-\\s]{6,15}$")
        self.phone_input.setValidator(QRegularExpressionValidator(phone_regex))
        form_layout.addRow("Telefon:", self.phone_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("np. jan.kowalski@example.com")
        # Walidator adresu email
        email_regex = QRegularExpression("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
        self.email_input.setValidator(QRegularExpressionValidator(email_regex))
        form_layout.addRow("Email:", self.email_input)
        
        # Informacje dodatkowe
        self.info_input = QTextEdit()
        self.info_input.setPlaceholderText("Wprowadź dodatkowe informacje o kliencie...")
        self.info_input.setMaximumHeight(100)
        form_layout.addRow("Informacje dodatkowe:", self.info_input)
        
        # Rabat
        self.discount_spin = QSpinBox()
        self.discount_spin.setRange(0, 50)
        self.discount_spin.setSingleStep(1)
        self.discount_spin.setSuffix("%")
        form_layout.addRow("Rabat:", self.discount_spin)
        
        # Typ klienta
        self.client_type_combo = QComboBox()
        self.client_type_combo.addItems(["Indywidualny", "Firma"])
        form_layout.addRow("Typ klienta:", self.client_type_combo)

        # Kod kreskowy
        barcode_layout = QHBoxLayout()
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("np. C-00001")
        barcode_layout.addWidget(self.barcode_input, 1)
        
        generate_barcode_button = QPushButton("Generuj kod")
        generate_barcode_button.setIcon(QIcon(os.path.join(ICONS_DIR, "barcode.png")))
        generate_barcode_button.clicked.connect(self.generate_barcode)
        barcode_layout.addWidget(generate_barcode_button)
        
        form_layout.addRow("Kod kreskowy:", barcode_layout)
        
        main_layout.addLayout(form_layout)
        
        # Dodanie pola informacji o polach wymaganych
        required_info = QLabel("* - pola wymagane")
        required_info.setStyleSheet("color: #e74c3c;")
        main_layout.addWidget(required_info)
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_client)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def load_client_data(self):
        """Ładuje dane klienta do formularza."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane klienta
            cursor.execute(
                "SELECT name, phone_number, email, additional_info, discount, barcode, client_type FROM clients WHERE id = ?",
                (self.client_id,)
            )
            
            client = cursor.fetchone()
            if not client:
                logger.error(f"Nie znaleziono klienta o ID: {self.client_id}")
                QMessageBox.critical(
                    self, 
                    "Błąd", 
                    f"Nie znaleziono klienta o ID: {self.client_id}"
                )
                self.reject()
                return
            
            # Rozpakowanie danych
            name, phone_number, email, additional_info, discount, barcode, client_type = client
            
            # Ustawienie danych w formularzu
            self.name_input.setText(name or "")
            self.phone_input.setText(phone_number or "")
            self.email_input.setText(email or "")
            self.info_input.setText(additional_info or "")
            self.discount_spin.setValue(int(discount) if discount is not None else 0)
            self.barcode_input.setText(barcode or "")
            
            # Ustawienie typu klienta
            if client_type == "Firma":
                self.client_type_combo.setCurrentText("Firma")
            else:
                self.client_type_combo.setCurrentText("Indywidualny")
            
            # Zapisanie nazwy klienta
            self.client_name = name
            
            logger.debug(f"Załadowano dane klienta o ID: {self.client_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania danych klienta:\n{str(e)}"
            )
    
    def generate_barcode(self):
        """Generuje unikalny kod kreskowy dla klienta."""
        try:
            cursor = self.conn.cursor()
            
            # Generowanie kodu w formacie C-XXXXX z ID klienta lub losową liczbą
            if self.client_id:
                barcode = f"C-{self.client_id:05d}"
            else:
                # Pobierz maksymalne ID z tabeli clients
                cursor.execute("SELECT MAX(id) FROM clients")
                max_id = cursor.fetchone()[0]
                
                if max_id:
                    barcode = f"C-{(max_id + 1):05d}"
                else:
                    barcode = "C-00001"
            
            # Ustaw wygenerowany kod
            self.barcode_input.setText(barcode)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania kodu kreskowego: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas generowania kodu kreskowego:\n{str(e)}"
            )
    
    def validate_form(self):
        """
        Sprawdza poprawność danych w formularzu.
        
        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym razie
        """
        # Sprawdzenie nazwy
        if not self.name_input.text().strip():
            QMessageBox.critical(
                self, 
                "Błąd", 
                "Nazwa klienta jest wymagana."
            )
            self.name_input.setFocus()
            return False
        
        # Sprawdzenie emaila
        email = self.email_input.text().strip()
        if email and not self.email_input.hasAcceptableInput():
            QMessageBox.warning(
                self, 
                "Nieprawidłowy email", 
                "Podany adres e-mail ma nieprawidłowy format."
            )
            self.email_input.setFocus()
            return False
        
        # Sprawdzenie telefonu
        phone = self.phone_input.text().strip()
        if phone and not self.phone_input.hasAcceptableInput():
            QMessageBox.warning(
                self, 
                "Nieprawidłowy telefon", 
                "Podany numer telefonu ma nieprawidłowy format."
            )
            self.phone_input.setFocus()
            return False
        
        # Sprawdzenie kodu kreskowego
        barcode = self.barcode_input.text().strip()
        if barcode:
            # Sprawdź unikalność kodu (jeśli inny klient już go ma)
            cursor = self.conn.cursor()
            
            # Sprawdź, czy kod jest już używany przez innego klienta
            if self.client_id:
                cursor.execute(
                    "SELECT id FROM clients WHERE barcode = ? AND id != ?",
                    (barcode, self.client_id)
                )
            else:
                cursor.execute(
                    "SELECT id FROM clients WHERE barcode = ?",
                    (barcode,)
                )
            
            if cursor.fetchone():
                QMessageBox.warning(
                    self, 
                    "Duplikat kodu", 
                    "Podany kod kreskowy jest już używany przez innego klienta."
                )
                self.barcode_input.setFocus()
                return False
            
            # Opcjonalnie: walidacja formatu kodu
            if not re.match(r'^C-\d{5}$', barcode):
                reply = QMessageBox.question(
                    self,
                    "Niestandardowy format kodu",
                    "Zalecany format kodu to C-XXXXX (gdzie X to cyfra).\n"
                    "Czy na pewno chcesz użyć niestandardowego formatu?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.barcode_input.setFocus()
                    return False
        
        return True
    
    def save_client(self):
        """Zapisuje dane klienta do bazy danych."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie danych
            name = self.name_input.text().strip()
            phone_number = self.phone_input.text().strip()
            email = self.email_input.text().strip()
            additional_info = self.info_input.toPlainText().strip()
            discount = self.discount_spin.value()
            barcode = self.barcode_input.text().strip()
            client_type = self.client_type_combo.currentText()
            
            # Zapis do bazy danych
            if self.client_id:  # Edycja istniejącego klienta
                cursor.execute(
                    """
                    UPDATE clients
                    SET name = ?, phone_number = ?, email = ?, additional_info = ?, discount = ?, barcode = ?, client_type = ?
                    WHERE id = ?
                    """,
                    (name, phone_number, email, additional_info, discount, barcode, client_type, self.client_id)
                )
                
                logger.info(f"Zaktualizowano klienta o ID: {self.client_id}")
                
            else:  # Nowy klient
                cursor.execute(
                    """
                    INSERT INTO clients
                    (name, phone_number, email, additional_info, discount, barcode, client_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, phone_number, email, additional_info, discount, barcode, client_type)
                )
                
                # Pobranie ID nowego klienta
                self.client_id = cursor.lastrowid
                
                logger.info(f"Utworzono nowego klienta o ID: {self.client_id}")
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Zapisanie nazwy klienta
            self.client_name = name
            
            # Zamknij dialog z sukcesem
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas zapisywania danych klienta:\n{str(e)}"
            )