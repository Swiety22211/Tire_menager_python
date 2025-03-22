#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł dialogu dodawania/edycji zamówienia w aplikacji Menadżer Serwisu Opon.
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, QPushButton, 
    QHeaderView, QDateEdit, QMessageBox, QCompleter
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from PySide6.QtCore import Qt, QDate

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

class OrderDialog(QDialog):
    """Dialog dodawania i edycji zamówień"""
    
    def __init__(self, db_connection, order_id=None, parent=None):
        """
        Inicjalizacja dialogu zamówień.
        
        Args:
            db_connection: Połączenie z bazą danych
            order_id (int, optional): ID zamówienia do edycji
            parent (QWidget, optional): Widget rodzica
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.order_id = order_id
        
        # Ustawienia okna
        self.setWindowTitle("Nowe zamówienie" if not order_id else "Edycja zamówienia")
        self.setMinimumSize(800, 600)
        
        # Główny układ
        main_layout = QVBoxLayout(self)
        
        # Górny panel informacji
        top_layout = QHBoxLayout()
        
        # Klient
        client_layout = QVBoxLayout()
        client_label = QLabel("Klient:")
        self.client_combo = QComboBox()
        self.load_clients()
        
        # Autouzupełnianie klientów
        self.client_combo.setEditable(True)
        self.client_combo.setInsertPolicy(QComboBox.NoInsert)
        
        client_layout.addWidget(client_label)
        client_layout.addWidget(self.client_combo)
        
        # Data zamówienia
        date_layout = QVBoxLayout()
        date_label = QLabel("Data zamówienia:")
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        
        # Status zamówienia
        status_layout = QVBoxLayout()
        status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Nowe", "W realizacji", "Zakończone", "Anulowane"
        ])
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        
        top_layout.addLayout(client_layout, 3)
        top_layout.addLayout(date_layout, 1)
        top_layout.addLayout(status_layout, 1)
        
        main_layout.addLayout(top_layout)
        
        # Separator
        separator = QLabel()
        separator.setStyleSheet("border: 1px solid #e0e0e0;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Sekcja pozycji zamówienia
        items_label = QLabel("Pozycje zamówienia:")
        main_layout.addWidget(items_label)
        
        # Tabela pozycji
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Nazwa", "Typ", "Ilość", "Cena", "Suma"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Dodaj domyślny wiersz
        self.add_item_row()
        
        # Przycisk dodania pozycji
        add_item_btn = QPushButton("+ Dodaj pozycję")
        add_item_btn.clicked.connect(self.add_item_row)
        
        main_layout.addWidget(self.items_table)
        main_layout.addWidget(add_item_btn)
        
        # Podsumowanie
        summary_layout = QHBoxLayout()
        
        # Notatki
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Notatki:")
        self.notes_input = QLineEdit()
        
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_input)
        
        # Kwota całkowita
        total_layout = QVBoxLayout()
        total_label = QLabel("Kwota całkowita:")
        self.total_amount_label = QLabel("0.00 zł")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount_label)
        
        summary_layout.addLayout(notes_layout, 3)
        summary_layout.addLayout(total_layout, 1)
        
        main_layout.addLayout(summary_layout)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        
        save_btn = QPushButton("Zapisz")
        save_btn.clicked.connect(self.save_order)
        
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        
        action_layout.addStretch(1)
        action_layout.addWidget(save_btn)
        action_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(action_layout)
        
        # Podłączenie sygnałów
        self.items_table.cellChanged.connect(self.update_total_amount)
        
        # Załaduj dane zamówienia, jeśli edytujemy istniejące
        if order_id:
            self.load_order_data()
    
    def load_clients(self):
        """Ładuje listę klientów do ComboBox."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name FROM clients ORDER BY name")
            clients = cursor.fetchall()
            
            # Model dla autouzupełniania
            model = QStandardItemModel()
            
            for client in clients:
                # Dodaj do ComboBox
                self.client_combo.addItem(client['name'], client['id'])
                
                # Dodaj do modelu autouzupełniania
                item = QStandardItem(client['name'])
                model.appendRow(item)
            
            # Ustaw model autouzupełniania
            completer = QCompleter(model)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.client_combo.setCompleter(completer)
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania klientów: {e}",
                NotificationTypes.ERROR
            )
    
    def add_item_row(self, name="", item_type="", quantity=1, price=0.0):
        """Dodaje nowy wiersz do tabeli pozycji zamówienia."""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Nazwa - combo z dostępnymi produktami
        name_combo = QComboBox()
        name_combo.setEditable(True)
        name_combo.addItem(name)
        self.load_product_items(name_combo)
        
        # Typ - combo z typami produktów
        type_combo = QComboBox()
        type_combo.addItems(["Opona", "Część", "Usługa"])
        type_combo.setCurrentText(item_type or "Usługa")
        
        # Ilość
        quantity_input = QLineEdit(str(quantity))
        quantity_input.setValidator(QIntValidator(1, 1000))
        
        # Cena
        price_input = QLineEdit(f"{price:.2f}")
        
        # Suma (tylko do odczytu)
        total_label = QLabel(f"{quantity * price:.2f}")
        
        # Dodaj widżety do komórek
        self.items_table.setCellWidget(row, 0, name_combo)
        self.items_table.setCellWidget(row, 1, type_combo)
        self.items_table.setCellWidget(row, 2, quantity_input)
        self.items_table.setCellWidget(row, 3, price_input)
        self.items_table.setItem(row, 4, QTableWidgetItem(total_label.text()))
        
        # Podłącz sygnały do aktualizacji
        name_combo.currentTextChanged.connect(self.update_total_amount)
        type_combo.currentTextChanged.connect(self.update_total_amount)
        quantity_input.textChanged.connect(self.update_total_amount)
        price_input.textChanged.connect(self.update_total_amount)
    
    def load_product_items(self, combo):
        """Ładuje listę produktów do ComboBox."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz opony z inwentarza
            cursor.execute("SELECT brand_model, size FROM inventory")
            for row in cursor.fetchall():
                combo.addItem(f"{row['brand_model']} {row['size']}")
            
            # Pobierz części
            cursor.execute("SELECT name FROM parts")
            for row in cursor.fetchall():
                combo.addItem(row['name'])
            
            # Domyślne usługi
            default_services = [
                "Wymiana opon", 
                "Wyważenie kół", 
                "Naprawa opony", 
                "Przegląd sezonowy",
                "Wymiana zaworków"
            ]
            combo.addItems(default_services)
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania produktów: {e}",
                NotificationTypes.ERROR
            )
    
    def update_total_amount(self, *args):
        """Aktualizuje kwotę całkowitą zamówienia."""
        total = 0.0
        
        for row in range(self.items_table.rowCount()):
            try:
                # Pobierz wartości z komórek
                name_combo = self.items_table.cellWidget(row, 0)
                quantity_input = self.items_table.cellWidget(row, 2)
                price_input = self.items_table.cellWidget(row, 3)
                
                # Konwersja wartości
                name = name_combo.currentText()
                quantity = int(quantity_input.text() or 0)
                price = float(price_input.text().replace(',', '.') or 0)
                
                # Oblicz sumę dla pozycji
                item_total = quantity * price
                
                # Ustaw sumę w tabeli
                self.items_table.setItem(row, 4, QTableWidgetItem(f"{item_total:.2f}"))
                
                # Dodaj do całkowitej kwoty
                total += item_total
            except Exception:
                # Ignoruj błędy konwersji
                pass
        
        # Zaktualizuj etykietę kwoty całkowitej
        self.total_amount_label.setText(f"{total:.2f} zł")
    
    def load_order_data(self):
        """Ładuje dane zamówienia do edycji."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz główne dane zamówienia
            cursor.execute("""
                SELECT client_id, order_date, status, total_amount, notes 
                FROM orders 
                WHERE id = ?
            """, (self.order_id,))
            order = cursor.fetchone()
            
            if not order:
                raise ValueError("Nie znaleziono zamówienia")
            
            # Ustaw dane zamówienia
            self.client_combo.setCurrentIndex(
                self.client_combo.findData(order['client_id'])
            )
            
            # Konwersja daty
            order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
            self.date_input.setDate(QDate(order_date.year, order_date.month, order_date.day))
            
            self.status_combo.setCurrentText(order['status'])
            self.notes_input.setText(order['notes'] or "")
            
            # Pobierz pozycje zamówienia
            cursor.execute("""
                SELECT item_type, name, quantity, price 
                FROM order_items 
                WHERE order_id = ?
            """, (self.order_id,))
            items = cursor.fetchall()
            
            # Usuń domyślny wiersz
            self.items_table.setRowCount(0)
            
            # Dodaj pozycje zamówienia
            for item in items:
                self.add_item_row(
                    name=item['name'], 
                    item_type=item['item_type'], 
                    quantity=item['quantity'], 
                    price=item['price']
                )
            
            # Aktualizuj kwotę całkowitą
            self.update_total_amount()
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def save_order(self):
        """Zapisuje zamówienie w bazie danych."""
        try:
            # Walidacja danych
            client_id = self.client_combo.currentData()
            if not client_id:
                raise ValueError("Nie wybrano klienta")
            
            # Przygotuj dane zamówienia
            order_date = self.date_input.date().toString("yyyy-MM-dd")
            status = self.status_combo.currentText()
            total_amount = float(self.total_amount_label.text().replace(" zł", ""))
            notes = self.notes_input.text()
            
            cursor = self.conn.cursor()
            
            if self.order_id:
                # Aktualizacja istniejącego zamówienia
                cursor.execute("""
                    UPDATE orders 
                    SET client_id = ?, order_date = ?, status = ?, 
                        total_amount = ?, notes = ?
                    WHERE id = ?
                """, (client_id, order_date, status, total_amount, notes, self.order_id))
                
                # Usuń istniejące pozycje
                cursor.execute("DELETE FROM order_items WHERE order_id = ?", (self.order_id,))
            else:
                # Nowe zamówienie
                cursor.execute("""
                    INSERT INTO orders 
                    (client_id, order_date, status, total_amount, notes) 
                    VALUES (?, ?, ?, ?, ?)
                """, (client_id, order_date, status, total_amount, notes))
                
                self.order_id = cursor.lastrowid
            
            # Dodaj pozycje zamówienia
            for row in range(self.items_table.rowCount()):
                name_combo = self.items_table.cellWidget(row, 0)
                type_combo = self.items_table.cellWidget(row, 1)
                quantity_input = self.items_table.cellWidget(row, 2)
                price_input = self.items_table.cellWidget(row, 3)
                
                name = name_combo.currentText()
                item_type = type_combo.currentText()
                quantity = int(quantity_input.text() or 0)
                price = float(price_input.text().replace(',', '.') or 0)
                
                # Pomiń puste wiersze
                if not name or quantity == 0:
                    continue
                
                # Znajdź ID produktu (opcjonalne)
                item_id = self.find_item_id(name, item_type)
                
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, item_type, item_id, name, quantity, price) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.order_id, item_type, item_id, name, quantity, price))
            
            # Zatwierdź zmiany
            self.conn.commit()
            
            # Powiadomienie o sukcesie
            NotificationManager.get_instance().show_notification(
                "Zamówienie zostało zapisane",
                NotificationTypes.SUCCESS
            )
            
            # Zamknij dialog
            self.accept()
        
        except Exception as e:
            # Wycofaj zmiany
            self.conn.rollback()
            
            # Powiadomienie o błędzie
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zapisywania zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def find_item_id(self, name, item_type):
        """Próbuje znaleźć ID produktu na podstawie nazwy i typu."""
        try:
            cursor = self.conn.cursor()
            
            if item_type == "Opona":
                cursor.execute(
                    "SELECT id FROM inventory WHERE brand_model || ' ' || size = ?", 
                    (name,)
                )
            elif item_type == "Część":
                cursor.execute("SELECT id FROM parts WHERE name = ?", (name,))
            else:
                # Dla usług zwróć None
                return None
            
            result = cursor.fetchone()
            return result['id'] if result else None
        
        except Exception:
            return None