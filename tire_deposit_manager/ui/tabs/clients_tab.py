#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka klientów - nowoczesny interfejs zarządzania listą klientów w aplikacji.
Umożliwia zarządzanie klientami oraz przypisanymi do nich pojazdami.
"""

import os
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QMenu,
    QComboBox, QFrame, QTabWidget, QSplitter, QToolButton, QScrollArea,
    QSpacerItem, QSizePolicy, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter

from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.client_details_dialog import ClientDetailsDialog
from ui.dialogs.vehicle_dialog import VehicleDialog  # Nowy dialog do dodawania pojazdów
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class StatusDelegate(QStyledItemDelegate):
    """
    Delegat do stylizowania komórek statusu w tabeli klientów.
    """
    def paint(self, painter, option, index):
        status = index.data()
        
        if status == "Stały":
            background_color = QColor("#51cf66")
            text_color = QColor(255, 255, 255)
        elif status == "Nowy":
            background_color = QColor("#ffa94d")
            text_color = QColor(255, 255, 255)
        elif status == "Firma":
            background_color = QColor("#4dabf7")
            text_color = QColor(255, 255, 255)
        else:
            # Domyślne kolory
            background_color = QColor("#2c3034")
            text_color = QColor(255, 255, 255)
        
        # Rysowanie zaokrąglonego prostokąta
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(background_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(option.rect.adjusted(4, 4, -4, -4), 10, 10)
        
        # Rysowanie tekstu
        painter.setPen(text_color)
        painter.drawText(
            option.rect, 
            Qt.AlignCenter, 
            status
        )
        painter.restore()

class ActionButtonDelegate(QStyledItemDelegate):
    """
    Delegat do wyświetlania przycisków akcji z emotikonami w tabeli.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        painter.save()
        
        # Obliczenie szerokości każdego przycisku
        button_width = min(option.rect.width() / 3, 30)
        
        # Obszary dla każdego przycisku
        view_rect = option.rect.adjusted(
            option.rect.width() / 2 - button_width * 1.5,
            option.rect.height() / 2 - 12, 
            option.rect.width() / 2 - button_width * 0.5, 
            option.rect.height() / 2 + 12
        )
        
        edit_rect = option.rect.adjusted(
            option.rect.width() / 2 - button_width * 0.5,
            option.rect.height() / 2 - 12, 
            option.rect.width() / 2 + button_width * 0.5, 
            option.rect.height() / 2 + 12
        )
        
        delete_rect = option.rect.adjusted(
            option.rect.width() / 2 + button_width * 0.5,
            option.rect.height() / 2 - 12, 
            option.rect.width() / 2 + button_width * 1.5, 
            option.rect.height() / 2 + 12
        )
        
        # Rysowanie emotikon zamiast ikon
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(Qt.white)
        
        # Emotikona "👁️" dla podglądu
        painter.drawText(view_rect, Qt.AlignCenter, "👁️")
        
        # Emotikona "✏️" dla edycji
        painter.drawText(edit_rect, Qt.AlignCenter, "✏️")
        
        # Emotikona "🗑️" dla usuwania
        painter.drawText(delete_rect, Qt.AlignCenter, "🗑️")
        
        painter.restore()
        
    def editorEvent(self, event, model, option, index):
        # Obsługa kliknięć
        if event.type() == QEvent.Type.MouseButtonRelease:
            # Obliczenie szerokości każdego przycisku
            button_width = min(option.rect.width() / 3, 30)
            
            # Obszary dla każdego przycisku
            view_rect = option.rect.adjusted(
                option.rect.width() / 2 - button_width * 1.5,
                option.rect.height() / 2 - 12, 
                option.rect.width() / 2 - button_width * 0.5, 
                option.rect.height() / 2 + 12
            )
            
            edit_rect = option.rect.adjusted(
                option.rect.width() / 2 - button_width * 0.5,
                option.rect.height() / 2 - 12, 
                option.rect.width() / 2 + button_width * 0.5, 
                option.rect.height() / 2 + 12
            )
            
            delete_rect = option.rect.adjusted(
                option.rect.width() / 2 + button_width * 0.5,
                option.rect.height() / 2 - 12, 
                option.rect.width() / 2 + button_width * 1.5, 
                option.rect.height() / 2 + 12
            )
            
            if view_rect.contains(event.pos()):
                # Wywołanie sygnału podglądu
                self.parent().view_client_requested.emit(index.row())
                return True
            elif edit_rect.contains(event.pos()):
                # Wywołanie sygnału edycji
                self.parent().edit_client_requested.emit(index.row())
                return True
            elif delete_rect.contains(event.pos()):
                # Wywołanie sygnału usuwania
                self.parent().delete_client_requested.emit(index.row())
                return True
                
        return super().editorEvent(event, model, option, index)

