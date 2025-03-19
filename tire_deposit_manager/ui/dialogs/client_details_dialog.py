#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog wyświetlający szczegóły klienta.
"""

import os
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QFrame, QSpacerItem, QSizePolicy, QFormLayout, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class ClientDetailsDialog(QDialog):
    """
    Dialog wyświetlający szczegóły klienta.
    Umożliwia przeglądanie informacji, historii wizyt, depozytów itp.
    """
    
    def __init__(self, db_connection, client_id, parent=None):
        """
        Inicjalizacja dialogu szczegółów klienta.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            client_id (int): ID klienta
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.client_id = client_id
        
        self.setWindowTitle("Szczegóły klienta")
        self.resize(800, 600)
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Ładowanie danych klienta
        self.load_client_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        
        # Ikona klienta
        icon_label = QLabel()
        icon_pixmap = QPixmap(os.path.join(ICONS_DIR, "client.png"))
        icon_label.setPixmap(icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        # Tytuł klienta
        self.title_label = QLabel("Szczegóły klienta")
        self.title_label.setObjectName("headerLabel")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        # Kod kreskowy klienta
        self.barcode_label = QLabel()
        self.barcode_label.setObjectName("barcodeLabel")
        header_layout.addWidget(self.barcode_label)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Główna sekcja z danymi
        content_layout = QVBoxLayout()
        
        # Ramka z danymi podstawowymi
        basic_info_frame = QFrame()
        basic_info_layout = QHBoxLayout(basic_info_frame)
        
        # Dane kontaktowe
        contact_layout = QFormLayout()
        
        self.name_label = QLabel()
        contact_layout.addRow("Nazwa:", self.name_label)
        
        self.phone_label = QLabel()
        contact_layout.addRow("Telefon:", self.phone_label)
        
        self.email_label = QLabel()
        contact_layout.addRow("E-mail:", self.email_label)
        
        basic_info_layout.addLayout(contact_layout)
        
        # Informacje dodatkowe
        additional_layout = QFormLayout()
        
        self.discount_label = QLabel()
        additional_layout.addRow("Rabat:", self.discount_label)
        
        self.additional_info_label = QLabel()
        self.additional_info_label.setWordWrap(True)
        additional_layout.addRow("Uwagi:", self.additional_info_label)
        
        basic_info_layout.addLayout(additional_layout)
        
        content_layout.addWidget(basic_info_frame)
        
        # Zakładki z historią
        tabs = QTabWidget()
        
        # Zakładka wizyt
        appointments_tab = QWidget()
        appointments_layout = QVBoxLayout(appointments_tab)
        
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(5)
        self.appointments_table.setHorizontalHeaderLabels([
            "Data", "Godzina", "Usługa", "Status", "Uwagi"
        ])
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        appointments_layout.addWidget(self.appointments_table)
        tabs.addTab(appointments_tab, "Wizyty")
        
        # Zakładka depozytów
        deposits_tab = QWidget()
        deposits_layout = QVBoxLayout(deposits_tab)
        
        self.deposits_table = QTableWidget()
        self.deposits_table.setColumnCount(6)
        self.deposits_table.setHorizontalHeaderLabels([
            "Data złożenia", "Opony", "Rozmiar", "Status", "Sezon", "Lokalizacja"
        ])
        self.deposits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        deposits_layout.addWidget(self.deposits_table)
        tabs.addTab(deposits_tab, "Depozyty")
        
        # Zakładka zamówień
        orders_tab = QWidget()
        orders_layout = QVBoxLayout(orders_tab)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels([
            "Data", "Wartość", "Status", "Szczegóły"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        orders_layout.addWidget(self.orders_table)
        tabs.addTab(orders_tab, "Zamówienia")
        
        content_layout.addWidget(tabs)
        
        main_layout.addLayout(content_layout)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edytuj")
        edit_button.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
        edit_button.clicked.connect(self.edit_client)
        action_layout.addWidget(edit_button)
        
        # Elastyczna przestrzeń
        action_layout.addStretch(1)
        
        # Przycisk zamknięcia
        close_button = QPushButton("Zamknij")
        close_button.setIcon(QIcon(os.path.join(ICONS_DIR, "close.png")))
        close_button.clicked.connect(self.accept)
        action_layout.addWidget(close_button)
        
        main_layout.addLayout(action_layout)
    
    def load_client_data(self):
        """Ładuje dane klienta z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Dane podstawowe klienta
            cursor.execute("""
                SELECT 
                    name, phone_number, email, 
                    additional_info, discount, barcode
                FROM clients 
                WHERE id = ?
            """, (self.client_id,))
            
            client_data = cursor.fetchone()
            
            if not client_data:
                logger.error(f"Nie znaleziono klienta o ID: {self.client_id}")
                QMessageBox.critical(self, "Błąd", f"Nie znaleziono klienta o ID: {self.client_id}")
                self.reject()
                return
            
            # Rozpakowanie danych
            name, phone, email, additional_info, discount, barcode = client_data
            
            # Aktualizacja interfejsu
            self.title_label.setText(f"Klient: {name}")
            self.name_label.setText(name or "-")
            self.phone_label.setText(phone or "-")
            self.email_label.setText(email or "-")
            self.discount_label.setText(f"{discount}%" if discount else "-")
            self.additional_info_label.setText(additional_info or "-")
            self.barcode_label.setText(f"Kod: {barcode}" if barcode else "-")
            
            # Ładowanie historii wizyt
            self.load_appointments()
            
            # Ładowanie historii depozytów
            self.load_deposits()
            
            # Ładowanie historii zamówień
            self.load_orders()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych klienta: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych klienta:\n{str(e)}")
    
    def load_appointments(self):
        """Ładuje historię wizyt klienta."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    appointment_date, appointment_time, 
                    service_type, status, notes
                FROM appointments
                WHERE client_id = ?
                ORDER BY appointment_date DESC
            """, (self.client_id,))
            
            appointments = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.appointments_table.setRowCount(0)
            
            # Wypełnienie tabeli
            for row, (date, time, service, status, notes) in enumerate(appointments):
                self.appointments_table.insertRow(row)
                
                # Formatowanie daty
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except (ValueError, TypeError):
                    formatted_date = date
                
                # Dodaj dane do tabeli
                data_items = [
                    formatted_date, 
                    time or "-", 
                    service or "-", 
                    status or "-", 
                    notes or "-"
                ]
                
                for col, value in enumerate(data_items):
                    item = QTableWidgetItem(str(value))
                    
                    # Kolorowanie statusu
                    if col == 3:  # Kolumna statusu
                        if value == "Zakończona":
                            item.setBackground(QColor("#2ecc71"))  # Zielony
                        elif value == "W trakcie":
                            item.setBackground(QColor("#f39c12"))  # Pomarańczowy
                        elif value == "Anulowana":
                            item.setBackground(QColor("#e74c3c"))  # Czerwony
                    
                    self.appointments_table.setItem(row, col, item)
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania wizyt klienta: {e}")
    
    def load_deposits(self):
        """Ładuje historię depozytów klienta."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    deposit_date, tire_brand, tire_size, 
                    status, season, location
                FROM deposits
                WHERE client_id = ?
                ORDER BY deposit_date DESC
            """, (self.client_id,))
            
            deposits = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.deposits_table.setRowCount(0)
            
            # Wypełnienie tabeli
            for row, (date, brand, size, status, season, location) in enumerate(deposits):
                self.deposits_table.insertRow(row)
                
                # Formatowanie daty
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except (ValueError, TypeError):
                    formatted_date = date
                
                # Dodaj dane do tabeli
                data_items = [
                    formatted_date, 
                    brand or "-", 
                    size or "-", 
                    status or "-", 
                    season or "-", 
                    location or "-"
                ]
                
                for col, value in enumerate(data_items):
                    item = QTableWidgetItem(str(value))
                    
                    # Kolorowanie statusu
                    if col == 3:  # Kolumna statusu
                        if value == "Aktywny":
                            item.setBackground(QColor("#2ecc71"))  # Zielony
                        elif value == "Zakończony":
                            item.setBackground(QColor("#3498db"))  # Niebieski
                        elif value == "Przeterminowany":
                            item.setBackground(QColor("#e74c3c"))  # Czerwony
                    
                    self.deposits_table.setItem(row, col, item)
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania depozytów klienta: {e}")
    
    def load_orders(self):
            """Ładuje historię zamówień klienta."""
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT 
                        order_date, total_amount, 
                        status, notes
                    FROM orders
                    WHERE client_id = ?
                    ORDER BY order_date DESC
                """, (self.client_id,))
                
                orders = cursor.fetchall()
                
                # Czyszczenie tabeli
                self.orders_table.setRowCount(0)
                
                # Wypełnienie tabeli
                for row, (date, total, status, notes) in enumerate(orders):
                    self.orders_table.insertRow(row)
                    
                    # Formatowanie daty
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%d.%m.%Y")
                    except (ValueError, TypeError):
                        formatted_date = date
                    
                    # Formatowanie kwoty
                    formatted_total = f"{float(total):.2f} PLN" if total is not None else "-"
                    
                    # Dodaj dane do tabeli
                    data_items = [
                        formatted_date, 
                        formatted_total, 
                        status or "-", 
                        notes or "-"
                    ]
                    
                    for col, value in enumerate(data_items):
                        item = QTableWidgetItem(str(value))
                        
                        # Kolorowanie statusu
                        if col == 2:  # Kolumna statusu
                            if value == "Zrealizowane":
                                item.setBackground(QColor("#2ecc71"))  # Zielony
                            elif value == "W trakcie":
                                item.setBackground(QColor("#f39c12"))  # Pomarańczowy
                            elif value == "Anulowane":
                                item.setBackground(QColor("#e74c3c"))  # Czerwony
                        
                        self.orders_table.setItem(row, col, item)
                
            except Exception as e:
                logger.error(f"Błąd podczas ładowania zamówień klienta: {e}")
        
    def edit_client(self):
        """Otwiera okno edycji klienta."""
        from ui.dialogs.client_dialog import ClientDialog
        dialog = ClientDialog(self.conn, client_id=self.client_id, parent=self)
        if dialog.exec() == dialog.Accepted:
            # Odśwież dane klienta
            self.load_client_data()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Zaktualizowano dane klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS
            )