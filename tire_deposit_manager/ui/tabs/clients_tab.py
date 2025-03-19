#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka klientów - zarządzanie listą klientów w aplikacji.
"""

import os
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.client_details_dialog import ClientDetailsDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class ClientsTab(QWidget):
    """
    Zakładka zarządzania klientami w aplikacji.
    Wyświetla listę klientów, umożliwia dodawanie, edycję i usuwanie.
    """
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki klientów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie danych klientów
        self.load_clients()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel wyszukiwania
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 10)
        
        search_label = QLabel("Szukaj:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Wprowadź nazwę, telefon lub email...")
        self.search_input.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_input, 1)
        
        layout.addWidget(search_panel)
        
        # Tabela klientów
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels([
            "ID", "Nazwa", "Telefon", "Email", "Rabat (%)", "Dodatkowe informacje"
        ])
        
        # Ustawienia tabeli
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clients_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Automatyczne rozszerzanie kolumn
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.clients_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Rabat
        
        # Podwójne kliknięcie otwiera szczegóły klienta
        self.clients_table.doubleClicked.connect(self.view_client_details)
        
        layout.addWidget(self.clients_table)
        
        # Panel przycisków
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Przyciski akcji
        add_button = QPushButton("Dodaj klienta")
        add_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add-client.png")))
        add_button.clicked.connect(self.add_client)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edytuj")
        edit_button.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
        edit_button.clicked.connect(self.edit_client)
        button_layout.addWidget(edit_button)
        
        # Elastyczna przestrzeń
        button_layout.addStretch(1)
        
        # Przycisk usuwania
        delete_button = QPushButton("Usuń")
        delete_button.setObjectName("deleteButton")
        delete_button.setIcon(QIcon(os.path.join(ICONS_DIR, "delete.png")))
        delete_button.clicked.connect(self.delete_client)
        button_layout.addWidget(delete_button)
        
        layout.addWidget(button_panel)
    
    def load_clients(self):
        """Ładuje listę klientów z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz wszystkich klientów
            cursor.execute("""
                SELECT 
                    id, name, phone_number, email, discount, additional_info 
                FROM clients 
                ORDER BY name
            """)
            
            clients = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.clients_table.setRowCount(0)
            
            # Wypełnienie tabeli
            for row, client in enumerate(clients):
                self.clients_table.insertRow(row)
                
                # Dodaj dane do tabeli
                for col, value in enumerate(client):
                    # Konwersja None na pusty string
                    display_value = str(value) if value is not None else ""
                    
                    # Specjalne formatowanie dla rabatu
                    if col == 4 and value is not None:
                        display_value = f"{float(value):.2f}%"
                    
                    item = QTableWidgetItem(display_value)
                    
                    # Wyrównanie ID do prawej
                    if col == 0:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
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
        # Pokaż wszystkie wiersze, jeśli tekst jest pusty
        if not text:
            for row in range(self.clients_table.rowCount()):
                self.clients_table.setRowHidden(row, False)
            return
        
        # Filtruj wiersze
        for row in range(self.clients_table.rowCount()):
            row_visible = False
            
            # Sprawdź każdą kolumnę
            for col in range(1, self.clients_table.columnCount()):
                item = self.clients_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    row_visible = True
                    break
            
            # Ukryj lub pokaż wiersz
            self.clients_table.setRowHidden(row, not row_visible)
    
    def add_client(self):
        """Otwiera okno dodawania nowego klienta."""
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == dialog.Accepted:
            # Odśwież listę klientów
            self.load_clients()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Dodano nowego klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS
            )
    
    def edit_client(self):
        """Otwiera okno edycji zaznaczonego klienta."""
        # Pobierz zaznaczony wiersz
        selected_rows = self.clients_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, 
                "Brak wyboru", 
                "Proszę wybrać klienta do edycji."
            )
            return
        
        # Pobierz ID klienta
        selected_row = selected_rows[0].row()
        client_id = int(self.clients_table.item(selected_row, 0).text())
        
        # Otwórz dialog edycji
        dialog = ClientDialog(self.conn, client_id=client_id, parent=self)
        if dialog.exec() == dialog.Accepted:
            # Odśwież listę klientów
            self.load_clients()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Zaktualizowano klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS
            )
    
    def view_client_details(self, index):
        """
        Wyświetla szczegóły klienta po podwójnym kliknięciu.
        
        Args:
            index (QModelIndex): Indeks klikniętego elementu
        """
        row = index.row()
        client_id = int(self.clients_table.item(row, 0).text())
        
        # Otwórz dialog szczegółów klienta
        try:
            from ui.dialogs.client_details_dialog import ClientDetailsDialog
            dialog = ClientDetailsDialog(self.conn, client_id, parent=self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Nie można wyświetlić szczegółów klienta:\n{str(e)}"
            )
    
    def delete_client(self):
        """Usuwa zaznaczonego klienta."""
        # Pobierz zaznaczony wiersz
        selected_rows = self.clients_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, 
                "Brak wyboru", 
                "Proszę wybrać klienta do usunięcia."
            )
            return
        
        # Pobierz ID i nazwę klienta
        selected_row = selected_rows[0].row()
        client_id = int(self.clients_table.item(selected_row, 0).text())
        client_name = self.clients_table.item(selected_row, 1).text()
        
        # Potwierdź usunięcie
        reply = QMessageBox.question(
            self, 
            "Potwierdź usunięcie", 
            f"Czy na pewno chcesz usunąć klienta {client_name}?\n\n"
            "Ta operacja jest nieodwracalna.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                
                # Usuń klienta
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                
                # Zatwierdź zmiany
                self.conn.commit()
                
                # Odśwież listę klientów
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"Usunięto klienta: {client_name}",
                    NotificationTypes.SUCCESS
                )
            
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Błąd podczas usuwania klienta: {e}")
                QMessageBox.critical(
                    self, 
                    "Błąd", 
                    f"Nie można usunąć klienta:\n{str(e)}"
                )
    
    def show_context_menu(self, position):
        """
        Wyświetla menu kontekstowe dla tabeli klientów.
        
        Args:
            position: Pozycja kursora
        """
        # Sprawdź, czy jakiś wiersz jest zaznaczony
        selected_rows = self.clients_table.selectedItems()
        if not selected_rows:
            return
        
        # Pobierz ID klienta
        selected_row = selected_rows[0].row()
        client_id = int(self.clients_table.item(selected_row, 0).text())
        client_name = self.clients_table.item(selected_row, 1).text()
        
        # Utwórz menu
        menu = QMenu()
        
        # Dodaj opcje
        view_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "view.png")), "Szczegóły klienta")
        edit_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "edit.png")), "Edytuj klienta")
        menu.addSeparator()
        delete_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "delete.png")), "Usuń klienta")
        
        # Wykonaj wybraną akcję
        action = menu.exec(self.clients_table.viewport().mapToGlobal(position))
        
        if not action:
            return
        
        if action == view_action:
            self.view_client_details(self.clients_table.model().index(selected_row, 0))
        elif action == edit_action:
            self.edit_client()
        elif action == delete_action:
            self.delete_client()
    
    def refresh_data(self):
        """Odświeża listę klientów."""
        self.load_clients()