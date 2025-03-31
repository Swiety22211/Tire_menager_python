#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zakładki magazynu opon w aplikacji Menadżer Serwisu Opon.
Obsługuje zarządzanie zapasem nowych i używanych opon, ewidencję, wycenę oraz drukowanie etykiet.
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
    QSpinBox, QDoubleSpinBox, QDateEdit, QCheckBox, QGridLayout
)
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtCore import Qt, QEvent, Signal, QDate, QDateTime, QRect, QSettings
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtWebEngineWidgets import QWebEngineView

from ui.dialogs.inventory_dialog import InventoryDialog
from utils.exporter import export_data_to_excel, export_data_to_pdf
from utils.paths import ICONS_DIR, CONFIG_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireInventoryManager")

# Wspólne style CSS - scentralizowane do łatwego zarządzania
# Wykorzystanie tych samych styli co w deposits_tab.py dla spójności wyglądu
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
    "SEARCH_PANEL": """
        QFrame#searchPanel {
            background-color: #2c3034;
            border-radius: 5px;
        }
    """,
    "SEARCH_BOX": """
        QFrame#searchBox {
            background-color: #343a40;
            border-radius: 5px;
        }
    """,
    "SEARCH_FIELD": """
        QLineEdit#searchField {
            border: none;
            background-color: transparent;
            color: white;
            font-size: 14px;
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
    "FILTER_BUTTON": """
        QPushButton#filterButton {
            background-color: #4dabf7;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton#filterButton:hover {
            background-color: #339af0;
        }
    """,
    "ADD_BUTTON": """
        QPushButton#addButton {
            background-color: #51cf66;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton#addButton:hover {
            background-color: #40c057;
        }
    """,
    "UTILITY_BUTTON": """
        QPushButton {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 15px;
            min-height: 30px;
            border: 1px solid #495057;
        }
        QPushButton:hover {
            background-color: #2c3034;
            border: 1px solid #6c757d;
        }
    """,
    "TABS": """
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
    """,
    "MENU": """
        QMenu {
            background-color: #2c3034;
            color: white;
            border: 1px solid #1a1d21;
        }
        QMenu::item {
            padding: 5px 20px 5px 20px;
        }
        QMenu::item:selected {
            background-color: #4dabf7;
        }
        QMenu::separator {
            height: 1px;
            background-color: #1a1d21;
            margin: 5px 0px 5px 0px;
        }
    """,
    "STAT_CARD": """
        QFrame#statCard {
            background-color: #343a40;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_BLUE": """
        QFrame#statCard {
            background-color: #1c7ed6;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_GREEN": """
        QFrame#statCard {
            background-color: #40c057;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_ORANGE": """
        QFrame#statCard {
            background-color: #fd7e14;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_RED": """
        QFrame#statCard {
            background-color: #fa5252;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_PURPLE": """
        QFrame#statCard {
            background-color: #7950f2;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_CARD_LIGHT_BLUE": """
        QFrame#statCard {
            background-color: #4dabf7;
            border-radius: 10px;
            padding: 10px;
        }
    """,
    "STAT_LABEL": """
        QLabel {
            color: white;
            font-weight: bold;
            font-size: 28px;
        }
    """,
    "STAT_TITLE": """
        QLabel {
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        }
    """,
    "SPIN_BOX": """
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
            border-left-width: 1px;
            border-left-color: #495057;
            border-left-style: solid;
            border-top-right-radius: 5px;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #495057;
            border-left-style: solid;
            border-bottom-right-radius: 5px;
        }
    """,
    "CHECK_BOX": """
        QCheckBox {
            color: white;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #343a40;
            border: 1px solid #6c757d;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            background-color: #4dabf7;
            border: 1px solid #4dabf7;
            border-radius: 3px;
        }
    """,
    "DATE_EDIT": """
        QDateEdit {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 30px;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #495057;
            border-left-style: solid;
        }
    """
}


class StatusColorDelegate(QStyledItemDelegate):
    """
    Delegat do stylizowania komórek statusu w tabeli magazynu.
    """
    def paint(self, painter, option, index):
        status = index.data()
        
        if status == _("Dostępna"):
            background_color = QColor("#51cf66")  # Zielony
            text_color = QColor(255, 255, 255)
        elif status == _("Rezerwacja"):
            background_color = QColor("#4dabf7")  # Niebieski
            text_color = QColor(255, 255, 255)
        elif status == _("Sprzedana"):
            background_color = QColor("#fa5252")  # Czerwony
            text_color = QColor(255, 255, 255)
        elif status == _("Zamówiona"):
            background_color = QColor("#ffa94d")  # Pomarańczowy
            text_color = QColor(255, 255, 255)
        elif status == _("Wycofana"):
            background_color = QColor("#adb5bd")  # Szary
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


class StockLevelDelegate(QStyledItemDelegate):
    """
    Delegat do kolorowania komórki z poziomem zapasu w zależności od ilości.
    """
    def paint(self, painter, option, index):
        value = index.data()
        try:
            quantity = int(value)
            
            if quantity == 0:
                background_color = QColor("#fa5252")  # Czerwony - brak
            elif quantity <= 2:
                background_color = QColor("#ffa94d")  # Pomarańczowy - niski
            elif quantity <= 5:
                background_color = QColor("#ffe066")  # Żółty - średni
                text_color = QColor(0, 0, 0)  # Czarny tekst dla lepszej widoczności
            else:
                background_color = QColor("#51cf66")  # Zielony - wysoki
            
            # Rysowanie tła
            painter.save()
            painter.fillRect(option.rect, background_color)
            
            # Rysowanie tekstu
            if quantity <= 5 and quantity > 2:
                painter.setPen(QColor(0, 0, 0))  # Czarny tekst dla żółtego tła
            else:
                painter.setPen(QColor(255, 255, 255))  # Biały tekst dla pozostałych
                
            painter.drawText(option.rect, Qt.AlignCenter, str(quantity))
            painter.restore()
            
        except (ValueError, TypeError):
            # Jeśli wartość nie jest liczbą, użyj domyślnego renderu
            super().paint(painter, option, index)


class PriceDelegate(QStyledItemDelegate):
    """
    Delegat do formatowania cen z symbolem waluty.
    """
    def __init__(self, currency="zł", parent=None):
        super().__init__(parent)
        self.currency = currency
        
    def displayText(self, value, locale):
        try:
            price = float(value)
            return f"{price:.2f} {self.currency}"
        except (ValueError, TypeError):
            return super().displayText(value, locale)


class ActionButtonDelegate(QStyledItemDelegate):
    """
    Delegat do wyświetlania przycisków akcji z emotikonami w tabeli.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()

        # Obliczenie szerokości przycisku i odstępów
        total_width = option.rect.width()
        button_width = 30
        spacing = (total_width - button_width) / 2  # Odstęp do wycentrowania

        # Pozycja x dla przycisku
        x_center = option.rect.left() + spacing

        # Pozycja y (centr pionowy)
        y_center = option.rect.top() + option.rect.height() / 2
        button_height = 24

        # Obszar przycisku
        button_rect = QRect(
            int(x_center), 
            int(y_center - button_height/2),
            int(button_width), 
            int(button_height)
        )

        # Rysowanie emotikony
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(Qt.white)
        painter.drawText(button_rect, Qt.AlignCenter, "⋮")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            # Obliczenie szerokości przycisku i odstępów
            total_width = option.rect.width()
            button_width = 30
            spacing = (total_width - button_width) / 2

            # Pozycja x dla przycisku
            x_center = option.rect.left() + spacing

            # Pozycja y (centr pionowy)
            y_center = option.rect.top() + option.rect.height() / 2
            button_height = 24

            # Obszar przycisku
            button_rect = QRect(
                int(x_center), 
                int(y_center - button_height/2),
                int(button_width), 
                int(button_height)
            )

            if button_rect.contains(event.pos()):
                self.parent().action_requested.emit(index.row())
                return True

        return super().editorEvent(event, model, option, index)


class InventoryTable(QTableWidget):
    """
    Tabela zapasów opon z obsługą akcji.
    """
    action_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Ustawienia tabeli
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Opcje wyglądu
        self.setColumnCount(10)
        self.setHorizontalHeaderLabels([
            _("ID"), _("Producent"), _("Model"), 
            _("Rozmiar"), _("Typ"), _("Ilość"), 
            _("Cena"), _("DOT"), _("Status"), _("Akcje")
        ])
        
        # Ustawienie rozciągania kolumn
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Domyślnie interaktywne
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Producent
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Model
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Rozmiar
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Typ
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Ilość
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Cena
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # DOT
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Status
        self.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # Akcje
        self.setColumnWidth(9, 50)  # Stała szerokość kolumny akcji
        
        # Delegaty
        self.setItemDelegateForColumn(5, StockLevelDelegate(self))  # Ilość
        self.setItemDelegateForColumn(6, PriceDelegate("zł", self))  # Cena
        self.setItemDelegateForColumn(8, StatusColorDelegate(self))  # Status
        self.setItemDelegateForColumn(9, ActionButtonDelegate(self))  # Akcje
        
        # Wysokość wiersza
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Ustawienie reguł stylów dla trybu ciemnego
        self.setStyleSheet(STYLES["TABLE_WIDGET"])


