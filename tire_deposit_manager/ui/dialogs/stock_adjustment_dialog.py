#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do korekty stanu magazynowego części/akcesoriów.
"""

import os
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QSpinBox, QRadioButton, QButtonGroup,
    QDialogButtonBox, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class StockAdjustmentDialog(QDialog):
    """
    Dialog do korekty stanu magazynowego części/akcesoriów.
    Umożliwia zwiększenie lub zmniejszenie stanu magazynowego oraz dodanie notatki o korekcie.
    """
    
    def __init__(self, db_connection, part_id, part_name, current_quantity, parent=None):
        """
        Inicjalizacja dialogu korekty stanu magazynowego.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            part_id (int): ID części/akcesorium
            part_name (str): Nazwa części/akcesorium
            current_quantity (int): Aktualny stan magazynowy
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.part_id = part_id
        self.part_name = part_name
        self.current_quantity = current_quantity
        
        self.setWindowTitle("Korekta stanu magazynowego")
        self.resize(500, 400)
        
        # Inicjalizacja UI
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Nagłówek
        header_label = QLabel(f"Korekta stanu magazynowego - {self.part_name}")
        header_label.setObjectName("headerLabel")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        main_layout.addWidget(header_label)
        
        # Formularz korekty
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Aktualny stan
        current_quantity_label = QLabel(f"{self.current_quantity}")
        current_quantity_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        form_layout.addRow("Aktualny stan:", current_quantity_label)
        
        # Rodzaj operacji
        operation_label = QLabel("Rodzaj operacji:")
        form_layout.addRow(operation_label)
        
        operation_layout = QHBoxLayout()
        
        self.operation_group = QButtonGroup()
        
        self.add_radio = QRadioButton("Dodaj")
        self.add_radio.setChecked(True)
        self.operation_group.addButton(self.add_radio)
        operation_layout.addWidget(self.add_radio)
        
        self.subtract_radio = QRadioButton("Odejmij")
        self.operation_group.addButton(self.subtract_radio)
        operation_layout.addWidget(self.subtract_radio)
        
        self.set_radio = QRadioButton("Ustaw wartość")
        self.operation_group.addButton(self.set_radio)
        operation_layout.addWidget(self.set_radio)
        
        form_layout.addRow("", operation_layout)
        
        # Ilość do korekty
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.update_new_quantity)
        form_layout.addRow("Ilość:", self.quantity_spin)
        
        # Powód korekty
        self.reason_combo = QComboBox()
        self.reason_combo.setEditable(True)
        self.reason_combo.addItems([
            "Dostawa towaru",
            "Sprzedaż",
            "Inwentaryzacja",
            "Zwrot od klienta",
            "Zwrot do dostawcy",
            "Uszkodzenie/utylizacja",
            "Korekta błędu",
            "Inne"
        ])
        form_layout.addRow("Powód korekty:", self.reason_combo)
        
        # Dokument źródłowy
        self.document_input = QLineEdit()
        self.document_input.setPlaceholderText("Nr faktury, dokument PZ/WZ, itp.")
        form_layout.addRow("Dokument źródłowy:", self.document_input)
        
        # Nowy stan
        self.new_quantity_label = QLabel(f"{self.current_quantity + 1}")
        self.new_quantity_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        form_layout.addRow("Nowy stan:", self.new_quantity_label)
        
        # Uwagi
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Wprowadź dodatkowe uwagi dotyczące korekty stanu...")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Uwagi:", self.notes_edit)
        
        main_layout.addLayout(form_layout)
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Zapisz")
        buttons.button(QDialogButtonBox.Cancel).setText("Anuluj")
        buttons.accepted.connect(self.save_adjustment)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        # Podłączenie sygnałów
        self.add_radio.toggled.connect(self.update_new_quantity)
        self.subtract_radio.toggled.connect(self.update_new_quantity)
        self.set_radio.toggled.connect(self.update_new_quantity)
    
    def update_new_quantity(self):
        """Aktualizuje etykietę nowego stanu na podstawie wybranej operacji i ilości."""
        adjustment_quantity = self.quantity_spin.value()
        
        if self.add_radio.isChecked():
            new_quantity = self.current_quantity + adjustment_quantity
        elif self.subtract_radio.isChecked():
            new_quantity = max(0, self.current_quantity - adjustment_quantity)
        else:  # Set value
            new_quantity = adjustment_quantity
        
        self.new_quantity_label.setText(f"{new_quantity}")
        
        # Zmień kolor tekstu w zależności od zmiany
        if new_quantity > self.current_quantity:
            self.new_quantity_label.setStyleSheet("color: #2ecc71;")  # Zielony dla zwiększenia
        elif new_quantity < self.current_quantity:
            self.new_quantity_label.setStyleSheet("color: #e74c3c;")  # Czerwony dla zmniejszenia
        else:
            self.new_quantity_label.setStyleSheet("")  # Domyślny kolor dla braku zmiany
    
    def save_adjustment(self):
        """Zapisuje korektę stanu magazynowego."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy tabela stock_adjustments istnieje
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_adjustments'")
            if not cursor.fetchone():
                # Utwórz tabelę stock_adjustments
                cursor.execute("""
                    CREATE TABLE stock_adjustments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        part_id INTEGER,
                        adjustment_date TEXT,
                        operation TEXT,
                        quantity INTEGER,
                        old_quantity INTEGER,
                        new_quantity INTEGER,
                        reason TEXT,
                        document TEXT,
                        notes TEXT,
                        user TEXT,
                        FOREIGN KEY(part_id) REFERENCES parts(id)
                    )
                """)
            
            # Przygotowanie danych
            adjustment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Określenie operacji
            if self.add_radio.isChecked():
                operation = "add"
                adjustment_quantity = self.quantity_spin.value()
                new_quantity = self.current_quantity + adjustment_quantity
            elif self.subtract_radio.isChecked():
                operation = "subtract"
                adjustment_quantity = self.quantity_spin.value()
                new_quantity = max(0, self.current_quantity - adjustment_quantity)
            else:  # Set value
                operation = "set"
                adjustment_quantity = self.quantity_spin.value()
                new_quantity = adjustment_quantity
            
            reason = self.reason_combo.currentText()
            document = self.document_input.text()
            notes = self.notes_edit.toPlainText()
            user = "System"  # W przyszłości można dodać system użytkowników
            
            # Zapis korekty do tabeli stock_adjustments
            cursor.execute("""
                INSERT INTO stock_adjustments (
                    part_id, adjustment_date, operation, quantity,
                    old_quantity, new_quantity, reason, document, notes, user
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.part_id, adjustment_date, operation, adjustment_quantity,
                self.current_quantity, new_quantity, reason, document, notes, user
            ))
            
            # Aktualizacja stanu w tabeli parts
            cursor.execute(
                "UPDATE parts SET quantity = ? WHERE id = ?",
                (new_quantity, self.part_id)
            )
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            logger.info(f"Zaktualizowano stan części/akcesorium ID {self.part_id} z {self.current_quantity} na {new_quantity}")
            
            # Zamknij dialog z sukcesem
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania korekty stanu: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania korekty stanu:\n{str(e)}")