class ClientsTable(QTableWidget):
    """
    Tabela klientów z obsługą akcji.
    """
    view_client_requested = Signal(int)
    edit_client_requested = Signal(int)
    delete_client_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Ustawienia tabeli
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        
        # Delegaty
        self.setItemDelegateForColumn(6, StatusDelegate(self))  # Kolumna "Typ"
        self.setItemDelegateForColumn(7, ActionButtonDelegate(self))  # Kolumna "Akcje"
        
        # Opcje wyglądu
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "ID", "Nazwisko i imię", "Telefon", "Email", "Nr rejestracyjny", "Pojazdy", "Typ", "Akcje"
        ])
        
        # Ustawienie rozciągania kolumn
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Pojazdy
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Typ
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Akcje
        
        # Wysokość wiersza
        self.verticalHeader().setDefaultSectionSize(50)

class ClientsTab(QWidget):
    """
    Zakładka zarządzania klientami w aplikacji.
    Wyświetla listę klientów, umożliwia dodawanie, edycję i usuwanie.
    Dodatkowo umożliwia przypisywanie pojazdów do klientów.
    """
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki klientów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.filtered_type = "Wszyscy"
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie danych klientów
        self.load_clients()
        
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Nagłówek z tytułem i przyciskiem dodawania
        header_layout = QHBoxLayout()
        
        # Tytuł
        title_label = QLabel("Klienci")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch(1)
        
        # Przycisk dodawania z emotikoną
        self.add_button = QPushButton("➕ Nowy klient")
        self.add_button.setObjectName("addButton")
        self.add_button.setMinimumWidth(150)
        self.add_button.clicked.connect(self.add_client)
        header_layout.addWidget(self.add_button)
        
        main_layout.addLayout(header_layout)
        
        # Panel wyszukiwania i filtrów
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Pole wyszukiwania z emotikoną
        search_box = QFrame()
        search_box.setObjectName("searchBox")
        search_box.setFixedHeight(40)
        search_box.setMinimumWidth(400)
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 10, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setFixedWidth(20)
        search_box_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Szukaj według nazwiska, telefonu lub nr rejestracyjnego...")
        self.search_input.textChanged.connect(self.filter_clients)
        search_box_layout.addWidget(self.search_input)
        
        search_layout.addWidget(search_box)
        
        # Combobox filtrów typu klienta
        type_layout = QHBoxLayout()
        type_label = QLabel("Typ:")
        type_label.setMinimumWidth(40)
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("filterCombo")
        self.type_combo.setFixedHeight(40)
        self.type_combo.setMinimumWidth(150)
        self.type_combo.addItems(["Wszyscy", "Indywidualni", "Firmowi", "Stali", "Nowi"])
        self.type_combo.currentTextChanged.connect(self.change_client_type_filter)
        type_layout.addWidget(self.type_combo)
        
        search_layout.addLayout(type_layout)
        
        # Combobox sortowania
        sort_layout = QHBoxLayout()
        sort_label = QLabel("Sortuj:")
        sort_label.setMinimumWidth(50)
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("filterCombo")
        self.sort_combo.setFixedHeight(40)
        self.sort_combo.setMinimumWidth(150)
        self.sort_combo.addItems(["Nazwisko", "Data dodania", "Liczba pojazdów"])
        self.sort_combo.currentTextChanged.connect(self.apply_sorting)
        sort_layout.addWidget(self.sort_combo)
        
        search_layout.addLayout(sort_layout)
        
        # Przycisk filtrowania z emotikoną
        self.filter_button = QPushButton("🔍 Filtruj")
        self.filter_button.setObjectName("filterButton")
        self.filter_button.setFixedHeight(40)
        self.filter_button.setMinimumWidth(100)
        self.filter_button.clicked.connect(self.apply_filters)
        search_layout.addWidget(self.filter_button)
        
        main_layout.addWidget(search_panel)
        
        # Zakładki z typami klientów
        self.tabs_widget = QTabWidget()
        self.tabs_widget.setObjectName("clientTypeTabs")
        self.tabs_widget.setTabPosition(QTabWidget.North)
        self.tabs_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #2c3034;
                padding: 10px 20px;
                margin-right: 5px;
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected {
                background: #4dabf7;
                font-weight: bold;
            }
        """)
        
        # Tworzenie zakładek
        self.all_tab = QWidget()
        self.individual_tab = QWidget()
        self.company_tab = QWidget()
        self.regular_tab = QWidget()
        self.new_tab = QWidget()
        
        # Dodanie zakładek do widgetu
        self.tabs_widget.addTab(self.all_tab, "Wszyscy (0)")
        self.tabs_widget.addTab(self.individual_tab, "Indywidualni (0)")
        self.tabs_widget.addTab(self.company_tab, "Firmowi (0)")
        self.tabs_widget.addTab(self.regular_tab, "Stali (0)")
        self.tabs_widget.addTab(self.new_tab, "Nowi (0)")
        
        # Layouts dla każdej zakładki
        self.setup_tab_content(self.all_tab)
        self.setup_tab_content(self.individual_tab)
        self.setup_tab_content(self.company_tab)
        self.setup_tab_content(self.regular_tab)
        self.setup_tab_content(self.new_tab)
        
        # Połączenie zmiany zakładki z filtrowaniem
        self.tabs_widget.currentChanged.connect(self.tab_changed)
        
        main_layout.addWidget(self.tabs_widget)
        
        # Panel nawigacji stron
        pagination_layout = QHBoxLayout()
        
        # Informacja o liczbie wyświetlanych rekordów
        self.records_info = QLabel("Wyświetlanie 0 z 0 rekordów")
        pagination_layout.addWidget(self.records_info)
        
        pagination_layout.addStretch(1)
        
        # Przyciski nawigacji z emotikonami
        self.prev_button = QPushButton("⬅️")
        self.prev_button.setFixedSize(40, 40)
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_1_button = QPushButton("1")
        self.page_1_button.setFixedSize(40, 40)
        self.page_1_button.setObjectName("currentPageButton")
        pagination_layout.addWidget(self.page_1_button)
        
        self.page_2_button = QPushButton("2")
        self.page_2_button.setFixedSize(40, 40)
        pagination_layout.addWidget(self.page_2_button)
        
        self.page_3_button = QPushButton("3")
        self.page_3_button.setFixedSize(40, 40)
        pagination_layout.addWidget(self.page_3_button)
        
        self.next_button = QPushButton("➡️")
        self.next_button.setFixedSize(40, 40)
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        pagination_layout.addStretch(1)
        
        # Przyciski importu/eksportu z emotikonami
        self.import_button = QPushButton("📥 Import klientów")
        self.import_button.clicked.connect(self.import_clients)
        pagination_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("📤 Eksport listy")
        self.export_button.clicked.connect(self.export_clients)
        pagination_layout.addWidget(self.export_button)
        
        main_layout.addLayout(pagination_layout)
    

    def setup_tab_content(self, tab):
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 10, 0, 0)
        
        # Tworzenie tabeli klientów
        clients_table = ClientsTable()
        clients_table.customContextMenuRequested.connect(self.show_context_menu)
        clients_table.doubleClicked.connect(self.view_client_details)
        
        # Podłączenie sygnałów akcji
        clients_table.view_client_requested.connect(self.handle_view_client)
        clients_table.edit_client_requested.connect(self.handle_edit_client)
        clients_table.delete_client_requested.connect(self.handle_delete_client)
        
        # Zapisanie referencji do tabeli jako atrybut tab
        tab.clients_table = clients_table
        
        tab_layout.addWidget(clients_table)
    
    def add_vehicle_to_client(self, client_id, client_name):
        """
        Dodaje nowy pojazd do wybranego klienta.
        
        Args:
            client_id (int): ID klienta
            client_name (str): Nazwa klienta
        """
        # Tutaj otwieramy dialog dodawania pojazdu
        try:
            dialog = VehicleDialog(self.conn, client_id=client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów, aby pokazać nowy pojazd
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"🚗 Dodano nowy pojazd dla klienta: {client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas dodawania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Nie można dodać pojazdu:\n{str(e)}"
            )
    
    def refresh_data(self):
        """Odświeża listę klientów."""
        self.load_clients()
        
        # Możemy teraz uzyskać dostęp do tabel przez atrybut każdej zakładki
        for tab in [self.all_tab, self.individual_tab, self.company_tab, self.regular_tab, self.new_tab]:
            if hasattr(tab, 'clients_table'):
                clients_table = tab.clients_table
                # Upewnij się, że sygnały są podłączone (można pominąć, jeśli są już podłączone w setup_tab_content)
                clients_table.view_client_requested.connect(self.handle_view_client)
                clients_table.edit_client_requested.connect(self.handle_edit_client)
                clients_table.delete_client_requested.connect(self.handle_delete_client)

    def load_clients(self):
        """Ładuje listę klientów z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz wszystkich klientów z informacjami o przypisanych pojazdach
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.phone_number, c.email, c.client_type, c.discount, c.additional_info,
                    (SELECT COUNT(*) FROM vehicles WHERE client_id = c.id) as vehicle_count,
                    (SELECT GROUP_CONCAT(registration_number, ', ') FROM vehicles WHERE client_id = c.id) as registration_numbers,
                    c.created_at
                FROM clients c
                ORDER BY c.name
            """)
            
            clients = cursor.fetchall()
            
            # Zmienne do śledzenia liczby klientów według typu
            all_count = len(clients)
            individual_count = 0
            company_count = 0
            regular_count = 0
            new_count = 0
            
            # Wypełnienie tabeli na aktywnej zakładce
            active_tab_index = self.tabs_widget.currentIndex()
            active_tab = self.tabs_widget.widget(active_tab_index)
            
            table = active_tab.findChild(QTableWidget)
            if table:
                # Czyszczenie tabeli
                table.setRowCount(0)
                
                # Wypełnienie tabeli
                for client in clients:
                    client_id, name, phone, email, client_type, discount, info, vehicle_count, reg_numbers, created_at = client
                    
                    # Zliczanie klientów według typów
                    if client_type == "Indywidualny":
                        individual_count += 1
                    elif client_type == "Firma":
                        company_count += 1
                    
                    if discount and discount > 0:
                        regular_count += 1
                    else:
                        new_count += 1
                    
                    # Filtrowanie według aktywnej zakładki
                    include_in_tab = True
                    if active_tab_index == 1 and client_type != "Indywidualny":  # Indywidualni
                        include_in_tab = False
                    elif active_tab_index == 2 and client_type != "Firma":  # Firmowi
                        include_in_tab = False
                    elif active_tab_index == 3 and (not discount or discount <= 0):  # Stali
                        include_in_tab = False
                    elif active_tab_index == 4 and discount and discount > 0:  # Nowi
                        include_in_tab = False
                    
                    if include_in_tab:
                        row = table.rowCount()
                        table.insertRow(row)
                        
                        # ID
                        id_item = QTableWidgetItem(str(client_id))
                        id_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 0, id_item)
                        
                        # Nazwa
                        table.setItem(row, 1, QTableWidgetItem(name))
                        
                        # Telefon
                        phone_item = QTableWidgetItem(phone if phone else "-")
                        phone_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 2, phone_item)
                        
                        # Email
                        email_item = QTableWidgetItem(email if email else "-")
                        table.setItem(row, 3, email_item)
                        
                        # Nr rejestracyjny (pierwszy z listy)
                        reg_number = "-"
                        if reg_numbers:
                            reg_numbers_list = reg_numbers.split(", ")
                            if reg_numbers_list and reg_numbers_list[0]:
                                reg_number = reg_numbers_list[0]
                        
                        reg_item = QTableWidgetItem(reg_number)
                        reg_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 4, reg_item)
                        
                        # Liczba pojazdów
                        vehicles_item = QTableWidgetItem(str(vehicle_count))
                        vehicles_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 5, vehicles_item)
                        
                        # Typ klienta
                        client_type_display = "Nowy"
                        if discount and discount > 0:
                            client_type_display = "Stały"
                        if client_type == "Firma":
                            client_type_display = "Firma"
                            
                        type_item = QTableWidgetItem(client_type_display)
                        type_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 6, type_item)
                        
                        # Akcje (puste - renderowane przez delegata)
                        table.setItem(row, 7, QTableWidgetItem(""))
            
            # Aktualizacja liczby klientów w zakładkach
            self.tabs_widget.setTabText(0, f"Wszyscy ({all_count})")
            self.tabs_widget.setTabText(1, f"Indywidualni ({individual_count})")
            self.tabs_widget.setTabText(2, f"Firmowi ({company_count})")
            self.tabs_widget.setTabText(3, f"Stali ({regular_count})")
            self.tabs_widget.setTabText(4, f"Nowi ({new_count})")
            
            # Aktualizacja informacji o liczbie rekordów
            current_count = table.rowCount() if table else 0
            self.records_info.setText(f"Wyświetlanie {current_count} z {all_count} rekordów")
            
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
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        
        if not table:
            return
        
        # Pokaż wszystkie wiersze, jeśli tekst jest pusty
        if not text:
            for row in range(table.rowCount()):
                table.setRowHidden(row, False)
            return
        
        # Filtruj wiersze
        for row in range(table.rowCount()):
            row_visible = False
            
            # Sprawdź kolumny nazwy, telefonu i nr rejestracyjnego
            name_item = table.item(row, 1)
            phone_item = table.item(row, 2)
            reg_item = table.item(row, 4)
            email_item = table.item(row, 3)
            
            if (name_item and text.lower() in name_item.text().lower()) or \
               (phone_item and text.lower() in phone_item.text().lower()) or \
               (reg_item and text.lower() in reg_item.text().lower()) or \
               (email_item and text.lower() in email_item.text().lower()):
                row_visible = True
            
            # Ukryj lub pokaż wiersz
            table.setRowHidden(row, not row_visible)
    
    def add_client(self):
        """Otwiera okno dodawania nowego klienta."""
        try:
            from ui.dialogs.client_dialog import ClientDialog
            dialog = ClientDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"✅ Dodano nowego klienta: {dialog.client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas dodawania klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas dodawania klienta:\n{str(e)}"
            )

    def change_client_type_filter(self, filter_type):
        """
        Zmienia aktywny filtr typu klientów.
        
        Args:
            filter_type (str): Wybrany typ klienta
        """
        # Mapowanie typu na indeks zakładki
        tab_mapping = {
            "Wszyscy": 0,
            "Indywidualni": 1,
            "Firmowi": 2,
            "Stali": 3,
            "Nowi": 4
        }
        
        # Zmiana aktywnej zakładki
        if filter_type in tab_mapping:
            self.tabs_widget.setCurrentIndex(tab_mapping[filter_type])

    def handle_view_client(self, row):
        """Obsługuje żądanie podglądu klienta."""
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        if table:
            self.view_client_details(table.model().index(row, 0))

    def handle_edit_client(self, row):
        """Obsługuje żądanie edycji klienta."""
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        if table:
            table.selectRow(row)
            self.edit_client()

    def handle_delete_client(self, row):
        """Obsługuje żądanie usunięcia klienta."""
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        if table:
            table.selectRow(row)
            self.delete_client()

    def view_client_details(self, index):
        """Wyświetla szczegóły klienta."""
        try:
            active_tab = self.tabs_widget.currentWidget()
            table = active_tab.findChild(QTableWidget)
            if table:
                row = index.row()
                client_id = int(table.item(row, 0).text())
                
                dialog = ClientDetailsDialog(self.conn, client_id, parent=self)
                dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas wyświetlania szczegółów klienta:\n{str(e)}"
            )

    def edit_client(self):
        """Otwiera okno edycji zaznaczonego klienta."""
        try:
            active_tab = self.tabs_widget.currentWidget()
            table = active_tab.findChild(QTableWidget)
            if not table:
                return
            
            selected_items = table.selectedItems()
            if not selected_items:
                QMessageBox.warning(
                    self, 
                    "Brak wyboru", 
                    "Proszę wybrać klienta do edycji."
                )
                return
            
            selected_row = selected_items[0].row()
            client_id = int(table.item(selected_row, 0).text())
            
            dialog = ClientDialog(self.conn, client_id=client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_clients()
                
                NotificationManager.get_instance().show_notification(
                    f"✅ Zaktualizowano klienta: {dialog.client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas edycji klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas edycji klienta:\n{str(e)}"
            )

    def delete_client(self):
        """Usuwa zaznaczonego klienta."""
        try:
            active_tab = self.tabs_widget.currentWidget()
            table = active_tab.findChild(QTableWidget)
            if not table:
                return
            
            selected_items = table.selectedItems()
            if not selected_items:
                QMessageBox.warning(
                    self, 
                    "Brak wyboru", 
                    "Proszę wybrać klienta do usunięcia."
                )
                return
            
            selected_row = selected_items[0].row()
            client_id = int(table.item(selected_row, 0).text())
            client_name = table.item(selected_row, 1).text()
            
            reply = QMessageBox.question(
                self, 
                "Potwierdź usunięcie", 
                f"Czy na pewno chcesz usunąć klienta {client_name}?\n\n"
                "Ta operacja jest nieodwracalna.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                self.conn.commit()
                self.load_clients()
                
                NotificationManager.get_instance().show_notification(
                    f"❌ Usunięto klienta: {client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas usuwania klienta: {e}")
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas usuwania klienta:\n{str(e)}"
            )

    def show_context_menu(self, position):
        """Wyświetla menu kontekstowe dla tabeli klientów."""
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        if not table:
            return
        
        selected_items = table.selectedItems()
        if not selected_items:
            return
        
        selected_row = selected_items[0].row()
        client_id = int(table.item(selected_row, 0).text())
        client_name = table.item(selected_row, 1).text()
        
        menu = QMenu()
        view_action = menu.addAction("👁️ Szczegóły klienta")
        edit_action = menu.addAction("✏️ Edytuj klienta")
        add_vehicle_action = menu.addAction("🚗 Dodaj pojazd")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Usuń klienta")
        
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

    def apply_filters(self):
        """Stosuje wybrane filtry do listy klientów."""
        search_text = self.search_input.text()
        if search_text:
            self.filter_clients(search_text)
        
        NotificationManager.get_instance().show_notification(
            f"Zastosowano filtry do listy klientów",
            NotificationTypes.INFO
        )

    def apply_sorting(self, sort_option):
        """Sortuje listę klientów według wybranej opcji."""
        active_tab = self.tabs_widget.currentWidget()
        table = active_tab.findChild(QTableWidget)
        if not table:
            return
        
        if sort_option == "Nazwisko":
            table.sortItems(1, Qt.AscendingOrder)
        elif sort_option == "Liczba pojazdów":
            table.sortItems(5, Qt.DescendingOrder)
        elif sort_option == "Data dodania":
            table.sortItems(0, Qt.DescendingOrder)

    def prev_page(self):
        """Przechodzi do poprzedniej strony wyników."""
        NotificationManager.get_instance().show_notification(
            "Przejście do poprzedniej strony",
            NotificationTypes.INFO
        )

    def next_page(self):
        """Przechodzi do następnej strony wyników."""
        NotificationManager.get_instance().show_notification(
            "Przejście do następnej strony",
            NotificationTypes.INFO
        )

    def import_clients(self):
        """Importuje klientów z pliku."""
        NotificationManager.get_instance().show_notification(
            "Funkcja importu klientów będzie dostępna wkrótce",
            NotificationTypes.INFO
        )

    def export_clients(self):
        """Eksportuje listę klientów do pliku."""
        NotificationManager.get_instance().show_notification(
            "Funkcja eksportu klientów będzie dostępna wkrótce",
            NotificationTypes.INFO
        )

    def tab_changed(self, index):
        """
        Obsługuje zmianę aktywnej zakładki.
        
        Args:
            index (int): Indeks nowej aktywnej zakładki
        """
        # Synchronizacja comboboxa z aktywną zakładką
        tab_mapping = {
            0: "Wszyscy",
            1: "Indywidualni",
            2: "Firmowi",
            3: "Stali",
            4: "Nowi"
        }
        
        if index in tab_mapping:
            self.type_combo.setCurrentText(tab_mapping[index])
            self.filtered_type = tab_mapping[index]
        
        #