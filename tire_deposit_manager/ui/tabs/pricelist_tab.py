#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zakładki cennika w aplikacji Menadżer Serwisu Opon.
Umożliwia wyświetlanie, edycję cen usług oraz kalkulację kosztów.
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QAbstractItemView, QDialog, QFileDialog,
    QFrame, QSplitter, QToolButton, QScrollArea, QMessageBox,
    QStyledItemDelegate, QSpacerItem, QSizePolicy, QTabWidget,
    QCheckBox, QDoubleSpinBox, QGroupBox, QRadioButton, QSpinBox
)
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtCore import Qt, QEvent, Signal, QRect, QSettings, QSize

from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireDepositManager")

# Wspólne style CSS - scentralizowane do łatwego zarządzania
STYLES = {
    "TABLE_WIDGET": """
        QTableWidget {
            background-color: #2c3034;
            color: #fff;
            border: none;
            gridline-color: #3a3f44;
        }
        QTableWidget::item {
            padding: 5px;
            border-bottom: 1px solid #3a3f44;
        }
        QTableWidget::item:selected {
            background-color: #4dabf7;
            color: white;
        }
        QHeaderView::section {
            background-color: #1a1d21;
            color: white;
            padding: 5px;
            border: none;
            font-weight: bold;
        }
        QTableWidget::item:alternate {
            background-color: #343a40;
        }
    """,
    "CATEGORY_FRAME": """
        QFrame {
            background-color: #2c3034;
            border-radius: 5px;
        }
    """,
    "TITLE_LABEL": """
        QLabel {
            color: white;
            font-size: 16px;
            font-weight: bold;
        }
    """,
    "NORMAL_LABEL": """
        QLabel {
            color: white;
        }
    """,
    "VALUE_LABEL": """
        QLabel {
            color: #4dabf7;
            font-weight: bold;
        }
    """,
    "ADD_BUTTON": """
        QPushButton {
            background-color: #51cf66;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #40c057;
        }
    """,
    "EDIT_BUTTON": """
        QPushButton {
            background-color: #4dabf7;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #339af0;
        }
    """,
    "SAVE_BUTTON": """
        QPushButton {
            background-color: #51cf66;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #40c057;
        }
    """,
    "REMOVE_BUTTON": """
        QPushButton {
            background-color: #fa5252;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #e03131;
        }
    """,
    "UTILITY_BUTTON": """
        QPushButton {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 15px;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color: #2c3034;
        }
    """,
    "COMBO_BOX": """
        QComboBox {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
        }
        QComboBox QAbstractItemView {
            background-color: #343a40;
            color: white;
            border: 1px solid #1a1d21;
            selection-background-color: #4dabf7;
        }
    """,
    "SPINBOX": """
        QSpinBox, QDoubleSpinBox {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 30px;
        }
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            border-radius: 3px;
            background-color: #495057;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-radius: 3px;
            background-color: #495057;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover,
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #6c757d;
        }
    """,
    "LINE_EDIT": """
        QLineEdit {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 30px;
        }
    """,
    "GROUP_BOX": """
        QGroupBox {
            border: 1px solid #495057;
            border-radius: 5px;
            margin-top: 20px;
            padding: 15px;
            color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            color: white;
            font-weight: bold;
        }
    """,
    "CHECK_BOX": """
        QCheckBox {
            color: white;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 1px solid #adb5bd;
        }
        QCheckBox::indicator:checked {
            background-color: #4dabf7;
        }
    """,
    "RADIO_BUTTON": """
        QRadioButton {
            color: white;
        }
        QRadioButton::indicator {
            width: 15px;
            height: 15px;
            border-radius: 7px;
            border: 1px solid #adb5bd;
        }
        QRadioButton::indicator:checked {
            background-color: #4dabf7;
            border: 4px solid #343a40;
        }
    """,
    "SUMMARY_FRAME": """
        QFrame {
            background-color: #4dabf7;
            border-radius: 5px;
            padding: 10px;
        }
        QLabel {
            color: white;
        }
    """,
    "PRICE_LABEL": """
        QLabel {
            color: white;
            font-size: 20px;
            font-weight: bold;
        }
    """,
    "TOTAL_LABEL": """
        QLabel {
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
    """,
    "SERVICE_ITEM_FRAME": """
        QFrame {
            background-color: #343a40;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
        }
    """
}

