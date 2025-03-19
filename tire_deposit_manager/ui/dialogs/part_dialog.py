#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do dodawania i edycji części/akcesoriów.
"""

import os
import logging
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QCompleter, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QRegularExpression, Signal
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QFont

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class PartDialog(QDialog):
    """
    Dialog do dodawania i edycji części/akcesoriów.
    Umożliwia wprowadzenie wszystkich informacji związanych z częściami i akcesoriami.
    """
    
    def __init__(self, db_connection, part_id=None, parent=None):
        """
        Inicjalizacja dialogu części/akcesorium.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            part_id (int, optional): ID części/akcesorium do edycji. Domyślnie None (nowa część).
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.part_id = part_id
        
        self.setWindowTitle("Dodaj nową część/akcesorium" if part_id is None else "Edytuj część/akcesorium")
        self.resize(600, 500)
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Jeśli edycja, załaduj dane części/akcesorium
        if part_id is not None:
            self.load_part_data()
        else:
            # Dla nowej części/akcesorium, ustaw domyślne wartości
            self.set_default_values()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Zakładki
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Zakładka podstawowych informacji
        basic_tab = QWidget()
        self.init_basic_tab(basic_tab)
        self.tabs.addTab(basic_tab, "Podstawowe informacje")
        
        # Zakładka szczegółów
        details_tab = QWidget()
        self.init_details_tab(details_tab)
        self.tabs.addTab(details_tab, "Szczegóły")
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_part)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def init_basic_tab(self, tab):
        """
        Inicjalizacja zakładki z podstawowymi informacjami o części/akcesorium.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Nazwa części/akcesorium
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Wprowadź nazwę części/akcesorium")
        layout.addRow("Nazwa*:", self.name_input)
        
        # Numer katalogowy
        self.catalog_number_input = QLineEdit()
        self.catalog_number_input.setPlaceholderText("np. AB-12345")
        layout.addRow("Numer katalogowy:", self.catalog_number_input)
        
        # Kategoria
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems([
            "Oleje",
            "Filtry",
            "Opony",
            "Felgi",
            "Akcesoria",
            "Części silnikowe",
            "Części zawieszenia",
            "Części elektryczne",
            "Części hamulcowe",
            "Inne"
        ])
        layout.addRow("Kategoria:", self.category_combo)
        
        # Producent
        self.manufacturer_input = QLineEdit()
        manufacturers = self.get_unique_values("manufacturer")
        self.manufacturer_input.setCompleter(QCompleter(manufacturers))
        layout.addRow("Producent:", self.manufacturer_input)
        
        # Ilość
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 9999)
        self.quantity_spin.setValue(0)
        layout.addRow("Ilość:", self.quantity_spin)
        
        # Minimalna ilość (przy której system ostrzega o niskim stanie)
        self.minimum_quantity_spin = QSpinBox()
        self.minimum_quantity_spin.setRange(0, 9999)
        self.minimum_quantity_spin.setValue(1)
        layout.addRow("Minimalna ilość:", self.minimum_quantity_spin)
        
        # Cena
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 99999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setValue(0)
        self.price_spin.setSuffix(" PLN")
        layout.addRow("Cena:", self.price_spin)
        
        # Lokalizacja
        self.location_input = QLineEdit()
        locations = self.get_unique_values("location")
        self.location_input.setCompleter(QCompleter(locations))
        layout.addRow("Lokalizacja:", self.location_input)
    
    def init_details_tab(self, tab):
        """
        Inicjalizacja zakładki ze szczegółami części/akcesorium.
        
        Args:
            tab (QWidget): Widget zakładki do zainicjowania
        """
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Opis
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Wprowadź dodatkowe informacje o części/akcesorium...")
        layout.addRow("Opis:", self.description_input)
        
        # Kod kreskowy
        barcode_layout = QHBoxLayout()
        
        self.barcode_input = QLineEdit()
        barcode_layout.addWidget(self.barcode_input, 1)
        
        generate_barcode_button = QPushButton("Generuj kod")
        generate_barcode_button.setIcon(QIcon(os.path.join(ICONS_DIR, "barcode.png")))
        generate_barcode_button.clicked.connect(self.generate_barcode)
        barcode_layout.addWidget(generate_barcode_button)
        
        layout.addRow("Kod kreskowy:", barcode_layout)
        
        # Podatek VAT
        self.vat_rate_combo = QComboBox()
        self.vat_rate_combo.addItems(["23%", "8%", "5%", "0%"])
        layout.addRow("Stawka VAT:", self.vat_rate_combo)
        
        # Jednostka miary
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["szt.", "kpl.", "para", "l", "ml", "kg", "g", "m", "cm"])
        layout.addRow("Jednostka miary:", self.unit_combo)
        
        # Pole dostawcy
        self.supplier_input = QLineEdit()
        suppliers = self.get_unique_values("supplier")
        self.supplier_input.setCompleter(QCompleter(suppliers))
        layout.addRow("Dostawca:", self.supplier_input)
        
        # Gwarancja
        self.warranty_input = QLineEdit()
        self.warranty_input.setPlaceholderText("np. 24 miesiące")
        layout.addRow("Gwarancja:", self.warranty_input)
    
    def set_default_values(self):
        """Ustawia domyślne wartości dla nowej części/akcesorium."""
        # Domyślne wartości są już ustawione w init_ui
        self.vat_rate_combo.setCurrentText("23%")
        self.unit_combo.setCurrentText("szt.")
    
    def load_part_data(self):
        """Ładuje dane części/akcesorium do formularza."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy tabela ma wszystkie potrzebne kolumny
            cursor.execute("PRAGMA table_info(parts)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Dodaj kolumny, jeśli ich nie ma
            if "supplier" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN supplier TEXT")
            
            if "vat_rate" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN vat_rate TEXT DEFAULT '23%'")
            
            if "unit" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN unit TEXT DEFAULT 'szt.'")
            
            if "warranty" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN warranty TEXT")
            
            # Pobierz dane części/akcesorium
            query = """
                SELECT name, catalog_number, category, manufacturer, 
                    quantity, price, location, description, barcode, 
                    minimum_quantity, supplier, vat_rate, unit, warranty
                FROM parts
                WHERE id = ?
            """
            cursor.execute(query, (self.part_id,))
            
            data = cursor.fetchone()
            if not data:
                logger.error(f"Nie znaleziono części/akcesorium o ID: {self.part_id}")
                QMessageBox.critical(self, "Błąd", f"Nie znaleziono części/akcesorium o ID: {self.part_id}")
                self.reject()
                return
            
            # Rozpakowanie danych
            (name, catalog_number, category, manufacturer, 
             quantity, price, location, description, barcode, 
             minimum_quantity, supplier, vat_rate, unit, warranty) = data
            
            # Ustawienie danych w formularzu
            self.name_input.setText(name or "")
            self.catalog_number_input.setText(catalog_number or "")
            
            if category:
                index = self.category_combo.findText(category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
                else:
                    self.category_combo.addItem(category)
                    self.category_combo.setCurrentText(category)
            
            self.manufacturer_input.setText(manufacturer or "")
            self.quantity_spin.setValue(quantity or 0)
            self.minimum_quantity_spin.setValue(minimum_quantity or 1)
            self.price_spin.setValue(price or 0)
            self.location_input.setText(location or "")
            self.description_input.setText(description or "")
            self.barcode_input.setText(barcode or "")
            self.supplier_input.setText(supplier or "")
            
            if vat_rate:
                index = self.vat_rate_combo.findText(vat_rate)
                if index >= 0:
                    self.vat_rate_combo.setCurrentIndex(index)
            
            if unit:
                index = self.unit_combo.findText(unit)
                if index >= 0:
                    self.unit_combo.setCurrentIndex(index)
            
            self.warranty_input.setText(warranty or "")
            
            logger.debug(f"Załadowano dane części/akcesorium o ID: {self.part_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych części/akcesorium: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych części/akcesorium:\n{str(e)}")
    
    def get_unique_values(self, column_name):
        """
        Pobiera unikalne wartości z określonej kolumny w tabeli części/akcesoriów.
        
        Args:
            column_name (str): Nazwa kolumny
            
        Returns:
            list: Lista unikalnych wartości
        """
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy tabela parts istnieje
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parts'")
            if not cursor.fetchone():
                return []
            
            # Sprawdź, czy kolumna istnieje
            cursor.execute(f"PRAGMA table_info(parts)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if column_name not in columns:
                return []
            
            cursor.execute(f"SELECT DISTINCT {column_name} FROM parts WHERE {column_name} IS NOT NULL AND {column_name} != ''")
            return [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania unikalnych wartości dla {column_name}: {e}")
            return []
    
    def generate_barcode(self):
        """Generuje unikalny kod kreskowy dla części/akcesorium."""
        try:
            cursor = self.conn.cursor()
            
            # Generowanie kodu w formacie P-XXXXX z ID części lub losową liczbą
            if self.part_id:
                barcode = f"P-{self.part_id:05d}"
            else:
                # Pobierz maksymalne ID z tabeli parts
                cursor.execute("SELECT MAX(id) FROM parts")
                max_id = cursor.fetchone()[0]
                
                if max_id:
                    barcode = f"P-{(max_id + 1):05d}"
                else:
                    barcode = "P-00001"
            
            # Ustaw wygenerowany kod
            self.barcode_input.setText(barcode)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania kodu kreskowego: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas generowania kodu kreskowego:\n{str(e)}")
    
    def validate_form(self):
        """
        Sprawdza poprawność danych w formularzu.
        
        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym razie
        """
        # Sprawdzenie nazwy
        if not self.name_input.text().strip():
            QMessageBox.critical(self, "Błąd", "Nazwa części/akcesorium jest wymagana.")
            return False
        
        return True
    
    def save_part(self):
        """Zapisuje część/akcesorium do bazy danych."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie danych
            name = self.name_input.text().strip()
            catalog_number = self.catalog_number_input.text().strip()
            category = self.category_combo.currentText().strip()
            manufacturer = self.manufacturer_input.text().strip()
            quantity = self.quantity_spin.value()
            minimum_quantity = self.minimum_quantity_spin.value()
            price = self.price_spin.value()
            location = self.location_input.text().strip()
            description = self.description_input.toPlainText().strip()
            barcode = self.barcode_input.text().strip()
            supplier = self.supplier_input.text().strip()
            vat_rate = self.vat_rate_combo.currentText()
            unit = self.unit_combo.currentText()
            warranty = self.warranty_input.text().strip()
            
            # Sprawdź, czy tabela ma wszystkie potrzebne kolumny
            cursor.execute("PRAGMA table_info(parts)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Dodaj kolumny, jeśli ich nie ma
            if "supplier" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN supplier TEXT")
            
            if "vat_rate" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN vat_rate TEXT DEFAULT '23%'")
            
            if "unit" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN unit TEXT DEFAULT 'szt.'")
            
            if "warranty" not in columns:
                cursor.execute("ALTER TABLE parts ADD COLUMN warranty TEXT")
            
            # Zapis do bazy danych
            if self.part_id:  # Edycja istniejącej części/akcesorium
                cursor.execute("""
                    UPDATE parts
                    SET name = ?, catalog_number = ?, category = ?, manufacturer = ?,
                        quantity = ?, minimum_quantity = ?, price = ?, location = ?,
                        description = ?, barcode = ?, supplier = ?, vat_rate = ?,
                        unit = ?, warranty = ?
                    WHERE id = ?
                """, (
                    name, catalog_number, category, manufacturer,
                    quantity, minimum_quantity, price, location,
                    description, barcode, supplier, vat_rate,
                    unit, warranty,
                    self.part_id
                ))
                
                logger.info(f"Zaktualizowano część/akcesorium o ID: {self.part_id}")
                
            else:  # Nowa część/akcesorium
                cursor.execute("""
                    INSERT INTO parts (
                        name, catalog_number, category, manufacturer,
                        quantity, minimum_quantity, price, location,
                        description, barcode, supplier, vat_rate,
                        unit, warranty
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, catalog_number, category, manufacturer,
                    quantity, minimum_quantity, price, location,
                    description, barcode, supplier, vat_rate,
                    unit, warranty
                ))
                
                # Pobranie ID nowej części/akcesorium
                self.part_id = cursor.lastrowid
                
                logger.info(f"Utworzono nową część/akcesorium o ID: {self.part_id}")
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Zamknij dialog z sukcesem
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania części/akcesorium: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania części/akcesorium:\n{str(e)}")