class InventoryTab(QWidget):
    """Zakładka magazynu opon w aplikacji Menadżer Serwisu Opon"""
    
    # Sygnały
    tire_added = Signal(int)  # Emitowany po dodaniu opony
    tire_updated = Signal(int)  # Emitowany po aktualizacji opony
    tire_deleted = Signal(int)  # Emitowany po usunięciu opony
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki magazynu opon.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.current_tab_index = 0  # Aktywna zakładka (0 - Nowe, 1 - Używane)
        self.current_status_filter = _("Wszystkie")  # Filtr statusu
        self.current_season_filter = _("Wszystkie")  # Filtr sezonu
        self.current_size_filter = _("Wszystkie")  # Filtr rozmiaru
        self.filter_text = ""  # Tekst wyszukiwania
        self.current_page = 0  # Aktywna strona paginacji
        self.records_per_page = 20  # Liczba rekordów na stronę
        self.total_pages = 0  # Całkowita liczba stron
        
        # Statystyki magazynu
        self.total_new_tires = 0
        self.total_used_tires = 0
        self.total_stock_value = 0.0
        self.low_stock_count = 0
        
        # Upewnij się, że tabela inventory istnieje w bazie danych
        self.create_inventory_table_if_not_exists()
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie danych
        self.load_statistics()
        self.load_inventory()
    
    def create_inventory_table_if_not_exists(self):
        """Tworzy tabelę inventory w bazie danych, jeśli nie istnieje."""
        try:
            cursor = self.conn.cursor()
            
            # Tabela przechowująca dane o oponach w magazynie
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    size TEXT NOT NULL,
                    type TEXT NOT NULL,  -- Zimowe, Letnie, Całoroczne
                    quantity INTEGER NOT NULL DEFAULT 0,
                    price REAL NOT NULL DEFAULT 0.0,
                    dot TEXT,  -- Data produkcji opony
                    condition TEXT NOT NULL,  -- Nowa, Używana
                    status TEXT NOT NULL DEFAULT 'Dostępna',  -- Dostępna, Rezerwacja, Sprzedana, Zamówiona, Wycofana
                    bieznik REAL,  -- Głębokość bieżnika dla używanych opon (w mm)
                    location TEXT,  -- Lokalizacja w magazynie
                    notes TEXT,  -- Notatki
                    receive_date TEXT,  -- Data przyjęcia na stan
                    supplier TEXT,  -- Dostawca
                    invoice_number TEXT,  -- Numer faktury zakupu
                    purchase_price REAL,  -- Cena zakupu
                    ean_code TEXT,  -- Kod EAN/Barcode
                    image_path TEXT,  -- Ścieżka do zdjęcia opony
                    last_updated TEXT  -- Data ostatniej aktualizacji
                )
            ''')
            
            # Upewniamy się, że transakcja zostaje zapisana
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia tabeli inventory: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas inicjalizacji bazy danych magazynu: {e}",
                NotificationTypes.ERROR
            )
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki magazynu."""
        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Tytuł zakładki magazynu
        title_label = QLabel(_("Zarządzanie Magazynem Opon"))
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        # Elastyczny odstęp
        header_layout.addStretch(1)
        
        # Przyciski akcji w nagłówku
        self.add_tire_btn = QPushButton("+ " + _("Dodaj nową oponę"))
        self.add_tire_btn.setObjectName("addButton")
        self.add_tire_btn.setFixedHeight(40)
        self.add_tire_btn.setMinimumWidth(150)
        self.add_tire_btn.setStyleSheet(STYLES["ADD_BUTTON"])
        self.add_tire_btn.clicked.connect(self.add_tire)
        header_layout.addWidget(self.add_tire_btn)
        
        self.import_btn = QPushButton("📥 " + _("Import"))
        self.import_btn.setFixedHeight(40)
        self.import_btn.setMinimumWidth(100)
        self.import_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.import_btn.clicked.connect(self.import_inventory)
        header_layout.addWidget(self.import_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        

        # Panel statystyk
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Karta statystyczna: Opony nowe
        self.new_tires_card = self.create_stat_card(
            "🆕", _("Opony nowe"), "0", 
            STYLES["STAT_CARD_BLUE"]
        )
        stats_layout.addWidget(self.new_tires_card)

        # Karta statystyczna: Opony używane
        self.used_tires_card = self.create_stat_card(
            "♻️", _("Opony używane"), "0", 
            STYLES["STAT_CARD_GREEN"]
        )
        stats_layout.addWidget(self.used_tires_card)

        # Karta statystyczna: Wartość magazynu
        self.stock_value_card = self.create_stat_card(
            "💰", _("Wartość magazynu"), "0 zł", 
            STYLES["STAT_CARD_PURPLE"]
        )
        stats_layout.addWidget(self.stock_value_card)

        # Karta statystyczna: Niski stan
        self.low_stock_card = self.create_stat_card(
            "⚠️", _("Niski stan"), "0", 
            STYLES["STAT_CARD_ORANGE"]
        )
        stats_layout.addWidget(self.low_stock_card)

        main_layout.addLayout(stats_layout)
        
        # Zakładki typów widoku
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(STYLES["TABS"])
        
        # Tworzenie zakładek
        self.new_tires_tab = QWidget()
        self.used_tires_tab = QWidget()
        
        # Dodanie zakładek do widgetu
        self.tabs.addTab(self.new_tires_tab, _("Opony Nowe"))
        self.tabs.addTab(self.used_tires_tab, _("Opony Używane"))
        
        # Połączenie zmiany zakładki z odpowiednim filtrowaniem
        self.tabs.currentChanged.connect(self.tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # Konfiguracja zakładek
        self.setup_new_tires_tab()
        self.setup_used_tires_tab()
        
        # Panel przycisków akcji masowych
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.generate_labels_btn = QPushButton(_("Generuj etykiety dla wybranych opon"))
        self.generate_labels_btn.setFixedHeight(40)
        self.generate_labels_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b5998;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 15px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #324b80;
            }
        """)
        self.generate_labels_btn.clicked.connect(self.generate_labels)
        actions_layout.addWidget(self.generate_labels_btn)

        self.inventory_report_btn = QPushButton(_("Raport Magazynowy"))
        self.inventory_report_btn.setFixedHeight(40)
        self.inventory_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 15px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.inventory_report_btn.clicked.connect(self.generate_inventory_report)
        actions_layout.addWidget(self.inventory_report_btn)

        self.export_inventory_btn = QPushButton(_("Eksportuj listę opon"))
        self.export_inventory_btn.setFixedHeight(40)
        self.export_inventory_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 15px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #5e35b1;
            }
        """)
        self.export_inventory_btn.clicked.connect(self.export_inventory)
        actions_layout.addWidget(self.export_inventory_btn)

        main_layout.addLayout(actions_layout)
    def delete_tire(self, tire_id):
        """Usuwa oponę z magazynu."""
        try:
            # Potwierdzenie usunięcia
            reply = QMessageBox.question(
                self, 
                _("Potwierdź usunięcie"), 
                _("Czy na pewno chcesz usunąć oponę z magazynu?\n\n"
                "Ta operacja jest nieodwracalna."),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Usuń oponę
                    cursor.execute("DELETE FROM inventory WHERE id = ?", (tire_id,))
                    
                    # Zatwierdź zmiany
                    self.conn.commit()
                    
                    # Odśwież dane
                    self.load_statistics()
                    self.load_inventory()
                    
                    # Odśwież listy rozmiarów
                    self.load_tire_sizes("Nowa")
                    self.load_tire_sizes("Używana")
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"🗑️ {_('Opona została usunięta z magazynu')}",
                        NotificationTypes.SUCCESS
                    )
                    
                    # Emituj sygnał
                    self.tire_deleted.emit(tire_id)
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
        except Exception as e:
            logger.error(f"Błąd podczas usuwania opony: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas usuwania opony: {e}",
                NotificationTypes.ERROR
            )
            
    def generate_labels(self):
        """Generuje etykiety dla wybranych opon z tabeli."""
        try:
            # Pobierz aktywną tabelę
            table = self.new_tires_table if self.current_tab_index == 0 else self.used_tires_table
            
            # Sprawdź czy są zaznaczone wiersze
            selected_rows = table.selectionModel().selectedRows()
            
            if not selected_rows:
                # Jeśli nic nie zaznaczono, pokaż komunikat
                QMessageBox.information(
                    self,
                    _("Brak zaznaczenia"),
                    _("Zaznacz opony, dla których chcesz wygenerować etykiety.")
                )
                return
                
            # Zbierz ID zaznaczonych opon
            tire_ids = []
            for index in selected_rows:
                row = index.row()
                tire_id_str = table.item(row, 0).text()
                tire_id = int(tire_id_str.replace('T', ''))
                tire_ids.append(tire_id)
            
            # Opcje drukowania
            print_options = QMessageBox.question(
                self,
                _("Opcje drukowania"),
                _("Wybierz opcję drukowania etykiet:"),
                _("Podgląd") + " | " + _("Drukuj bezpośrednio") + " | " + _("Anuluj"),
                0, 2
            )
            
            if print_options == 2:  # Anuluj
                return
                
            # Generuj i drukuj etykiety
            self.generate_tire_labels_batch(tire_ids, preview=(print_options == 0))
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiet: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania etykiet: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_tire_label(self, tire_id):
        """Generuje i drukuje etykietę dla pojedynczej opony."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane opony
            query = """
            SELECT 
                id, manufacturer, model, size, type, 
                price, dot, condition, status, quantity,
                bieznik, ean_code
            FROM 
                inventory
            WHERE 
                id = ?
            """
            
            cursor.execute(query, (tire_id,))
            tire = cursor.fetchone()
            
            if not tire:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono opony o ID {tire_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Formatowanie ID opony
            tire_id_str = f"T{str(tire['id']).zfill(3)}"
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            
            # Przygotowanie danych do szablonu
            template_data = {
                "tire_id": tire_id_str,
                "manufacturer": tire['manufacturer'],
                "model": tire['model'],
                "size": tire['size'],
                "type": tire['type'],
                "price": f"{tire['price']:.2f} zł",
                "dot": tire['dot'] or "",
                "condition": tire['condition'],
                "status": tire['status'],
                "quantity": str(tire['quantity']),
                "bieznik": f"{tire['bieznik']} mm" if tire['bieznik'] else "",
                "ean_code": tire['ean_code'] or "",
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone
            }
            
            # Pobierz szablon etykiety
            template = self.get_label_template()
            
            # Wypełnij szablon danymi
            html_content = template
            for key, value in template_data.items():
                html_content = html_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd wydruku
            self.print_html_preview(html_content, _("Podgląd etykiety opony"))
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Wygenerowano etykietę dla opony {tire_id_str}",
                NotificationTypes.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiety: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania etykiety: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_tire_labels_batch(self, tire_ids, preview=True):
        """
        Generuje etykiety dla wielu opon.
        
        Args:
            tire_ids (list): Lista ID opon
            preview (bool): Czy wyświetlić podgląd przed drukowaniem
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            
            # Pobierz szablon etykiety
            template = self.get_label_template()
            
            # Przygotuj złożony dokument HTML z wieloma etykietami
            all_labels_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Etykiety opon</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .label-container {
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: space-between;
                    }
                    .label {
                        width: 48%;
                        margin-bottom: 10px;
                        padding: 10px;
                        border: 1px solid #000;
                        box-sizing: border-box;
                        page-break-inside: avoid;
                    }
                    @media print {
                        .label { page-break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                <div class="label-container">
            """
            
            # Pobierz dane dla każdej opony i dodaj do dokumentu
            for tire_id in tire_ids:
                # Pobierz dane opony
                query = """
                SELECT 
                    id, manufacturer, model, size, type, 
                    price, dot, condition, status, quantity,
                    bieznik, ean_code
                FROM 
                    inventory
                WHERE 
                    id = ?
                """
                
                cursor.execute(query, (tire_id,))
                tire = cursor.fetchone()
                
                if not tire:
                    continue
                
                # Formatowanie ID opony
                tire_id_str = f"T{str(tire['id']).zfill(3)}"
                
                # Przygotowanie danych do szablonu
                template_data = {
                    "tire_id": tire_id_str,
                    "manufacturer": tire['manufacturer'],
                    "model": tire['model'],
                    "size": tire['size'],
                    "type": tire['type'],
                    "price": f"{tire['price']:.2f} zł",
                    "dot": tire['dot'] or "",
                    "condition": tire['condition'],
                    "status": tire['status'],
                    "quantity": str(tire['quantity']),
                    "bieznik": f"{tire['bieznik']} mm" if tire['bieznik'] else "",
                    "ean_code": tire['ean_code'] or "",
                    "company_name": company_name,
                    "company_address": company_address,
                    "company_phone": company_phone
                }
                
                # Wypełnij szablon danymi
                label_html = template
                for key, value in template_data.items():
                    label_html = label_html.replace("{" + key + "}", str(value))
                
                # Dodaj do całego dokumentu
                all_labels_html += f'<div class="label">{label_html}</div>'
            
            # Zamknij dokument HTML
            all_labels_html += """
                </div>
            </body>
            </html>
            """
            
            # Wyświetl podgląd lub drukuj bezpośrednio
            if preview:
                self.print_html_preview(all_labels_html, _("Podgląd etykiet opon"))
            else:
                self.print_html_directly(all_labels_html)
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Wygenerowano etykiety dla {len(tire_ids)} opon",
                NotificationTypes.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiet: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania etykiet: {e}",
                NotificationTypes.ERROR
            )
    
    def print_html_preview(self, html_content, title=_("Podgląd wydruku")):
        """Wyświetla podgląd wydruku HTML przed drukowaniem."""
        try:
            # Przygotowanie dokumentu HTML do drukowania
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtCore import QUrl, QTemporaryFile, QIODevice, QFile
            
            # Zapisz treść HTML do tymczasowego pliku
            temp_file = QTemporaryFile()
            if temp_file.open():
                temp_file.write(html_content.encode('utf-8'))
                temp_file.close()
            
            # Utwórz widok do renderowania HTML
            view = QWebEngineView()
            view.load(QUrl.fromLocalFile(temp_file.fileName()))
            
            # Poczekaj na załadowanie strony
            from PySide6.QtCore import QEventLoop
            loop = QEventLoop()
            view.loadFinished.connect(loop.quit)
            loop.exec()
            
            # Utwórz okno podglądu wydruku
            printer = QPrinter()
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle(title)
            preview.resize(1000, 800)
            
            # Połącz sygnał paintRequested z funkcją drukowania
            preview.paintRequested.connect(lambda p: view.page().print(p, lambda: None))
            
            # Pokaż podgląd
            preview.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania podglądu wydruku: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania podglądu wydruku: {e}",
                NotificationTypes.ERROR
            )
    
    def print_html_directly(self, html_content):
        """Drukuje dokument HTML bezpośrednio na drukarce."""
        try:
            # Przygotowanie dokumentu HTML do drukowania
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtCore import QUrl, QTemporaryFile
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            
            # Zapisz treść HTML do tymczasowego pliku
            temp_file = QTemporaryFile()
            if temp_file.open():
                temp_file.write(html_content.encode('utf-8'))
                temp_file.close()
            
            # Utwórz widok do renderowania HTML
            view = QWebEngineView()
            view.load(QUrl.fromLocalFile(temp_file.fileName()))
            
            # Poczekaj na załadowanie strony
            from PySide6.QtCore import QEventLoop
            loop = QEventLoop()
            view.loadFinished.connect(loop.quit)
            loop.exec()
            
            # Utwórz obiekt drukarki i dialog drukowania
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QDialog.Accepted:
                # Drukuj na wybranej drukarce
                view.page().print(printer, lambda: None)
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Wysłano dokument do drukowania"),
                    NotificationTypes.SUCCESS
                )
            
        except Exception as e:
            logger.error(f"Błąd podczas drukowania: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas drukowania: {e}",
                NotificationTypes.ERROR
            )
    
    def get_label_template(self, template_name="default"):
        """
        Pobiera szablon etykiety z pliku konfiguracyjnego.
        
        Args:
            template_name (str): Nazwa szablonu etykiety
        
        Returns:
            str: Szablon etykiety
        """
        try:
            # Pobierz dane firmy
            settings = QSettings("TireDepositManager", "Settings")
            company_data = {
                "company_name": settings.value("company_name", "Serwis Opon"),
                "company_address": settings.value("company_address", ""),
                "company_phone": settings.value("company_phone", "")
            }
            
            # Ścieżka do pliku szablonów
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            # Wczytaj szablony
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                # Jeśli plik nie istnieje, użyj domyślnego szablonu
                templates = {
                    "tire_label": {
                        "default": self.get_default_tire_label_template()
                    }
                }
            
            # Wybierz szablon
            template = templates.get("tire_label", {}).get(template_name, self.get_default_tire_label_template())
            
            return template
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu etykiety: {e}")
            return self.get_default_tire_label_template()
    
    def get_default_tire_label_template(self):
        """Zwraca domyślny szablon etykiety opony."""
        return """
        <div style="font-family: Arial, sans-serif; max-width: 300px; border: 1px solid #ccc; padding: 10px; box-sizing: border-box;">
            <div style="text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                {company_name}
            </div>
            <div style="text-align: center; font-size: 12px; margin-bottom: 8px;">
                {company_address} | {company_phone}
            </div>
            <div style="border-top: 1px solid #ccc; margin: 5px 0;"></div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <div style="font-weight: bold; font-size: 16px;">{manufacturer}</div>
                <div style="font-weight: bold; font-size: 16px;">{model}</div>
            </div>
            
            <div style="font-size: 18px; font-weight: bold; margin: 5px 0; text-align: center;">
                {size}
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 5px 0;">
                <tr>
                    <td style="padding: 3px; font-size: 12px;">Typ:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{type}</td>
                    <td style="padding: 3px; font-size: 12px;">DOT:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{dot}</td>
                </tr>
                <tr>
                    <td style="padding: 3px; font-size: 12px;">Status:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{status}</td>
                    <td style="padding: 3px; font-size: 12px;">Stan:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{condition}</td>
                </tr>
                <tr>
                    <td style="padding: 3px; font-size: 12px;">Bieżnik:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{bieznik}</td>
                    <td style="padding: 3px; font-size: 12px;">ID:</td>
                    <td style="padding: 3px; font-size: 12px; font-weight: bold;">{tire_id}</td>
                </tr>
            </table>
            
            <div style="border-top: 1px solid #ccc; margin: 5px 0;"></div>
            
            <div style="text-align: center; font-size: 20px; font-weight: bold; margin: 10px 0;">
                {price}
            </div>
            
            <div style="font-size: 10px; text-align: center; margin-top: 5px;">
                EAN: {ean_code}
            </div>
        </div>
        """
    
    def generate_inventory_report(self):
        """Generuje raport magazynowy z aktualnymi danymi."""
        try:
            # Zapytaj o typ raportu
            from PySide6.QtWidgets import QInputDialog
            
            report_types = [
                _("Raport stanu magazynowego"),
                _("Raport niskiego stanu"),
                _("Raport wartości magazynu"),
                _("Raport sprzedanych opon")
            ]
            
            report_type, ok = QInputDialog.getItem(
                self, 
                _("Wybierz typ raportu"), 
                _("Wybierz typ raportu, który chcesz wygenerować:"),
                report_types, 0, False
            )
            
            if not ok:
                return
                
            # Pobierz dane do raportu w zależności od typu
            cursor = self.conn.cursor()
            
            if report_type == report_types[0]:  # Raport stanu magazynowego
                title = _("Raport Stanu Magazynowego Opon")
                
                query = """
                    SELECT 
                        manufacturer, model, size, type, 
                        SUM(quantity) as total_qty, 
                        condition,
                        AVG(price) as avg_price,
                        SUM(quantity * price) as total_value
                    FROM 
                        inventory
                    WHERE 
                        status = 'Dostępna'
                    GROUP BY 
                        manufacturer, model, size, type, condition
                    ORDER BY 
                        manufacturer, model, size
                """
                cursor.execute(query)
                data = cursor.fetchall()
                
                # Przygotuj HTML
                html_content = self.generate_inventory_report_html(
                    title, data, 
                    ["Producent", "Model", "Rozmiar", "Typ", "Ilość", "Stan", "Śr. cena", "Wartość"],
                    ["manufacturer", "model", "size", "type", "total_qty", "condition", "avg_price", "total_value"],
                    format_funcs={
                        "avg_price": lambda x: f"{float(x):.2f} zł",
                        "total_value": lambda x: f"{float(x):.2f} zł"
                    }
                )
                
            elif report_type == report_types[1]:  # Raport niskiego stanu
                title = _("Raport Niskiego Stanu Magazynowego")
                
                query = """
                    SELECT 
                        manufacturer, model, size, type, 
                        quantity, condition, price,
                        quantity * price as value,
                        location
                    FROM 
                        inventory
                    WHERE 
                        status = 'Dostępna' AND quantity > 0 AND quantity <= 2
                    ORDER BY 
                        quantity, manufacturer, model
                """
                cursor.execute(query)
                data = cursor.fetchall()
                
                # Przygotuj HTML
                html_content = self.generate_inventory_report_html(
                    title, data, 
                    ["Producent", "Model", "Rozmiar", "Typ", "Ilość", "Stan", "Cena", "Wartość", "Lokalizacja"],
                    ["manufacturer", "model", "size", "type", "quantity", "condition", "price", "value", "location"],
                    format_funcs={
                        "price": lambda x: f"{float(x):.2f} zł",
                        "value": lambda x: f"{float(x):.2f} zł"
                    }
                )
                
            elif report_type == report_types[2]:  # Raport wartości magazynu
                title = _("Raport Wartości Magazynu Opon")
                
                query = """
                    SELECT 
                        type, condition,
                        COUNT(DISTINCT manufacturer || model || size) as models_count,
                        SUM(quantity) as total_qty,
                        SUM(quantity * price) as total_value
                    FROM 
                        inventory
                    WHERE 
                        status IN ('Dostępna', 'Rezerwacja', 'Zamówiona')
                    GROUP BY 
                        type, condition
                    ORDER BY 
                        condition, type
                """
                cursor.execute(query)
                data = cursor.fetchall()
                
                # Przygotuj HTML
                html_content = self.generate_inventory_report_html(
                    title, data, 
                    ["Typ", "Stan", "Liczba modeli", "Łączna ilość", "Wartość"],
                    ["type", "condition", "models_count", "total_qty", "total_value"],
                    format_funcs={
                        "total_value": lambda x: f"{float(x):.2f} zł"
                    },
                    summary=True
                )
                
            elif report_type == report_types[3]:  # Raport sprzedanych opon
                # Opcje okresu raportu
                period_options = [
                    _("Ostatni tydzień"),
                    _("Ostatni miesiąc"),
                    _("Ostatni kwartał"),
                    _("Bieżący rok"),
                    _("Wszystkie")
                ]
                
                period, ok = QInputDialog.getItem(
                    self, 
                    _("Wybierz okres"), 
                    _("Za jaki okres chcesz wygenerować raport:"),
                    period_options, 1, False
                )
                
                if not ok:
                    return
                    
                title = f"{_('Raport Sprzedanych Opon')} - {period}"
                
                # Określenie daty początkowej w zależności od wybranego okresu
                today = datetime.now()
                
                if period == period_options[0]:  # Ostatni tydzień
                    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
                elif period == period_options[1]:  # Ostatni miesiąc
                    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
                elif period == period_options[2]:  # Ostatni kwartał
                    start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
                elif period == period_options[3]:  # Bieżący rok
                    start_date = f"{today.year}-01-01"
                else:  # Wszystkie
                    start_date = "2000-01-01"  # Data w przeszłości
                
                query = """
                    SELECT 
                        manufacturer, model, size, type, condition,
                        SUM(last_quantity) as sold_qty,
                        AVG(price) as avg_price,
                        SUM(last_quantity * price) as total_value,
                        MAX(last_updated) as last_sale
                    FROM (
                        SELECT 
                            manufacturer, model, size, type, condition, price,
                            quantity as last_quantity,
                            last_updated
                        FROM 
                            inventory
                        WHERE 
                            status = 'Sprzedana' AND
                            last_updated >= ?
                    )
                    GROUP BY 
                        manufacturer, model, size, type, condition
                    ORDER BY 
                        last_sale DESC
                """
                cursor.execute(query, (start_date,))
                data = cursor.fetchall()
                
                # Przygotuj HTML
                html_content = self.generate_inventory_report_html(
                    title, data, 
                    ["Producent", "Model", "Rozmiar", "Typ", "Stan", "Sprzedana ilość", "Śr. cena", "Wartość sprzedaży", "Ostatnia sprzedaż"],
                    ["manufacturer", "model", "size", "type", "condition", "sold_qty", "avg_price", "total_value", "last_sale"],
                    format_funcs={
                        "avg_price": lambda x: f"{float(x):.2f} zł",
                        "total_value": lambda x: f"{float(x):.2f} zł",
                        "last_sale": lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
                    },
                    summary=True
                )
            
            # Wyświetl podgląd raportu
            self.print_html_preview(html_content, title)
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania raportu magazynowego: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania raportu: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_inventory_report_html(self, title, data, headers, keys, format_funcs=None, summary=False):
        """
        Generuje dokument HTML z raportem magazynowym.
        
        Args:
            title (str): Tytuł raportu
            data (list): Lista danych (rekordów) do raportu
            headers (list): Nagłówki kolumn
            keys (list): Klucze do pobrania wartości z rekordów
            format_funcs (dict, optional): Słownik funkcji formatujących dla konkretnych kolumn
            summary (bool): Czy dodać podsumowanie
            
        Returns:
            str: Dokument HTML z raportem
        """
        if format_funcs is None:
            format_funcs = {}
            
        # Pobierz dane firmy
        settings = QSettings("TireDepositManager", "Settings")
        company_name = settings.value("company_name", "Serwis Opon")
        company_address = settings.value("company_address", "")
        company_phone = settings.value("company_phone", "")
        
        # Przygotuj HTML
        current_date = datetime.now().strftime("%d-%m-%Y")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ text-align: center; color: #333; font-size: 24px; margin-bottom: 5px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .report-date {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 14px; }}
                .company-info {{ text-align: center; margin-bottom: 15px; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background-color: #4dabf7; color: white; font-weight: bold; padding: 8px; text-align: left; }}
                td {{ padding: 6px 8px; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .numeric {{ text-align: right; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
                .summary {{ margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-top: 2px solid #4dabf7; }}
                .summary table {{ margin-top: 0; }}
                .summary th {{ background-color: #343a40; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <div class="company-info">
                    {company_name}<br>
                    {company_address} | {company_phone}
                </div>
                <div class="report-date">
                    Wygenerowano: {current_date}
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
        """
        
        # Dodaj nagłówki tabeli
        for header in headers:
            html += f"<th>{header}</th>\n"
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Dodaj wiersze danych
        total_sums = {key: 0 for key in keys if key.startswith("total_") or key.endswith("_qty") or key.endswith("_value") or key.endswith("_count")}
        
        for item in data:
            html += "<tr>\n"
            
            for i, key in enumerate(keys):
                value = item.get(key, "")
                
                # Zastosuj funkcję formatującą, jeśli podano
                if key in format_funcs and value is not None and value != "":
                    formatted_value = format_funcs[key](value)
                else:
                    formatted_value = value
                
                # Agreguj do sum dla podsumowania
                if key in total_sums and value is not None:
                    try:
                        total_sums[key] += float(value)
                    except (ValueError, TypeError):
                        pass  # Ignoruj błędy konwersji
                
                # Określ klasę dla komórki tabeli
                css_class = ""
                if isinstance(value, (int, float)) or (key.startswith("total_") or key.endswith("_qty") or key.endswith("_value")):
                    css_class = ' class="numeric"'
                
                html += f"<td{css_class}>{formatted_value}</td>\n"
                
            html += "</tr>\n"
        
        html += """
                </tbody>
            </table>
        """
        
        # Dodaj podsumowanie, jeśli wymagane
        if summary and total_sums:
            html += """
            <div class="summary">
                <h2>Podsumowanie</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Miara</th>
                            <th>Wartość</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Dodaj podsumowanie
            for key, total in total_sums.items():
                if total > 0:
                    # Przygotuj czytelną nazwę
                    if key == "total_qty":
                        name = "Łączna ilość"
                    elif key == "total_value":
                        name = "Łączna wartość"
                        total = f"{total:.2f} zł"
                    elif key == "sold_qty":
                        name = "Łącznie sprzedano"
                    elif key == "models_count":
                        name = "Liczba modeli"
                    else:
                        name = key.replace("_", " ").title()
                    
                    html += f"<tr><td>{name}</td><td class='numeric'>{total}</td></tr>\n"
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # Dodaj stopkę
        html += """
            <div class="footer">
                <p>Raport wygenerowany przez Menadżer Serwisu Opon</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def setup_new_tires_tab(self):
        """Konfiguruje zakładkę nowych opon."""
        # Główny layout zakładki
        layout = QVBoxLayout(self.new_tires_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Panel wyszukiwania i filtrowania
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setStyleSheet(STYLES["SEARCH_PANEL"])
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 10, 10, 10)
        search_layout.setSpacing(10)
        
        # Pole wyszukiwania
        search_box = QFrame()
        search_box.setObjectName("searchBox")
        search_box.setStyleSheet(STYLES["SEARCH_BOX"])
        search_box.setMinimumWidth(300)
        
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 10, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("""
            background-color: transparent; 
            color: #adb5bd;
        """)
        search_box_layout.addWidget(search_icon)
        
        self.new_tires_search_field = QLineEdit()
        self.new_tires_search_field.setObjectName("searchField")
        self.new_tires_search_field.setStyleSheet(STYLES["SEARCH_FIELD"])
        self.new_tires_search_field.setPlaceholderText(_("Szukaj po producencie, modelu, rozmiarze..."))
        self.new_tires_search_field.textChanged.connect(lambda: self.filter_inventory(0))
        search_box_layout.addWidget(self.new_tires_search_field)
        
        search_layout.addWidget(search_box)
        
        # Filtry
        self.new_tires_status_combo = QComboBox()
        self.new_tires_status_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.new_tires_status_combo.setMinimumWidth(150)
        self.new_tires_status_combo.addItem(_("Wszystkie"))
        self.new_tires_status_combo.addItem(_("Dostępna"))
        self.new_tires_status_combo.addItem(_("Rezerwacja"))
        self.new_tires_status_combo.addItem(_("Sprzedana"))
        self.new_tires_status_combo.addItem(_("Zamówiona"))
        self.new_tires_status_combo.addItem(_("Wycofana"))
        self.new_tires_status_combo.currentTextChanged.connect(lambda: self.filter_inventory(0))
        search_layout.addWidget(self.new_tires_status_combo)
        
        self.new_tires_season_combo = QComboBox()
        self.new_tires_season_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.new_tires_season_combo.setMinimumWidth(150)
        self.new_tires_season_combo.addItem(_("Wszystkie"))
        self.new_tires_season_combo.addItem(_("Zimowe"))
        self.new_tires_season_combo.addItem(_("Letnie"))
        self.new_tires_season_combo.addItem(_("Całoroczne"))
        self.new_tires_season_combo.currentTextChanged.connect(lambda: self.filter_inventory(0))
        search_layout.addWidget(self.new_tires_season_combo)
        
        self.new_tires_size_combo = QComboBox()
        self.new_tires_size_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.new_tires_size_combo.setMinimumWidth(150)
        self.new_tires_size_combo.addItem(_("Wszystkie"))
        search_layout.addWidget(self.new_tires_size_combo)
        
        # Przycisk filtrowania
        self.new_tires_filter_btn = QPushButton(_("Filtruj"))
        self.new_tires_filter_btn.setObjectName("filterButton")
        self.new_tires_filter_btn.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.new_tires_filter_btn.setFixedHeight(40)
        self.new_tires_filter_btn.clicked.connect(lambda: self.filter_inventory(0))
        search_layout.addWidget(self.new_tires_filter_btn)
        
        layout.addWidget(search_panel)
        
        # Tabela opon
        self.new_tires_table = InventoryTable()
        self.new_tires_table.action_requested.connect(self.show_tire_actions)
        layout.addWidget(self.new_tires_table)
        
        # Panel paginacji
        pagination_panel = QHBoxLayout()
        pagination_panel.setContentsMargins(10, 5, 10, 5)
        
        self.new_tires_prev_btn = QPushButton("◀ " + _("Poprzednia"))
        self.new_tires_prev_btn.setFixedHeight(30)
        self.new_tires_prev_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.new_tires_prev_btn.clicked.connect(lambda: self.change_page(-1, 0))
        pagination_panel.addWidget(self.new_tires_prev_btn)
        
        pagination_panel.addStretch(1)
        
        self.new_tires_page_label = QLabel(_("Strona") + " 1 " + _("z") + " 1")
        self.new_tires_page_label.setAlignment(Qt.AlignCenter)
        self.new_tires_page_label.setStyleSheet("color: white; font-size: 14px;")
        pagination_panel.addWidget(self.new_tires_page_label)
        
        pagination_panel.addStretch(1)
        
        self.new_tires_next_btn = QPushButton(_("Następna") + " ▶")
        self.new_tires_next_btn.setFixedHeight(30)
        self.new_tires_next_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.new_tires_next_btn.clicked.connect(lambda: self.change_page(1, 0))
        pagination_panel.addWidget(self.new_tires_next_btn)
        
        layout.addLayout(pagination_panel)
        
        # Załaduj rozmiary opon
        self.load_tire_sizes("Nowa")

    def setup_used_tires_tab(self):
        """Konfiguruje zakładkę używanych opon."""
        # Główny layout zakładki
        layout = QVBoxLayout(self.used_tires_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Panel wyszukiwania i filtrowania
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setStyleSheet(STYLES["SEARCH_PANEL"])
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 10, 10, 10)
        search_layout.setSpacing(10)
        
        # Pole wyszukiwania
        search_box = QFrame()
        search_box.setObjectName("searchBox")
        search_box.setStyleSheet(STYLES["SEARCH_BOX"])
        search_box.setMinimumWidth(300)
        
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 10, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("""
            background-color: transparent; 
            color: #adb5bd;
        """)
        search_box_layout.addWidget(search_icon)
        
        self.used_tires_search_field = QLineEdit()
        self.used_tires_search_field.setObjectName("searchField")
        self.used_tires_search_field.setStyleSheet(STYLES["SEARCH_FIELD"])
        self.used_tires_search_field.setPlaceholderText(_("Szukaj po producencie, modelu, rozmiarze..."))
        self.used_tires_search_field.textChanged.connect(lambda: self.filter_inventory(1))
        search_box_layout.addWidget(self.used_tires_search_field)
        
        search_layout.addWidget(search_box)
        
        # Filtry
        self.used_tires_status_combo = QComboBox()
        self.used_tires_status_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.used_tires_status_combo.setMinimumWidth(150)
        self.used_tires_status_combo.addItem(_("Wszystkie"))
        self.used_tires_status_combo.addItem(_("Dostępna"))
        self.used_tires_status_combo.addItem(_("Rezerwacja"))
        self.used_tires_status_combo.addItem(_("Sprzedana"))
        self.used_tires_status_combo.addItem(_("Wycofana"))
        self.used_tires_status_combo.currentTextChanged.connect(lambda: self.filter_inventory(1))
        search_layout.addWidget(self.used_tires_status_combo)
        
        self.used_tires_season_combo = QComboBox()
        self.used_tires_season_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.used_tires_season_combo.setMinimumWidth(150)
        self.used_tires_season_combo.addItem(_("Wszystkie"))
        self.used_tires_season_combo.addItem(_("Zimowe"))
        self.used_tires_season_combo.addItem(_("Letnie"))
        self.used_tires_season_combo.addItem(_("Całoroczne"))
        self.used_tires_season_combo.currentTextChanged.connect(lambda: self.filter_inventory(1))
        search_layout.addWidget(self.used_tires_season_combo)
        
        self.used_tires_size_combo = QComboBox()
        self.used_tires_size_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.used_tires_size_combo.setMinimumWidth(150)
        self.used_tires_size_combo.addItem(_("Wszystkie"))
        search_layout.addWidget(self.used_tires_size_combo)
        
        # Przycisk filtrowania
        self.used_tires_filter_btn = QPushButton(_("Filtruj"))
        self.used_tires_filter_btn.setObjectName("filterButton")
        self.used_tires_filter_btn.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.used_tires_filter_btn.setFixedHeight(40)
        self.used_tires_filter_btn.clicked.connect(lambda: self.filter_inventory(1))
        search_layout.addWidget(self.used_tires_filter_btn)
        
        layout.addWidget(search_panel)
        
        # Tabela opon
        self.used_tires_table = InventoryTable()
        self.used_tires_table.action_requested.connect(self.show_tire_actions)
        layout.addWidget(self.used_tires_table)
        
        # Panel paginacji
        pagination_panel = QHBoxLayout()
        pagination_panel.setContentsMargins(10, 5, 10, 5)
        
        self.used_tires_prev_btn = QPushButton("◀ " + _("Poprzednia"))
        self.used_tires_prev_btn.setFixedHeight(30)
        self.used_tires_prev_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.used_tires_prev_btn.clicked.connect(lambda: self.change_page(-1, 1))
        pagination_panel.addWidget(self.used_tires_prev_btn)
        
        pagination_panel.addStretch(1)
        
        self.used_tires_page_label = QLabel(_("Strona") + " 1 " + _("z") + " 1")
        self.used_tires_page_label.setAlignment(Qt.AlignCenter)
        self.used_tires_page_label.setStyleSheet("color: white; font-size: 14px;")
        pagination_panel.addWidget(self.used_tires_page_label)
        
        pagination_panel.addStretch(1)
        
        self.used_tires_next_btn = QPushButton(_("Następna") + " ▶")
        self.used_tires_next_btn.setFixedHeight(30)
        self.used_tires_next_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.used_tires_next_btn.clicked.connect(lambda: self.change_page(1, 1))
        pagination_panel.addWidget(self.used_tires_next_btn)
        
        layout.addLayout(pagination_panel)
        
        # Załaduj rozmiary opon
        self.load_tire_sizes("Używana")

    def load_inventory(self):
        """Ładuje dane do tabel opon."""
        try:
            # Załaduj dane do odpowiedniej tabeli w zależności od aktywnej zakładki
            if self.current_tab_index == 0:
                self.load_inventory_data("Nowa", self.new_tires_table, self.new_tires_page_label)
            else:
                self.load_inventory_data("Używana", self.used_tires_table, self.used_tires_page_label)
                
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych magazynu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania danych magazynu: {e}",
                NotificationTypes.ERROR
            )

    def load_inventory_data(self, condition, table, page_label):
        """
        Ładuje dane opon do tabeli.
        
        Args:
            condition (str): Stan opon ('Nowa' lub 'Używana')
            table (InventoryTable): Tabela do załadowania danych
            page_label (QLabel): Etykieta z informacją o paginacji
        """
        try:
            cursor = self.conn.cursor()
            
            # Budowanie zapytania SQL używającego nazw kolumn z istniejącej bazy
            query = """
                SELECT 
                    id, brand_model, size, season_type, 
                    quantity, price, dot, status
                FROM 
                    inventory
                WHERE 
                    condition = ?
            """
            
            params = [condition]
            
            # Dodaj filtrowanie
            if self.current_status_filter != _("Wszystkie"):
                query += " AND status = ?"
                params.append(self.current_status_filter)
                
            if self.current_season_filter != _("Wszystkie"):
                query += " AND season_type = ?"  # Używamy season_type zamiast type
                params.append(self.current_season_filter)
                
            if self.current_size_filter != _("Wszystkie"):
                query += " AND size = ?"
                params.append(self.current_size_filter)
                
            if self.filter_text:
                query += """
                    AND (brand_model LIKE ? OR size LIKE ?)
                """
                search_param = f"%{self.filter_text}%"
                params.extend([search_param, search_param])
                
            # Sortowanie
            query += " ORDER BY brand_model, size"
            
            # Paginacja - najpierw pobierz całkowitą liczbę wierszy
            count_query = "SELECT COUNT(*) FROM (" + query + ")"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # Oblicz całkowitą liczbę stron
            self.total_pages = (total_records + self.records_per_page - 1) // self.records_per_page
            if self.total_pages == 0:
                self.total_pages = 1
                
            # Upewnij się, że bieżąca strona jest w prawidłowym zakresie
            if self.current_page >= self.total_pages:
                self.current_page = self.total_pages - 1
            if self.current_page < 0:
                self.current_page = 0
                
            # Aktualizuj etykietę paginacji
            page_label.setText(f"{_('Strona')} {self.current_page + 1} {_('z')} {self.total_pages}")
            
            # Dodaj parametry paginacji do zapytania
            query += f" LIMIT {self.records_per_page} OFFSET {self.current_page * self.records_per_page}"
            
            # Wykonaj zapytanie z paginacją
            cursor.execute(query, params)
            tires = cursor.fetchall()
            
            # Wypełnij tabelę danymi
            table.setRowCount(0)  # Wyczyść tabelę
            
            for row_idx, tire in enumerate(tires):
                table.insertRow(row_idx)
                
                # Dodaj dane do tabeli
                # ID opony - format T001, T002, itd.
                id_item = QTableWidgetItem(f"T{str(tire['id']).zfill(3)}")
                id_item.setData(Qt.UserRole, tire['id'])  # Zachowaj oryginalne ID
                table.setItem(row_idx, 0, id_item)
                
                # Rozdziel brand_model na manufacturer i model
                brand_model = tire['brand_model'] or ""
                parts = brand_model.split(' ', 1)
                manufacturer = parts[0] if parts else ""
                model = parts[1] if len(parts) > 1 else ""
                
                # Pozostałe dane
                table.setItem(row_idx, 1, QTableWidgetItem(manufacturer))
                table.setItem(row_idx, 2, QTableWidgetItem(model))
                table.setItem(row_idx, 3, QTableWidgetItem(tire['size']))
                table.setItem(row_idx, 4, QTableWidgetItem(tire['season_type']))  # Używamy season_type zamiast type
                table.setItem(row_idx, 5, QTableWidgetItem(str(tire['quantity'])))
                table.setItem(row_idx, 6, QTableWidgetItem(str(tire['price'])))
                table.setItem(row_idx, 7, QTableWidgetItem(tire['dot'] or ""))
                table.setItem(row_idx, 8, QTableWidgetItem(tire['status']))
                
                # Dodaj kolumnę akcji (pusta, obsługiwana przez delegat)
                table.setItem(row_idx, 9, QTableWidgetItem(""))
                
            # Aktualizuj stany przycisków paginacji
            if condition == "Nowa":
                self.new_tires_prev_btn.setEnabled(self.current_page > 0)
                self.new_tires_next_btn.setEnabled(self.current_page < self.total_pages - 1)
            else:
                self.used_tires_prev_btn.setEnabled(self.current_page > 0)
                self.used_tires_next_btn.setEnabled(self.current_page < self.total_pages - 1)
                
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych magazynu: {e}")
            raise e

    def load_statistics(self):
        """Ładuje statystyki dotyczące magazynu opon."""
        try:
            cursor = self.conn.cursor()
            
            # Liczba nowych opon
            cursor.execute("""
                SELECT COUNT(*) as count, SUM(quantity) as total
                FROM inventory 
                WHERE condition = 'Nowa' AND status IN ('Dostępna', 'Rezerwacja', 'Zamówiona')
            """)
            result = cursor.fetchone()
            self.total_new_tires = result['total'] or 0
            
            # Aktualizuj kartę statystyki - używamy bezpośrednio atrybutu value_label
            self.new_tires_card.value_label.setText(str(self.total_new_tires))
            
            # Liczba używanych opon
            cursor.execute("""
                SELECT COUNT(*) as count, SUM(quantity) as total
                FROM inventory 
                WHERE condition = 'Używana' AND status IN ('Dostępna', 'Rezerwacja', 'Zamówiona')
            """)
            result = cursor.fetchone()
            self.total_used_tires = result['total'] or 0
            
            # Aktualizuj kartę statystyki - używamy bezpośrednio atrybutu value_label
            self.used_tires_card.value_label.setText(str(self.total_used_tires))
            
            # Wartość magazynu
            cursor.execute("""
                SELECT SUM(quantity * price) as value
                FROM inventory 
                WHERE status IN ('Dostępna', 'Rezerwacja', 'Zamówiona')
            """)
            result = cursor.fetchone()
            self.total_stock_value = result['value'] or 0.0
            
            # Aktualizuj kartę statystyki - używamy bezpośrednio atrybutu value_label
            self.stock_value_card.value_label.setText(f"{self.total_stock_value:.2f} zł")
            
            # Liczba pozycji o niskim stanie (ilość <= 2)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM inventory 
                WHERE quantity > 0 AND quantity <= 2 AND status = 'Dostępna'
            """)
            result = cursor.fetchone()
            self.low_stock_count = result['count'] or 0
            
            # Aktualizuj kartę statystyki - używamy bezpośrednio atrybutu value_label
            self.low_stock_card.value_label.setText(str(self.low_stock_count))
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania statystyk magazynu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania statystyk: {e}",
                NotificationTypes.ERROR
            )

    def create_stat_card(self, icon, title, value, style):
        """
        Tworzy kartę statystyczną z wybraną ikoną, tytułem i wartością.
        
        Args:
            icon (str): Emotikona/ikona
            title (str): Tytuł karty
            value (str): Wartość statystyki
            style (str): Style CSS dla karty
            
        Returns:
            QFrame: Karta statystyczna
        """
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(100)
        card.setStyleSheet(style)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Tytuł z ikoną - z przezroczystym tłem
        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px; background: transparent;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)
        
        layout.addLayout(title_layout)
        
        # Wartość - również z przezroczystym tłem
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-weight: bold; font-size: 28px; background: transparent;")
        layout.addWidget(value_label)
        
        # Zapisanie referencji do etykiety wartości
        card.value_label = value_label
        
        return card

    def tab_changed(self, index):
        """
        Obsługa zmiany zakładki.
        
        Args:
            index (int): Indeks wybranej zakładki
        """
        self.current_tab_index = index
        self.current_page = 0  # Resetuj paginację
        
        # Resetuj filtry dla odpowiedniej zakładki
        if index == 0:  # Zakładka nowych opon
            self.current_status_filter = self.new_tires_status_combo.currentText()
            self.current_season_filter = self.new_tires_season_combo.currentText()
            self.current_size_filter = self.new_tires_size_combo.currentText()
            self.filter_text = self.new_tires_search_field.text()
        else:  # Zakładka używanych opon
            self.current_status_filter = self.used_tires_status_combo.currentText()
            self.current_season_filter = self.used_tires_season_combo.currentText()
            self.current_size_filter = self.used_tires_size_combo.currentText()
            self.filter_text = self.used_tires_search_field.text()
        
        # Załaduj dane
        self.load_inventory()

    def filter_inventory(self, tab_index):
        """
        Obsługuje filtrowanie danych w tabeli.
        
        Args:
            tab_index (int): Indeks zakładki (0 - Nowe, 1 - Używane)
        """
        self.current_tab_index = tab_index
        self.current_page = 0  # Resetuj paginację
        
        if tab_index == 0:  # Zakładka nowych opon
            self.current_status_filter = self.new_tires_status_combo.currentText()
            self.current_season_filter = self.new_tires_season_combo.currentText()
            self.current_size_filter = self.new_tires_size_combo.currentText()
            self.filter_text = self.new_tires_search_field.text()
        else:  # Zakładka używanych opon
            self.current_status_filter = self.used_tires_status_combo.currentText()
            self.current_season_filter = self.used_tires_season_combo.currentText()
            self.current_size_filter = self.used_tires_size_combo.currentText()
            self.filter_text = self.used_tires_search_field.text()
        
        # Załaduj dane z nowymi filtrami
        self.load_inventory()

    def change_page(self, direction, tab_index):
        """
        Zmienia stronę w paginacji.
        
        Args:
            direction (int): Kierunek zmiany (-1 lub 1)
            tab_index (int): Indeks zakładki (0 - Nowe, 1 - Używane)
        """
        self.current_tab_index = tab_index
        self.current_page += direction
        
        # Upewnij się, że strona jest w prawidłowym zakresie
        if self.current_page < 0:
            self.current_page = 0
        if self.current_page >= self.total_pages:
            self.current_page = self.total_pages - 1
            
        # Załaduj dane dla nowej strony
        self.load_inventory()

    def load_tire_sizes(self, condition):
        """
        Ładuje dostępne rozmiary opon do kombo boxów.
        
        Args:
            condition (str): Stan opon ('Nowa' lub 'Używana')
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz unikalne rozmiary opon
            query = """
                SELECT DISTINCT size
                FROM inventory
                WHERE condition = ?
                ORDER BY size
            """
            
            cursor.execute(query, (condition,))
            sizes = cursor.fetchall()
            
            # Wybierz odpowiedni kombo box w zależności od stanu opon
            combo_box = self.new_tires_size_combo if condition == "Nowa" else self.used_tires_size_combo
            
            # Zachowaj aktualnie wybrany element
            current_text = combo_box.currentText()
            
            # Wyczyść kombo box
            combo_box.clear()
            
            # Dodaj opcję "Wszystkie"
            combo_box.addItem(_("Wszystkie"))
            
            # Dodaj rozmiary
            for size in sizes:
                combo_box.addItem(size['size'])
                
            # Przywróć poprzednie wybrane
            index = combo_box.findText(current_text)
            if index >= 0:
                combo_box.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"Błąd podczas ładowania rozmiarów opon: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania listy rozmiarów: {e}",
                NotificationTypes.ERROR
            )

    def show_tire_actions(self, row):
        """
        Wyświetla menu kontekstowe z akcjami dla wybranej opony.
        
        Args:
            row (int): Indeks wiersza w tabeli
        """
        # Wybierz aktywną tabelę
        table = self.new_tires_table if self.current_tab_index == 0 else self.used_tires_table
        
        # Pobierz ID opony
        id_item = table.item(row, 0)
        if id_item is None:
            return
            
        tire_id = id_item.data(Qt.UserRole)
        
        # Pobierz status opony
        status_item = table.item(row, 8)
        if status_item is None:
            return
            
        status = status_item.text()
        
        # Pobierz model opony dla tytuły menu
        manufacturer = table.item(row, 1).text()
        model = table.item(row, 2).text()
        size = table.item(row, 3).text()
        
        # Utwórz menu kontekstowe
        menu = QMenu(self)
        menu.setStyleSheet(STYLES["MENU"])
        
        # Nagłówek menu
        title_action = QAction(f"{manufacturer} {model} {size}", self)
        title_action.setEnabled(False)
        title_font = title_action.font()
        title_font.setBold(True)
        title_action.setFont(title_font)
        menu.addAction(title_action)
        menu.addSeparator()
        
        # Akcje dla wszystkich opon
        edit_action = QAction(_("Edytuj dane opony"), self)
        edit_action.triggered.connect(lambda: self.edit_tire(tire_id))
        menu.addAction(edit_action)
        
        history_action = QAction(_("Historia zmian"), self)
        history_action.triggered.connect(lambda: self.show_tire_history(tire_id))
        menu.addAction(history_action)
        
        print_label_action = QAction(_("Drukuj etykietę"), self)
        print_label_action.triggered.connect(lambda: self.generate_tire_label(tire_id))
        menu.addAction(print_label_action)
        
        menu.addSeparator()
        
        # Akcje zależne od statusu
        if status == _("Dostępna"):
            reserve_action = QAction(_("Oznacz jako zarezerwowane"), self)
            reserve_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Rezerwacja")))
            menu.addAction(reserve_action)
            
            sell_action = QAction(_("Oznacz jako sprzedane"), self)
            sell_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Sprzedana")))
            menu.addAction(sell_action)
            
        elif status == _("Rezerwacja"):
            available_action = QAction(_("Oznacz jako dostępne"), self)
            available_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Dostępna")))
            menu.addAction(available_action)
            
            sell_action = QAction(_("Oznacz jako sprzedane"), self)
            sell_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Sprzedana")))
            menu.addAction(sell_action)
            
        elif status == _("Zamówiona"):
            receive_action = QAction(_("Przyjmij na magazyn"), self)
            receive_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Dostępna")))
            menu.addAction(receive_action)
        
        elif status == _("Sprzedana"):
            return_action = QAction(_("Przyjmij zwrot"), self)
            return_action.triggered.connect(lambda: self.change_tire_status(tire_id, _("Dostępna")))
            menu.addAction(return_action)
        
        menu.addSeparator()
        
        # Akcja usunięcia
        delete_action = QAction(_("Usuń oponę"), self)
        delete_action.triggered.connect(lambda: self.delete_tire(tire_id))
        menu.addAction(delete_action)
        
        # Wyświetl menu
        global_pos = table.mapToGlobal(table.visualItemRect(table.item(row, 9)).center())
        menu.exec(global_pos)

    def add_tire(self):
        """Dodaje nową oponę do magazynu."""
        try:
            # Utwórz dialog dodawania opony
            dialog = InventoryDialog(self.conn)
            
            # Wyświetl dialog
            if dialog.exec() == QDialog.Accepted:
                # Jeśli dialog został zaakceptowany, odśwież dane
                self.load_statistics()
                self.load_inventory()
                
                # Odśwież listy rozmiarów
                self.load_tire_sizes("Nowa")
                self.load_tire_sizes("Używana")
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Opona została dodana do magazynu"),
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                self.tire_added.emit(dialog.get_tire_id())
        except Exception as e:
            logger.error(f"Błąd podczas dodawania opony: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania opony: {e}",
                NotificationTypes.ERROR
            )

    def edit_tire(self, tire_id):
        """
        Edytuje dane opony.
        
        Args:
            tire_id (int): ID opony do edycji
        """
        try:
            # Utwórz dialog edycji opony
            dialog = InventoryDialog(self.conn, tire_id)
            
            # Wyświetl dialog
            if dialog.exec() == QDialog.Accepted:
                # Jeśli dialog został zaakceptowany, odśwież dane
                self.load_statistics()
                self.load_inventory()
                
                # Odśwież listy rozmiarów
                self.load_tire_sizes("Nowa")
                self.load_tire_sizes("Używana")
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Dane opony zostały zaktualizowane"),
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                self.tire_updated.emit(tire_id)
        except Exception as e:
            logger.error(f"Błąd podczas edycji opony: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas edycji opony: {e}",
                NotificationTypes.ERROR
            )

    def change_tire_status(self, tire_id, new_status):
        """
        Zmienia status opony.
        
        Args:
            tire_id (int): ID opony
            new_status (str): Nowy status opony
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz aktualne dane opony
            cursor.execute("SELECT status, quantity FROM inventory WHERE id = ?", (tire_id,))
            tire = cursor.fetchone()
            
            if not tire:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono opony o ID {tire_id}",
                    NotificationTypes.ERROR
                )
                return
                
            old_status = tire['status']
            
            # Jeśli status już jest ustawiony, nie rób nic
            if old_status == new_status:
                return
                
            # Aktualizacja statusu i daty
            cursor.execute(
                "UPDATE inventory SET status = ?, last_updated = ? WHERE id = ?",
                (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tire_id)
            )
            
            # Zatwierdź transakcję
            self.conn.commit()
            
            # Odśwież dane
            self.load_statistics()
            self.load_inventory()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"{_('Status opony zmieniony:')} {old_status} → {new_status}",
                NotificationTypes.SUCCESS
            )
            
            # Emituj sygnał
            self.tire_updated.emit(tire_id)
            
        except Exception as e:
            logger.error(f"Błąd podczas zmiany statusu opony: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zmiany statusu opony: {e}",
                NotificationTypes.ERROR
            )

    def show_tire_history(self, tire_id):
        """
        Wyświetla historię zmian dla opony.
        
        Args:
            tire_id (int): ID opony
        """
        # Ta funkcja wymaga implementacji systemu historii zmian
        # Dla przykładu wyświetlimy komunikat
        QMessageBox.information(
            self,
            _("Historia zmian"),
            _("Funkcjonalność historii zmian zostanie zaimplementowana w przyszłej wersji.")
        )

    def import_inventory(self):
        """Importuje dane opon z pliku CSV lub Excel."""
        try:
            # Wybór pliku
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                _("Wybierz plik do importu"),
                "",
                _("Pliki CSV (*.csv);;Pliki Excel (*.xlsx *.xls)")
            )
            
            if not file_path:
                return
                
            # Sprawdź typ pliku
            if file_path.lower().endswith(('.xlsx', '.xls')):
                # Implementacja importu z Excela
                # TODO: Dodać obsługę importu z Excela
                NotificationManager.get_instance().show_notification(
                    _("Import z plików Excel zostanie dodany w przyszłej wersji"),
                    NotificationTypes.INFO
                )
            elif file_path.lower().endswith('.csv'):
                # Implementacja importu z CSV
                self.import_inventory_from_csv(file_path)
            else:
                NotificationManager.get_instance().show_notification(
                    _("Nieobsługiwany format pliku"),
                    NotificationTypes.ERROR
                )
                
        except Exception as e:
            logger.error(f"Błąd podczas importu danych: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas importu danych: {e}",
                NotificationTypes.ERROR
            )

    def import_inventory_from_csv(self, file_path):
        """
        Importuje dane opon z pliku CSV.
        
        Args:
            file_path (str): Ścieżka do pliku CSV
        """
        try:
            import csv
            
            # Odczytaj plik CSV
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                
                # Sprawdź czy struktura pliku jest poprawna
                required_fields = ['manufacturer', 'model', 'size', 'type', 'condition', 'quantity', 'price']
                
                if not all(field in csv_reader.fieldnames for field in required_fields):
                    NotificationManager.get_instance().show_notification(
                        _("Plik CSV nie zawiera wszystkich wymaganych pól"),
                        NotificationTypes.ERROR
                    )
                    return
                    
                # Liczniki importu
                imported_count = 0
                error_count = 0
                
                # Pobierz kursor bazy danych
                cursor = self.conn.cursor()
                
                # Rozpocznij transakcję
                self.conn.execute("BEGIN")
                
                try:
                    # Pobierz aktualną datę/czas
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Importuj dane
                    for row in csv_reader:
                        try:
                            # Przygotuj zapytanie
                            query = """
                                INSERT INTO inventory (
                                    manufacturer, model, size, type, condition,
                                    quantity, price, dot, status, bieznik,
                                    location, notes, receive_date, supplier,
                                    invoice_number, purchase_price, ean_code,
                                    last_updated
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """
                            
                            # Przygotuj parametry
                            params = [
                                row.get('manufacturer', ''),
                                row.get('model', ''),
                                row.get('size', ''),
                                row.get('type', ''),
                                row.get('condition', 'Nowa'),
                                int(row.get('quantity', 0)),
                                float(row.get('price', 0.0)),
                                row.get('dot', ''),
                                row.get('status', 'Dostępna'),
                                float(row.get('bieznik', 0.0)) if row.get('bieznik') else None,
                                row.get('location', ''),
                                row.get('notes', ''),
                                row.get('receive_date', now),
                                row.get('supplier', ''),
                                row.get('invoice_number', ''),
                                float(row.get('purchase_price', 0.0)) if row.get('purchase_price') else None,
                                row.get('ean_code', ''),
                                now
                            ]
                            
                            # Wykonaj zapytanie
                            cursor.execute(query, params)
                            imported_count += 1
                            
                        except Exception as e:
                            logger.error(f"Błąd podczas importu wiersza: {e}")
                            error_count += 1
                    
                    # Zatwierdź transakcję
                    self.conn.commit()
                    
                    # Powiadomienie
                    if error_count == 0:
                        NotificationManager.get_instance().show_notification(
                            f"{_('Import zakończony pomyślnie:')} {imported_count} {_('opon dodano')}",
                            NotificationTypes.SUCCESS
                        )
                    else:
                        NotificationManager.get_instance().show_notification(
                            f"{_('Import zakończony z błędami:')} {imported_count} {_('opon dodano,')} {error_count} {_('błędów')}",
                            NotificationTypes.WARNING
                        )
                        
                    # Odśwież dane
                    self.load_statistics()
                    self.load_inventory()
                    
                    # Odśwież listy rozmiarów
                    self.load_tire_sizes("Nowa")
                    self.load_tire_sizes("Używana")
                    
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
                    
        except Exception as e:
            logger.error(f"Błąd podczas importu z CSV: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas importu z CSV: {e}",
                NotificationTypes.ERROR
            )

    def refresh_data(self):
        """Odświeża dane w tabelach i statystykach."""
        try:
            # Odśwież statystyki
            self.load_statistics()
            
            # Odśwież dane w tabeli
            self.load_inventory()
            
            # Odśwież listy rozmiarów
            self.load_tire_sizes("Nowa")
            self.load_tire_sizes("Używana")
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Dane zostały odświeżone"),
                NotificationTypes.INFO
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas odświeżania danych: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas odświeżania danych: {e}",
                NotificationTypes.ERROR
            )

    def export_inventory(self):
        """Eksportuje dane opon do pliku Excel lub PDF."""
        try:
            # Wybierz format eksportu
            from PySide6.QtWidgets import QInputDialog
            
            export_formats = [
                _("Plik Excel (*.xlsx)"),
                _("Plik PDF (*.pdf)")
            ]
            
            export_format, ok = QInputDialog.getItem(
                self, 
                _("Wybierz format eksportu"), 
                _("Wybierz format pliku:"),
                export_formats, 0, False
            )
            
            if not ok:
                return
                
            # Wybierz zakres danych
            data_ranges = [
                _("Wszystkie opony"),
                _("Tylko opony nowe"),
                _("Tylko opony używane"),
                _("Tylko wyświetlane (z filtrami)")
            ]
            
            data_range, ok = QInputDialog.getItem(
                self, 
                _("Wybierz zakres danych"), 
                _("Wybierz zakres danych do eksportu:"),
                data_ranges, 0, False
            )
            
            if not ok:
                return
                
            # Wybierz ścieżkę do zapisu pliku
            default_filename = f"eksport_opon_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            if export_format == export_formats[0]:  # Excel
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    _("Zapisz jako"),
                    default_filename + ".xlsx",
                    "Excel (*.xlsx)"
                )
            else:  # PDF
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    _("Zapisz jako"),
                    default_filename + ".pdf",
                    "PDF (*.pdf)"
                )
                
            if not file_path:
                return
                
            # Pobierz dane do eksportu
            cursor = self.conn.cursor()
            
            query = """
                SELECT 
                    id, manufacturer, model, size, type, 
                    quantity, price, dot, status, condition,
                    bieznik, location, receive_date, supplier,
                    invoice_number, purchase_price, ean_code,
                    notes, last_updated
                FROM 
                    inventory
            """
            
            params = []
            
            # Dodaj filtry w zależności od wybranego zakresu
            if data_range == data_ranges[1]:  # Tylko opony nowe
                query += " WHERE condition = 'Nowa'"
            elif data_range == data_ranges[2]:  # Tylko opony używane
                query += " WHERE condition = 'Używana'"
            elif data_range == data_ranges[3]:  # Tylko wyświetlane (z filtrami)
                condition = "Nowa" if self.current_tab_index == 0 else "Używana"
                query += " WHERE condition = ?"
                params.append(condition)
                
                if self.current_status_filter != _("Wszystkie"):
                    query += " AND status = ?"
                    params.append(self.current_status_filter)
                    
                if self.current_season_filter != _("Wszystkie"):
                    query += " AND type = ?"
                    params.append(self.current_season_filter)
                    
                if self.current_size_filter != _("Wszystkie"):
                    query += " AND size = ?"
                    params.append(self.current_size_filter)
                    
                if self.filter_text:
                    query += """
                        AND (manufacturer LIKE ? OR model LIKE ? OR size LIKE ?)
                    """
                    search_param = f"%{self.filter_text}%"
                    params.extend([search_param, search_param, search_param])
                    
            # Sortowanie
            query += " ORDER BY manufacturer, model, size"
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            # Eksportuj dane
            if export_format == export_formats[0]:  # Excel
                export_data_to_excel(file_path, data, _("Magazyn Opon"))
            else:  # PDF
                export_data_to_pdf(file_path, data, _("Magazyn Opon"))
                
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"{_('Dane wyeksportowano do pliku:')} {file_path}",
                NotificationTypes.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu danych: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas eksportu danych: {e}",
                NotificationTypes.ERROR
            )