class PriceListEditorDialog(QDialog):
    """Dialog do edycji cennika usług."""
    
    def __init__(self, parent=None, price_data=None, category=None):
        """
        Inicjalizacja dialogu edycji cennika.
        
        Args:
            parent (QWidget): Widget rodzica
            price_data (dict): Dane cennika do edycji
            category (str): Kategoria cennika
        """
        super().__init__(parent)
        
        self.price_data = price_data or {}
        self.category = category
        self.result_data = {}
        
        self.setWindowTitle(_("Edycja cennika"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Wypełnienie danych
        if price_data:
            self.load_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Kategoria cennika
        category_layout = QHBoxLayout()
        category_label = QLabel(_("Kategoria:"))
        category_label.setStyleSheet(STYLES["NORMAL_LABEL"])
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.category_combo.addItems([
            _("Wymiana opon na felgach aluminiowych"),
            _("Wymiana opon na felgach stalowych"),
            _("Wyważanie kół"),
            _("Naprawy"),
            _("Usługi dodatkowe")
        ])
        
        if self.category:
            index = self.category_combo.findText(self.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        category_layout.addWidget(self.category_combo, 1)
        layout.addLayout(category_layout)
        
        # Struktura tabeli zależna od wybranej kategorii
        self.category_combo.currentTextChanged.connect(self.update_table_structure)
        
        # Tabela z cenami
        self.prices_table = QTableWidget()
        self.prices_table.setStyleSheet(STYLES["TABLE_WIDGET"])
        self.prices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prices_table.setSelectionMode(QTableWidget.SingleSelection)
        self.prices_table.setAlternatingRowColors(True)
        self.prices_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.prices_table)
        
        # Przyciski dodawania/usuwania
        buttons_layout = QHBoxLayout()
        
        self.add_row_button = QPushButton(_("Dodaj pozycję"))
        self.add_row_button.setStyleSheet(STYLES["ADD_BUTTON"])
        self.add_row_button.clicked.connect(self.add_table_row)
        buttons_layout.addWidget(self.add_row_button)
        
        self.remove_row_button = QPushButton(_("Usuń pozycję"))
        self.remove_row_button.setStyleSheet(STYLES["REMOVE_BUTTON"])
        self.remove_row_button.clicked.connect(self.remove_table_row)
        buttons_layout.addWidget(self.remove_row_button)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Przyciski zapisz/anuluj
        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.addStretch()
        
        cancel_button = QPushButton(_("Anuluj"))
        cancel_button.setStyleSheet(STYLES["UTILITY_BUTTON"])
        cancel_button.clicked.connect(self.reject)
        dialog_buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton(_("Zapisz"))
        save_button.setStyleSheet(STYLES["SAVE_BUTTON"])
        save_button.clicked.connect(self.save_prices)
        dialog_buttons_layout.addWidget(save_button)
        
        layout.addLayout(dialog_buttons_layout)
        
        # Inicjalizacja struktury tabeli
        self.update_table_structure()
    
    def update_table_structure(self):
        """Aktualizuje strukturę tabeli w zależności od wybranej kategorii."""
        category = self.category_combo.currentText()
        
        # Czyszczenie tabeli
        self.prices_table.clear()
        
        if _("Wymiana opon na felgach aluminiowych") in category or _("Wymiana opon na felgach stalowych") in category:
            # Tabela dla wymiany opon
            self.prices_table.setColumnCount(3)
            self.prices_table.setHorizontalHeaderLabels([_("Średnica koła"), _("Cena za 1 koło"), _("Cena za 4 koła")])
            
            # Dostosowanie szerokości kolumn
            self.prices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.prices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.prices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            
        elif _("Wyważanie kół") in category:
            # Tabela dla wyważania kół
            self.prices_table.setColumnCount(4)
            self.prices_table.setHorizontalHeaderLabels([
                _("Typ felgi"), _("Średnica koła"), _("Cena za 1 koło"), _("Cena za 4 koła")
            ])
            
            # Dostosowanie szerokości kolumn
            self.prices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.prices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.prices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.prices_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            
        elif _("Naprawy") in category:
            # Tabela dla napraw
            self.prices_table.setColumnCount(2)
            self.prices_table.setHorizontalHeaderLabels([_("Usługa"), _("Cena")])
            
            # Dostosowanie szerokości kolumn
            self.prices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.prices_table.setColumnWidth(1, 150)
            
        elif _("Usługi dodatkowe") in category:
            # Tabela dla usług dodatkowych
            self.prices_table.setColumnCount(2)
            self.prices_table.setHorizontalHeaderLabels([_("Usługa"), _("Cena")])
            
            # Dostosowanie szerokości kolumn
            self.prices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.prices_table.setColumnWidth(1, 150)
        
        # Załaduj dane, jeśli są dostępne
        self.load_data()
    
    def load_data(self):
        """Ładuje dane do tabeli."""
        category = self.category_combo.currentText()
        
        # Sprawdź, czy mamy dane dla tej kategorii
        if category not in self.price_data:
            return
        
        category_data = self.price_data[category]
        
        # Wypełnij tabelę w zależności od kategorii
        if _("Wymiana opon na felgach aluminiowych") in category or _("Wymiana opon na felgach stalowych") in category:
            if "sizes" in category_data:
                sizes_data = category_data["sizes"]
                self.prices_table.setRowCount(len(sizes_data))
                
                for i, item in enumerate(sizes_data):
                    self.prices_table.setItem(i, 0, QTableWidgetItem(item["size"]))
                    self.prices_table.setItem(i, 1, QTableWidgetItem(str(item["price_single"])))
                    self.prices_table.setItem(i, 2, QTableWidgetItem(str(item["price_set"])))
        
        elif _("Wyważanie kół") in category:
            if "balancing" in category_data:
                balancing_data = category_data["balancing"]
                self.prices_table.setRowCount(len(balancing_data))
                
                for i, item in enumerate(balancing_data):
                    self.prices_table.setItem(i, 0, QTableWidgetItem(item["rim_type"]))
                    self.prices_table.setItem(i, 1, QTableWidgetItem(item["size"]))
                    self.prices_table.setItem(i, 2, QTableWidgetItem(str(item["price_single"])))
                    self.prices_table.setItem(i, 3, QTableWidgetItem(str(item["price_set"])))
        
        elif _("Naprawy") in category or _("Usługi dodatkowe") in category:
            key = "repairs" if _("Naprawy") in category else "additional_services"
            if key in category_data:
                services_data = category_data[key]
                self.prices_table.setRowCount(len(services_data))
                
                for i, item in enumerate(services_data):
                    self.prices_table.setItem(i, 0, QTableWidgetItem(item["name"]))
                    self.prices_table.setItem(i, 1, QTableWidgetItem(str(item["price"])))
    
    def add_table_row(self):
        """Dodaje nowy wiersz do tabeli."""
        current_row = self.prices_table.rowCount()
        self.prices_table.insertRow(current_row)
        
        category = self.category_combo.currentText()
        
        # Dodaj domyślne wartości w zależności od kategorii
        if _("Wymiana opon na felgach aluminiowych") in category or _("Wymiana opon na felgach stalowych") in category:
            self.prices_table.setItem(current_row, 0, QTableWidgetItem(_("Nowy rozmiar")))
            self.prices_table.setItem(current_row, 1, QTableWidgetItem("0"))
            self.prices_table.setItem(current_row, 2, QTableWidgetItem("0"))
        
        elif _("Wyważanie kół") in category:
            self.prices_table.setItem(current_row, 0, QTableWidgetItem(_("Aluminiowa")))
            self.prices_table.setItem(current_row, 1, QTableWidgetItem(_("Nowy rozmiar")))
            self.prices_table.setItem(current_row, 2, QTableWidgetItem("0"))
            self.prices_table.setItem(current_row, 3, QTableWidgetItem("0"))
        
        elif _("Naprawy") in category or _("Usługi dodatkowe") in category:
            self.prices_table.setItem(current_row, 0, QTableWidgetItem(_("Nowa usługa")))
            self.prices_table.setItem(current_row, 1, QTableWidgetItem("0"))
        
        # Zaznacz nowo dodany wiersz
        self.prices_table.selectRow(current_row)
    
    def remove_table_row(self):
        """Usuwa zaznaczony wiersz z tabeli."""
        current_row = self.prices_table.currentRow()
        if current_row >= 0:
            self.prices_table.removeRow(current_row)
    
    def save_prices(self):
        """Zapisuje dane cennika."""
        category = self.category_combo.currentText()
        category_data = {}
        
        # Pobierz dane z tabeli
        if _("Wymiana opon na felgach aluminiowych") in category or _("Wymiana opon na felgach stalowych") in category:
            sizes_data = []
            for i in range(self.prices_table.rowCount()):
                size = self.prices_table.item(i, 0).text()
                price_single = float(self.prices_table.item(i, 1).text() or 0)
                price_set = float(self.prices_table.item(i, 2).text() or 0)
                
                sizes_data.append({
                    "size": size,
                    "price_single": price_single,
                    "price_set": price_set
                })
            
            category_data["sizes"] = sizes_data
        
        elif _("Wyważanie kół") in category:
            balancing_data = []
            for i in range(self.prices_table.rowCount()):
                rim_type = self.prices_table.item(i, 0).text()
                size = self.prices_table.item(i, 1).text()
                price_single = float(self.prices_table.item(i, 2).text() or 0)
                price_set = float(self.prices_table.item(i, 3).text() or 0)
                
                balancing_data.append({
                    "rim_type": rim_type,
                    "size": size,
                    "price_single": price_single,
                    "price_set": price_set
                })
            
            category_data["balancing"] = balancing_data
        
        elif _("Naprawy") in category:
            repairs_data = []
            for i in range(self.prices_table.rowCount()):
                name = self.prices_table.item(i, 0).text()
                price = float(self.prices_table.item(i, 1).text() or 0)
                
                repairs_data.append({
                    "name": name,
                    "price": price
                })
            
            category_data["repairs"] = repairs_data
        
        elif _("Usługi dodatkowe") in category:
            services_data = []
            for i in range(self.prices_table.rowCount()):
                name = self.prices_table.item(i, 0).text()
                price = float(self.prices_table.item(i, 1).text() or 0)
                
                services_data.append({
                    "name": name,
                    "price": price
                })
            
            category_data["additional_services"] = services_data
        
        # Przygotuj wynik
        self.result_data = {
            "category": category,
            "data": category_data
        }
        
        # Zamknij dialog z akceptacją
        self.accept()


class ServiceItem(QFrame):
    """Widget reprezentujący pojedynczą usługę w kalkulatorze."""
    
    # Sygnały
    price_changed = Signal()
    removed = Signal()
    
    def __init__(self, service_data, parent=None):
        """
        Inicjalizacja widgetu usługi.
        
        Args:
            service_data (dict): Dane usługi
            parent (QWidget): Widget rodzica
        """
        super().__init__(parent)
        
        self.service_data = service_data
        self.price = 0
        
        self.setObjectName("serviceItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(STYLES["SERVICE_ITEM_FRAME"])
        
        # Inicjalizacja UI
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizacja interfejsu usługi."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Nazwa usługi
        self.service_label = QLabel(self.service_data.get("name", ""))
        self.service_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.service_label, 1)  # 1 = stretch
        
        # Liczba
        quantity_layout = QHBoxLayout()
        quantity_layout.setSpacing(5)
        
        quantity_label = QLabel(_("Ilość:"))
        quantity_label.setStyleSheet("color: white;")
        quantity_layout.addWidget(quantity_label)
        
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setStyleSheet(STYLES["SPINBOX"])
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(self.service_data.get("quantity", 1))
        self.quantity_spinbox.valueChanged.connect(self.update_price)
        quantity_layout.addWidget(self.quantity_spinbox)
        
        layout.addLayout(quantity_layout)
        
        # Cena
        price_layout = QHBoxLayout()
        price_layout.setSpacing(5)
        
        price_label = QLabel(_("Cena:"))
        price_label.setStyleSheet("color: white;")
        price_layout.addWidget(price_label)
        
        self.price_label = QLabel()
        self.price_label.setStyleSheet("color: #4dabf7; font-weight: bold;")
        price_layout.addWidget(self.price_label)
        
        layout.addLayout(price_layout)
        
        # Przycisk usunięcia
        remove_button = QPushButton("✖")
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #fa5252;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                min-width: 30px;
                min-height: 30px;
                max-width: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #e03131;
            }
        """)
        remove_button.setToolTip(_("Usuń pozycję"))
        remove_button.clicked.connect(self.on_remove)
        layout.addWidget(remove_button)
        
        # Aktualizuj cenę
        self.update_price()
    
    def update_price(self):
        """Aktualizuje cenę na podstawie ilości."""
        quantity = self.quantity_spinbox.value()
        base_price = self.service_data.get("price", 0)
        
        # Obliczenie ceny
        self.price = base_price * quantity
        
        # Aktualizacja etykiety
        self.price_label.setText(f"{self.price:.2f} zł")
        
        # Emisja sygnału
        self.price_changed.emit()
    
    def on_remove(self):
        """Obsługuje usunięcie usługi."""
        self.removed.emit()
        self.deleteLater()
    
    def get_service_data(self):
        """Zwraca aktualne dane usługi."""
        return {
            "name": self.service_data.get("name", ""),
            "price": self.service_data.get("price", 0),
            "quantity": self.quantity_spinbox.value(),
            "total_price": self.price
        }

class PriceListTab(QWidget):
    """Zakładka cennika w aplikacji."""
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki cennika.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.price_data = {}
        self.calculator_items = []
        # Inicjalizacja pustej listy od razu w konstruktorze
        self.all_services = []
        
        # Ładowanie danych cennika
        self.load_price_data()
        
        # Inicjalizacja UI
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Panel z cennikiem (węższy)
        price_list_panel = QFrame()
        price_list_panel.setObjectName("priceListPanel")
        price_list_panel.setStyleSheet(STYLES["CATEGORY_FRAME"])
        price_list_layout = QVBoxLayout(price_list_panel)
        price_list_layout.setContentsMargins(15, 15, 15, 15)
        price_list_layout.setSpacing(15)
        
        # Nagłówek cennika z przyciskiem edycji
        header_layout = QHBoxLayout()
        
        header_label = QLabel(_("Cennik usług"))
        header_label.setStyleSheet(STYLES["TITLE_LABEL"])
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        edit_price_list_button = QPushButton(_("Edytuj cennik"))
        edit_price_list_button.setStyleSheet(STYLES["EDIT_BUTTON"])
        edit_price_list_button.clicked.connect(self.edit_price_list)
        header_layout.addWidget(edit_price_list_button)
        
        price_list_layout.addLayout(header_layout)
        
        # Utwórz widok przewijania dla cennika
        price_list_scroll = QScrollArea()
        price_list_scroll.setWidgetResizable(True)
        price_list_scroll.setFrameShape(QFrame.NoFrame)
        
        # Widget zawierający kategorie cennika
        price_list_content = QWidget()
        price_list_content_layout = QVBoxLayout(price_list_content)
        price_list_content_layout.setContentsMargins(0, 0, 0, 0)
        price_list_content_layout.setSpacing(20)
        
        # Dodanie sekcji cennika
        self.create_price_list_sections(price_list_content_layout)
        
        # Ustawienie widgetu w obszarze przewijania
        price_list_scroll.setWidget(price_list_content)
        
        # Dodanie obszaru przewijania do panelu cennika
        price_list_layout.addWidget(price_list_scroll)
        
        # Dodanie panelu cennika do głównego układu (proporcja 1 - węższy)
        main_layout.addWidget(price_list_panel, 1)  # Proporcja 1 (węższy)
        
        # Panel kalkulatora cen (szerszy)
        calculator_panel = QFrame()
        calculator_panel.setObjectName("calculatorPanel")
        calculator_panel.setStyleSheet(STYLES["CATEGORY_FRAME"])
        calculator_layout = QVBoxLayout(calculator_panel)
        calculator_layout.setContentsMargins(15, 15, 15, 15)
        calculator_layout.setSpacing(15)
        
        # Nagłówek kalkulatora
        calculator_header = QLabel(_("Kalkulator cen"))
        calculator_header.setStyleSheet(STYLES["TITLE_LABEL"])
        calculator_layout.addWidget(calculator_header)
        
        # Panel wyboru usług
        service_selection_frame = QFrame()
        service_selection_frame.setStyleSheet("background-color: #343a40; border-radius: 5px;")
        service_selection_layout = QVBoxLayout(service_selection_frame)
        service_selection_layout.setContentsMargins(15, 15, 15, 15)
        service_selection_layout.setSpacing(10)
        
        # Etykieta wyboru usług
        selection_label = QLabel(_("Wybierz usługi"))
        selection_label.setStyleSheet("color: white; font-weight: bold;")
        service_selection_layout.addWidget(selection_label)
        
        # Wyszukiwarka usług z autouzupełnianiem
        search_service_layout = QHBoxLayout()
        search_service_layout.setSpacing(10)
        
        service_label = QLabel(_("Usługa:"))
        service_label.setStyleSheet("color: white;")
        search_service_layout.addWidget(service_label)
        
        self.service_search = QLineEdit()
        self.service_search.setStyleSheet(STYLES["LINE_EDIT"])
        self.service_search.setPlaceholderText(_("Szukaj usługi..."))
        search_service_layout.addWidget(self.service_search, 1)  # 1 = stretch
        
        service_selection_layout.addLayout(search_service_layout)
        
        # Lista wszystkich usług podzielonych na kategorie
        all_services_layout = QVBoxLayout()
        all_services_layout.setSpacing(5)
        
        # Przewijana lista usług
        services_scroll = QScrollArea()
        services_scroll.setWidgetResizable(True)
        services_scroll.setFrameShape(QFrame.NoFrame)
        services_scroll.setStyleSheet("background-color: transparent;")
        
        # Widget zawierający wszystkie usługi
        services_content = QWidget()
        services_content.setStyleSheet("background-color: transparent;")
        self.services_content_layout = QVBoxLayout(services_content)
        self.services_content_layout.setContentsMargins(0, 0, 0, 0)
        self.services_content_layout.setSpacing(10)
        
        # Wypełnienie listy usług
        self.populate_services_list()
        
        # Ustawienie widgetu w obszarze przewijania
        services_scroll.setWidget(services_content)
        services_scroll.setMaximumHeight(200)  # Ograniczenie wysokości
        
        all_services_layout.addWidget(services_scroll)
        service_selection_layout.addLayout(all_services_layout)
        
        calculator_layout.addWidget(service_selection_frame)
        
        # Lista wybranych usług
        selected_services_label = QLabel(_("Wybrane usługi"))
        selected_services_label.setStyleSheet(STYLES["TITLE_LABEL"])
        calculator_layout.addWidget(selected_services_label)
        
        # Kontener na wybrane usługi
        self.selected_services_container = QWidget()
        self.selected_services_layout = QVBoxLayout(self.selected_services_container)
        self.selected_services_layout.setContentsMargins(0, 0, 0, 0)
        self.selected_services_layout.setSpacing(10)
        self.selected_services_layout.addStretch(1)
        
        # Obszar przewijania dla wybranych usług
        services_scroll = QScrollArea()
        services_scroll.setWidgetResizable(True)
        services_scroll.setWidget(self.selected_services_container)
        services_scroll.setFrameShape(QFrame.NoFrame)
        
        calculator_layout.addWidget(services_scroll, 1)  # 1 = stretch
        
        # Podsumowanie
        summary_frame = QFrame()
        summary_frame.setStyleSheet(STYLES["SUMMARY_FRAME"])
        summary_layout = QVBoxLayout(summary_frame)
        
        # Przycisk czyszczenia kalkulatora
        clear_button = QPushButton(_("Wyczyść kalkulator"))
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #343a40;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #212529;
            }
        """)
        clear_button.clicked.connect(self.clear_calculator)
        summary_layout.addWidget(clear_button)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: white; max-height: 1px;")
        summary_layout.addWidget(separator)
        
        # Suma
        total_layout = QHBoxLayout()
        
        total_label = QLabel(_("RAZEM:"))
        total_label.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        total_layout.addWidget(total_label)
        
        self.total_price_label = QLabel("0.00 zł")
        self.total_price_label.setStyleSheet(STYLES["TOTAL_LABEL"])
        self.total_price_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_layout.addWidget(self.total_price_label)
        
        summary_layout.addLayout(total_layout)
        
        calculator_layout.addWidget(summary_frame)
        
        # Dodanie kalkulatora do głównego układu (proporcja 2 - szerszy)
        main_layout.addWidget(calculator_panel, 2)  # Proporcja 2 (szerszy)

        # Inicjalizacja wyszukiwania usług
        self.setup_service_search()

        # Wypełnienie listy usług (teraz self.all_services jest już zainicjalizowane)
        self.populate_services_list()
    
    def create_price_list_sections(self, parent_layout):
        """
        Tworzy sekcje cennika.
        
        Args:
            parent_layout (QLayout): Układ rodzica
        """
        # Sprawdź czy mamy dane cennika
        if not self.price_data:
            empty_label = QLabel(_("Brak danych cennika. Kliknij 'Edytuj cennik', aby dodać."))
            empty_label.setStyleSheet("color: white; font-style: italic;")
            parent_layout.addWidget(empty_label)
            return
        
        # Sekcja wymiany opon na felgach aluminiowych
        self.create_rim_replacement_section(
            parent_layout,
            _("Wymiana opon na felgach aluminiowych"),
            self.price_data.get(_("Wymiana opon na felgach aluminiowych"), {})
        )
        
        # Sekcja wymiany opon na felgach stalowych
        self.create_rim_replacement_section(
            parent_layout,
            _("Wymiana opon na felgach stalowych"),
            self.price_data.get(_("Wymiana opon na felgach stalowych"), {})
        )
        
        # Sekcja wyważania kół
        self.create_wheel_balancing_section(
            parent_layout,
            _("Wyważanie kół"),
            self.price_data.get(_("Wyważanie kół"), {})
        )
        
        # Sekcja napraw
        self.create_services_section(
            parent_layout,
            _("Naprawy"),
            self.price_data.get(_("Naprawy"), {}).get("repairs", [])
        )
        
        # Sekcja usług dodatkowych
        self.create_services_section(
            parent_layout,
            _("Usługi dodatkowe"),
            self.price_data.get(_("Usługi dodatkowe"), {}).get("additional_services", [])
        )
    
    def create_rim_replacement_section(self, parent_layout, title, data):
        """
        Tworzy sekcję wymiany opon (aluminiowe lub stalowe).
        
        Args:
            parent_layout (QLayout): Układ rodzica
            title (str): Tytuł sekcji
            data (dict): Dane sekcji
        """
        if not data or "sizes" not in data:
            return
        
        # Ramka sekcji
        section_frame = QFrame()
        section_frame.setStyleSheet("background-color: #343a40; border-radius: 5px;")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(15, 15, 15, 15)
        section_layout.setSpacing(10)
        
        # Tytuł sekcji
        section_title = QLabel(title)
        section_title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        section_layout.addWidget(section_title)
        
        # Tabela z cenami
        table = QTableWidget()
        table.setStyleSheet(STYLES["TABLE_WIDGET"])
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([_("Średnica koła"), _("Cena za 1 koło"), _("Cena za 4 koła")])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Wyłącz przewijanie pionowe
        
        # Dostosowanie szerokości kolumn
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Wypełnienie tabeli
        sizes_data = data.get("sizes", [])
        table.setRowCount(len(sizes_data))
        
        for i, item in enumerate(sizes_data):
            table.setItem(i, 0, QTableWidgetItem(item["size"]))
            table.setItem(i, 1, QTableWidgetItem(f"{item['price_single']:.2f} zł"))
            table.setItem(i, 2, QTableWidgetItem(f"{item['price_set']:.2f} zł"))
        
        # Dopasowanie wysokości tabeli do zawartości - bez przewijania
        table.setFixedHeight(len(sizes_data) * 30 + 30)
        
        section_layout.addWidget(table)
        
        # Informacje dodatkowe
        if "additional_info" in data:
            info_label = QLabel(data["additional_info"])
            info_label.setStyleSheet("color: #adb5bd; font-style: italic;")
            info_label.setWordWrap(True)
            section_layout.addWidget(info_label)
        
        parent_layout.addWidget(section_frame)

    def create_wheel_balancing_section(self, parent_layout, title, data):
        """
        Tworzy sekcję wyważania kół.
        
        Args:
            parent_layout (QLayout): Układ rodzica
            title (str): Tytuł sekcji
            data (dict): Dane sekcji
        """
        if not data or "balancing" not in data:
            return
        
        # Ramka sekcji
        section_frame = QFrame()
        section_frame.setStyleSheet("background-color: #343a40; border-radius: 5px;")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(15, 15, 15, 15)
        section_layout.setSpacing(10)
        
        # Tytuł sekcji
        section_title = QLabel(title)
        section_title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        section_layout.addWidget(section_title)
        
        # Tabela z cenami
        table = QTableWidget()
        table.setStyleSheet(STYLES["TABLE_WIDGET"])
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            _("Typ felgi"), _("Średnica koła"), _("Cena za 1 koło"), _("Cena za 4 koła")
        ])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Wyłącz przewijanie pionowe
        
        # Dostosowanie szerokości kolumn
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        # Wypełnienie tabeli
        balancing_data = data.get("balancing", [])
        table.setRowCount(len(balancing_data))
        
        for i, item in enumerate(balancing_data):
            table.setItem(i, 0, QTableWidgetItem(item["rim_type"]))
            table.setItem(i, 1, QTableWidgetItem(item["size"]))
            table.setItem(i, 2, QTableWidgetItem(f"{item['price_single']:.2f} zł"))
            table.setItem(i, 3, QTableWidgetItem(f"{item['price_set']:.2f} zł"))
        
        # Dopasowanie wysokości tabeli do zawartości - bez przewijania
        table.setFixedHeight(len(balancing_data) * 30 + 30)
        
        section_layout.addWidget(table)
        
        parent_layout.addWidget(section_frame)

    def create_services_section(self, parent_layout, title, services_data):
        """
        Tworzy sekcję usług (naprawy lub usługi dodatkowe).
        
        Args:
            parent_layout (QLayout): Układ rodzica
            title (str): Tytuł sekcji
            services_data (list): Dane usług
        """
        if not services_data:
            return
        
        # Ramka sekcji
        section_frame = QFrame()
        section_frame.setStyleSheet("background-color: #343a40; border-radius: 5px;")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(15, 15, 15, 15)
        section_layout.setSpacing(10)
        
        # Tytuł sekcji
        section_title = QLabel(title)
        section_title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        section_layout.addWidget(section_title)
        
        # Tabela z cenami
        table = QTableWidget()
        table.setStyleSheet(STYLES["TABLE_WIDGET"])
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([_("Usługa"), _("Cena")])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Wyłącz przewijanie pionowe
        
        # Dostosowanie szerokości kolumn
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 150)
        
        # Wypełnienie tabeli
        table.setRowCount(len(services_data))
        
        for i, item in enumerate(services_data):
            table.setItem(i, 0, QTableWidgetItem(item["name"]))
            table.setItem(i, 1, QTableWidgetItem(f"{item['price']:.2f} zł"))
        
        # Dopasowanie wysokości tabeli do zawartości - bez przewijania
        table.setFixedHeight(len(services_data) * 30 + 30)
        
        section_layout.addWidget(table)
        
        parent_layout.addWidget(section_frame)
    
    def load_price_data(self):
        """Ładuje dane cennika z bazy danych lub pliku."""
        try:
            # Sprawdź czy istnieje tabela cennika w bazie danych
            cursor = self.conn.cursor()
            
            # Sprawdź czy tabela istnieje
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='price_list'
            """)
            
            if cursor.fetchone():
                # Pobierz dane z bazy
                cursor.execute("SELECT data FROM price_list WHERE id = 1")
                result = cursor.fetchone()
                
                if result and result[0]:
                    try:
                        self.price_data = json.loads(result[0])
                        logger.info("Dane cennika załadowane z bazy danych")
                    except json.JSONDecodeError:
                        logger.error("Błąd dekodowania danych cennika z bazy danych")
                        self.price_data = {}
                else:
                    # Brak danych w bazie
                    logger.info("Brak danych cennika w bazie danych")
                    self.init_default_prices()
            else:
                # Utwórz tabelę i dodaj domyślne dane
                logger.info("Tworzenie tabeli cennika w bazie danych")
                
                cursor.execute("""
                    CREATE TABLE price_list (
                        id INTEGER PRIMARY KEY,
                        data TEXT,
                        last_updated TEXT
                    )
                """)
                
                self.init_default_prices()
                self.save_price_data()
                
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych cennika: {e}")
            self.init_default_prices()
    
    def init_default_prices(self):
        """Inicjalizuje domyślne ceny."""
        self.price_data = {
            _("Wymiana opon na felgach aluminiowych"): {
                "sizes": [
                    {"size": "do 14\"", "price_single": 36, "price_set": 130},
                    {"size": "15\"", "price_single": 41, "price_set": 150},
                    {"size": "16\"", "price_single": 45, "price_set": 160},
                    {"size": "17\"", "price_single": 47, "price_set": 170},
                    {"size": "18\"", "price_single": 49, "price_set": 180},
                    {"size": "19\"", "price_single": 53, "price_set": 200},
                    {"size": "20\"", "price_single": 60, "price_set": 230}
                ],
                "additional_info": "* dopłata do opon typu Run Flat: 10 zł/szt\n** dopłata do opon terenowych Off Road: 10 zł/szt"
            },
            _("Wymiana opon na felgach stalowych"): {
                "sizes": [
                    {"size": "do 14\"", "price_single": 35, "price_set": 120},
                    {"size": "15\"", "price_single": 35, "price_set": 120},
                    {"size": "16\"", "price_single": 36, "price_set": 130},
                    {"size": "14\"-15\" (dostawcze)", "price_single": 40, "price_set": 150},
                    {"size": "16\"-17\" (dostawcze)", "price_single": 45, "price_set": 170}
                ]
            },
            _("Wyważanie kół"): {
                "balancing": [
                    {"rim_type": "Aluminiowa", "size": "14\"-18\"", "price_single": 35, "price_set": 120},
                    {"rim_type": "Aluminiowa", "size": "19\"-22\"", "price_single": 40, "price_set": 140},
                    {"rim_type": "Stalowa", "size": "13\"-16\"", "price_single": 30, "price_set": 100},
                    {"rim_type": "Stalowa", "size": "dostawcze", "price_single": 40, "price_set": 140}
                ]
            },
            _("Naprawy"): {
                "repairs": [
                    {"name": "Naprawa na zimno", "price": 50},
                    {"name": "Naprawa na gorąco 110TL", "price": 70},
                    {"name": "Naprawa na gorąco 115TL", "price": 80},
                    {"name": "Naprawa na gorąco 120TL", "price": 100},
                    {"name": "Wymiana zaworu", "price": 20},
                    {"name": "Uszczelnienie koła", "price": 20},
                    {"name": "Wymiana opony z wyważeniem - motocykl", "price": 70},
                    {"name": "Wymiana opony - motocykl", "price": 40},
                    {"name": "Wyważenie koła - motocykl", "price": 40},
                    {"name": "Odkręcenie koła zapasowego", "price": 50},
                    {"name": "Demontaż opony z felgi", "price": 10},
                    {"name": "Diagnostyka TPMS", "price": 100},
                    {"name": "Programowanie TPMS", "price": 100}
                ]
            },
            _("Usługi dodatkowe"): {
                "additional_services": [
                    {"name": "Worek na opony/koła", "price": 2},
                    {"name": "Zawór gumowy", "price": 8},
                    {"name": "Zawór wzmacniany", "price": 10},
                    {"name": "Konserwacja opon (4szt)", "price": 80},
                    {"name": "Konserwacja kół (4szt)", "price": 100},
                    {"name": "Przechowywanie (4szt na 1 sezon)", "price": 120}
                ]
            }
        }
    
    def save_price_data(self):
        """Zapisuje dane cennika do bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Konwersja danych do formatu JSON
            data_json = json.dumps(self.price_data, ensure_ascii=False)
            
            # Sprawdź czy istnieje rekord
            cursor.execute("SELECT id FROM price_list WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                # Aktualizuj istniejący rekord
                cursor.execute(
                    "UPDATE price_list SET data = ?, last_updated = ? WHERE id = 1",
                    (data_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
            else:
                # Dodaj nowy rekord
                cursor.execute(
                    "INSERT INTO price_list (id, data, last_updated) VALUES (?, ?, ?)",
                    (1, data_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
            
            self.conn.commit()
            logger.info("Dane cennika zapisane do bazy danych")
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania danych cennika: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zapisywania cennika: {e}",
                NotificationTypes.ERROR
            )
    
    def edit_price_list(self):
        """Otwiera dialog edycji cennika."""
        try:
            dialog = PriceListEditorDialog(self, self.price_data)
            
            if dialog.exec() == QDialog.Accepted:
                # Aktualizacja danych cennika
                category = dialog.result_data["category"]
                category_data = dialog.result_data["data"]
                
                self.price_data[category] = category_data
                
                # Zapisanie danych
                self.save_price_data()
                
                # Odświeżenie widoku
                self.refresh_price_list()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Cennik został zaktualizowany."),
                    NotificationTypes.SUCCESS
                )
                
        except Exception as e:
            logger.error(f"Błąd podczas edycji cennika: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas edycji cennika: {e}",
                NotificationTypes.ERROR
            )
    
    def refresh_price_list(self):
        """Odświeża widok cennika."""
        try:
            # Znajdź układ zawierający sekcje cennika
            price_list_content = None
            
            # Przeszukaj hierarchię widgetów, aby znaleźć zawartość cennika
            for child in self.findChildren(QScrollArea):
                if child.parentWidget() and "priceListPanel" in child.parentWidget().objectName():
                    price_list_content = child.widget()
                    break
            
            if price_list_content:
                # Usuń istniejące elementy
                for i in reversed(range(price_list_content.layout().count())):
                    item = price_list_content.layout().itemAt(i)
                    if item.widget():
                        item.widget().deleteLater()
                
                # Dodaj nowe sekcje
                self.create_price_list_sections(price_list_content.layout())
                
                # Aktualizuj listę usług w kalkulatorze
                self.update_service_items()
            
        except Exception as e:
            logger.error(f"Błąd podczas odświeżania cennika: {e}")
    
    def update_service_items(self):
        """Aktualizuje listę usług w zależności od wybranej kategorii."""
        try:
            category = self.category_combo.currentText()
            self.service_combo.clear()
            
            if category in self.price_data:
                if _("Wymiana opon na felgach") in category:
                    # Dla wymiany opon
                    for size_data in self.price_data[category].get("sizes", []):
                        self.service_combo.addItem(
                            f"{_('Wymiana opon')} {size_data['size']} - {size_data['price_set']:.2f} zł",
                            {
                                "name": f"{_('Wymiana opon')} {size_data['size']}",
                                "price": size_data['price_set'],
                                "category": category
                            }
                        )
                        
                        self.service_combo.addItem(
                            f"{_('Wymiana opony')} {size_data['size']} - {size_data['price_single']:.2f} zł",
                            {
                                "name": f"{_('Wymiana opony')} {size_data['size']}",
                                "price": size_data['price_single'],
                                "category": category
                            }
                        )
                
                elif _("Wyważanie kół") in category:
                    # Dla wyważania kół
                    for balancing_data in self.price_data[category].get("balancing", []):
                        self.service_combo.addItem(
                            f"{_('Wyważanie kół')} {balancing_data['rim_type']} {balancing_data['size']} - {balancing_data['price_set']:.2f} zł",
                            {
                                "name": f"{_('Wyważanie kół')} {balancing_data['rim_type']} {balancing_data['size']}",
                                "price": balancing_data['price_set'],
                                "category": category
                            }
                        )
                        
                        self.service_combo.addItem(
                            f"{_('Wyważanie koła')} {balancing_data['rim_type']} {balancing_data['size']} - {balancing_data['price_single']:.2f} zł",
                            {
                                "name": f"{_('Wyważanie koła')} {balancing_data['rim_type']} {balancing_data['size']}",
                                "price": balancing_data['price_single'],
                                "category": category
                            }
                        )
                
                elif _("Naprawy") in category:
                    # Dla napraw
                    for repair_data in self.price_data[category].get("repairs", []):
                        self.service_combo.addItem(
                            f"{repair_data['name']} - {repair_data['price']:.2f} zł",
                            {
                                "name": repair_data['name'],
                                "price": repair_data['price'],
                                "category": category
                            }
                        )
                
                elif _("Usługi dodatkowe") in category:
                    # Dla usług dodatkowych
                    for service_data in self.price_data[category].get("additional_services", []):
                        self.service_combo.addItem(
                            f"{service_data['name']} - {service_data['price']:.2f} zł",
                            {
"name": service_data['name'],
                                "price": service_data['price'],
                                "category": category
                            }
                        )
        
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji listy usług: {e}")
    
    def add_service_to_calculator(self):
        """Dodaje wybraną usługę do kalkulatora."""
        try:
            current_index = self.service_combo.currentIndex()
            
            if current_index >= 0:
                service_data = self.service_combo.itemData(current_index)
                
                if service_data:
                    # Tworzenie nowego elementu usługi
                    service_widget = ServiceItem(service_data)
                    service_widget.price_changed.connect(self.update_total_price)
                    service_widget.removed.connect(self.update_total_price)
                    
                    # Dodanie do layoutu przed elementem stretch
                    count = self.selected_services_layout.count()
                    if count > 0 and self.selected_services_layout.itemAt(count - 1).spacerItem():
                        self.selected_services_layout.insertWidget(count - 1, service_widget)
                    else:
                        self.selected_services_layout.addWidget(service_widget)
                    
                    # Aktualizacja sumy
                    self.update_total_price()
                    
                    # Dodanie do listy elementów kalkulatora
                    self.calculator_items.append(service_widget)
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"{_('Dodano usługę:')} {service_data['name']}",
                        NotificationTypes.SUCCESS,
                        3000
                    )
        
        except Exception as e:
            logger.error(f"Błąd podczas dodawania usługi do kalkulatora: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania usługi: {e}",
                NotificationTypes.ERROR
            )
    
    def update_total_price(self):
        """Aktualizuje łączną cenę w kalkulatorze."""
        try:
            total_price = 0
            
            # Pobierz wszystkie widgety usług
            for i in range(self.selected_services_layout.count()):
                item = self.selected_services_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), ServiceItem):
                    total_price += item.widget().price
            
            # Aktualizacja etykiety sumy
            self.total_price_label.setText(f"{total_price:.2f} zł")
            
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji ceny: {e}")
    
    def clear_calculator(self):
        """Czyści kalkulator z wybranych usług."""
        try:
            # Potwierdzenie
            if self.calculator_items:
                reply = QMessageBox.question(
                    self,
                    _("Potwierdź czyszczenie"),
                    _("Czy na pewno chcesz wyczyścić kalkulator?"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Usuń wszystkie widgety usług
                    for i in reversed(range(self.selected_services_layout.count())):
                        item = self.selected_services_layout.itemAt(i)
                        if item.widget() and isinstance(item.widget(), ServiceItem):
                            item.widget().deleteLater()
                    
                    # Wyczyść listę elementów
                    self.calculator_items.clear()
                    
                    # Dodaj stretch
                    if self.selected_services_layout.count() == 0:
                        self.selected_services_layout.addStretch(1)
                    
                    # Aktualizacja sumy
                    self.update_total_price()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        _("Kalkulator został wyczyszczony."),
                        NotificationTypes.INFO,
                        3000
                    )
        
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia kalkulatora: {e}")
    
    def get_calculator_data(self):
        """
        Zwraca dane kalkulatora.
        
        Returns:
            dict: Dane kalkulatora
        """
        calculator_data = {
            "services": [],
            "total_price": 0
        }
        
        try:
            # Pobierz wszystkie widgety usług
            for i in range(self.selected_services_layout.count()):
                item = self.selected_services_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), ServiceItem):
                    service_widget = item.widget()
                    service_data = service_widget.get_service_data()
                    calculator_data["services"].append(service_data)
                    calculator_data["total_price"] += service_data["total_price"]
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania danych kalkulatora: {e}")
        
        return calculator_data
    
    def generate_price_quote(self):
        """Generuje wycenę na podstawie kalkulatora."""
        try:
            # Pobierz dane kalkulatora
            calculator_data = self.get_calculator_data()
            
            if not calculator_data["services"]:
                NotificationManager.get_instance().show_notification(
                    _("Dodaj usługi do kalkulatora, aby wygenerować wycenę."),
                    NotificationTypes.WARNING,
                    3000
                )
                return
            
            # Dialog wygenerowania wyceny - można zaimplementować w przyszłości
            # Jako przykład, możemy wygenerować prosty raport w konsoli
            print("=== WYCENA USŁUG ===")
            print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print("-------------------")
            
            for service in calculator_data["services"]:
                print(f"{service['name']} x{service['quantity']}: {service['total_price']:.2f} zł")
            
            print("-------------------")
            print(f"RAZEM: {calculator_data['total_price']:.2f} zł")
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Wycena została wygenerowana."),
                NotificationTypes.SUCCESS,
                3000
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania wyceny: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania wyceny: {e}",
                NotificationTypes.ERROR
            )
    
    def refresh_data(self):
        """Odświeża dane w zakładce."""
        self.load_price_data()
        self.refresh_price_list()
        
        NotificationManager.get_instance().show_notification(
            _("Dane cennika zostały odświeżone."),
            NotificationTypes.INFO,
            3000
        )

    def setup_service_search(self):
        """Konfiguruje funkcjonalność wyszukiwania usług z autouzupełnianiem."""
        # Lista wszystkich usług do autouzupełniania
        self.all_services = []
        
        # Wypełnienie listy wszystkich usług
        for category, data in self.price_data.items():
            if _("Wymiana opon") in category and "sizes" in data:
                for size_data in data["sizes"]:
                    self.all_services.append({
                        "name": f"{_('Wymiana opon')} {size_data['size']}",
                        "display_name": f"{_('Wymiana opon')} {size_data['size']} - {size_data['price_set']:.2f} zł",
                        "price": size_data['price_set'],
                        "category": category
                    })
                    
                    self.all_services.append({
                        "name": f"{_('Wymiana opony')} {size_data['size']}",
                        "display_name": f"{_('Wymiana opony')} {size_data['size']} - {size_data['price_single']:.2f} zł",
                        "price": size_data['price_single'],
                        "category": category
                    })
            
            elif _("Wyważanie kół") in category and "balancing" in data:
                for balancing_data in data["balancing"]:
                    self.all_services.append({
                        "name": f"{_('Wyważanie kół')} {balancing_data['rim_type']} {balancing_data['size']}",
                        "display_name": f"{_('Wyważanie kół')} {balancing_data['rim_type']} {balancing_data['size']} - {balancing_data['price_set']:.2f} zł",
                        "price": balancing_data['price_set'],
                        "category": category
                    })
                    
                    self.all_services.append({
                        "name": f"{_('Wyważanie koła')} {balancing_data['rim_type']} {balancing_data['size']}",
                        "display_name": f"{_('Wyważanie koła')} {balancing_data['rim_type']} {balancing_data['size']} - {balancing_data['price_single']:.2f} zł",
                        "price": balancing_data['price_single'],
                        "category": category
                    })
            
            elif _("Naprawy") in category and "repairs" in data:
                for repair_data in data["repairs"]:
                    self.all_services.append({
                        "name": repair_data['name'],
                        "display_name": f"{repair_data['name']} - {repair_data['price']:.2f} zł",
                        "price": repair_data['price'],
                        "category": category
                    })
            
            elif _("Usługi dodatkowe") in category and "additional_services" in data:
                for service_data in data["additional_services"]:
                    self.all_services.append({
                        "name": service_data['name'],
                        "display_name": f"{service_data['name']} - {service_data['price']:.2f} zł",
                        "price": service_data['price'],
                        "category": category
                    })
        
        # Połączenie z edycją pola wyszukiwania
        self.service_search.textChanged.connect(self.filter_services)
        self.service_search.returnPressed.connect(self.add_service_from_search)
    
    def filter_services(self, text):
        """
        Filtruje listę usług na podstawie wpisanego tekstu.
        
        Args:
            text (str): Tekst wyszukiwania
        """
        # Czyszczenie istniejących elementów z listy
        self.clear_services_list()
        
        # Jeśli tekst jest pusty, pokazuj wszystkie usługi pogrupowane
        if not text:
            self.populate_services_list()
            return
        
        # Filtrowanie usług
        filtered_services = [
            service for service in self.all_services
            if text.lower() in service["name"].lower()
        ]
        
        # Wyświetlenie przefiltrowanych usług
        if filtered_services:
            # Dodaj tytuł dla wyników wyszukiwania
            results_label = QLabel(_("Wyniki wyszukiwania"))
            results_label.setStyleSheet("color: white; font-weight: bold;")
            self.services_content_layout.addWidget(results_label)
            
            # Dodaj przefiltrowane usługi
            for service in filtered_services:
                service_btn = QPushButton(service["display_name"])
                service_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2c3034;
                        color: white;
                        text-align: left;
                        border-radius: 5px;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #4dabf7;
                    }
                """)
                service_btn.clicked.connect(lambda checked=False, s=service: self.add_service_to_calculator_data(s))
                self.services_content_layout.addWidget(service_btn)
        else:
            # Komunikat o braku wyników
            no_results_label = QLabel(_("Brak wyników dla: ") + text)
            no_results_label.setStyleSheet("color: #adb5bd; font-style: italic;")
            self.services_content_layout.addWidget(no_results_label)
        
        # Dodaj elastyczny odstęp na końcu
        self.services_content_layout.addStretch(1)
    
    def add_service_from_search(self):
        """Dodaje usługę na podstawie wyszukiwania po naciśnięciu Enter."""
        search_text = self.service_search.text()
        
        if not search_text:
            return
        
        # Wyszukaj usługę
        matching_services = [
            service for service in self.all_services
            if search_text.lower() in service["name"].lower()
        ]
        
        if matching_services:
            # Dodaj pierwszą pasującą usługę
            self.add_service_to_calculator_data(matching_services[0])
            
            # Wyczyść pole wyszukiwania
            self.service_search.clear()
        else:
            # Powiadomienie o braku wyników
            NotificationManager.get_instance().show_notification(
                _("Nie znaleziono pasującej usługi."),
                NotificationTypes.WARNING,
                3000
            )
    
    def clear_services_list(self):
        """Czyści listę usług."""
        for i in reversed(range(self.services_content_layout.count())):
            item = self.services_content_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.services_content_layout.removeItem(item)
    
    def populate_services_list(self):
        """Wypełnia listę usług pogrupowanych według kategorii."""
        # Upewnij się, że all_services istnieje
        if not hasattr(self, 'all_services') or self.all_services is None:
            self.all_services = []
            # Możliwe, że setup_service_search nie został jeszcze wywołany
            self.setup_service_search()
            
        # Bieżąca kategoria
        current_category = None
        category_label = None
        
        # Kategorie w kolejności
        categories_order = [
            _("Wymiana opon na felgach aluminiowych"),
            _("Wymiana opon na felgach stalowych"),
            _("Wyważanie kół"),
            _("Naprawy"),
            _("Usługi dodatkowe")
        ]
        
        # Sortowanie usług według kategorii
        for category in categories_order:
            # Filtrowanie usług dla tej kategorii
            category_services = [
                service for service in self.all_services
                if service["category"] == category
            ]
            
            if category_services:
                # Dodaj etykietę kategorii
                category_label = QLabel(category)
                category_label.setStyleSheet("color: white; font-weight: bold;")
                self.services_content_layout.addWidget(category_label)
                
                # Dodaj usługi tej kategorii
                for service in category_services:
                    service_btn = QPushButton(service["display_name"])
                    service_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2c3034;
                            color: white;
                            text-align: left;
                            border-radius: 5px;
                            padding: 8px;
                        }
                        QPushButton:hover {
                            background-color: #4dabf7;
                        }
                    """)
                    service_btn.clicked.connect(lambda checked=False, s=service: self.add_service_to_calculator_data(s))
                    self.services_content_layout.addWidget(service_btn)
        
        # Dodaj elastyczny odstęp na końcu
        self.services_content_layout.addStretch(1)
    
    def add_service_to_calculator_data(self, service_data):
        """
        Dodaje wybraną usługę do kalkulatora na podstawie danych.
        
        Args:
            service_data (dict): Dane usługi
        """
        try:
            # Tworzenie nowego elementu usługi
            service_widget = ServiceItem(service_data)
            service_widget.price_changed.connect(self.update_total_price)
            service_widget.removed.connect(self.update_total_price)
            
            # Dodanie do layoutu przed elementem stretch
            count = self.selected_services_layout.count()
            if count > 0 and self.selected_services_layout.itemAt(count - 1).spacerItem():
                self.selected_services_layout.insertWidget(count - 1, service_widget)
            else:
                self.selected_services_layout.addWidget(service_widget)
            
            # Aktualizacja sumy
            self.update_total_price()
            
            # Dodanie do listy elementów kalkulatora
            self.calculator_items.append(service_widget)
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"{_('Dodano usługę:')} {service_data['name']}",
                NotificationTypes.SUCCESS,
                3000
            )
        
        except Exception as e:
            logger.error(f"Błąd podczas dodawania usługi do kalkulatora: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania usługi: {e}",
                NotificationTypes.ERROR
            )