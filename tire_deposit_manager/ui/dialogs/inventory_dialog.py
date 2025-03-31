#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do dodawania i edycji opon w magazynie.
"""

import os
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, 
    QTextEdit, QDialogButtonBox, QDateEdit, QCheckBox,
    QFileDialog, QFrame, QTabWidget, QPushButton, QMessageBox, QStyle
)
from PySide6.QtCore import Qt, QDate, QSettings
from PySide6.QtGui import QIcon, QPixmap, QPalette

from utils.i18n import _  # Funkcja do obsługi lokalizacji
from ui.notifications import NotificationManager, NotificationTypes

# Logger
logger = logging.getLogger("TireInventoryManager")

class InventoryDialog(QDialog):
    """
    Dialog do dodawania/edycji opony w magazynie.
    """
    def __init__(self, db_connection, tire_id=None, condition="Nowa", parent=None):
        """
        Inicjalizacja dialogu.
        
        Args:
            db_connection: Połączenie z bazą danych
            tire_id (int, optional): ID opony do edycji (None dla nowej opony)
            condition (str, optional): Domyślny stan opony przy dodawaniu ("Nowa" lub "Używana")
            parent: Widget rodzic
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.tire_id = tire_id
        self.default_condition = condition
        self.tire_data = None
        
        # Ustawienia okna
        if tire_id:
            self.setWindowTitle(_("Edycja opony"))
        else:
            self.setWindowTitle(_("Dodaj nową oponę"))
        
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)
        
        # Inicjalizacja interfejsu
        self.init_ui()
        
        # Wczytanie danych opony do edycji
        if tire_id:
            self.load_tire_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        main_layout = QVBoxLayout(self)
        
        # Zakładki formularza
        self.tabs = QTabWidget()
        
        # Zakładka danych podstawowych
        basic_tab = QFrame()
        basic_layout = QFormLayout(basic_tab)
        basic_layout.setSpacing(10)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pola formularza dla danych podstawowych
        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText(_("np. Continental, Michelin, Goodyear..."))
        basic_layout.addRow(_("Producent:"), self.manufacturer_input)
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(_("np. CrossContact, Pilot Sport, EfficientGrip..."))
        basic_layout.addRow(_("Model:"), self.model_input)
        
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText(_("np. 205/55R16, 225/45R17..."))
        basic_layout.addRow(_("Rozmiar:"), self.size_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([_("Letnie"), _("Zimowe"), _("Całoroczne")])
        basic_layout.addRow(_("Typ:"), self.type_combo)
        
        self.condition_combo = QComboBox()
        self.condition_combo.addItems([_("Nowa"), _("Używana")])
        
        # Ustawienie domyślnej wartości stanu
        if self.default_condition == "Używana":
            self.condition_combo.setCurrentText(_("Używana"))
        else:
            self.condition_combo.setCurrentText(_("Nowa"))
            
        # Połączenie zmiany stanu z funkcją aktualizacji UI
        self.condition_combo.currentTextChanged.connect(self.update_fields_visibility)
        basic_layout.addRow(_("Stan:"), self.condition_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            _("Dostępna"), _("Rezerwacja"), _("Zamówiona"), _("Sprzedana"), _("Wycofana")
        ])
        basic_layout.addRow(_("Status:"), self.status_combo)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(0)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)  # Domyślnie 1 sztuka
        basic_layout.addRow(_("Ilość:"), self.quantity_spin)
        
        self.dot_input = QLineEdit()
        self.dot_input.setPlaceholderText(_("np. 2023, 2023/42, 4221..."))
        basic_layout.addRow(_("DOT:"), self.dot_input)
        
        self.bieznik_spin = QDoubleSpinBox()
        self.bieznik_spin.setMinimum(0)
        self.bieznik_spin.setMaximum(20)
        self.bieznik_spin.setSingleStep(0.5)
        self.bieznik_spin.setSuffix(" mm")
        basic_layout.addRow(_("Bieżnik:"), self.bieznik_spin)
        
        # Pola cenowe
        price_box = QFrame()
        price_layout = QHBoxLayout(price_box)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(10)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMinimum(0)
        self.price_spin.setMaximum(9999.99)
        self.price_spin.setSuffix(" zł")
        self.price_spin.setDecimals(2)
        
        self.purchase_price_spin = QDoubleSpinBox()
        self.purchase_price_spin.setMinimum(0)
        self.purchase_price_spin.setMaximum(9999.99)
        self.purchase_price_spin.setSuffix(" zł")
        self.purchase_price_spin.setDecimals(2)
        
        price_layout.addWidget(QLabel(_("Cena sprzedaży:")))
        price_layout.addWidget(self.price_spin)
        price_layout.addWidget(QLabel(_("Cena zakupu:")))
        price_layout.addWidget(self.purchase_price_spin)
        
        basic_layout.addRow("", price_box)
        
        # Uwagi
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(_("Opcjonalne uwagi dotyczące opony..."))
        self.notes_edit.setMaximumHeight(80)
        basic_layout.addRow(_("Uwagi:"), self.notes_edit)
        
        # Zakładka danych dodatkowych
        advanced_tab = QFrame()
        advanced_layout = QFormLayout(advanced_tab)
        advanced_layout.setSpacing(10)
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        
        self.receive_date_edit = QDateEdit()
        self.receive_date_edit.setCalendarPopup(True)
        self.receive_date_edit.setDate(QDate.currentDate())
        advanced_layout.addRow(_("Data przyjęcia:"), self.receive_date_edit)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText(_("np. Regał A3, Półka B2..."))
        advanced_layout.addRow(_("Lokalizacja:"), self.location_input)
        
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText(_("np. Nazwa hurtowni, dostawcy..."))
        advanced_layout.addRow(_("Dostawca:"), self.supplier_input)
        
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText(_("np. FV/2023/12345"))
        advanced_layout.addRow(_("Nr faktury:"), self.invoice_input)
        
        self.ean_input = QLineEdit()
        self.ean_input.setPlaceholderText(_("np. 12345678901234"))
        advanced_layout.addRow(_("Kod EAN:"), self.ean_input)
        
        # Możliwość dodania zdjęcia opony
        image_frame = QFrame()
        image_layout = QHBoxLayout(image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_path = ""
        self.image_label = QLabel(_("Brak zdjęcia"))
        self.image_label.setMinimumSize(80, 80)
        self.image_label.setMaximumSize(100, 100)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        image_layout.addWidget(self.image_label)
        
        image_buttons_layout = QVBoxLayout()
        
        self.add_image_btn = QPushButton(_("Dodaj zdjęcie"))
        self.add_image_btn.clicked.connect(self.add_image)
        image_buttons_layout.addWidget(self.add_image_btn)
        
        self.remove_image_btn = QPushButton(_("Usuń zdjęcie"))
        self.remove_image_btn.clicked.connect(self.remove_image)
        self.remove_image_btn.setEnabled(False)
        image_buttons_layout.addWidget(self.remove_image_btn)
        
        image_buttons_layout.addStretch()
        
        image_layout.addLayout(image_buttons_layout)
        image_layout.addStretch()
        
        advanced_layout.addRow(_("Zdjęcie:"), image_frame)
        
        # Dodanie zakładek do widgetu
        self.tabs.addTab(basic_tab, _("Dane podstawowe"))
        self.tabs.addTab(advanced_tab, _("Dodatkowe informacje"))
        
        main_layout.addWidget(self.tabs)
        
        # Przyciski dialogu
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Dodanie czystej przestrzeni przed przyciskami
        main_layout.addSpacing(10)
        
        main_layout.addWidget(button_box)
        
        # Inicjalne ustawienie widoczności pól
        self.update_fields_visibility()
    
    def update_fields_visibility(self):
        """Aktualizuje widoczność pól w zależności od stanu opony."""
        is_used = self.condition_combo.currentText() == _("Używana")
        
        # Pole bieżnika jest widoczne tylko dla używanych opon
        self.bieznik_spin.setEnabled(is_used)
        self.bieznik_spin.setVisible(is_used)
        
    def load_tire_data(self):
        """Wczytuje dane opony do edycji."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane opony o podanym ID
            query = """
                SELECT * FROM inventory WHERE id = ?
            """
            
            cursor.execute(query, (self.tire_id,))
            tire = cursor.fetchone()
            
            if not tire:
                raise Exception(f"Nie znaleziono opony o ID {self.tire_id}")
            
            self.tire_data = tire
            
            # Rozdziel brand_model na manufacturer i model
            brand_model = tire["brand_model"] or ""
            parts = brand_model.split(' ', 1)
            manufacturer = parts[0] if parts else ""
            model = parts[1] if len(parts) > 1 else ""
            
            # Wypełnij formularz danymi
            self.manufacturer_input.setText(manufacturer)
            self.model_input.setText(model)
            self.size_input.setText(tire["size"] or "")
            
            # Ustaw typ z listy wyboru (używamy season_type zamiast type)
            type_index = self.type_combo.findText(tire["season_type"] or _("Letnie"))
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            
            # Ustaw stan z listy wyboru
            condition_index = self.condition_combo.findText(tire["condition"] or _("Nowa"))
            if condition_index >= 0:
                self.condition_combo.setCurrentIndex(condition_index)
            
            # Ustaw status z listy wyboru
            status_index = self.status_combo.findText(tire["status"] or _("Dostępna"))
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
            
            # Ustaw wartości liczbowe
            self.quantity_spin.setValue(tire["quantity"] or 0)
            self.price_spin.setValue(tire["price"] or 0.0)
            
            # Parsuj informacje z pola notes
            notes = tire["notes"] or ""
            
            # Próba wyłuskania dodatkowych informacji z pola notes
            if "Bieżnik:" in notes:
                try:
                    bieznik_text = notes.split("Bieżnik:")[1].split("mm")[0].strip()
                    self.bieznik_spin.setValue(float(bieznik_text))
                except:
                    pass
                    
            if "Cena zakupu:" in notes:
                try:
                    price_text = notes.split("Cena zakupu:")[1].split("zł")[0].strip()
                    self.purchase_price_spin.setValue(float(price_text))
                except:
                    pass
            
            # Pozostałe dane
            self.dot_input.setText(tire["dot"] or "")
            self.notes_edit.setText(notes.split("\n\n")[0] if "\n\n" in notes else notes)
            
            # Pozostałe informacje
            # Te dane już nie są przechowywane oddzielnie, więc zostawiamy puste lub domyślne wartości
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych opony: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania danych opony: {e}",
                NotificationTypes.ERROR
            )

    def save_tire(self):
        """Zapisuje dane opony."""
        try:
            # Walidacja pól
            if not self.validate_form():
                return
            
            # Przygotowanie danych używając nazw kolumn z istniejącej bazy danych
            manufacturer = self.manufacturer_input.text().strip()
            model = self.model_input.text().strip()
            
            # Połącz producenta i model w jedno pole brand_model
            brand_model = f"{manufacturer} {model}".strip()
            
            tire_data = {
                "brand_model": brand_model,  # Używamy brand_model zamiast manufacturer i model
                "size": self.size_input.text().strip(),
                "season_type": self.type_combo.currentText(),  # Używamy season_type zamiast type
                "condition": self.condition_combo.currentText(),
                "quantity": self.quantity_spin.value(),
                "price": self.price_spin.value(),
                "dot": self.dot_input.text().strip(),
                "status": self.status_combo.currentText(),
                "notes": self.notes_edit.toPlainText().strip(),
            }
            
            # Dodatkowe dane, które można umieścić w polu notes
            additional_info = [
                f"Bieżnik: {self.bieznik_spin.value()} mm" if self.condition_combo.currentText() == _("Używana") else "",
                f"Lokalizacja: {self.location_input.text().strip()}",
                f"Data przyjęcia: {self.receive_date_edit.date().toString('yyyy-MM-dd')}",
                f"Dostawca: {self.supplier_input.text().strip()}",
                f"Faktura: {self.invoice_input.text().strip()}",
                f"Cena zakupu: {self.purchase_price_spin.value()} zł",
                f"EAN: {self.ean_input.text().strip()}"
            ]
            
            # Dodaj dodatkowe informacje do pola notes
            additional_notes = "\n".join([info for info in additional_info if info])
            if additional_notes:
                if tire_data["notes"]:
                    tire_data["notes"] += "\n\n" + additional_notes
                else:
                    tire_data["notes"] = additional_notes
            
            cursor = self.conn.cursor()
            
            # Rozpocznij transakcję
            self.conn.execute("BEGIN")
            
            try:
                if self.tire_id:
                    # Aktualizacja istniejącej opony
                    query_parts = []
                    params = []
                    
                    for key, value in tire_data.items():
                        query_parts.append(f"{key} = ?")
                        params.append(value)
                    
                    # Dodaj ID opony do parametrów
                    params.append(self.tire_id)
                    
                    query = f"UPDATE inventory SET {', '.join(query_parts)} WHERE id = ?"
                    cursor.execute(query, params)
                    
                else:
                    # Dodanie nowej opony
                    fields = ", ".join(tire_data.keys())
                    placeholders = ", ".join(["?" for _ in tire_data.keys()])
                    
                    query = f"INSERT INTO inventory ({fields}) VALUES ({placeholders})"
                    cursor.execute(query, list(tire_data.values()))
                    
                    self.tire_id = cursor.lastrowid
                
                # Zatwierdź zmiany
                self.conn.commit()
                
                # Zamknij dialog
                super().accept()
                
            except Exception as e:
                # W przypadku błędu, cofnij transakcję
                self.conn.rollback()
                raise e
                
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania danych opony: {e}")
            QMessageBox.warning(self, _("Błąd"), f"{_('Wystąpił błąd podczas zapisywania danych opony')}: {e}")

    def validate_form(self):
        """
        Waliduje pola formularza.
        
        Returns:
            bool: True jeśli wszystkie pola są poprawne, False w przeciwnym razie
        """
        # Walidacja producenta
        if not self.manufacturer_input.text().strip():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Pole 'Producent' jest wymagane."))
            self.tabs.setCurrentIndex(0)  # Przełącz na zakładkę podstawowych informacji
            self.manufacturer_input.setFocus()
            return False
        
        # Walidacja modelu
        if not self.model_input.text().strip():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Pole 'Model' jest wymagane."))
            self.tabs.setCurrentIndex(0)
            self.model_input.setFocus()
            return False
        
        # Walidacja rozmiaru
        if not self.size_input.text().strip():
            QMessageBox.warning(self, _("Błąd walidacji"), _("Pole 'Rozmiar' jest wymagane."))
            self.tabs.setCurrentIndex(0)
            self.size_input.setFocus()
            return False
        
        # Walidacja głębokości bieżnika dla używanych opon
        if self.condition_combo.currentText() == _("Używana") and self.bieznik_spin.value() == 0:
            reply = QMessageBox.question(
                self,
                _("Potwierdź bieżnik"),
                _("Głębokość bieżnika jest ustawiona na 0 mm. Czy na pewno jest to poprawna wartość?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.tabs.setCurrentIndex(0)
                self.bieznik_spin.setFocus()
                return False
        
        return True

    def get_tire_id(self):
        """
        Zwraca ID zapisanej opony.
        
        Returns:
            int: ID opony
        """
        return self.tire_id


    # Poprawka dla metody add_image
    def add_image(self):
        """Dodaje zdjęcie opony."""
        try:
            # Wybór pliku zdjęcia
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                _("Wybierz zdjęcie opony"), 
                "",
                "Image Files (*.png *.jpg *.jpeg)"
            )
            
            if not file_path:
                return
                    
            # Ustaw wybrane zdjęcie
            self.image_path = file_path
            self.set_image(file_path)
            self.remove_image_btn.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Błąd podczas dodawania zdjęcia: {e}")
            # Poprawka: Używamy zwykłego tekstu bez próby tłumaczenia w bloku wyjątku
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania zdjęcia: {e}",
                NotificationTypes.ERROR
            )
        
    # Poprawka dla metody remove_image
    def remove_image(self):
        """Usuwa zdjęcie opony."""
        try:
            self.image_path = ""
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText(_("Brak zdjęcia"))
            self.remove_image_btn.setEnabled(False)
            
        except Exception as e:
            logger.error(f"Błąd podczas usuwania zdjęcia: {e}")
            # Poprawka: Używamy zwykłego tekstu bez próby tłumaczenia w bloku wyjątku
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas usuwania zdjęcia: {e}",
                NotificationTypes.ERROR
            )
    
    def set_image(self, file_path):
        """Ustawia zdjęcie opony z podanej ścieżki."""
        try:
            if not file_path or not os.path.exists(file_path):
                return
                
            # Wczytaj zdjęcie i przeskaluj do rozmiaru etykiety
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
                self.image_label.setText("")
            
        except Exception as e:
            logger.error(f"Błąd podczas ustawiania zdjęcia: {e}")
    
    def accept(self):
        """Obsługuje zatwierdzenie dialogu i zapis danych."""
        self.save_tire()  # Prosta delegacja do metody save_tire
                
