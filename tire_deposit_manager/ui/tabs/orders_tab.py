#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zakładki zamówień w aplikacji Menadżer Serwisu Opon.
Obsługuje wyświetlanie, filtrowanie i zarządzanie zamówieniami.
"""

import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QAbstractItemView, QDialog, QFileDialog
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QDate

from ui.dialogs.order_dialog import OrderDialog
from utils.exporter import export_data_to_excel, export_data_to_pdf
from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes

class OrdersTab(QWidget):
    """Zakładka zamówień w aplikacji Menadżer Serwisu Opon"""
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki zamówień.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.init_ui()
        self.load_orders()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki zamówień."""
        layout = QVBoxLayout(self)
        
        # Górny panel filtrów
        filter_layout = QHBoxLayout()
        
        # Zakres dat
        date_layout = QHBoxLayout()
        
        date_from_label = QLabel("Okres: Od")
        self.date_from_input = QLineEdit()
        self.date_from_input.setPlaceholderText("01-03-2025")
        self.date_from_input.setFixedWidth(100)
        
        date_to_label = QLabel("Do")
        self.date_to_input = QLineEdit()
        self.date_to_input.setPlaceholderText("20-03-2025")
        self.date_to_input.setFixedWidth(100)
        
        date_layout.addWidget(date_from_label)
        date_layout.addWidget(self.date_from_input)
        date_layout.addWidget(date_to_label)
        date_layout.addWidget(self.date_to_input)
        
        # Status zamówień
        status_label = QLabel("Status:")
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Wszystkie", "Nowe", "W realizacji", 
            "Zakończone", "Anulowane"
        ])
        
        # Sortowanie
        sort_label = QLabel("Sortuj wg:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Data (najnowsze)", "Data (najstarsze)", 
            "Kwota (malejąco)", "Kwota (rosnąco)"
        ])
        
        # Wyszukiwarka
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Szukaj zamówienia lub klienta")
        
        # Przyciski akcji
        self.new_order_btn = QPushButton("+ Nowe zamówienie")
        self.new_order_btn.clicked.connect(self.add_order)
        
        self.filter_btn = QPushButton("Filtry")
        
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.clicked.connect(self.load_orders)
        
        # Dodanie elementów do layoutu filtrów
        filter_layout.addLayout(date_layout)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_combo)
        filter_layout.addWidget(sort_label)
        filter_layout.addWidget(self.sort_combo)
        filter_layout.addStretch(1)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.new_order_btn)
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Zakładki statusów zamówień
        self.status_tabs = QHBoxLayout()
        status_tabs_data = [
            ("Wszystkie (23)", "all"),
            ("Nowe (5)", "new"),
            ("W realizacji (8)", "in_progress"),
            ("Zakończone (9)", "completed"),
            ("Anulowane (1)", "cancelled")
        ]
        
        self.status_tab_buttons = {}
        for label, key in status_tabs_data:
            btn = QPushButton(label)
            btn.setProperty("status_type", key)
            btn.clicked.connect(self.filter_by_status)
            self.status_tab_buttons[key] = btn
            self.status_tabs.addWidget(btn)
        
        layout.addLayout(self.status_tabs)
        
        # Tabela zamówień
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels([
            "Nr", "Data", "Klient", "Usługa", "Status", "Kwota", "Akcje"
        ])
        
        # Konfiguracja tabeli
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Dodanie tabeli do layoutu
        layout.addWidget(self.orders_table)
        
        # Dolny panel paginacji
        bottom_layout = QHBoxLayout()
        
        # Informacja o wyniku
        self.result_label = QLabel("Wyświetlanie 5 z 23 zamówień")
        
        # Przyciski paginacji
        self.prev_btn = QPushButton("←")
        self.next_btn = QPushButton("→")
        
        # Przyciski eksportu
        self.export_btn = QPushButton("Eksport")
        self.export_btn.clicked.connect(self.show_export_menu)
        
        self.report_btn = QPushButton("Raport")
        
        bottom_layout.addWidget(self.result_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.prev_btn)
        bottom_layout.addWidget(QLabel("1"))
        bottom_layout.addWidget(self.next_btn)
        bottom_layout.addWidget(self.export_btn)
        bottom_layout.addWidget(self.report_btn)
        
        layout.addLayout(bottom_layout)
    
    def export_to_excel(self):
        """Eksportuje zamówienia do pliku Excel."""
        try:
            # Pobierz ścieżkę pliku do zapisu
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Eksport zamówień do Excel", 
                "", 
                "Pliki Excel (*.xlsx);;Wszystkie pliki (*)"
            )
            
            if not file_path:
                return
            
            # Przygotuj dane do eksportu
            cursor = self.conn.cursor()
            query = """
            SELECT o.id, o.order_date, c.name, 
                   GROUP_CONCAT(oi.name, ', ') as services, 
                   o.status, o.total_amount
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            """
            
            cursor.execute(query)
            orders = cursor.fetchall()
            
            # Przygotuj dane do eksportu
            export_data = []
            headers = ["Nr", "Data", "Klient", "Usługa", "Status", "Kwota"]
            
            for order in orders:
                export_data.append([
                    order['id'],
                    datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    order['name'],
                    order['services'],
                    order['status'],
                    f"{order['total_amount']:.2f} zł"
                ])
            
            # Wywołaj eksport do Excel
            export_data_to_excel(file_path, headers, export_data, "Zamówienia")
            
            NotificationManager.get_instance().show_notification(
                f"Zamówienia wyeksportowane do: {file_path}",
                NotificationTypes.SUCCESS
            )
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do Excel: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_pdf(self):
        """Eksportuje zamówienia do pliku PDF."""
        try:
            # Pobierz ścieżkę pliku do zapisu
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Eksport zamówień do PDF", 
                "", 
                "Pliki PDF (*.pdf);;Wszystkie pliki (*)"
            )
            
            if not file_path:
                return
            
            # Przygotuj dane do eksportu
            cursor = self.conn.cursor()
            query = """
            SELECT o.id, o.order_date, c.name, 
                   GROUP_CONCAT(oi.name, ', ') as services, 
                   o.status, o.total_amount
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            """
            
            cursor.execute(query)
            orders = cursor.fetchall()
            
            # Przygotuj dane do eksportu
            export_data = []
            headers = ["Nr", "Data", "Klient", "Usługa", "Status", "Kwota"]
            
            for order in orders:
                export_data.append([
                    order['id'],
                    datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    order['name'],
                    order['services'],
                    order['status'],
                    f"{order['total_amount']:.2f} zł"
                ])
            
            # Wywołaj eksport do PDF
            export_data_to_pdf(file_path, headers, export_data, "Zamówienia")
            
            NotificationManager.get_instance().show_notification(
                f"Zamówienia wyeksportowane do: {file_path}",
                NotificationTypes.SUCCESS
            )
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do PDF: {e}",
                NotificationTypes.ERROR
            )
    
    def search(self, text):
            """Wyszukuje zamówienia wg podanego tekstu."""
            try:
                cursor = self.conn.cursor()
                
                query = """
                SELECT o.id, o.order_date, c.name, 
                    GROUP_CONCAT(oi.name, ', ') as services, 
                    o.status, o.total_amount
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE 
                    LOWER(c.name) LIKE LOWER(?) OR 
                    LOWER(oi.name) LIKE LOWER(?) OR 
                    o.id LIKE ?
                GROUP BY o.id
                """
                
                search_param = f"%{text}%"
                cursor.execute(query, (search_param, search_param, search_param))
                orders = cursor.fetchall()
                
                # Czyszczenie tabeli
                self.orders_table.setRowCount(0)
                
                # Wypełnianie tabeli
                for row_data in orders:
                    row_position = self.orders_table.rowCount()
                    self.orders_table.insertRow(row_position)
                    
                    # Formatowanie danych
                    order_id = str(row_data['id'])
                    order_date = datetime.strptime(row_data['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    client_name = row_data['name']
                    services = row_data['services']
                    status = row_data['status']
                    total_amount = f"{row_data['total_amount']:.2f} zł"
                    
                    # Dodawanie danych do komórek
                    self.orders_table.setItem(row_position, 0, QTableWidgetItem(order_id))
                    self.orders_table.setItem(row_position, 1, QTableWidgetItem(order_date))
                    self.orders_table.setItem(row_position, 2, QTableWidgetItem(client_name))
                    self.orders_table.setItem(row_position, 3, QTableWidgetItem(services))
                    
                    # Status z kolorami
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(self.get_status_color(status))
                    self.orders_table.setItem(row_position, 4, status_item)
                    
                    self.orders_table.setItem(row_position, 5, QTableWidgetItem(total_amount))
                    
                    # Kolumna akcji (ikony)
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Ikony akcji
                    view_btn = QPushButton()
                    view_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "view.png")))
                    view_btn.clicked.connect(lambda checked, order_id=order_id: self.view_order(order_id))
                    
                    edit_btn = QPushButton()
                    edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
                    edit_btn.clicked.connect(lambda checked, order_id=order_id: self.edit_order(order_id))
                    
                    more_btn = QPushButton()
                    more_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "more.png")))
                    more_btn.clicked.connect(lambda checked, order_id=order_id: self.show_more_actions(order_id))
                    
                    actions_layout.addWidget(view_btn)
                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(more_btn)
                    
                    self.orders_table.setCellWidget(row_position, 6, actions_widget)
                
                # Aktualizacja etykiety wyniku
                self.result_label.setText(f"Wyświetlanie {len(orders)} z {len(orders)} zamówień")
                
            except Exception as e:
                NotificationManager.get_instance().show_notification(
                    f"Błąd podczas wyszukiwania zamówień: {e}",
                    NotificationTypes.ERROR
                )
    
    def load_orders(self):
        """Ładuje zamówienia z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Query do pobrania zamówień z informacjami o kliencie
            query = """
            SELECT o.id, o.order_date, c.name, 
                   GROUP_CONCAT(oi.name, ', ') as services, 
                   o.status, o.total_amount
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            """
            
            cursor.execute(query)
            orders = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.orders_table.setRowCount(0)
            
            # Wypełnianie tabeli
            for row_data in orders:
                row_position = self.orders_table.rowCount()
                self.orders_table.insertRow(row_position)
                
                # Formatowanie danych
                order_id = str(row_data['id'])
                order_date = datetime.strptime(row_data['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                client_name = row_data['name']
                services = row_data['services']
                status = row_data['status']
                total_amount = f"{row_data['total_amount']:.2f} zł"
                
                # Dodawanie danych do komórek
                self.orders_table.setItem(row_position, 0, QTableWidgetItem(order_id))
                self.orders_table.setItem(row_position, 1, QTableWidgetItem(order_date))
                self.orders_table.setItem(row_position, 2, QTableWidgetItem(client_name))
                self.orders_table.setItem(row_position, 3, QTableWidgetItem(services))
                
                # Status z kolorami
                status_item = QTableWidgetItem(status)
                status_item.setForeground(self.get_status_color(status))
                self.orders_table.setItem(row_position, 4, status_item)
                
                self.orders_table.setItem(row_position, 5, QTableWidgetItem(total_amount))
                
                # Kolumna akcji (ikony)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                # Ikony akcji
                view_btn = QPushButton()
                view_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "view.png")))
                view_btn.clicked.connect(lambda checked, order_id=order_id: self.view_order(order_id))
                
                edit_btn = QPushButton()
                edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
                edit_btn.clicked.connect(lambda checked, order_id=order_id: self.edit_order(order_id))
                
                more_btn = QPushButton()
                more_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "more.png")))
                more_btn.clicked.connect(lambda checked, order_id=order_id: self.show_more_actions(order_id))
                
                actions_layout.addWidget(view_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(more_btn)
                
                self.orders_table.setCellWidget(row_position, 6, actions_widget)
            
            # Aktualizacja etykiety wyniku
            self.result_label.setText(f"Wyświetlanie {len(orders)} z {len(orders)} zamówień")
            
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania zamówień: {e}",
                NotificationTypes.ERROR
            )
    
    def get_status_color(self, status):
        """Zwraca kolor tekstu w zależności od statusu."""
        status_colors = {
            "Zakończone": Qt.green,
            "W realizacji": Qt.blue,
            "Oczekujące": Qt.yellow,
            "Anulowane": Qt.red
        }
        return status_colors.get(status, Qt.black)
    
    def add_order(self):
        """Otwiera dialog dodawania nowego zamówienia."""
        dialog = OrderDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_orders()
            NotificationManager.get_instance().show_notification(
                "Dodano nowe zamówienie",
                NotificationTypes.SUCCESS
            )
    
    def view_order(self, order_id):
        """Wyświetla szczegóły zamówienia."""
        # TODO: Implementacja wyświetlania szczegółów zamówienia
        NotificationManager.get_instance().show_notification(
            f"Wyświetlanie zamówienia {order_id}",
            NotificationTypes.INFO
        )
    
    def edit_order(self, order_id):
        """Edytuje wybrane zamówienie."""
        # TODO: Implementacja edycji zamówienia
        NotificationManager.get_instance().show_notification(
            f"Edycja zamówienia {order_id}",
            NotificationTypes.INFO
        )
    
    def show_more_actions(self, order_id):
        """Wyświetla menu dodatkowych akcji dla zamówienia."""
        menu = QMenu(self)
        
        actions = [
            ("Zmień status", self.change_order_status),
            ("Usuń", self.delete_order)
        ]
        
        for label, slot in actions:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, oid=order_id: slot(oid))
            menu.addAction(action)
        
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def change_order_status(self, order_id):
        """Zmienia status zamówienia."""
        # TODO: Implementacja zmiany statusu zamówienia
        NotificationManager.get_instance().show_notification(
            f"Zmiana statusu zamówienia {order_id}",
            NotificationTypes.INFO
        )
    
    def delete_order(self, order_id):
        """Usuwa zamówienie."""
        # TODO: Implementacja usuwania zamówienia
        NotificationManager.get_instance().show_notification(
            f"Usuwanie zamówienia {order_id}",
            NotificationTypes.WARNING
        )
    
    def filter_by_status(self):
        """Filtruje zamówienia po statusie."""
        sender = self.sender()
        status_type = sender.property("status_type")
        
        # Zaznacz aktywną zakładkę
        for key, btn in self.status_tab_buttons.items():
            btn.setProperty("active", key == status_type)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # TODO: Implementacja filtrowania zamówień
        NotificationManager.get_instance().show_notification(
            f"Filtrowanie zamówień: {status_type}",
            NotificationTypes.INFO
        )
    
    def show_export_menu(self):
        """Wyświetla menu eksportu zamówień."""
        menu = QMenu(self)
        
        export_actions = [
            ("Eksportuj do Excel", self.export_to_excel),
            ("Eksportuj do PDF", self.export_to_pdf)
        ]
        
        for label, slot in export_actions:
            action = QAction(label, self)
            action.triggered.connect(slot)
            menu.addAction(action)
        
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))