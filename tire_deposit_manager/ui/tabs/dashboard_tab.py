#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł z zakładką Pulpit dla aplikacji Menadżer Serwisu Opon.
Zmodernizowana wersja z lepszym wyglądem i responsywnością.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QIcon, QColor, QFont
from PySide6.QtCore import Qt, QSize, QTimer

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class CustomFrame(QFrame):
    """Niestandardowa ramka do wyświetlania danych statystycznych."""
    
    def __init__(self, title, value, change="", bg_color="#3498db", parent=None):
        """
        Inicjalizacja ramki.
        
        Args:
            title (str): Tytuł ramki
            value (str): Główna wartość do wyświetlenia
            change (str, optional): Informacja o zmianie/trendzie
            bg_color (str, optional): Kolor tła
            parent (QWidget, optional): Widget nadrzędny
        """
        super().__init__(parent)
        
        # Ustawienie właściwości ramki
        self.setProperty("dashboard", "true")  # Dla celów stylizacji
        self.setMinimumHeight(130)  # Zwiększona wysokość dla lepszego wyglądu
        self.setStyleSheet(f"background-color: {bg_color}; border-radius: 8px; padding: 10px;")
        
        # Układ pionowy dla elementów
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Większe marginesy wewnętrzne
        layout.setSpacing(5)  # Odstęp między elementami
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setProperty("dashboard", "title")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        # Wartość
        value_label = QLabel(value)
        value_label.setProperty("dashboard", "value")
        value_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        
        # Dodaj referencję, aby móc później aktualizować
        self.value_label = value_label
        
        # Zmiana/trend
        if change:
            change_label = QLabel(change)
            change_label.setProperty("dashboard", "change")
            change_label.setStyleSheet("color: white; font-size: 14px;")
            layout.addWidget(change_label, 0, Qt.AlignRight)
            
            # Dodaj referencję, aby móc później aktualizować
            self.change_label = change_label
        
        # Dodanie elementów do układu
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()  # Elastyczne wypełnienie
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def update_values(self, value, change=None):
        """Aktualizuje wyświetlane wartości w ramce."""
        self.value_label.setText(str(value))
        if change is not None and hasattr(self, 'change_label'):
            self.change_label.setText(change)

