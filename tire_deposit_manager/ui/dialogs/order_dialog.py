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
    QHeaderView, QDateEdit, QMessageBox, QCompleter, QFrame,
    QSpacerItem, QSizePolicy, QToolButton, QGroupBox, QCheckBox,
    QGridLayout, QSpinBox, QDoubleSpinBox, QWidget,
    QStyledItemDelegate, QStyle
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QIntValidator, QDoubleValidator,
    QIcon, QFont, QColor
)
from PySide6.QtCore import Qt, QDate, QSize

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR
from ui.dialogs.client_dialog import ClientDialog


class OrderDialog(QDialog):
    """Dialog dodawania i edycji zamówień z ulepszonym interfejsem"""
    
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
        
        # Inicjalizacja zmiennych, które będą używane później
        self.discount_spin = None
        self.items_table = None
        self.client_combo = None
        self.date_input = None
        self.status_combo = None
        self.notes_input = None
        self.total_amount_label = None
        self.client_info_label = None
        self.send_email_checkbox = None
        
        # Ustawienia okna
        self.setWindowTitle("Nowe zamówienie" if not order_id else "Edycja zamówienia")
        self.setMinimumSize(1100, 950)  # Zwiększone wymiary okna
        
        # Główny styl aplikacji
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
                background-color: transparent;  /* Dodane, by mieć pewność że etykiety są przezroczyste */
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
                color: #4dabf7;
            }
            QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
                min-height: 25px;
                selection-background-color: #4dabf7;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #333333;
            }
            QPushButton {
                background-color: #3d5afe;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #536dfe;
            }
            QPushButton:pressed {
                background-color: #304ffe;
            }
            QTableWidget {
                background-color: #2a2a2a;
                alternate-background-color: #303030;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a3a;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #4dabf7;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #3d5afe;
            }
            QToolButton {
                background-color: transparent;
                border: none;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #4dabf7;
            }
            QFrame#clientInfoFrame {
                background-color: #2c2c2c;
                border-radius: 6px;
                padding: 12px;
                margin-top: 8px;
                border-left: 3px solid #4dabf7;
            }
        """)
        
        # Główny layout z lepszymi marginesami
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Nagłówek z emotikoną
        header_layout = QHBoxLayout()
        header_icon = QLabel("📋")
        header_icon.setStyleSheet("font-size: 22px;")
        header_label = QLabel("Nowe zamówienie" if not order_id else f"Edycja zamówienia #{order_id}")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4dabf7;")
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #3a3a3a; max-height: 1px; margin: 10px 0px;")
        main_layout.addWidget(separator)

        # Dane zamówienia - GroupBox
        order_info_group = QGroupBox("Informacje o zamówieniu")
        order_info_group.setStyleSheet("""
            QGroupBox {
                background-color: #252525;
                padding: 15px;
            }
        """)
        order_info_layout = QGridLayout(order_info_group)
        order_info_layout.setColumnStretch(1, 2)
        order_info_layout.setVerticalSpacing(12)
        order_info_layout.setHorizontalSpacing(15)
        
        # Klient
        client_label = QLabel("Klient:")
        client_label.setStyleSheet("font-weight: bold;")
        order_info_layout.addWidget(client_label, 0, 0, Qt.AlignRight)

        # Kontener dla pola klienta i przycisku
        client_container = QWidget()
        client_layout = QHBoxLayout(client_container)
        client_layout.setContentsMargins(0, 0, 0, 0)
        client_layout.setSpacing(8)

        # Pole wyszukiwania klienta
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Wpisz, aby wyszukać klienta...")
        self.client_input.setMinimumWidth(350)
        self.client_input.setMinimumHeight(35)
        self.client_input.textChanged.connect(self.on_client_text_changed)

        # Lista klientów do autouzupełniania - zostanie wypełniona w load_clients()
        self.clients_list = []
        self.clients_data = []
        self.client_id = None

        # Załaduj klientów od razu po inicjalizacji
        self.load_clients()

        # Przycisk dodawania nowego klienta z emotikoną
        add_client_btn = QPushButton("➕ Nowy klient")
        add_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
        """)
        add_client_btn.clicked.connect(self.add_new_client)

        client_layout.addWidget(self.client_input)
        client_layout.addWidget(add_client_btn)
        order_info_layout.addWidget(client_container, 0, 1)

        # Panel informacji o kliencie
        client_info_frame = QFrame()
        client_info_frame.setObjectName("clientInfoFrame")
        client_info_layout = QVBoxLayout(client_info_frame)
        client_info_layout.setContentsMargins(12, 12, 12, 12)

        self.client_info_label = QLabel("Wybierz klienta, aby zobaczyć szczegóły")
        self.client_info_label.setWordWrap(True)
        self.client_info_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
        client_info_layout.addWidget(self.client_info_label)

        order_info_layout.addWidget(client_info_frame, 1, 0, 1, 2)
        
        # Zmniejszenie odstępu między Data a Status
        date_status_container = QWidget()
        date_status_container.setStyleSheet("background-color: transparent;")  # Usuwamy ewentualne tło
        date_status_layout = QHBoxLayout(date_status_container)
        date_status_layout.setContentsMargins(0, 0, 0, 0)
        date_status_layout.setSpacing(5)  # Bardzo mały odstęp

        # Data - uproszczony układ
        date_label = QLabel("Data:")
        date_label.setStyleSheet("font-weight: bold; background-color: transparent;")

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        self.date_input.setMinimumHeight(35)
        self.date_input.setMinimumWidth(150)
        self.date_input.setButtonSymbols(QDateEdit.NoButtons)

        # Dodaj elementy bezpośrednio do głównego layoutu
        date_status_layout.addWidget(date_label)
        date_status_layout.addWidget(self.date_input)
        date_status_layout.addSpacing(10)  # Mały odstęp

        # Status - uproszczony układ
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        date_status_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumHeight(35)
        self.status_combo.setMinimumWidth(150)
        self.status_combo.addItems([
            "🆕 Nowe", "⏳ W realizacji", "✅ Zakończone", "❌ Anulowane"
        ])
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        date_status_layout.addWidget(self.status_combo)
        date_status_layout.addStretch(1)  # Dodaj odstęp po prawej stronie

        # Dodaj widget do głównego layoutu
        order_info_layout.addWidget(date_status_container, 2, 0, 1, 2)

        # 3. Opcja powiadomienia email
        email_layout = QHBoxLayout()
        self.send_email_checkbox = QCheckBox("📧 Wyślij powiadomienie email")
        self.send_email_checkbox.setChecked(False)
        email_layout.addWidget(self.send_email_checkbox)
        email_layout.addStretch()

        order_info_layout.addLayout(email_layout, 3, 0, 1, 2)  # Zmieniony indeks wiersza

        main_layout.addWidget(order_info_group)
        
        # Sekcja pozycji zamówienia
        items_group = QGroupBox("Pozycje zamówienia")
        items_group.setStyleSheet("""
            QGroupBox {
                background-color: #252525;
                padding: 15px;
            }
        """)
        items_layout = QVBoxLayout(items_group)

        # Tabela pozycji - ulepszony wygląd
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Nazwa", "Typ", "Ilość", "Cena (zł)", "Suma (zł)", "Akcje"
        ])

        # Konfiguracja tabeli
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.setColumnWidth(1, 120)
        self.items_table.setColumnWidth(2, 80)
        self.items_table.setColumnWidth(3, 120)
        self.items_table.setColumnWidth(4, 120)
        self.items_table.setColumnWidth(5, 80)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(True)
        self.items_table.verticalHeader().setDefaultSectionSize(60)

        # Panel przycisków dla tabeli
        table_buttons_layout = QHBoxLayout()

        add_item_btn = QPushButton("➕ Dodaj pozycję")
        add_item_btn.setMinimumHeight(35)  # Zmniejszona wysokość z 40 na 35
        add_item_btn.setMaximumWidth(150)  # Dodane ograniczenie szerokości
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;  /* Zmniejszone padding */
                font-weight: bold;
                font-size: 12px;    /* Zmniejszona czcionka */
            }
            QPushButton:hover {
                background-color: #43a047;
            }
        """)
        add_item_btn.clicked.connect(lambda: self.add_item_row())

        clear_table_btn = QPushButton("🧹 Wyczyść")
        clear_table_btn.setMinimumHeight(35)  # Zmniejszona wysokość
        clear_table_btn.setMaximumWidth(100)  # Dodane ograniczenie szerokości
        clear_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;  /* Zmniejszone padding */
                font-weight: bold;
                font-size: 12px;    /* Zmniejszona czcionka */
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        clear_table_btn.clicked.connect(self.clear_items_table)

        table_buttons_layout.addWidget(add_item_btn)
        table_buttons_layout.addSpacing(10)
        table_buttons_layout.addWidget(clear_table_btn)
        table_buttons_layout.addStretch()

        items_layout.addWidget(self.items_table)
        items_layout.addSpacing(10)
        items_layout.addLayout(table_buttons_layout)

        main_layout.addWidget(items_group)
        
        # Podsumowanie z bardziej wyróżniającym się designem
        summary_group = QGroupBox("Podsumowanie")
        summary_group.setStyleSheet("""
            QGroupBox {
                background-color: #252525;
                padding: 15px;
            }
        """)
        summary_layout = QGridLayout(summary_group)
        summary_layout.setVerticalSpacing(12)
        summary_layout.setHorizontalSpacing(15)

        # Notatki
        notes_label = QLabel("📝 Notatki:")
        notes_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(notes_label, 0, 0)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Dodatkowe informacje o zamówieniu...")
        self.notes_input.setMinimumHeight(35)
        summary_layout.addWidget(self.notes_input, 0, 1, 1, 3)

        # Upust
        discount_label = QLabel("💰 Upust:")
        discount_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(discount_label, 1, 0)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setSuffix(" %")
        self.discount_spin.setDecimals(1)
        self.discount_spin.setSingleStep(5)
        self.discount_spin.setMinimumHeight(35)
        self.discount_spin.valueChanged.connect(self.update_total_amount)
        summary_layout.addWidget(self.discount_spin, 1, 1)

        # Kwota całkowita - bardziej wyróżniona
        payment_label = QLabel("💵 Do zapłaty:")
        payment_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(payment_label, 1, 2, Qt.AlignRight)

        self.total_amount_label = QLabel("0.00 zł")
        self.total_amount_label.setStyleSheet("""
            font-weight: bold;
            font-size: 18px;
            color: #4dabf7;
            background-color: #333333;
            padding: 8px 15px;
            border-radius: 5px;
        """)
        summary_layout.addWidget(self.total_amount_label, 1, 3, Qt.AlignRight)

        main_layout.addWidget(summary_group)
        
        # Przyciski akcji - bardziej nowoczesne
        action_layout = QHBoxLayout()

        print_btn = QPushButton("🖨️ Drukuj")
        print_btn.setMinimumWidth(130)
        print_btn.setMinimumHeight(50)
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        print_btn.clicked.connect(self.print_order)

        cancel_btn = QPushButton("❌ Anuluj")
        cancel_btn.setMinimumWidth(130)
        cancel_btn.setMinimumHeight(50)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        save_btn = QPushButton("💾 Zapisz zamówienie")
        save_btn.setMinimumWidth(200)
        save_btn.setMinimumHeight(50)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        save_btn.clicked.connect(self.save_order)

        action_layout.addStretch(1)
        action_layout.addWidget(print_btn)
        action_layout.addSpacing(10)
        action_layout.addWidget(cancel_btn)
        action_layout.addSpacing(10)
        action_layout.addWidget(save_btn)

        main_layout.addSpacing(15)
        main_layout.addLayout(action_layout)
        main_layout.addSpacing(10)
        
        # Podłączenie sygnałów
        self.items_table.cellChanged.connect(self.update_total_amount)
        
        # Dodaj domyślny wiersz (po zainicjowaniu wszystkich kontrolek)
        self.add_item_row()
        
        # Załaduj dane zamówienia, jeśli edytujemy istniejące
        if order_id:
            self.load_order_data()

    def load_clients(self):
        """Ładuje listę klientów do autocomplete."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy kolumna 'phone' istnieje w tabeli 'clients'
            cursor.execute("PRAGMA table_info(clients)")
            columns = cursor.fetchall()
            has_phone_column = any(col['name'] == 'phone' for col in columns)
            has_email_column = any(col['name'] == 'email' for col in columns)
            
            # Przygotuj zapytanie w zależności od dostępnych kolumn
            select_cols = ["id", "name"]
            if has_phone_column:
                select_cols.append("phone")
            if has_email_column:
                select_cols.append("email")
            
            query = f"SELECT {', '.join(select_cols)} FROM clients ORDER BY name"
            cursor.execute(query)
            clients = cursor.fetchall()
            
            # Zapisz listę klientów
            self.clients_data = clients
            
            # Utwórz listę nazw do autocomplete
            client_names = []
            for client in clients:
                display_text = client['name']
                
                # Dodaj telefon jeśli istnieje
                if has_phone_column and 'phone' in client and client['phone']:
                    display_text += f" | Tel: {client['phone']}"
                
                # Dodaj email jeśli istnieje
                if has_email_column and 'email' in client and client['email']:
                    display_text += f" | {client['email']}"
                    
                client_names.append(display_text)
            
            self.clients_list = client_names
            
            # Dodanie autocomplete do pola wyszukiwania klienta
            completer = QCompleter(self.clients_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.client_input.setCompleter(completer)
                
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania klientów: {e}",
                NotificationTypes.ERROR
            )

    def on_client_text_changed(self, text):
        """Obsługuje zmianę tekstu w polu klienta."""
        if not text:
            self.client_id = None
            self.client_info_label.setText("Wybierz klienta, aby zobaczyć szczegóły")
            self.client_info_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
            return
        
        # Szukaj klienta - bardziej liberalne podejście
        found = False
        for i, display_name in enumerate(self.clients_list):
            # Sprawdź różne warianty pasowania
            if (text.lower() == display_name.lower() or 
                text.lower() in display_name.lower() or 
                display_name.lower().startswith(text.lower())):
                
                self.client_id = self.clients_data[i]['id']
                self.update_client_info()
                found = True
                break
        
        # Jeśli nie znaleziono klienta
        if not found:
            self.client_id = None
            self.client_info_label.setText(f"Nie znaleziono klienta: '{text}'")
            self.client_info_label.setStyleSheet("color: #ff6b6b;")

    def update_client_info(self):
        """Aktualizuje informacje o kliencie po zmianie wyboru."""
        try:
            client_id = self.client_id
            
            if not client_id:
                self.client_info_label.setText("Wybierz klienta, aby zobaczyć szczegóły")
                self.client_info_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
                return
            
            cursor = self.conn.cursor()
            
            # Zapytanie z pełnym zestawem kolumn
            cursor.execute("""
                SELECT * FROM clients WHERE id = ?
            """, (client_id,))
            
            client = cursor.fetchone()
            
            if not client:
                self.client_info_label.setText("Nie znaleziono klienta")
                self.client_info_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
                return
            
            # Podstawowe informacje o kliencie
            info = f"<b>Klient:</b> {client['name']}"
            
            # Sprawdź numer telefonu - może być w różnych kolumnach
            if 'phone_number' in client.keys() and client['phone_number']:
                info += f" | <b>Telefon:</b> {client['phone_number']}"
            elif 'phone' in client.keys() and client['phone']:
                info += f" | <b>Telefon:</b> {client['phone']}"
            
            # Email
            if 'email' in client.keys() and client['email']:
                info += f" | <b>Email:</b> {client['email']}"
            
            # Rabat
            if 'discount' in client.keys() and client['discount']:
                try:
                    discount_value = float(client['discount'])
                    if discount_value > 0:
                        info += f" | <b>Rabat:</b> {discount_value}%"
                except (ValueError, TypeError):
                    pass
            
            # Dodatkowe informacje
            if 'additional_info' in client.keys() and client['additional_info']:
                info += f"<br><b>Informacje:</b> {client['additional_info']}"
            
            # Pobierz pojazdy klienta - najpierw sprawdź, czy tabela istnieje
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT * FROM vehicles WHERE client_id = ? LIMIT 5
                """, (client_id,))
                
                vehicles = cursor.fetchall()
                
                if vehicles:
                    # Dodaj informacje o pojazdach
                    info += "<br><b>Pojazdy:</b> "
                    vehicle_list = []
                    
                    for vehicle in vehicles:
                        vehicle_text = ""
                        
                        # Marka i model
                        if 'make' in vehicle.keys() and 'model' in vehicle.keys():
                            make = vehicle['make'] or ""
                            model = vehicle['model'] or ""
                            vehicle_text = f"{make} {model}".strip()
                        
                        # Rok produkcji
                        if 'year' in vehicle.keys() and vehicle['year']:
                            vehicle_text += f" ({vehicle['year']})"
                        
                        # Numer rejestracyjny
                        if 'registration_number' in vehicle.keys() and vehicle['registration_number']:
                            vehicle_text += f" [{vehicle['registration_number']}]"
                        
                        if vehicle_text:
                            vehicle_list.append(vehicle_text)
                    
                    if vehicle_list:
                        info += ", ".join(vehicle_list)
                        
                        # Sprawdź całkowitą liczbę pojazdów
                        cursor.execute("SELECT COUNT(*) AS count FROM vehicles WHERE client_id = ?", (client_id,))
                        total_count = cursor.fetchone()['count']
                        
                        if total_count > 5:
                            info += f" <i>...i {total_count - 5} więcej</i>"
                else:
                    info += "<br><b>Pojazdy:</b> Brak przypisanych pojazdów"
            
            # Ustaw tekst i styl
            self.client_info_label.setText(info)
            self.client_info_label.setStyleSheet("""
                color: #ffffff;
                background-color: #3a3a3a;
                padding: 8px;
                border-radius: 4px;
            """)
                
        except Exception as e:
            # Zachowaj minimalny log błędów
            print(f"Błąd w update_client_info: {str(e)}")
            
            # Dla użytkownika prosty komunikat
            self.client_info_label.setText("Wystąpił błąd podczas ładowania danych klienta")
            self.client_info_label.setStyleSheet("color: #ff6b6b;")

    def add_new_client(self):
        """Dodaje nowego klienta bezpośrednio z dialogu zamówienia."""
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Odśwież listę klientów
            self.load_clients()
            
            # Ustaw nowo dodanego klienta
            for i, client in enumerate(self.clients_data):
                if client['id'] == dialog.client_id:
                    self.client_id = client['id']
                    self.client_input.setText(self.clients_list[i])
                    self.update_client_info()
                    break
            
            NotificationManager.get_instance().show_notification(
                f"Dodano nowego klienta: {dialog.client_name}",
                NotificationTypes.SUCCESS,
                duration=3000
            )
    
    def add_item_row(self, name="", item_type="Usługa", quantity=1, price=0.0):
        """Dodaje nowy wiersz do tabeli pozycji zamówienia."""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Nazwa - combo z dostępnymi produktami
        name_combo = QComboBox()
        name_combo.setEditable(True)
        name_combo.setMinimumHeight(35)
        name_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                color: #ffffff;
            }
            QComboBox:focus {
                border: 1px solid #4dabf7;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #3a3a3a;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: #ffffff;
                selection-background-color: #4dabf7;
                selection-color: #ffffff;
                border: 1px solid #3a3a3a;
            }
        """)
        self.load_product_items(name_combo)
        
        if name:
            # Znajdź indeks elementu po nazwie
            for i in range(name_combo.count()):
                if name_combo.itemText(i) == name:
                    name_combo.setCurrentIndex(i)
                    break
            else:
                name_combo.setCurrentText(name)
        else:
            # Pozostaw puste pole, jeśli nie podano nazwy
            name_combo.setCurrentText("")

        # Typ - combo z typami produktów
        type_combo = QComboBox()
        type_combo.addItems(["Opona", "Część", "Usługa"])
        type_combo.setCurrentText(item_type)
        type_combo.setMinimumHeight(30)
        type_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                background-color: #3a3a3a;
                border: 1px solid #505050;
                border-radius: 4px;
                color: #ffffff;
            }
            QComboBox:focus {
                border: 1px solid #4dabf7;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #505050;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        
        # Ilość - spinner z lepszym wyglądem
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 100)
        quantity_spin.setValue(quantity)
        quantity_spin.valueChanged.connect(self.update_total_amount)
        quantity_spin.setMinimumHeight(30)
        quantity_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                background-color: #3a3a3a;
                border: 1px solid #505050;
                border-radius: 4px;
                color: #ffffff;
            }
            QSpinBox:focus {
                border: 1px solid #4dabf7;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #505050;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #606060;
            }
        """)
        
        # Cena - pole tekstowe z lepszym wyglądem
        price_edit = QLineEdit()
        if price > 0:
            price_edit.setText(f"{price:.2f}")
        price_edit.setPlaceholderText("Cena")
        price_edit.setValidator(QDoubleValidator(0, 10000, 2))
        price_edit.textChanged.connect(self.update_total_amount)
        price_edit.setMinimumHeight(30)
        price_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        price_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                background-color: #3a3a3a;
                border: 1px solid #505050;
                border-radius: 4px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
            }
        """)
        
        # Suma (tylko do odczytu) - lepszy wygląd
        sum_item = QTableWidgetItem("0.00")
        sum_item.setFlags(sum_item.flags() & ~Qt.ItemIsEditable)
        sum_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sum_item.setForeground(QColor("#4dabf7"))  # Niebieska wartość dla lepszej widoczności
        
        # Kontener akcji z lepszym wyglądem
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 0, 5, 0)
        actions_layout.setSpacing(3)
        actions_layout.setAlignment(Qt.AlignCenter)
        
        # Przyciski usuwania pozycji
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(40)
        delete_btn.setMaximumHeight(30)
        delete_btn.setToolTip("Usuń pozycję")
        delete_btn.clicked.connect(lambda: self.remove_item_row(row))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        actions_layout.addWidget(delete_btn)
        
        # Dodaj widżety do komórek
        self.items_table.setCellWidget(row, 0, name_combo)
        self.items_table.setCellWidget(row, 1, type_combo)
        self.items_table.setCellWidget(row, 2, quantity_spin)
        self.items_table.setCellWidget(row, 3, price_edit)
        self.items_table.setItem(row, 4, sum_item)
        self.items_table.setCellWidget(row, 5, actions_widget)
        
        # Podłącz sygnały do aktualizacji
        name_combo.currentTextChanged.connect(lambda: self.update_price_from_product(row))
        type_combo.currentTextChanged.connect(lambda: self.update_price_from_product(row))
        
        # Aktualizuj sumy - tylko jeśli wszystkie kontrolki są już zainicjowane
        if hasattr(self, 'discount_spin') and self.discount_spin is not None:
            self.update_total_amount()
        
        return row
    
    def remove_item_row(self, row):
        """Usuwa wiersz z tabeli pozycji."""
        # Sprawdź, czy indeks wiersza jest poprawny
        if row >= 0 and row < self.items_table.rowCount():
            self.items_table.removeRow(row)
            self.update_total_amount()
    
    def clear_items_table(self):
        """Czyści tabelę pozycji."""
        self.items_table.setRowCount(0)
        self.add_item_row()  # Dodaj jeden pusty wiersz
        self.update_total_amount()
    
    def update_price_from_product(self, row):
        """Aktualizuje cenę na podstawie wybranego produktu."""
        try:
            # Sprawdź, czy indeks wiersza jest poprawny
            if row < 0 or row >= self.items_table.rowCount():
                return
                
            name_combo = self.items_table.cellWidget(row, 0)
            type_combo = self.items_table.cellWidget(row, 1)
            price_edit = self.items_table.cellWidget(row, 3)
            
            if not all([name_combo, type_combo, price_edit]):
                return
                
            product_name = name_combo.currentText()
            product_type = type_combo.currentText()
            
            # Pomijamy nagłówki sekcji
            if product_name.startswith("---"):
                return
                
            # Pobierz cenę z bazy danych
            cursor = self.conn.cursor()
            
            if product_type == "Opona":
                # Próba wyodrębnnienia marki i rozmiaru z nazwy
                parts = product_name.split(" ", 1)
                if len(parts) >= 2:
                    brand = parts[0]
                    size = parts[1]
                    cursor.execute(
                        "SELECT price FROM inventory WHERE brand_model LIKE ? AND size LIKE ?", 
                        (f"%{brand}%", f"%{size}%")
                    )
                    result = cursor.fetchone()
                    if result:
                        price_edit.setText(f"{result['price']:.2f}")
            
            elif product_type == "Usługa":
                # Sprawdź w tabeli usług (jeśli istnieje)
                cursor.execute(
                    "SELECT price FROM services WHERE name LIKE ?", 
                    (f"%{product_name}%",)
                )
                result = cursor.fetchone()
                if result:
                    price_edit.setText(f"{result['price']:.2f}")
                else:
                    # Domyślne ceny dla popularnych usług
                    default_prices = {
                        "Wymiana opon": 80.0,
                        "Wyważenie kół": 40.0,
                        "Naprawa opony": 50.0,
                        "Przegląd sezonowy": 100.0,
                        "Wymiana zaworków": 20.0
                    }
                    
                    for service_name, price in default_prices.items():
                        if service_name.lower() in product_name.lower():
                            price_edit.setText(f"{price:.2f}")
                            break
        
        except Exception as e:
            # Ignoruj błędy podczas próby automatycznego ustawienia ceny
            pass
    
    def load_product_items(self, combo):
        """Ładuje listę produktów do ComboBox."""
        try:
            cursor = self.conn.cursor()
            
            # Utwórz model dla combo, który będzie zawierał role
            model = QStandardItemModel()
            combo.setModel(model)
            
            # Sekcja: Opony
            header_item = QStandardItem("--- OPONY ---")
            header_item.setFlags(Qt.ItemIsEnabled)  # Nie można wybrać nagłówka
            header_item.setData(QColor("#4dabf7"), Qt.ForegroundRole)
            header_item.setData(QFont("Arial", 9, QFont.Bold), Qt.FontRole)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setData("header", Qt.UserRole)  # Specjalne oznaczenie nagłówków
            model.appendRow(header_item)
            
            # Pobierz opony z inwentarza
            try:
                cursor.execute("SELECT brand_model, size FROM inventory")
                for row in cursor.fetchall():
                    item = QStandardItem(f"{row['brand_model']} {row['size']}")
                    item.setData("tire", Qt.UserRole)  # Typ elementu
                    model.appendRow(item)
            except Exception:
                # Jeśli tabela nie istnieje, dodaj przykładowe opony
                sample_tires = [
                    "Michelin CrossClimate 205/55R16",
                    "Continental WinterContact 195/65R15",
                    "Goodyear EfficientGrip 225/45R17",
                    "Pirelli P Zero 235/35R19"
                ]
                for tire in sample_tires:
                    item = QStandardItem(tire)
                    item.setData("tire", Qt.UserRole)
                    model.appendRow(item)
            
            # Sekcja: Części
            header_item = QStandardItem("--- CZĘŚCI ---")
            header_item.setFlags(Qt.ItemIsEnabled)  # Nie można wybrać nagłówka
            header_item.setData(QColor("#fcc419"), Qt.ForegroundRole)
            header_item.setData(QFont("Arial", 9, QFont.Bold), Qt.FontRole)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setData("header", Qt.UserRole)
            model.appendRow(header_item)
            
            # Pobierz części z bazy danych
            try:
                cursor.execute("SELECT name FROM parts")
                for row in cursor.fetchall():
                    item = QStandardItem(row['name'])
                    item.setData("part", Qt.UserRole)
                    model.appendRow(item)
            except Exception:
                # Jeśli tabela nie istnieje, dodaj przykładowe części
                sample_parts = [
                    "Zaworek do opon", 
                    "Ciężarki wyważające", 
                    "Zestaw naprawczy do opon",
                    "Śruby do felg"
                ]
                for part in sample_parts:
                    item = QStandardItem(part)
                    item.setData("part", Qt.UserRole)
                    model.appendRow(item)
            
            # Sekcja: Usługi
            header_item = QStandardItem("--- USŁUGI ---")
            header_item.setFlags(Qt.ItemIsEnabled)  # Nie można wybrać nagłówka
            header_item.setData(QColor("#51cf66"), Qt.ForegroundRole)
            header_item.setData(QFont("Arial", 9, QFont.Bold), Qt.FontRole)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setData("header", Qt.UserRole)
            model.appendRow(header_item)
            
            # Domyślne usługi
            default_services = [
                "Wymiana opon komplet", 
                "Wyważenie kół (szt.)", 
                "Naprawa opony", 
                "Przegląd sezonowy",
                "Wymiana zaworków",
                "Przechowywanie opon (sezon)",
                "Pompowanie azotem"
            ]
            for service in default_services:
                item = QStandardItem(service)
                item.setData("service", Qt.UserRole)
                model.appendRow(item)
            
            # Ustaw renderer dla ComboBox, który ukryje nagłówki na liście wyboru
            combo.setItemDelegate(ComboBoxItemDelegate())
            
            # Ustaw model autouzupełniania tylko jeśli combo jest edytowalne
            if combo.isEditable():
                completer = QCompleter(model)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                combo.setCompleter(completer)
            
            # Domyślnie ustaw pierwszy aktywny element (nie nagłówek)
            for i in range(1, model.rowCount()):
                item = model.item(i)
                if item.data(Qt.UserRole) != "header":
                    combo.setCurrentIndex(i)
                    break
                
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania produktów: {e}",
                NotificationTypes.ERROR
            )
    
    def update_total_amount(self):
        """Aktualizuje kwotę całkowitą zamówienia."""
        # Sprawdź, czy wszystkie potrzebne kontrolki są już zainicjowane
        if not hasattr(self, 'discount_spin') or self.discount_spin is None:
            return
            
        if not hasattr(self, 'items_table') or self.items_table is None:
            return
            
        if not hasattr(self, 'total_amount_label') or self.total_amount_label is None:
            return
            
        total = 0.0
        
        for row in range(self.items_table.rowCount()):
            try:
                # Pobierz wartości z komórek
                quantity_spin = self.items_table.cellWidget(row, 2)
                price_edit = self.items_table.cellWidget(row, 3)
                
                if not quantity_spin or not price_edit:
                    continue
                
                # Konwersja wartości
                quantity = quantity_spin.value()
                
                # Pobierz cenę z pola tekstowego
                price_text = price_edit.text().strip()
                if not price_text:  # Jeśli puste, użyj 0
                    price = 0.0
                else:
                    # Zamień przecinki na kropki i konwertuj na float
                    price_text = price_text.replace(',', '.')
                    try:
                        price = float(price_text)
                    except:
                        price = 0.0
                
                # Oblicz sumę dla pozycji
                item_total = quantity * price
                
                # Ustaw sumę w tabeli
                sum_item = self.items_table.item(row, 4)
                if sum_item:
                    sum_item.setText(f"{item_total:.2f}")
                
                # Dodaj do całkowitej kwoty
                total += item_total
            except Exception as e:
                # Ignoruj błędy konwersji
                print(f"Błąd w update_total_amount dla wiersza {row}: {e}")
                pass
        
        # Zastosuj upust
        discount = self.discount_spin.value()
        if discount > 0:
            discount_amount = total * (discount / 100)
            total -= discount_amount
        
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
            # Znajdź klienta o danym ID i ustaw jego nazwę w polu tekstowym
            for i, client in enumerate(self.clients_data):
                if client['id'] == order['client_id']:
                    self.client_input.setText(self.clients_list[i])
                    self.client_id = order['client_id']  # Ustaw też ID klienta
                    self.update_client_info()  # Aktualizuj informacje o kliencie
                    break
            
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
    
    def print_order(self):
        """Drukuje zamówienie."""
        # Tutaj można zaimplementować generowanie i drukowanie dokumentu
        NotificationManager.get_instance().show_notification(
            "Funkcja drukowania zamówienia nie jest jeszcze zaimplementowana.",
            NotificationTypes.INFO
        )
    
    def find_item_id(self, name, item_type):
        """Próbuje znaleźć ID produktu na podstawie nazwy i typu."""
        try:
            cursor = self.conn.cursor()
            
            if item_type == "Opona":
                # Pobierz części nazwy dla lepszego dopasowania
                parts = name.split()
                if len(parts) >= 2:
                    brand = parts[0]
                    size_pattern = "%" + " ".join(parts[1:]) + "%"
                    
                    cursor.execute(
                        "SELECT id FROM inventory WHERE brand_model LIKE ? AND size LIKE ?", 
                        (f"%{brand}%", size_pattern)
                    )
                else:
                    cursor.execute(
                        "SELECT id FROM inventory WHERE brand_model || ' ' || size LIKE ?", 
                        (f"%{name}%",)
                    )
            elif item_type == "Część":
                cursor.execute("SELECT id FROM parts WHERE name LIKE ?", (f"%{name}%",))
            elif item_type == "Usługa":
                # Sprawdź czy istnieje tabela usług
                try:
                    cursor.execute("SELECT id FROM services WHERE name LIKE ?", (f"%{name}%",))
                    result = cursor.fetchone()
                    if result:
                        return result['id']
                except:
                    # Tabela usług może nie istnieć
                    pass
                return None
            else:
                # Dla innych typów zwróć None
                return None
            
            result = cursor.fetchone()
            return result['id'] if result else None
        
        except Exception as e:
            # Logowanie błędu bez przerywania działania
            print(f"Błąd podczas wyszukiwania ID produktu: {e}")
            return None
            
    def save_order(self):
        """Zapisuje zamówienie w bazie danych."""
        try:
            # Walidacja danych
            client_id = self.client_id
            if not client_id:
                raise ValueError("Nie wybrano klienta")
            
            # Sprawdź czy są pozycje zamówienia
            if self.items_table.rowCount() == 0:
                raise ValueError("Zamówienie musi zawierać co najmniej jedną pozycję")
            
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
                quantity_spin = self.items_table.cellWidget(row, 2)
                price_edit = self.items_table.cellWidget(row, 3)
                
                if not all([name_combo, type_combo, quantity_spin, price_edit]):
                    continue
                
                name = name_combo.currentText()
                
                # Pomiń nagłówki sekcji
                if name.startswith("---"):
                    continue
                
                item_type = type_combo.currentText()
                quantity = quantity_spin.value()
                
                # Pobierz cenę z pola tekstowego
                price_text = price_edit.text().strip()
                if not price_text:  # Jeśli puste, propuść wiersz
                    continue
                
                price_text = price_text.replace(',', '.')
                try:
                    price = float(price_text)
                except:
                    continue  # Pomiń wiersz z nieprawidłową ceną
                
                # Pomiń puste wiersze lub z zerową ceną/ilością
                if not name or quantity == 0 or price == 0:
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
            
            # Wysyłanie powiadomienia email, jeśli zaznaczono opcję
            if self.send_email_checkbox.isChecked():
                self.send_order_email(self.order_id)
            
            # Powiadomienie o sukcesie
            NotificationManager.get_instance().show_notification(
                "Zamówienie zostało zapisane",
                NotificationTypes.SUCCESS
            )
            
            # Zamknij dialog
            self.accept()
            
        except ValueError as e:
            # Obsługa błędów walidacji
            QMessageBox.warning(self, "Błąd walidacji", str(e))
            
        except Exception as e:
            # Wycofaj zmiany
            if hasattr(self, 'conn') and self.conn:
                self.conn.rollback()
            
            # Powiadomienie o błędzie
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zapisywania zamówienia: {e}",
                NotificationTypes.ERROR
            )

    def send_order_email(self, order_id):
        """Wysyła powiadomienie email o zamówieniu."""
        try:
            from datetime import datetime
            from utils.paths import CONFIG_DIR
            import json
            import os
            
            cursor = self.conn.cursor()
            
            # Pobierz dane zamówienia i klienta
            cursor.execute("""
                SELECT o.id, o.order_date, o.status, o.total_amount, o.notes,
                    c.name as client_name, c.email as client_email
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order = cursor.fetchone()
            
            if not order:
                raise ValueError(f"Nie znaleziono zamówienia o ID {order_id}")
            
            # Sprawdź czy klient ma email
            if not order['client_email']:
                raise ValueError(f"Klient {order['client_name']} nie ma podanego adresu email")
            
            # Pobierz pozycje zamówienia
            cursor.execute("""
                SELECT item_type, name, quantity, price, quantity * price as item_total
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
            """, (order_id,))
            
            items = cursor.fetchall()
            
            # Formatowanie daty
            order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            current_date = datetime.now().strftime("%d-%m-%Y")
            
            # Pobierz dane firmy z ustawień
            from PySide6.QtCore import QSettings
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            company_email = settings.value("email_address", "")
            company_website = settings.value("company_website", "")
            
            # Przygotowanie HTML z listą pozycji zamówienia
            items_html = """
            <table border="0" cellspacing="0" cellpadding="8" style="width:100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; border-bottom: 1px solid #ddd;">Nazwa</th>
                    <th style="text-align:left; border-bottom: 1px solid #ddd;">Rodzaj</th>
                    <th style="text-align:center; border-bottom: 1px solid #ddd;">Ilość</th>
                    <th style="text-align:right; border-bottom: 1px solid #ddd;">Cena</th>
                    <th style="text-align:right; border-bottom: 1px solid #ddd;">Suma</th>
                </tr>
            """
            
            for item in items:
                items_html += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="text-align:left; border-bottom: 1px solid #ddd;">{item['name']}</td>
                    <td style="text-align:left; border-bottom: 1px solid #ddd;">{item['item_type']}</td>
                    <td style="text-align:center; border-bottom: 1px solid #ddd;">{item['quantity']}</td>
                    <td style="text-align:right; border-bottom: 1px solid #ddd;">{item['price']:.2f} zł</td>
                    <td style="text-align:right; border-bottom: 1px solid #ddd;">{item['item_total']:.2f} zł</td>
                </tr>
                """
            
            items_html += """
            </table>
            """
            
            # Przygotowanie danych do szablonu
            template_data = {
                "order_id": f"#{order_id}",
                "client_name": order['client_name'],
                "client_email": order['client_email'],
                "order_date": order_date,
                "status": order['status'],
                "total_amount": f"{order['total_amount']:.2f} zł",
                "notes": order['notes'] or "",
                "current_date": current_date,
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone,
                "company_email": company_email,
                "company_website": company_website,
                "items_table": items_html
            }
            
            # Pobierz odpowiedni szablon z pliku templates.json
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    
                # Znajdź odpowiedni szablon dla statusu zamówienia
                status_key = order['status'].lower().replace(' ', '_')
                template_key = f"order_{status_key}"
                    
                # Pobierz szablon
                email_templates = templates.get("email", {})
                
                if template_key in email_templates:
                    template = email_templates[template_key]
                elif "order_general" in email_templates:
                    template = email_templates["order_general"]
                else:
                    # Domyślny szablon, jeśli nie znaleziono właściwego
                    template = {
                        "subject": f"Zamówienie {template_data['order_id']} - {order['status']}",
                        "body": f"""
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                h1 {{ color: #4dabf7; }}
                                .header {{ border-bottom: 2px solid #4dabf7; padding-bottom: 10px; }}
                                .footer {{ margin-top: 30px; font-size: 12px; color: #777; border-top: 1px solid #ddd; padding-top: 10px; }}
                                .order-details {{ margin: 20px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>Informacja o zamówieniu {template_data['order_id']}</h1>
                                </div>
                                
                                <p>Szanowny Kliencie,</p>
                                
                                <p>informujemy, że Twoje zamówienie ma aktualny status: <strong>{order['status']}</strong>.</p>
                                
                                <div class="order-details">
                                    <p><strong>Klient:</strong> {template_data['client_name']}<br>
                                    <strong>Data zamówienia:</strong> {template_data['order_date']}<br>
                                    <strong>Kwota całkowita:</strong> {template_data['total_amount']}</p>
                                    
                                    <h3>Pozycje zamówienia:</h3>
                                    {template_data['items_table']}
                                </div>
                                
                                <p>Dziękujemy za skorzystanie z naszych usług.</p>
                                
                                <div class="footer">
                                    <p>{template_data['company_name']}<br>
                                    {template_data['company_address']}<br>
                                    Tel: {template_data['company_phone']}<br>
                                    Email: {template_data['company_email']}<br>
                                    {template_data['company_website']}</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                    }
            else:
                # Domyślny szablon, jeśli plik templates.json nie istnieje
                template = {
                    "subject": f"Zamówienie {template_data['order_id']} - {order['status']}",
                    "body": f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            h1 {{ color: #4dabf7; }}
                            .header {{ border-bottom: 2px solid #4dabf7; padding-bottom: 10px; }}
                            .footer {{ margin-top: 30px; font-size: 12px; color: #777; border-top: 1px solid #ddd; padding-top: 10px; }}
                            .order-details {{ margin: 20px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Informacja o zamówieniu {template_data['order_id']}</h1>
                            </div>
                            
                            <p>Szanowny Kliencie,</p>
                            
                            <p>informujemy, że Twoje zamówienie ma aktualny status: <strong>{order['status']}</strong>.</p>
                            
                            <div class="order-details">
                                <p><strong>Klient:</strong> {template_data['client_name']}<br>
                                <strong>Data zamówienia:</strong> {template_data['order_date']}<br>
                                <strong>Kwota całkowita:</strong> {template_data['total_amount']}</p>
                                
                                <h3>Pozycje zamówienia:</h3>
                                {template_data['items_table']}
                            </div>
                            
                            <p>Dziękujemy za skorzystanie z naszych usług.</p>
                            
                            <div class="footer">
                                <p>{template_data['company_name']}<br>
                                {template_data['company_address']}<br>
                                Tel: {template_data['company_phone']}<br>
                                Email: {template_data['company_email']}<br>
                                {template_data['company_website']}</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                }
                
            # Podstaw dane w szablonie
            subject = template["subject"]
            body = template["body"]
            
            # Zastąp zmienne w szablonie
            for key, value in template_data.items():
                subject = subject.replace("{" + key + "}", str(value))
                body = body.replace("{" + key + "}", str(value))
            
            # Wysyłka emaila
            # Pobierz ustawienia SMTP
            smtp_server = settings.value("smtp_server", "")
            smtp_port = settings.value("smtp_port", 587, type=int)
            use_ssl = settings.value("use_ssl", True, type=bool)
            email_address = settings.value("email_address", "")
            email_password = settings.value("email_password", "")
            
            # Sprawdź czy mamy wszystkie potrzebne dane
            if not smtp_server or not email_address or not email_password:
                raise ValueError("Brak konfiguracji SMTP. Przejdź do Ustawienia > Komunikacja, aby skonfigurować wysyłanie emaili.")
            
            # Pokazujemy komunikat, że wysyłamy email
            NotificationManager.get_instance().show_notification(
                f"Wysyłanie powiadomienia email do {order['client_email']}...",
                NotificationTypes.INFO
            )
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Przygotuj wiadomość
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = order['client_email']
            msg['Subject'] = subject
            
            # Dodanie treści HTML
            msg.attach(MIMEText(body, 'html'))
            
            # Utworzenie sesji SMTP
            session = smtplib.SMTP(smtp_server, smtp_port)
            
            # Włącz debugowanie SMTP
            session.set_debuglevel(1)
            
            # Dla większości serwerów konieczne jest rozpoczęcie sesji TLS
            if use_ssl:
                session.starttls()
            
            # Logowanie do serwera SMTP
            session.login(email_address, email_password)
            
            # Wysłanie wiadomości
            session.sendmail(email_address, order['client_email'], msg.as_string())
            
            # Zakończenie sesji
            session.quit()
            
            # Powiadomienie o sukcesie
            NotificationManager.get_instance().show_notification(
                f"Email z powiadomieniem o zamówieniu został wysłany do {order['client_email']}",
                NotificationTypes.SUCCESS
            )
            
            # Zapisz log wysłanego emaila
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                # Sprawdź czy tabela email_logs istnieje
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reference_id INTEGER,
                        reference_type TEXT,
                        email TEXT,
                        subject TEXT,
                        sent_date TEXT,
                        status TEXT
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO email_logs 
                    (reference_id, reference_type, email, subject, sent_date, status) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    order_id, 
                    "order", 
                    order['client_email'], 
                    msg['Subject'], 
                    current_datetime, 
                    "Wysłany"
                ))
                
                self.conn.commit()
            except Exception as e:
                print(f"Błąd podczas zapisywania logu email: {e}")
            
        except ValueError as e:
            # Pokazanie komunikatu o błędzie
            NotificationManager.get_instance().show_notification(
                str(e),
                NotificationTypes.WARNING
            )
        except Exception as e:
            # Loguj błąd
            import logging
            logger = logging.getLogger("TireDepositManager")
            logger.error(f"Błąd podczas wysyłania powiadomienia email: {e}")
            
            # Pokazanie komunikatu o błędzie
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania powiadomienia email: {e}",
                NotificationTypes.ERROR
            )  

class ComboBoxItemDelegate(QStyledItemDelegate):
    """Niestandardowy delegat dla ComboBox, który ukrywa nagłówki na liście wyboru."""
    
    def paint(self, painter, option, index):
        # Jeśli element to nagłówek, ukryj go na rozwiniętej liście
        if index.data(Qt.UserRole) == "header" and option.state & QStyle.State_Selected:
            # Nie rysuj nic dla wybranych nagłówków
            return
        
        super().paint(painter, option, index)
    
    def sizeHint(self, option, index):
        # Nagłówki mają mniejszą wysokość na liście
        if index.data(Qt.UserRole) == "header":
            size = super().sizeHint(option, index)
            return QSize(size.width(), 20)  # mniejsza wysokość dla nagłówków
        
        return super().sizeHint(option, index)