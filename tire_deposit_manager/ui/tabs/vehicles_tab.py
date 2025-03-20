#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł implementujący zakładkę pojazdów w dialogu szczegółów klienta.
"""

import os
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from ui.dialogs.vehicle_dialog import VehicleDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class VehiclesTab(QWidget):
    """
    Zakładka pojazdów w dialogu szczegółów klienta.
    Umożliwia przeglądanie, dodawanie, edycję i usuwanie pojazdów klienta.
    """
    
    def __init__(self, db_connection, client_id, parent=None):
        """
        Inicjalizacja zakładki pojazdów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            client_id (int): ID klienta
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.client_id = client_id
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie listy pojazdów klienta
        self.load_vehicles()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # Panel przycisków
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 10)
        
        # Przycisk dodawania pojazdu
        add_button = QPushButton("🚗 Dodaj pojazd")
        add_button.setObjectName("addButton")
        add_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add.png")))
        add_button.clicked.connect(self.add_vehicle)
        button_layout.addWidget(add_button)
        
        # Elastyczna przestrzeń
        button_layout.addStretch(1)
        
        # Przycisk odświeżania
        refresh_button = QPushButton("🔄 Odśwież")
        refresh_button.setObjectName("refreshButton")
        refresh_button.clicked.connect(self.load_vehicles)
        button_layout.addWidget(refresh_button)
        
        layout.addWidget(button_panel)
        
        # Tabela pojazdów
        self.vehicles_table = QTableWidget()
        self.vehicles_table.setColumnCount(8)
        self.vehicles_table.setHorizontalHeaderLabels([
            "ID", "Marka", "Model", "Rok", "Nr rejestracyjny", "Rozmiar opon", "Typ", "Akcje"
        ])
        
        # Ustawienia tabeli
        self.vehicles_table.setAlternatingRowColors(True)
        self.vehicles_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.vehicles_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.vehicles_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.vehicles_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Automatyczne rozszerzanie kolumn
        self.vehicles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vehicles_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.vehicles_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Rok
        self.vehicles_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Akcje
        
        # Podwójne kliknięcie otwiera edycję pojazdu
        self.vehicles_table.doubleClicked.connect(self.edit_vehicle)
        
        layout.addWidget(self.vehicles_table)
    
    def load_vehicles(self):
        """Ładuje listę pojazdów klienta z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz wszystkie pojazdy klienta
            cursor.execute("""
                SELECT 
                    id, make, model, year, registration_number, 
                    tire_size, vehicle_type, notes
                FROM vehicles 
                WHERE client_id = ?
                ORDER BY make, model
            """, (self.client_id,))
            
            vehicles = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.vehicles_table.setRowCount(0)
            
            # Wypełnienie tabeli
            for row, vehicle in enumerate(vehicles):
                self.vehicles_table.insertRow(row)
                
                # Dodaj dane do tabeli
                for col, value in enumerate(vehicle):
                    # Kolumnę akcji pomijamy
                    if col < 7:
                        # Konwersja None na pusty string
                        display_value = str(value) if value is not None else "-"
                        
                        item = QTableWidgetItem(display_value)
                        
                        # Wyrównanie ID do prawej
                        if col == 0:
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        
                        self.vehicles_table.setItem(row, col, item)
                
                # Kolumna akcji
                actions_item = QTableWidgetItem()
                actions_item.setTextAlignment(Qt.AlignCenter)
                self.vehicles_table.setItem(row, 7, actions_item)
            
            logger.debug(f"Załadowano {len(vehicles)} pojazdów klienta o ID: {self.client_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania pojazdów: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas ładowania listy pojazdów:\n{str(e)}"
            )
    
    def add_vehicle(self):
        """Otwiera okno dodawania nowego pojazdu."""
        try:
            dialog = VehicleDialog(self.conn, client_id=self.client_id, parent=self.parentWidget())
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę pojazdów
                self.load_vehicles()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"🚗 Dodano nowy pojazd",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas dodawania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania pojazdu:\n{str(e)}"
            )
    
    def edit_vehicle(self, index=None):
        """
        Otwiera okno edycji zaznaczonego pojazdu.
        
        Args:
            index (QModelIndex, optional): Indeks klikniętego elementu. Domyślnie None.
        """
        try:
            # Pobierz zaznaczony wiersz
            if index:
                selected_row = index.row()
            else:
                selected_items = self.vehicles_table.selectedItems()
                if not selected_items:
                    QMessageBox.warning(
                        self, 
                        "Brak wyboru", 
                        "Proszę wybrać pojazd do edycji."
                    )
                    return
                selected_row = selected_items[0].row()
            
            # Pobierz ID pojazdu
            vehicle_id = int(self.vehicles_table.item(selected_row, 0).text())
            
            # Otwórz dialog edycji
            dialog = VehicleDialog(self.conn, vehicle_id=vehicle_id, parent=self.parentWidget())
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę pojazdów
                self.load_vehicles()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"✅ Zaktualizowano dane pojazdu",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas edycji pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas edycji pojazdu:\n{str(e)}"
            )
    
    def delete_vehicle(self):
        """Usuwa zaznaczony pojazd."""
        try:
            # Pobierz zaznaczony wiersz
            selected_items = self.vehicles_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(
                    self, 
                    "Brak wyboru", 
                    "Proszę wybrać pojazd do usunięcia."
                )
                return
            
            # Pobierz ID pojazdu
            selected_row = selected_items[0].row()
            vehicle_id = int(self.vehicles_table.item(selected_row, 0).text())
            
            # Pobierz informacje o pojeździe do wyświetlenia
            make = self.vehicles_table.item(selected_row, 1).text()
            model = self.vehicles_table.item(selected_row, 2).text()
            registration = self.vehicles_table.item(selected_row, 4).text()
            
            # Potwierdź usunięcie
            reply = QMessageBox.question(
                self, 
                "Potwierdź usunięcie", 
                f"Czy na pewno chcesz usunąć pojazd {make} {model} ({registration})?\n\n"
                "Ta operacja jest nieodwracalna.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                # Usuń pojazd
                cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
                
                # Zatwierdź zmiany
                self.conn.commit()
                
                # Odśwież listę pojazdów
                self.load_vehicles()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"🗑️ Usunięto pojazd: {make} {model}",
                    NotificationTypes.SUCCESS
                )
        
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas usuwania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Nie można usunąć pojazdu:\n{str(e)}"
            )
    
    def show_context_menu(self, position):
        """
        Wyświetla menu kontekstowe dla tabeli klientów.
        
        Args:
            position: Pozycja kursora
        """
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        
        if not table:
            return
        
        # Sprawdź, czy jakiś wiersz jest zaznaczony
        selected_items = table.selectedItems()
        if not selected_items:
            return
        
        # Pobierz ID klienta
        selected_row = selected_items[0].row()
        client_id = int(table.item(selected_row, 0).text())
        client_name = table.item(selected_row, 1).text()
        
        # Utwórz menu
        menu = QMenu()
        
        # Dodaj opcje z emotikonami
        view_action = menu.addAction("👁️ Szczegóły klienta")
        edit_action = menu.addAction("✏️ Edytuj klienta")
        add_vehicle_action = menu.addAction("🚗 Dodaj pojazd")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Usuń klienta")
        
        # Wykonaj wybraną akcję
        action = menu.exec(table.viewport().mapToGlobal(position))
        
        if not action:
            return
        
        if action == view_action:
            self.view_client_details(table.model().index(selected_row, 0))
        elif action == edit_action:
            self.edit_client()
        elif action == add_vehicle_action:
            self.add_vehicle_to_client(client_id, client_name)
        elif action == delete_action:
            self.delete_client()