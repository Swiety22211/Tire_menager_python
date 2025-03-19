#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do wyboru klienta z listy.
"""

import os
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class ClientSelectorDialog(QDialog):
    """
    Dialog umożliwiający wybór klienta z listy.
    """
    
    def __init__(self, db_connection, parent=None):
        """
        Inicjalizacja dialogu wyboru klienta.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        
        self.selected_client_id = None
        self.selected_client_name = None
        
        self.setWindowTitle("Wybierz klienta")
        self.resize(700, 500)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Ładowanie listy klientów
        self.load_clients()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika dialogu."""
        main_layout = QVBoxLayout(self)
        
        # Panel wyszukiwania
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Szukaj:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Wprowadź nazwę klienta, telefon lub adres email...")
        self.search_input.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_input, 1)
        
        main_layout.addLayout(search_layout)
        
        # Tabela klientów
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels(["ID", "Nazwa", "Telefon", "Email"])
        
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.clients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nazwa
        self.clients_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Telefon
        self.clients_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Email
        
        self.clients_table.doubleClicked.connect(self.select_client)
        
        main_layout.addWidget(self.clients_table)
        
        # Panel przycisków
        buttons_layout = QHBoxLayout()
        
        add_new_client_button = QPushButton("Dodaj nowego klienta")
        add_new_client_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add-client.png")))
        add_new_client_button.clicked.connect(self.add_new_client)
        buttons_layout.addWidget(add_new_client_button)
        
        buttons_layout.addStretch(1)
        
        select_button = QPushButton("Wybierz")
        select_button.setIcon(QIcon(os.path.join(ICONS_DIR, "accept.png")))
        select_button.clicked.connect(self.select_client)
        buttons_layout.addWidget(select_button)
        
        cancel_button = QPushButton("Anuluj")
        cancel_button.setIcon(QIcon(os.path.join(ICONS_DIR, "cancel.png")))
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        main_layout.addLayout(buttons_layout)
    
    def load_clients(self):
        """Ładuje listę klientów z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobranie wszystkich klientów
            cursor.execute(
                "SELECT id, name, phone_number, email FROM clients ORDER BY name"
            )
            
            clients = cursor.fetchall()
            
            # Wypełnienie tabeli
            self.clients_table.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                for col, value in enumerate(client):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.clients_table.setItem(row, col, item)
            
            logger.debug(f"Załadowano {len(clients)} klientów")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania klientów: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania listy klientów:\n{str(e)}"
            )
    
    def filter_clients(self, text):
        """
        Filtruje listę klientów na podstawie wprowadzonego tekstu.
        
        Args:
            text (str): Tekst wprowadzony w polu wyszukiwania
        """
        # Pokazujemy wszystkie wiersze, jeśli nie ma filtra
        if not text:
            for row in range(self.clients_table.rowCount()):
                self.clients_table.setRowHidden(row, False)
            return
        
        # Filtrowanie po nazwie, telefonie i emailu
        for row in range(self.clients_table.rowCount()):
            name_item = self.clients_table.item(row, 1)
            phone_item = self.clients_table.item(row, 2)
            email_item = self.clients_table.item(row, 3)
            
            # Sprawdzamy, czy tekst zawiera się w którejkolwiek kolumnie
            if (name_item and text.lower() in name_item.text().lower()) or \
               (phone_item and text.lower() in phone_item.text().lower()) or \
               (email_item and text.lower() in email_item.text().lower()):
                self.clients_table.setRowHidden(row, False)
            else:
                self.clients_table.setRowHidden(row, True)
    
    def select_client(self):
        """Wybiera klienta z tabeli."""
        # Sprawdzenie, czy jakiś wiersz jest zaznaczony
        selected_items = self.clients_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, 
                "Brak wyboru", 
                "Proszę wybrać klienta z listy."
            )
            return
        
        # Pobranie ID i nazwy zaznaczonego klienta
        selected_row = selected_items[0].row()
        self.selected_client_id = int(self.clients_table.item(selected_row, 0).text())
        self.selected_client_name = self.clients_table.item(selected_row, 1).text()
        
        # Zaakceptowanie dialogu
        self.accept()
    
    def add_new_client(self):
        """Otwiera dialog dodawania nowego klienta."""
        from ui.dialogs.client_dialog import ClientDialog
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Odświeżenie listy klientów
            self.load_clients()
            
            # Ustawienie nowo dodanego klienta jako aktualnie wybranego
            self.selected_client_id = dialog.client_id
            self.selected_client_name = dialog.client_name
            
            # Automatyczne zaakceptowanie dialogu
            self.accept()