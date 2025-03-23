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
        
        # Ustawienia okna
        self.setWindowTitle("Nowe zamówienie" if not order_id else "Edycja zamówienia")
        self.setMinimumSize(1000, 650)
        
        # Dostosowania stylu
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #4dabf7;
            }
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:disabled {
                background-color: #515151;
                color: #a0a0a0;
            }
            QTableWidget {
                background-color: #2c2c2c;
                alternate-background-color: #353535;
                color: #ffffff;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 15px;
                margin: 5px;   /* Dodanie marginesu */
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #505050;
                font-weight: bold;
            }
            QToolButton {
                background-color: transparent;
                border: none;
            }
            QFrame#separatorLine {
                background-color: #3a3a3a;
                max-height: 1px;
            }
        """)
        
        # Główny układ
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        header_label = QLabel("📋 " + ("Nowe zamówienie" if not order_id else f"Edycja zamówienia #{order_id}"))
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(header_label)
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setObjectName("separatorLine")
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Dane zamówienia - GroupBox
        order_info_group = QGroupBox("Informacje o zamówieniu")
        order_info_layout = QGridLayout(order_info_group)
        order_info_layout.setColumnStretch(1, 2)  # Druga kolumna będzie szersza
        
        # Klient
        order_info_layout.addWidget(QLabel("Klient:"), 0, 0)
        
        # Kontener dla combo klienta i przycisku dodawania
        client_container = QWidget()
        client_layout = QHBoxLayout(client_container)
        client_layout.setContentsMargins(0, 0, 0, 0)
        client_layout.setSpacing(5)
        
        self.client_combo = QComboBox()
        self.client_combo.setMinimumWidth(300)
        self.client_combo.setMinimumHeight(30)
        
        # Autouzupełnianie klientów
        self.client_combo.setEditable(True)
        self.client_combo.setInsertPolicy(QComboBox.NoInsert)
        self.load_clients()
        
        add_client_btn = QPushButton("➕ Nowy klient")
        add_client_btn.clicked.connect(self.add_new_client)
        
        client_layout.addWidget(self.client_combo)
        client_layout.addWidget(add_client_btn)
        
        order_info_layout.addWidget(client_container, 0, 1)
        
        # Data zamówienia
        order_info_layout.addWidget(QLabel("Data zamówienia:"), 1, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        self.date_input.setMinimumHeight(30)
        order_info_layout.addWidget(self.date_input, 1, 1)
        
        # Status zamówienia
        order_info_layout.addWidget(QLabel("Status:"), 2, 0)
        self.status_combo = QComboBox()
        self.status_combo.setMinimumHeight(30)
        self.status_combo.addItems([
            "Nowe", "W realizacji", "Zakończone", "Anulowane"
        ])
        
        # Ustaw style dla statusów
        self.status_combo.setItemData(0, QColor("#4dabf7"), Qt.ForegroundRole)  # Nowe - niebieskie
        self.status_combo.setItemData(1, QColor("#fcc419"), Qt.ForegroundRole)  # W realizacji - żółte
        self.status_combo.setItemData(2, QColor("#51cf66"), Qt.ForegroundRole)  # Zakończone - zielone
        self.status_combo.setItemData(3, QColor("#ff6b6b"), Qt.ForegroundRole)  # Anulowane - czerwone
        
        order_info_layout.addWidget(self.status_combo, 2, 1)
        
        main_layout.addWidget(order_info_group)
        
        # Sekcja pozycji zamówienia - GroupBox
        items_group = QGroupBox("Pozycje zamówienia")
        items_layout = QVBoxLayout(items_group)
        
        # Tabela pozycji
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)  # Dodano kolumnę akcji
        self.items_table.setHorizontalHeaderLabels([
            "Nazwa", "Typ", "Ilość", "Cena (zł)", "Suma (zł)", "Akcje"
        ])
        
        # Konfiguracja tabeli
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Nazwa - rozciągnięta
        self.items_table.setColumnWidth(1, 120)  # Typ - zwiększona szerokość
        self.items_table.setColumnWidth(2, 80)   # Ilość - zwiększona szerokość 
        self.items_table.setColumnWidth(3, 120)  # Cena - zwiększona szerokość
        self.items_table.setColumnWidth(4, 120)  # Suma - zwiększona szerokość
        self.items_table.setColumnWidth(5, 80)   # Akcje - zwiększona szerokość
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)  # Ukryj numery wierszy
        self.items_table.setShowGrid(True)
        
        # Ustawienie większej wysokości wierszy
        self.items_table.verticalHeader().setDefaultSectionSize(60)  # Zwiększenie wysokości wierszy
        
        # Aktualizacja stylu tabeli
        self.items_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #404040;
                background-color: #2c2c2c;
                selection-background-color: #4dabf7;
                selection-color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #404040;
                margin: 5px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #505050;
                height: 25px;
            }
            QTableWidget::item:selected {
                background-color: #4dabf7;
            }
        """)
        
        # Panel przycisków dla tabeli - lepszy wygląd
        table_buttons_layout = QHBoxLayout()
        
        add_item_btn = QPushButton("➕ Dodaj pozycję")
        add_item_btn.setMinimumHeight(40)
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;  /* Zielony */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        add_item_btn.clicked.connect(lambda: self.add_item_row())
        
        clear_table_btn = QPushButton("🧹 Wyczyść")
        clear_table_btn.setMinimumHeight(40)
        clear_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #868e96;  /* Szary */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
        """)
        clear_table_btn.clicked.connect(self.clear_items_table)
        
        table_buttons_layout.addWidget(add_item_btn)
        table_buttons_layout.addSpacing(10)  # Dodanie odstępu między przyciskami
        table_buttons_layout.addWidget(clear_table_btn)
        table_buttons_layout.addStretch()
        
        # Dodanie odstępu przed przyciskami
        items_layout.addWidget(self.items_table)
        items_layout.addSpacing(10)
        items_layout.addLayout(table_buttons_layout)
        items_layout.addSpacing(5)  # Dodanie odstępu po przyciskach
        
        main_layout.addWidget(items_group)
        
        # Podsumowanie - GroupBox
        summary_group = QGroupBox("Podsumowanie")
        summary_layout = QGridLayout(summary_group)
        
        # Notatki
        summary_layout.addWidget(QLabel("Notatki:"), 0, 0)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Dodatkowe informacje o zamówieniu...")
        self.notes_input.setMinimumHeight(30)
        summary_layout.addWidget(self.notes_input, 0, 1, 1, 3)
        
        # Upust
        summary_layout.addWidget(QLabel("Upust:"), 1, 0)
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setSuffix(" %")
        self.discount_spin.setDecimals(1)
        self.discount_spin.setSingleStep(5)
        self.discount_spin.setMinimumHeight(30)
        self.discount_spin.valueChanged.connect(self.update_total_amount)
        summary_layout.addWidget(self.discount_spin, 1, 1)
        
        # Kwota całkowita
        summary_layout.addWidget(QLabel("Do zapłaty:"), 1, 2, Qt.AlignRight)
        self.total_amount_label = QLabel("0.00 zł")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4dabf7;")
        summary_layout.addWidget(self.total_amount_label, 1, 3, Qt.AlignRight)
        
        main_layout.addWidget(summary_group)
        
        # Przyciski akcji - lepszy wygląd
        action_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Zapisz zamówienie")
        save_btn.setMinimumWidth(200)  # Zwiększona szerokość
        save_btn.setMinimumHeight(50)  # Zwiększona wysokość
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:pressed {
                background-color: #228be6;
            }
        """)
        save_btn.clicked.connect(self.save_order)
        
        print_btn = QPushButton("🖨️ Drukuj")
        print_btn.setMinimumWidth(120)
        print_btn.setMinimumHeight(50)
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
        print_btn.clicked.connect(self.print_order)
        
        cancel_btn = QPushButton("❌ Anuluj")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(50)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        action_layout.addStretch(1)
        action_layout.addWidget(print_btn)
        action_layout.addSpacing(10)  # Dodanie odstępu między przyciskami
        action_layout.addWidget(cancel_btn)
        action_layout.addSpacing(10)  # Dodanie odstępu między przyciskami
        action_layout.addWidget(save_btn)
        
        main_layout.addSpacing(15)  # Dodanie odstępu przed przyciskami
        main_layout.addLayout(action_layout)
        main_layout.addSpacing(10)  # Dodanie odstępu po przyciskach
        
        # Podłączenie sygnałów
        self.items_table.cellChanged.connect(self.update_total_amount)
        
        # Dodaj domyślny wiersz (po zainicjowaniu wszystkich kontrolek)
        self.add_item_row()
        
        # Załaduj dane zamówienia, jeśli edytujemy istniejące
        if order_id:
            self.load_order_data()
    
    def load_clients(self):
        """Ładuje listę klientów do ComboBox."""
        try:
            cursor = self.conn.cursor()
            
            # Sprawdź, czy kolumna 'phone' istnieje w tabeli 'clients'
            cursor.execute("PRAGMA table_info(clients)")
            columns = cursor.fetchall()
            has_phone_column = any(col['name'] == 'phone' for col in columns)
            
            if has_phone_column:
                cursor.execute("SELECT id, name, phone FROM clients ORDER BY name")
            else:
                cursor.execute("SELECT id, name FROM clients ORDER BY name")
            
            clients = cursor.fetchall()
            
            # Model dla autouzupełniania
            model = QStandardItemModel()
            
            for client in clients:
                # Dodaj do ComboBox z nazwą i telefonem (jeśli dostępny)
                if has_phone_column and 'phone' in client and client['phone']:
                    display_name = f"{client['name']} - {client['phone']}"
                else:
                    display_name = client['name']
                
                self.client_combo.addItem(display_name, client['id'])
                
                # Dodaj do modelu autouzupełniania
                item = QStandardItem(display_name)
                model.appendRow(item)
            
            # Ustaw model autouzupełniania tylko jeśli combo jest edytowalne
            if self.client_combo.isEditable():
                completer = QCompleter(model)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                self.client_combo.setCompleter(completer)
        
        except Exception as e:
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania klientów: {e}",
                NotificationTypes.ERROR
            )
    
    def add_new_client(self):
        """Dodaje nowego klienta bezpośrednio z dialogu zamówienia."""
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Odśwież listę klientów
            self.client_combo.clear()
            self.load_clients()
            
            # Wybierz nowo dodanego klienta
            # Szukamy po nazwie, ponieważ nie mamy bezpośredniego dostępu do ID
            index = self.client_combo.findText(dialog.client_name, Qt.MatchContains)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)
            
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
        name_combo.setMinimumHeight(30)
        name_combo.setStyleSheet("""
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
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: #ffffff;
                selection-background-color: #4dabf7;
                selection-color: #ffffff;
                border: 1px solid #505050;
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
        
        # Przycisk usuwania wiersza
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(40)
        delete_btn.setMaximumHeight(30)
        delete_btn.setToolTip("Usuń pozycję")
        delete_btn.clicked.connect(lambda: self.remove_item_row(row))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ff6b6b;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #505050;
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
            client_id = self.client_combo.currentData()
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