class DashboardTab(QWidget):
    """Zakładka Pulpit w aplikacji Menadżer Serwisu Opon"""
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki Pulpit.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Inicjalizacja interfejsu
        self.init_ui()
        
        # Wczytanie danych
        self.load_data()
        
        # Timer do automatycznego odświeżania co 5 minut
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # 5 minut w milisekundach
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        # Główny układ
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Obszar przewijania dla lepszej responsywności
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Widget zawartości do przewijania
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # Sekcja 1: Kafelki z danymi statystycznymi
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)  # Większy odstęp między kafelkami
        
        # Kafelek: Klienci
        self.clients_frame = CustomFrame(
            "Klienci", 
            "0", 
            "+1.2% wzrost", 
            "#3498db"
        )
        
        # Kafelek: Aktywne depozyty
        self.deposits_frame = CustomFrame(
            "Aktywne depozyty", 
            "0", 
            "+0.7% wzrost", 
            "#27ae60"
        )
        
        # Kafelek: Opony na stanie
        self.tires_frame = CustomFrame(
            "Opony na stanie", 
            "0", 
            "+1.2% wzrost", 
            "#f39c12"
        )
        
        # Kafelek: Zaplanowane wizyty
        self.visits_frame = CustomFrame(
            "Zaplanowane wizyty", 
            "0", 
            "+0.0% wzrost", 
            "#e74c3c"
        )
        
        # Dodanie kafelków do układu statystyk
        stats_layout.addWidget(self.clients_frame)
        stats_layout.addWidget(self.deposits_frame)
        stats_layout.addWidget(self.tires_frame)
        stats_layout.addWidget(self.visits_frame)
        
        # Sekcja 2: Dodatkowe kafelki (części i akcesoria)
        parts_frame = CustomFrame(
            "Części i akcesoria", 
            "0", 
            "Aż 24% stali magazynowej to części nowe", 
            "#9b59b6"
        )
        parts_frame.setMinimumHeight(100)  # Nieco niższy kafelek
        
        # Sekcja 3: Tabele z danymi
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(15)  # Większy odstęp między tabelami
        
        # Panel nadchodzących wizyt
        visits_panel = QWidget()
        visits_layout = QVBoxLayout(visits_panel)
        visits_layout.setContentsMargins(0, 0, 0, 0)
        visits_layout.setSpacing(10)
        
        # Etykieta z tytułem sekcji
        visits_title = QLabel("Nadchodzące wizyty")
        visits_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        visits_layout.addWidget(visits_title)
        
        # Tabela z nadchodzącymi wizytami
        self.visits_table = QTableWidget(0, 4)
        self.visits_table.setHorizontalHeaderLabels(["Klient", "Telefon", "Data i godzina", "Status"])
        self.visits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.visits_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.visits_table.setAlternatingRowColors(True)
        self.visits_table.verticalHeader().setVisible(False)
        visits_layout.addWidget(self.visits_table)
        
        # Przycisk "Zobacz wszystkie"
        see_all_visits_btn = QPushButton("Zobacz wszystkie")
        see_all_visits_btn.setObjectName("seeAllButton")
        see_all_visits_btn.setMinimumHeight(35)  # Wyższy przycisk
        visits_layout.addWidget(see_all_visits_btn, 0, Qt.AlignRight)
        
        # Panel ostatnich działań
        actions_panel = QWidget()
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        
        # Etykieta z tytułem sekcji
        actions_title = QLabel("Ostatnie działania")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        actions_layout.addWidget(actions_title)
        
        # Tabela z ostatnimi działaniami
        self.actions_table = QTableWidget(0, 4)
        self.actions_table.setHorizontalHeaderLabels(["Użytkownik", "Działanie", "Data", "Status"])
        self.actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.actions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.actions_table.setAlternatingRowColors(True)
        self.actions_table.verticalHeader().setVisible(False)
        actions_layout.addWidget(self.actions_table)
        
        # Przycisk "Zobacz wszystkie"
        see_all_actions_btn = QPushButton("Zobacz wszystkie")
        see_all_actions_btn.setObjectName("seeAllButton")
        see_all_actions_btn.setMinimumHeight(35)  # Wyższy przycisk
        actions_layout.addWidget(see_all_actions_btn, 0, Qt.AlignRight)
        
        # Dodanie paneli do układu tabel
        tables_layout.addWidget(visits_panel)
        tables_layout.addWidget(actions_panel)
        
        # Sekcja 4: Skróty akcji - Quick Access
        shortcuts_title = QLabel("Szybkie akcje")
        shortcuts_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        
        shortcuts_grid = QGridLayout()
        shortcuts_grid.setSpacing(15)  # Większy odstęp między przyciskami
        
        # Przyciski szybkich akcji - większe, bardziej wyraziste
        shortcut_buttons = [
            {"icon": "👤", "text": "Dodaj klienta", "slot": self.add_client, "color": "#2980b9"},
            {"icon": "📦", "text": "Nowy depozyt", "slot": self.add_deposit, "color": "#27ae60"},
            {"icon": "📝", "text": "Zaplanuj wizytę", "slot": self.schedule_visit, "color": "#e74c3c"},
            {"icon": "📊", "text": "Generuj raport", "slot": self.generate_report, "color": "#9b59b6"}
        ]
        
        # Utworzenie przycisków w układzie siatki 2x2
        for i, btn_info in enumerate(shortcut_buttons):
            row, col = divmod(i, 2)
            
            btn = QPushButton(f"{btn_info['icon']} {btn_info['text']}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_info['color']};
                    color: white;
                    font-size: 15px;
                    font-weight: bold;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {btn_info['color']}cc;  /* Dodanie przezroczystości dla efektu hover */
                }}
            """)
            btn.setMinimumHeight(80)  # Wyższy przycisk
            btn.clicked.connect(btn_info['slot'])
            
            shortcuts_grid.addWidget(btn, row, col)
        
        # Dodanie sekcji do głównego układu
        scroll_layout.addLayout(stats_layout)
        scroll_layout.addWidget(parts_frame)
        scroll_layout.addLayout(tables_layout)
        scroll_layout.addWidget(shortcuts_title)
        scroll_layout.addLayout(shortcuts_grid)
        scroll_layout.addStretch()  # Elastyczne wypełnienie na końcu
        
        # Finalizacja obszaru przewijania
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def load_data(self):
        """Ładuje i wyświetla dane na pulpicie."""
        try:
            # Pobranie i wyświetlenie liczby klientów
            self.load_clients_count()
            
            # Pobranie i wyświetlenie liczby aktywnych depozytów
            self.load_deposits_count()
            
            # Pobranie i wyświetlenie liczby opon na stanie
            self.load_tires_count()
            
            # Pobranie i wyświetlenie liczby zaplanowanych wizyt
            self.load_visits_count()
            
            # Pobranie i wyświetlenie nadchodzących wizyt
            self.load_upcoming_visits()
            
            # Pobranie i wyświetlenie ostatnich działań
            self.load_recent_activities()
        except Exception as e:
            logger.error(f"Błąd ładowania danych pulpitu: {e}")
    
    def load_clients_count(self):
        """Pobiera i wyświetla liczbę klientów."""
        try:
            cursor = self.conn.cursor()
            
            # Uproszczone zapytanie - tylko pobiera liczbę klientów
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]
            
            # Aktualizuj ramkę z danymi statystycznymi
            self.clients_frame.update_values(clients_count, "+1.2% wzrost")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania liczby klientów: {e}")
    
    def load_deposits_count(self):
        """Pobiera i wyświetla liczbę aktywnych depozytów."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdzamy, czy kolumna status istnieje
            cursor.execute("PRAGMA table_info(deposits)")
            columns = cursor.fetchall()
            has_status = any(col[1] == 'status' for col in columns)
            
            # Jeśli istnieje kolumna status, filtrujemy po Aktywny, w przeciwnym razie pobieramy wszystkie
            if has_status:
                cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
            else:
                cursor.execute("SELECT COUNT(*) FROM deposits")
            
            deposits_count = cursor.fetchone()[0]
            
            # Aktualizuj ramkę z danymi statystycznymi
            self.deposits_frame.update_values(deposits_count, "+0.7% wzrost")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania liczby depozytów: {e}")
    
    def load_tires_count(self):
        """Pobiera i wyświetla liczbę opon na stanie."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdzamy czy tabela inventory istnieje
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM inventory")
                tires_count = cursor.fetchone()[0]
            else:
                tires_count = 0
            
            # Aktualizuj ramkę z danymi statystycznymi
            self.tires_frame.update_values(tires_count, "+1.2% wzrost")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania liczby opon: {e}")
    
    def load_visits_count(self):
        """Pobiera i wyświetla liczbę zaplanowanych wizyt."""
        try:
            # Sprawdzamy, czy tabela appointments istnieje
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
            
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM appointments")
                visits_count = cursor.fetchone()[0]
            else:
                visits_count = 0
            
            # Aktualizuj ramkę z danymi statystycznymi
            self.visits_frame.update_values(visits_count, "+0.0% wzrost")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania liczby wizyt: {e}")
    
    def load_upcoming_visits(self):
        """Pobiera i wyświetla nadchodzące wizyty."""
        try:
            # Wyczyszczenie tabeli
            self.visits_table.setRowCount(0)
            
            # Sprawdzamy, czy tabela appointments istnieje
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
            
            if cursor.fetchone():
                # Sprawdzamy dostępne kolumny
                cursor.execute("PRAGMA table_info(appointments)")
                appointment_columns = [col[1] for col in cursor.fetchall()]
                
                cursor.execute("PRAGMA table_info(clients)")
                client_columns = [col[1] for col in cursor.fetchall()]
                
                # Jeśli brak danych lub brak wymaganych kolumn, wyświetlamy informację
                if not appointment_columns or not client_columns:
                    self.visits_table.insertRow(0)
                    info_item = QTableWidgetItem("Brak danych o wizytach")
                    info_item.setTextAlignment(Qt.AlignCenter)
                    self.visits_table.setSpan(0, 0, 1, 4)  # Połącz komórki
                    self.visits_table.setItem(0, 0, info_item)
                    return
                
                # Dopasowujemy zapytanie do dostępnych kolumn
                if 'client_id' in appointment_columns and 'id' in client_columns and 'name' in client_columns:
                    # Pobieramy podstawowe dane
                    cursor.execute("""
                        SELECT c.name, '' as phone, 'Data nieznana' as date, 'Oczekująca' as status 
                        FROM appointments a
                        JOIN clients c ON a.client_id = c.id
                        LIMIT 5
                    """)
                    
                    visits = cursor.fetchall()
                    
                    # Wypełniamy tabelę dostępnymi danymi
                    for i, (name, phone, date, status) in enumerate(visits):
                        self.visits_table.insertRow(i)
                        self.visits_table.setItem(i, 0, QTableWidgetItem(name))
                        self.visits_table.setItem(i, 1, QTableWidgetItem(phone))
                        self.visits_table.setItem(i, 2, QTableWidgetItem(date))
                        
                        status_item = QTableWidgetItem(status)
                        if status == "Potwierdzona":
                            status_item.setForeground(QColor("#27ae60"))  # Zielony
                        elif status == "Oczekująca":
                            status_item.setForeground(QColor("#f39c12"))  # Pomarańczowy
                        elif status == "Anulowana":
                            status_item.setForeground(QColor("#e74c3c"))  # Czerwony
                        
                        self.visits_table.setItem(i, 3, status_item)
                else:
                    # Brak wymaganych relacji między tabelami
                    self.visits_table.insertRow(0)
                    info_item = QTableWidgetItem("Brak odpowiednich danych o wizytach")
                    info_item.setTextAlignment(Qt.AlignCenter)
                    self.visits_table.setSpan(0, 0, 1, 4)  # Połącz komórki
                    self.visits_table.setItem(0, 0, info_item)
            else:
                # Brak tabeli wizyt
                self.visits_table.insertRow(0)
                info_item = QTableWidgetItem("Tabela wizyt nie istnieje")
                info_item.setTextAlignment(Qt.AlignCenter)
                self.visits_table.setSpan(0, 0, 1, 4)  # Połącz komórki
                self.visits_table.setItem(0, 0, info_item)
        except Exception as e:
            logger.error(f"Błąd podczas ładowania nadchodzących wizyt: {e}")
            # Wyświetl informację o błędzie
            self.visits_table.insertRow(0)
            info_item = QTableWidgetItem(f"Błąd ładowania danych: {str(e)}")
            info_item.setTextAlignment(Qt.AlignCenter)
            self.visits_table.setSpan(0, 0, 1, 4)  # Połącz komórki
            self.visits_table.setItem(0, 0, info_item)
    
    def load_recent_activities(self):
        """Pobiera i wyświetla ostatnie działania."""
        try:
            # Wyczyszczenie tabeli
            self.actions_table.setRowCount(0)
            
            # Sprawdzamy, czy tabela activities istnieje
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
            
            if cursor.fetchone():
                # Sprawdzamy dostępne kolumny
                cursor.execute("PRAGMA table_info(activities)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Budujemy dynamiczne zapytanie na podstawie dostępnych kolumn
                select_fields = []
                if 'user' in columns:
                    select_fields.append('user')
                else:
                    select_fields.append("'System' as user")
                
                if 'action' in columns:
                    select_fields.append('action')
                else:
                    select_fields.append("'Akcja' as action")
                
                if 'date' in columns:
                    select_fields.append('date')
                else:
                    select_fields.append("'Nieznana data' as date")
                
                # Sprawdzamy, czy istnieje kolumna status lub podobna
                status_column = next((col for col in columns if col.lower() in ['status', 'order', 'type']), None)
                if status_column:
                    select_fields.append(status_column)
                else:
                    select_fields.append("'Status' as status")
                
                query = f"SELECT {', '.join(select_fields)} FROM activities LIMIT 5"
                cursor.execute(query)
                
                activities = cursor.fetchall()
                
                # Wypełnienie tabeli danymi
                for i, row in enumerate(activities):
                    self.actions_table.insertRow(i)
                    for j, value in enumerate(row):
                        self.actions_table.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                # Brak tabeli aktywności - wyświetlamy przykładowe dane
                example_activities = [
                    ["System", "Utworzenie konta", datetime.now().strftime("%Y-%m-%d"), "Zakończone"],
                    ["Admin", "Dodanie klienta", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "Zakończone"]
                ]
                
                for i, (user, action, date, status) in enumerate(example_activities):
                    self.actions_table.insertRow(i)
                    self.actions_table.setItem(i, 0, QTableWidgetItem(user))
                    self.actions_table.setItem(i, 1, QTableWidgetItem(action))
                    self.actions_table.setItem(i, 2, QTableWidgetItem(date))
                    
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(QColor("#27ae60"))  # Zielony
                    self.actions_table.setItem(i, 3, status_item)
                
                # Dodaj informacyjny wiersz
                self.actions_table.insertRow(2)
                info_item = QTableWidgetItem("Przykładowe dane (tabela aktywności nie istnieje)")
                info_item.setTextAlignment(Qt.AlignCenter)
                self.actions_table.setSpan(2, 0, 1, 4)  # Połącz komórki
                self.actions_table.setItem(2, 0, info_item)
        except Exception as e:
            logger.error(f"Błąd podczas ładowania ostatnich działań: {e}")
            # Wyświetl informację o błędzie
            self.actions_table.setRowCount(0)
            self.actions_table.insertRow(0)
            info_item = QTableWidgetItem(f"Błąd ładowania danych: {str(e)}")
            info_item.setTextAlignment(Qt.AlignCenter)
            self.actions_table.setSpan(0, 0, 1, 4)  # Połącz komórki
            self.actions_table.setItem(0, 0, info_item)
    
    def refresh_data(self):
        """Odświeża wszystkie dane na pulpicie."""
        self.load_data()
    
    def search(self, text):
        """Obsługuje wyszukiwanie na zakładce pulpitu."""
        # Implementacja wyszukiwania wg tekstu
        pass
    
    # Sloty dla przycisków szybkich akcji
    def add_client(self):
        """Slot dla przycisku 'Dodaj klienta'."""
        # Wywołanie odpowiedniego widoku/formularza
        from ui.dialogs.client_dialog import ClientDialog
        dialog = ClientDialog(self.conn, parent=self)
        dialog.exec()
    
    def add_deposit(self):
        """Slot dla przycisku 'Nowy depozyt'."""
        # Wywołanie odpowiedniego widoku/formularza
        pass
    
    def schedule_visit(self):
        """Slot dla przycisku 'Zaplanuj wizytę'."""
        # Wywołanie odpowiedniego widoku/formularza
        pass
    
    def generate_report(self):
        """Slot dla przycisku 'Generuj raport'."""
        # Wywołanie odpowiedniego widoku/formularza
        pass