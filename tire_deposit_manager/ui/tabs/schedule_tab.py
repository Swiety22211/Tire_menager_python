#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka harmonogramu wizyt - zarządzanie planowaniem wizyt w serwisie.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QMenu,
    QDialog, QSpacerItem, QSizePolicy, QFrame, QGridLayout, QComboBox,
    QCalendarWidget, QTimeEdit, QSplitter
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime, Signal, Slot
from PySide6.QtGui import QIcon, QColor, QFont

from ui.dialogs.appointment_dialog import AppointmentDialog
from ui.dialogs.appointment_details_dialog import AppointmentDetailsDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class ScheduleTab(QWidget):
    """
    Zakładka harmonogramu umożliwiająca planowanie i zarządzanie wizytami w serwisie.
    """
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki harmonogramu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Ładowanie danych
        self.load_appointments()
    
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
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Wpisz nazwę klienta, typ usługi...")
        self.search_input.textChanged.connect(self.search_appointments)
        search_layout.addWidget(self.search_input, 1)
        
        date_label = QLabel("Data:")
        search_layout.addWidget(date_label)
        
        self.date_selector = QComboBox()
        self.date_selector.addItems(["Dzisiaj", "Jutro", "Ten tydzień", "Przyszły tydzień", "Ten miesiąc", "Wszystkie"])
        self.date_selector.currentIndexChanged.connect(self.filter_by_date)
        search_layout.addWidget(self.date_selector)
        
        status_label = QLabel("Status:")
        search_layout.addWidget(status_label)
        
        self.status_selector = QComboBox()
        self.status_selector.addItems(["Wszystkie", "Zaplanowane", "W trakcie", "Zakończone", "Anulowane"])
        self.status_selector.currentIndexChanged.connect(self.filter_by_status)
        search_layout.addWidget(self.status_selector)
        
        refresh_button = QPushButton("Odśwież")
        refresh_button.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.png")))
        refresh_button.clicked.connect(self.refresh_data)
        search_layout.addWidget(refresh_button)
        
        layout.addWidget(search_panel)
        
        # Splitter do podziału na kalendarz i tabelę
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel kalendarza po lewej
        calendar_panel = QWidget()
        calendar_layout = QVBoxLayout(calendar_panel)
        
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.calendar_date_changed)
        calendar_layout.addWidget(self.calendar)
        
        # Informacje o wizytach na wybrany dzień
        appointments_info_frame = QFrame()
        appointments_info_frame.setFrameShape(QFrame.StyledPanel)
        appointments_info_layout = QVBoxLayout(appointments_info_frame)
        
        self.selected_date_label = QLabel("Wizyty na dzień: " + QDate.currentDate().toString("dd.MM.yyyy"))
        self.selected_date_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        appointments_info_layout.addWidget(self.selected_date_label)
        
        self.appointments_count_label = QLabel("Liczba wizyt: 0")
        appointments_info_layout.addWidget(self.appointments_count_label)
        
        calendar_layout.addWidget(appointments_info_frame)
        
        # Przyciski poniżej kalendarza
        calendar_buttons = QWidget()
        calendar_buttons_layout = QHBoxLayout(calendar_buttons)
        calendar_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        prev_month_button = QPushButton("Poprzedni miesiąc")
        prev_month_button.setIcon(QIcon(os.path.join(ICONS_DIR, "prev.png")))
        prev_month_button.clicked.connect(self.prev_month)
        calendar_buttons_layout.addWidget(prev_month_button)
        
        today_button = QPushButton("Dziś")
        today_button.clicked.connect(self.go_to_today)
        calendar_buttons_layout.addWidget(today_button)
        
        next_month_button = QPushButton("Następny miesiąc")
        next_month_button.setIcon(QIcon(os.path.join(ICONS_DIR, "next.png")))
        next_month_button.clicked.connect(self.next_month)
        calendar_buttons_layout.addWidget(next_month_button)
        
        calendar_layout.addWidget(calendar_buttons)
        
        splitter.addWidget(calendar_panel)
        
        # Panel z tabelą po prawej
        table_panel = QWidget()
        table_layout = QVBoxLayout(table_panel)
        
        # Tabela wizyt
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(7)
        self.appointments_table.setHorizontalHeaderLabels([
            "ID", "Klient", "Data", "Godzina", "Usługa", "Status", "Uwagi"
        ])
        
        self.appointments_table.setAlternatingRowColors(True)
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.appointments_table.customContextMenuRequested.connect(self.show_context_menu)
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointments_table.doubleClicked.connect(self.view_appointment_details)
        
        table_layout.addWidget(self.appointments_table)
        
        # Panel przycisków
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        add_button = QPushButton("Nowa wizyta")
        add_button.setObjectName("actionButton")
        add_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add.png")))
        add_button.clicked.connect(self.add_appointment)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edytuj")
        edit_button.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
        edit_button.clicked.connect(self.edit_selected_appointment)
        button_layout.addWidget(edit_button)
        
        change_status_button = QPushButton("Zmień status")
        change_status_button.setIcon(QIcon(os.path.join(ICONS_DIR, "status.png")))
        change_status_button.clicked.connect(self.change_appointment_status)
        button_layout.addWidget(change_status_button)
        
        # Odstęp między lewymi a prawymi przyciskami
        button_layout.addStretch(1)
        
        delete_button = QPushButton("Usuń")
        delete_button.setObjectName("deleteButton")
        delete_button.setIcon(QIcon(os.path.join(ICONS_DIR, "delete.png")))
        delete_button.clicked.connect(self.delete_selected_appointment)
        button_layout.addWidget(delete_button)
        
        table_layout.addWidget(button_panel)
        
        splitter.addWidget(table_panel)
        
        # Ustaw proporcje splittera - 1:2 (kalendarz:tabela)
        splitter.setSizes([100, 200])
        
        layout.addWidget(splitter)
    
    def load_appointments(self):
        """Ładuje wszystkie wizyty z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź czy tabela appointments istnieje
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # Utwórz tabelę appointments jeśli nie istnieje
                cursor.execute('''
                    CREATE TABLE appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        appointment_date TEXT,
                        appointment_time TEXT,
                        service_type TEXT,
                        status TEXT DEFAULT 'Zaplanowana',
                        notes TEXT,
                        duration INTEGER DEFAULT 60,
                        FOREIGN KEY(client_id) REFERENCES clients(id)
                    )
                ''')
                self.conn.commit()
                logger.info("Utworzono tabelę appointments")
            
            # Budowa zapytania z filtrowaniem
            query = '''
                SELECT 
                    a.id, c.name, a.appointment_date, a.appointment_time, 
                    a.service_type, a.status, a.notes
                FROM 
                    appointments a
                LEFT JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    1=1
            '''
            
            params = []
            
            # Filtrowanie tekstu wyszukiwania
            search_text = self.search_input.text().strip()
            if search_text:
                query += ''' AND (
                    c.name LIKE ? OR 
                    a.service_type LIKE ? OR 
                    a.notes LIKE ?
                )'''
                search_param = f"%{search_text}%"
                params.extend([search_param, search_param, search_param])
            
            # Filtrowanie daty
            if hasattr(self, 'date_selector'):
                date_filter = self.date_selector.currentText()
                today = datetime.now().date()
                
                if date_filter == "Dzisiaj":
                    query += " AND a.appointment_date = ?"
                    params.append(today.strftime("%Y-%m-%d"))
                elif date_filter == "Jutro":
                    tomorrow = today + timedelta(days=1)
                    query += " AND a.appointment_date = ?"
                    params.append(tomorrow.strftime("%Y-%m-%d"))
                elif date_filter == "Ten tydzień":
                    # Początek tygodnia (poniedziałek)
                    start_of_week = today - timedelta(days=today.weekday())
                    # Koniec tygodnia (niedziela)
                    end_of_week = start_of_week + timedelta(days=6)
                    query += " AND a.appointment_date BETWEEN ? AND ?"
                    params.append(start_of_week.strftime("%Y-%m-%d"))
                    params.append(end_of_week.strftime("%Y-%m-%d"))
                elif date_filter == "Przyszły tydzień":
                    # Początek następnego tygodnia
                    start_of_next_week = today + timedelta(days=7-today.weekday())
                    # Koniec następnego tygodnia
                    end_of_next_week = start_of_next_week + timedelta(days=6)
                    query += " AND a.appointment_date BETWEEN ? AND ?"
                    params.append(start_of_next_week.strftime("%Y-%m-%d"))
                    params.append(end_of_next_week.strftime("%Y-%m-%d"))
                elif date_filter == "Ten miesiąc":
                    # Pierwszy dzień miesiąca
                    start_of_month = today.replace(day=1)
                    # Ostatni dzień miesiąca (zależy od miesiąca)
                    if today.month == 12:
                        end_of_month = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
                    else:
                        end_of_month = today.replace(month=today.month+1, day=1) - timedelta(days=1)
                    query += " AND a.appointment_date BETWEEN ? AND ?"
                    params.append(start_of_month.strftime("%Y-%m-%d"))
                    params.append(end_of_month.strftime("%Y-%m-%d"))
            
            # Filtrowanie statusu
            if hasattr(self, 'status_selector') and self.status_selector.currentText() != "Wszystkie":
                status = self.status_selector.currentText()
                query += " AND a.status = ?"
                params.append(status)
            
            # Sortowanie
            query += " ORDER BY a.appointment_date ASC, a.appointment_time ASC"
            
            # Wykonanie zapytania
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Wypełnienie tabeli
            self.appointments_table.setRowCount(0)  # Czyszczenie tabeli
            
            for row_idx, row_data in enumerate(rows):
                self.appointments_table.insertRow(row_idx)
                
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    
                    # Stylizacja statusu
                    if col_idx == 5:  # Status
                        if cell_data == "Zaplanowana":
                            item.setBackground(QColor("#3498db"))  # Niebieski
                            item.setForeground(QColor("#ffffff"))  # Biały tekst
                        elif cell_data == "W trakcie":
                            item.setBackground(QColor("#f39c12"))  # Pomarańczowy
                            item.setForeground(QColor("#ffffff"))  # Biały tekst
                        elif cell_data == "Zakończona":
                            item.setBackground(QColor("#2ecc71"))  # Zielony
                            item.setForeground(QColor("#ffffff"))  # Biały tekst
                        elif cell_data == "Anulowana":
                            item.setBackground(QColor("#e74c3c"))  # Czerwony
                            item.setForeground(QColor("#ffffff"))  # Biały tekst
                    
                    # Formatowanie daty
                    if col_idx == 2 and cell_data:  # Data
                        try:
                            date = datetime.strptime(cell_data, "%Y-%m-%d")
                            item.setText(date.strftime("%d.%m.%Y"))
                        except ValueError:
                            pass
                    
                    self.appointments_table.setItem(row_idx, col_idx, item)
            
            # Aktualizacja etykiety liczby wizyt
            self.update_appointments_info()
            
            logger.debug(f"Załadowano {self.appointments_table.rowCount()} wizyt")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania wizyt: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania wizyt: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def update_appointments_info(self):
        """Aktualizuje informacje o wizytach na wybrany dzień."""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")
        
        try:
            cursor = self.conn.cursor()
            
            # Pobierz liczbę wizyt na wybrany dzień
            cursor.execute(
                "SELECT COUNT(*) FROM appointments WHERE appointment_date = ?",
                (date_str,)
            )
            count = cursor.fetchone()[0]
            
            # Aktualizacja etykiet
            self.selected_date_label.setText("Wizyty na dzień: " + selected_date.toString("dd.MM.yyyy"))
            self.appointments_count_label.setText(f"Liczba wizyt: {count}")
            
            # Dodatkowo podświetl wizyty w tabeli
            for row in range(self.appointments_table.rowCount()):
                date_item = self.appointments_table.item(row, 2)
                if date_item and date_item.text() == selected_date.toString("dd.MM.yyyy"):
                    # Podświetl wiersz
                    for col in range(self.appointments_table.columnCount()):
                        cell = self.appointments_table.item(row, col)
                        if cell and col != 5:  # Nie zmieniaj komórki statusu
                            cell.setBackground(QColor("#d6eaf8"))  # Jasny niebieski
                else:
                    # Przywróć domyślne tło dla pozostałych wierszy
                    for col in range(self.appointments_table.columnCount()):
                        cell = self.appointments_table.item(row, col)
                        if cell and col != 5:  # Nie zmieniaj komórki statusu
                            cell.setBackground(QColor())
        
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji informacji o wizytach: {e}")
    
    def calendar_date_changed(self):
        """Obsługuje zmianę daty w kalendarzu."""
        self.update_appointments_info()
        
        # Opcjonalnie - filtrowanie tabeli do wybranego dnia
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        # Ustaw filtr daty na "Dzisiaj" i zmodyfikuj zapytanie, aby brało pod uwagę wybraną datę
        # To jest niestandardowe zachowanie, więc najpierw sprawdzamy czy chcemy to zrobić
        filter_table = False
        
        if filter_table:
            cursor = self.conn.cursor()
            query = '''
                SELECT 
                    a.id, c.name, a.appointment_date, a.appointment_time, 
                    a.service_type, a.status, a.notes
                FROM 
                    appointments a
                LEFT JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.appointment_date = ?
                ORDER BY 
                    a.appointment_time ASC
            '''
            
            cursor.execute(query, (selected_date,))
            rows = cursor.fetchall()
            
            # Wypełnienie tabeli
            self.appointments_table.setRowCount(0)  # Czyszczenie tabeli
            
            for row_idx, row_data in enumerate(rows):
                self.appointments_table.insertRow(row_idx)
                
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    
                    # Stylizacja statusu
                    if col_idx == 5:  # Status
                        if cell_data == "Zaplanowana":
                            item.setBackground(QColor("#3498db"))  # Niebieski
                        elif cell_data == "W trakcie":
                            item.setBackground(QColor("#f39c12"))  # Pomarańczowy
                        elif cell_data == "Zakończona":
                            item.setBackground(QColor("#2ecc71"))  # Zielony
                        elif cell_data == "Anulowana":
                            item.setBackground(QColor("#e74c3c"))  # Czerwony
                        item.setForeground(QColor("#ffffff"))  # Biały tekst
                    
                    # Formatowanie daty
                    if col_idx == 2 and cell_data:  # Data
                        try:
                            date = datetime.strptime(cell_data, "%Y-%m-%d")
                            item.setText(date.strftime("%d.%m.%Y"))
                        except ValueError:
                            pass
                    
                    self.appointments_table.setItem(row_idx, col_idx, item)
    
    def prev_month(self):
        """Przejście do poprzedniego miesiąca w kalendarzu."""
        current_date = self.calendar.selectedDate()
        month = current_date.month()
        year = current_date.year()
        
        if month == 1:
            # Jeśli styczeń, cofamy się do grudnia poprzedniego roku
            new_date = QDate(year - 1, 12, current_date.day())
        else:
            # Inaczej cofamy się o miesiąc
            new_date = QDate(year, month - 1, min(current_date.day(), 28))  # Maksymalnie 28 dla bezpieczeństwa
        
        self.calendar.setSelectedDate(new_date)
    
    def next_month(self):
        """Przejście do następnego miesiąca w kalendarzu."""
        current_date = self.calendar.selectedDate()
        month = current_date.month()
        year = current_date.year()
        
        if month == 12:
            # Jeśli grudzień, przechodzimy do stycznia następnego roku
            new_date = QDate(year + 1, 1, current_date.day())
        else:
            # Inaczej przechodzimy do następnego miesiąca
            new_date = QDate(year, month + 1, min(current_date.day(), 28))  # Maksymalnie 28 dla bezpieczeństwa
        
        self.calendar.setSelectedDate(new_date)
    
    def go_to_today(self):
        """Przejście do dzisiejszej daty w kalendarzu."""
        self.calendar.setSelectedDate(QDate.currentDate())
    
    def search_appointments(self):
        """Wyszukuje wizyty na podstawie wprowadzonego tekstu."""
        self.load_appointments()
    
    def filter_by_date(self):
        """Filtruje wizyty według wybranego zakresu dat."""
        self.load_appointments()
    
    def filter_by_status(self):
        """Filtruje wizyty według wybranego statusu."""
        self.load_appointments()
    
    def refresh_data(self):
        """Odświeża dane w zakładce."""
        self.load_appointments()
    
    def add_appointment(self):
        """Otwiera okno dodawania nowej wizyty."""
        try:
            # Ustaw domyślną datę i godzinę na podstawie wybranej daty w kalendarzu
            selected_date = self.calendar.selectedDate()
            
            dialog = AppointmentDialog(self.conn, selected_date=selected_date, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_appointments()
                NotificationManager.get_instance().show_notification(
                    "Wizyta została dodana pomyślnie.",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas dodawania wizyty: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania wizyty: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def edit_selected_appointment(self):
        """Edytuje zaznaczoną wizytę."""
        # Pobranie zaznaczonego wiersza z tabeli
        selected_rows = self.appointments_table.selectedItems()
        if not selected_rows:
            NotificationManager.get_instance().show_notification(
                "Nie wybrano żadnej wizyty do edycji.",
                NotificationTypes.WARNING
            )
            return
        
        # Pobranie ID wizyty
        selected_row = selected_rows[0].row()
        appointment_id = int(self.appointments_table.item(selected_row, 0).text())
        
        # Otwarcie okna edycji
        self.edit_appointment(appointment_id)
    
    def edit_appointment(self, appointment_id):
        """
        Edytuje wizytę o podanym ID.
        
        Args:
            appointment_id (int): ID wizyty do edycji
        """
        try:
            dialog = AppointmentDialog(self.conn, appointment_id=appointment_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_appointments()
                NotificationManager.get_instance().show_notification(
                    "Wizyta została zaktualizowana pomyślnie.",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas edycji wizyty: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas edycji wizyty: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def delete_selected_appointment(self):
        """Usuwa zaznaczoną wizytę."""
        # Pobranie zaznaczonego wiersza z tabeli
        selected_rows = self.appointments_table.selectedItems()
        if not selected_rows:
            NotificationManager.get_instance().show_notification(
                "Nie wybrano żadnej wizyty do usunięcia.",
                NotificationTypes.WARNING
            )
            return
        
        # Pobranie ID wizyty
        selected_row = selected_rows[0].row()
        appointment_id = int(self.appointments_table.item(selected_row, 0).text())
        client_name = self.appointments_table.item(selected_row, 1).text()
        
        # Potwierdzenie usunięcia
        confirmation = QMessageBox.question(
            self,
            "Potwierdź usunięcie",
            f"Czy na pewno chcesz usunąć wizytę klienta {client_name}?\n\n"
            "Ta operacja jest nieodwracalna.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmation == QMessageBox.Yes:
            # Usunięcie wizyty
            self.delete_appointment(appointment_id)
    
    def delete_appointment(self, appointment_id):
        """
        Usuwa wizytę o podanym ID.
        
        Args:
            appointment_id (int): ID wizyty do usunięcia
        """
        try:
            cursor = self.conn.cursor()
            
            # Usunięcie wizyty
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Odświeżenie danych
            self.load_appointments()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                "Wizyta została usunięta pomyślnie.",
                NotificationTypes.SUCCESS
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas usuwania wizyty: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas usuwania wizyty: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def view_appointment_details(self, index):
        """
        Wyświetla szczegóły wizyty po kliknięciu w tabeli.
        
        Args:
            index: Indeks klikniętego elementu
        """
        row = index.row()
        appointment_id = int(self.appointments_table.item(row, 0).text())
        self.view_appointment_details_by_id(appointment_id)
    
    def view_appointment_details_by_id(self, appointment_id):
        """
        Wyświetla szczegóły wizyty na podstawie ID.
        
        Args:
            appointment_id (int): ID wizyty
        """
        try:
            dialog = AppointmentDetailsDialog(self.conn, appointment_id, parent=self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów wizyty: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania szczegółów wizyty: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def change_appointment_status(self):
        """Zmienia status zaznaczonej wizyty."""
        # Pobranie zaznaczonego wiersza z tabeli
        selected_rows = self.appointments_table.selectedItems()
        if not selected_rows:
            NotificationManager.get_instance().show_notification(
                "Nie wybrano żadnej wizyty do zmiany statusu.",
                NotificationTypes.WARNING
            )
            return
        
        # Pobranie ID wizyty i aktualnego statusu
        selected_row = selected_rows[0].row()
        appointment_id = int(self.appointments_table.item(selected_row, 0).text())
        current_status = self.appointments_table.item(selected_row, 5).text()
        
        # Wybór nowego statusu
        statuses = ["Zaplanowana", "W trakcie", "Zakończona", "Anulowana"]
        current_index = statuses.index(current_status) if current_status in statuses else 0
        
        menu = QMenu(self)
        
        for status in statuses:
            if status != current_status:
                action = menu.addAction(status)
                action.triggered.connect(lambda checked, s=status: self.update_appointment_status(appointment_id, s))
        
        # Sprawdzenie czy menu ma jakieś elementy
        if not menu.actions():
            NotificationManager.get_instance().show_notification(
                "Brak dostępnych statusów do zmiany.",
                NotificationTypes.INFO
            )
            return
        
        # Wyświetlenie menu pod kursorem myszy
        cursor_pos = self.appointments_table.viewport().mapToGlobal(
            self.appointments_table.visualRect(
                self.appointments_table.currentIndex()
            ).bottomLeft()
        )
        menu.exec(cursor_pos)
    
    def update_appointment_status(self, appointment_id, new_status):
        """
        Aktualizuje status wizyty.
        
        Args:
            appointment_id (int): ID wizyty
            new_status (str): Nowy status wizyty
        """
        try:
            cursor = self.conn.cursor()
            
            # Aktualizacja statusu
            cursor.execute(
                "UPDATE appointments SET status = ? WHERE id = ?",
                (new_status, appointment_id)
            )
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Odświeżenie danych
            self.load_appointments()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Status wizyty został zmieniony na '{new_status}'.",
                NotificationTypes.SUCCESS
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas aktualizacji statusu wizyty: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas aktualizacji statusu wizyty: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def show_context_menu(self, position):
        """
        Wyświetla menu kontekstowe dla tabeli wizyt.
        
        Args:
            position: Pozycja kursora
        """
        menu = QMenu()
        
        selected_rows = self.appointments_table.selectedItems()
        if not selected_rows:
            return
        
        # Pobierz ID zaznaczonej wizyty
        selected_row = selected_rows[0].row()
        appointment_id = int(self.appointments_table.item(selected_row, 0).text())
        current_status = self.appointments_table.item(selected_row, 5).text()
        
        # Dodanie akcji do menu
        view_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "view.png")), "Szczegóły wizyty")
        edit_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "edit.png")), "Edytuj wizytę")
        
        menu.addSeparator()
        
        # Dodanie podmenu do zmiany statusu
        status_menu = QMenu("Zmień status", self)
        
        statuses = ["Zaplanowana", "W trakcie", "Zakończona", "Anulowana"]
        for status in statuses:
            if status != current_status:
                status_action = status_menu.addAction(status)
                status_action.triggered.connect(lambda checked, s=status: self.update_appointment_status(appointment_id, s))
        
        menu.addMenu(status_menu)
        
        menu.addSeparator()
        
        # Akcje komunikacji
        email_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "email.png")), "Wyślij przypomnienie e-mail")
        sms_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "sms.png")), "Wyślij przypomnienie SMS")
        
        menu.addSeparator()
        
        delete_action = menu.addAction(QIcon(os.path.join(ICONS_DIR, "delete.png")), "Usuń wizytę")
        
        # Wykonanie wybranej akcji
        action = menu.exec(self.appointments_table.viewport().mapToGlobal(position))
        if not action:
            return
        
        if action == view_action:
            self.view_appointment_details_by_id(appointment_id)
        elif action == edit_action:
            self.edit_appointment(appointment_id)
        elif action == email_action:
            self.send_email_reminder(appointment_id)
        elif action == sms_action:
            self.send_sms_reminder(appointment_id)
        elif action == delete_action:
            self.delete_selected_appointment()
    
    def send_email_reminder(self, appointment_id):
        """
        Wysyła przypomnienie e-mail o wizycie.
        
        Args:
            appointment_id (int): ID wizyty
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane wizyty i klienta
            cursor.execute("""
                SELECT 
                    a.appointment_date, a.appointment_time, a.service_type,
                    c.name, c.email
                FROM 
                    appointments a
                JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.id = ?
            """, (appointment_id,))
            
            result = cursor.fetchone()
            if not result:
                NotificationManager.get_instance().show_notification(
                    "Nie znaleziono danych wizyty.",
                    NotificationTypes.ERROR
                )
                return
            
            appointment_date, appointment_time, service_type, client_name, client_email = result
            
            if not client_email:
                NotificationManager.get_instance().show_notification(
                    f"Klient {client_name} nie ma adresu e-mail.",
                    NotificationTypes.WARNING
                )
                return
            
            # Przygotowanie treści e-maila
            email_subject = f"Przypomnienie o wizycie w serwisie"
            email_body = f"""Szanowny/a {client_name},

Przypominamy o zaplanowanej wizycie w naszym serwisie:

Data: {appointment_date}
Godzina: {appointment_time}
Usługa: {service_type}

W razie pytań lub konieczności zmiany terminu prosimy o kontakt.

Z poważaniem,
Zespół Serwisu Opon MATEO
"""
            
            # Otwarcie okna do wysłania e-maila
            from ui.dialogs.send_email_dialog import SendEmailDialog
            dialog = SendEmailDialog(
                self.conn, 
                appointment_id, 
                email_to=client_email,
                email_subject=email_subject,
                email_body=email_body,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania przypomnienia e-mail: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania przypomnienia e-mail: {str(e)}",
                NotificationTypes.ERROR
            )
    
    def send_sms_reminder(self, appointment_id):
        """
        Wysyła przypomnienie SMS o wizycie.
        
        Args:
            appointment_id (int): ID wizyty
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane wizyty i klienta
            cursor.execute("""
                SELECT 
                    a.appointment_date, a.appointment_time, a.service_type,
                    c.name, c.phone_number
                FROM 
                    appointments a
                JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.id = ?
            """, (appointment_id,))
            
            result = cursor.fetchone()
            if not result:
                NotificationManager.get_instance().show_notification(
                    "Nie znaleziono danych wizyty.",
                    NotificationTypes.ERROR
                )
                return
            
            appointment_date, appointment_time, service_type, client_name, phone_number = result
            
            if not phone_number:
                NotificationManager.get_instance().show_notification(
                    f"Klient {client_name} nie ma numeru telefonu.",
                    NotificationTypes.WARNING
                )
                return
            
            # Przygotowanie treści SMS
            sms_text = f"Przypomnienie: {client_name}, masz wizytę {appointment_date} o {appointment_time} - {service_type}. Pozdrawiamy, Serwis Opon MATEO"
            
            # Otwarcie okna do wysłania SMS
            from ui.dialogs.send_sms_dialog import SendSMSDialog
            dialog = SendSMSDialog(
                self.conn, 
                appointment_id,
                phone_number=phone_number,
                sms_text=sms_text,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania przypomnienia SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania przypomnienia SMS: {str(e)}",
                NotificationTypes.ERROR
            )