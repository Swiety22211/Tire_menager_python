#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zakładki zamówień w aplikacji Menadżer Serwisu Opon.
Obsługuje wyświetlanie, filtrowanie i zarządzanie zamówieniami.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QAbstractItemView, QDialog, QFileDialog,
    QFrame, QSplitter, QToolButton, QScrollArea, QMessageBox,
    QStyledItemDelegate, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtCore import Qt, QEvent, Signal, QDate, QRect

from ui.dialogs.order_dialog import OrderDialog
from utils.exporter import export_data_to_excel, export_data_to_pdf
from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Dodana funkcja do obsługi lokalizacji

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
    "NAV_BUTTON": """
        QPushButton {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #2c3034;
        }
    """,
    "PAGE_BUTTON": """
        QPushButton {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #2c3034;
        }
    """,
    "CURRENT_PAGE_BUTTON": """
        QPushButton {
            background-color: #4dabf7;
            color: white;
            font-weight: bold;
            border-radius: 5px;
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
    """
}


class StatusDelegate(QStyledItemDelegate):
    """
    Delegat do stylizowania komórek statusu w tabeli zamówień.
    """
    def paint(self, painter, option, index):
        status = index.data()
        
        if status == _("Zakończone"):
            background_color = QColor("#51cf66")  # Zielony
            text_color = QColor(255, 255, 255)
        elif status == _("W realizacji"):
            background_color = QColor("#4dabf7")  # Niebieski
            text_color = QColor(255, 255, 255)
        elif status == _("Nowe"):
            background_color = QColor("#ffa94d")  # Pomarańczowy
            text_color = QColor(255, 255, 255)
        elif status == _("Anulowane"):
            background_color = QColor("#fa5252")  # Czerwony
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

        # Obliczenie szerokości każdego przycisku i odstępów
        total_width = option.rect.width()
        button_width = min(total_width / 4, 30)  # Mniejsza szerokość z większymi marginesami
        spacing = (total_width - (button_width * 3)) / 4  # Równe odstępy

        # Pozycje x dla każdego przycisku
        x1 = option.rect.left() + spacing
        x2 = x1 + button_width + spacing
        x3 = x2 + button_width + spacing

        # Pozycja y (centr pionowy)
        y_center = option.rect.top() + option.rect.height() / 2
        button_height = 24

        # Obszary dla każdego przycisku
        view_rect = QRect(
            int(x1), 
            int(y_center - button_height/2),
            int(button_width), 
            int(button_height)
        )

        edit_rect = QRect(
            int(x2), 
            int(y_center - button_height/2),
            int(button_width), 
            int(button_height)
        )

        more_rect = QRect(
            int(x3), 
            int(y_center - button_height/2),
            int(button_width), 
            int(button_height)
        )

        # Rysowanie emotikon zamiast ikon
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(Qt.white)

        painter.drawText(view_rect, Qt.AlignCenter, "👁️")
        painter.drawText(edit_rect, Qt.AlignCenter, "✏️")
        painter.drawText(more_rect, Qt.AlignCenter, "⋮")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            # Obliczenie szerokości każdego przycisku i odstępów
            total_width = option.rect.width()
            button_width = min(total_width / 4, 30)  # Mniejsza szerokość z większymi marginesami
            spacing = (total_width - (button_width * 3)) / 4  # Równe odstępy

            # Pozycje x dla każdego przycisku
            x1 = option.rect.left() + spacing
            x2 = x1 + button_width + spacing
            x3 = x2 + button_width + spacing

            # Pozycja y (centr pionowy)
            y_center = option.rect.top() + option.rect.height() / 2
            button_height = 24

            # Obszary dla każdego przycisku
            view_rect = QRect(
                int(x1), 
                int(y_center - button_height/2),
                int(button_width), 
                int(button_height)
            )

            edit_rect = QRect(
                int(x2), 
                int(y_center - button_height/2),
                int(button_width), 
                int(button_height)
            )

            more_rect = QRect(
                int(x3), 
                int(y_center - button_height/2),
                int(button_width), 
                int(button_height)
            )

            if view_rect.contains(event.pos()):
                self.parent().view_order_requested.emit(index.row())
                return True
            elif edit_rect.contains(event.pos()):
                self.parent().edit_order_requested.emit(index.row())
                return True
            elif more_rect.contains(event.pos()):
                self.parent().more_actions_requested.emit(index.row())
                return True

        return super().editorEvent(event, model, option, index)


class OrdersTable(QTableWidget):
    """
    Tabela zamówień z obsługą akcji.
    """
    view_order_requested = Signal(int)
    edit_order_requested = Signal(int)
    more_actions_requested = Signal(int)
    
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
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            _("ID"), _("Data"), _("Klient"), _("Usługa"), 
            _("Status"), _("Kwota"), _("Akcje")
        ])
        
        # Ustawienie rozciągania kolumn
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Domyślnie interaktywne
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Data
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Klient
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Usługa
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Kwota
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Akcje
        self.setColumnWidth(6, 190)  # Stała szerokość kolumny akcji
        
        # Delegaty
        self.setItemDelegateForColumn(4, StatusDelegate(self))  # Status
        self.setItemDelegateForColumn(6, ActionButtonDelegate(self))  # Akcje
        
        # Wysokość wiersza
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Ustawienie reguł stylów dla trybu ciemnego
        self.setStyleSheet(STYLES["TABLE_WIDGET"])


class OrdersTab(QWidget):
    """Zakładka zamówień w aplikacji Menadżer Serwisu Opon"""
    
    # Sygnały związane z obsługą zamówień
    order_added = Signal(int)  # Emitowany po dodaniu zamówienia
    order_updated = Signal(int)  # Emitowany po aktualizacji zamówienia
    order_deleted = Signal(int)  # Emitowany po usunięciu zamówienia
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki zamówień.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.filtered_status = _("Wszystkie")
        self.records_per_page = 20  # Liczba rekordów na stronę dla paginacji
        self.current_page = 0  # Aktualna strona
        self.filter_text = ""  # Tekst wyszukiwania
        self.total_pages = 0  # Całkowita liczba stron
        self.date_from = None  # Data początkowa filtra
        self.date_to = None  # Data końcowa filtra
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie zamówień
        self.load_orders()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki zamówień."""
        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Tytuł zakładki zamówień
        title_label = QLabel(_("Zarządzanie Zamówieniami"))
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        # Elastyczny odstęp
        header_layout.addStretch(1)
        
        main_layout.addLayout(header_layout)
        
        # Panel wyszukiwania i filtrów
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        search_panel.setStyleSheet(STYLES["SEARCH_PANEL"])
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(10)
        
        # Pole wyszukiwania z emotikoną
        search_box = QFrame()
        search_box.setObjectName("searchBox")
        search_box.setFixedHeight(40)  # Ujednolicony rozmiar
        search_box.setMinimumWidth(300)
        search_box.setStyleSheet(STYLES["SEARCH_BOX"])
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 10, 0)
        search_box_layout.setSpacing(5)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("""
            background-color: transparent; 
            color: #adb5bd;
        """)
        search_icon.setFixedWidth(20)
        search_box_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText(_("Szukaj według numeru zamówienia, klienta lub usługi..."))
        self.search_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        self.search_input.textChanged.connect(self.filter_orders)
        search_box_layout.addWidget(self.search_input)
        
        search_layout.addWidget(search_box, 1)  # Rozciągnij pole wyszukiwania
        
        # Filtrowanie po dacie
        date_layout = QHBoxLayout()
        date_layout.setSpacing(5)
        
        date_label = QLabel(_("Okres:"))
        date_layout.addWidget(date_label)
        
        self.date_from_input = QLineEdit()
        self.date_from_input.setObjectName("dateField")
        self.date_from_input.setPlaceholderText(_("Od (DD-MM-YYYY)"))
        self.date_from_input.setFixedWidth(120)
        self.date_from_input.setFixedHeight(40)  # Ujednolicony rozmiar
        self.date_from_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        date_layout.addWidget(self.date_from_input)
        
        date_to_label = QLabel(_("do"))
        date_layout.addWidget(date_to_label)
        
        self.date_to_input = QLineEdit()
        self.date_to_input.setObjectName("dateField")
        self.date_to_input.setPlaceholderText(_("Do (DD-MM-YYYY)"))
        self.date_to_input.setFixedWidth(120)
        self.date_to_input.setFixedHeight(40)  # Ujednolicony rozmiar
        self.date_to_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        date_layout.addWidget(self.date_to_input)
        
        search_layout.addLayout(date_layout)
        
        # Combobox sortowania
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(5)
        
        sort_label = QLabel(_("Sortuj:"))
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("filterCombo")
        self.sort_combo.setFixedHeight(40)  # Ujednolicony rozmiar
        self.sort_combo.setMinimumWidth(150)
        self.sort_combo.addItems([
            _("Data (najnowsze)"), 
            _("Data (najstarsze)"), 
            _("Kwota (malejąco)"), 
            _("Kwota (rosnąco)")
        ])
        self.sort_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.sort_combo.currentTextChanged.connect(self.apply_sorting)
        sort_layout.addWidget(self.sort_combo)
        
        search_layout.addLayout(sort_layout)
        
        # Przycisk filtrowania z emotikoną
        self.filter_button = QPushButton("🔍 " + _("Filtruj"))
        self.filter_button.setObjectName("filterButton")
        self.filter_button.setFixedHeight(40)  # Ujednolicony rozmiar
        self.filter_button.setMinimumWidth(100)
        self.filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.filter_button.clicked.connect(self.apply_filters)
        search_layout.addWidget(self.filter_button)
        
        # Przycisk odświeżania
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.refresh_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.refresh_btn.clicked.connect(self.load_orders)
        search_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(search_panel)
        
        # Zakładki statusów zamówień
        self.status_tabs = QHBoxLayout()
        self.status_tabs.setSpacing(10)
        
        self.status_tab_buttons = {}
        status_types = [
            (_("Wszystkie"), "all", 0),
            (_("Nowe"), "new", 0),
            (_("W realizacji"), "in_progress", 0),
            (_("Zakończone"), "completed", 0),
            (_("Anulowane"), "cancelled", 0)
        ]
        
        for label, key, count in status_types:
            btn = QPushButton(f"{label} ({count})")
            btn.setProperty("status_type", key)
            btn.setFixedHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #343a40;
                    color: white;
                    border-radius: 5px;
                    font-size: 13px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #2c3034;
                }
                QPushButton[active="true"] {
                    background-color: #4dabf7;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(self.filter_by_status)
            self.status_tab_buttons[key] = btn
            self.status_tabs.addWidget(btn)
        
        self.status_tab_buttons["all"].setProperty("active", True)
        self.status_tab_buttons["all"].style().polish(self.status_tab_buttons["all"])
        
        self.status_tabs.addStretch(1)
        
        # Przycisk "Dodaj zamówienie" - teraz tworzony, ale dodany później do dolnego paska
        self.add_order_btn = QPushButton("➕ " + _("Nowe zamówienie"))
        self.add_order_btn.setObjectName("addButton")
        self.add_order_btn.setFixedHeight(40)  # Ujednolicony rozmiar z przyciskami w zakładce Klienci
        self.add_order_btn.setMinimumWidth(150)
        self.add_order_btn.setStyleSheet(STYLES["ADD_BUTTON"])
        self.add_order_btn.clicked.connect(self.add_order)
        
        main_layout.addLayout(self.status_tabs)
        
        # Tabela zamówień
        self.setup_orders_table()
        main_layout.addWidget(self.orders_table)
        
        # Panel nawigacji stron
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(10)
        
        # Informacja o liczbie wyświetlanych rekordów
        self.records_info = QLabel(_("Wyświetlanie 0 z 0 zamówień"))
        self.records_info.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        pagination_layout.addWidget(self.records_info)
        
        pagination_layout.addStretch(1)
        
        # Przyciski nawigacji z emotikonami
        self.prev_button = QPushButton("⬅️")
        self.prev_button.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.prev_button.setStyleSheet(STYLES["NAV_BUTTON"])
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_1_button = QPushButton("1")
        self.page_1_button.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.page_1_button.setObjectName("currentPageButton")
        self.page_1_button.setStyleSheet(STYLES["CURRENT_PAGE_BUTTON"])
        self.page_1_button.clicked.connect(lambda: self.go_to_page(int(self.page_1_button.text()) - 1))
        pagination_layout.addWidget(self.page_1_button)
        
        self.page_2_button = QPushButton("2")
        self.page_2_button.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.page_2_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_2_button.clicked.connect(lambda: self.go_to_page(int(self.page_2_button.text()) - 1))
        pagination_layout.addWidget(self.page_2_button)
        
        self.page_3_button = QPushButton("3")
        self.page_3_button.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.page_3_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_3_button.clicked.connect(lambda: self.go_to_page(int(self.page_3_button.text()) - 1))
        pagination_layout.addWidget(self.page_3_button)
        
        self.next_button = QPushButton("➡️")
        self.next_button.setFixedSize(40, 40)  # Ujednolicony rozmiar
        self.next_button.setStyleSheet(STYLES["NAV_BUTTON"])
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        pagination_layout.addStretch(1)
        
        # Przycisk dodawania zamówienia przeniesiony na dolny pasek
        pagination_layout.addWidget(self.add_order_btn)
        
        # Przyciski eksportu z emotikonami
        self.export_btn = QPushButton("📊 " + _("Raport"))
        self.export_btn.setFixedHeight(40)  # Ujednolicony rozmiar
        self.export_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.export_btn.clicked.connect(self.show_export_menu)
        pagination_layout.addWidget(self.export_btn)
        
        self.export_excel_btn = QPushButton("📥 " + _("Eksport Excel"))
        self.export_excel_btn.setFixedHeight(40)  # Ujednolicony rozmiar
        self.export_excel_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        pagination_layout.addWidget(self.export_excel_btn)
        
        self.export_pdf_btn = QPushButton("📄 " + _("Eksport PDF"))
        self.export_pdf_btn.setFixedHeight(40)  # Ujednolicony rozmiar
        self.export_pdf_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        pagination_layout.addWidget(self.export_pdf_btn)
        
        main_layout.addLayout(pagination_layout)
    
    def setup_orders_table(self):
        """
        Konfiguruje tabelę zamówień.
        """
        self.orders_table = OrdersTable()
        self.orders_table.customContextMenuRequested.connect(self.show_context_menu)
        self.orders_table.doubleClicked.connect(self.on_table_double_clicked)
        
        # Podłączenie sygnałów akcji
        self.orders_table.view_order_requested.connect(self.handle_view_order)
        self.orders_table.edit_order_requested.connect(self.handle_edit_order)
        self.orders_table.more_actions_requested.connect(self.show_more_actions)
    
    def on_table_double_clicked(self, index):
        """
        Obsługuje podwójne kliknięcie w tabelę.
        
        Args:
            index (QModelIndex): Indeks klikniętej komórki
        """
        row = index.row()
        order_id = int(self.orders_table.item(row, 0).text())
        self.view_order(order_id)
    
    def load_orders(self):
        """
        Ładuje zamówienia z bazy danych z uwzględnieniem filtrów.
        """
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie parametrów zapytania
            params = []
            
            # Bazowe zapytanie zoptymalizowane
            base_query = """
            SELECT 
                o.id, 
                o.order_date, 
                c.name AS client_name, 
                GROUP_CONCAT(oi.name, ', ') AS services, 
                o.status, 
                o.total_amount,
                (SELECT COUNT(*) FROM orders) AS total_count,
                (SELECT COUNT(*) FROM orders WHERE status = 'Nowe') AS new_count,
                (SELECT COUNT(*) FROM orders WHERE status = 'W realizacji') AS in_progress_count,
                (SELECT COUNT(*) FROM orders WHERE status = 'Zakończone') AS completed_count,
                (SELECT COUNT(*) FROM orders WHERE status = 'Anulowane') AS cancelled_count
            FROM 
                orders o
            JOIN 
                clients c ON o.client_id = c.id
            LEFT JOIN 
                order_items oi ON o.id = oi.order_id
            """
            
            # Warunki filtrowania
            where_clauses = []
            
            # Filtrowanie po tekście
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                where_clauses.append("""(
                    c.name LIKE ? OR 
                    o.id LIKE ? OR 
                    oi.name LIKE ?
                )""")
                params.extend([filter_text, filter_text, filter_text])
            
            # Filtrowanie po dacie
            if self.date_from:
                where_clauses.append("o.order_date >= ?")
                params.append(self.date_from)
            
            if self.date_to:
                where_clauses.append("o.order_date <= ?")
                params.append(self.date_to)
            
            # Filtrowanie po statusie
            if self.filtered_status != _("Wszystkie"):
                where_clauses.append("o.status = ?")
                params.append(self.filtered_status)
            
            # Dodanie warunków WHERE
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            # Grupowanie wyników
            base_query += " GROUP BY o.id"
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Data (najnowsze)"):
                base_query += " ORDER BY o.order_date DESC"
            elif sort_field == _("Data (najstarsze)"):
                base_query += " ORDER BY o.order_date ASC"
            elif sort_field == _("Kwota (malejąco)"):
                base_query += " ORDER BY o.total_amount DESC"
            elif sort_field == _("Kwota (rosnąco)"):
                base_query += " ORDER BY o.total_amount ASC"
            
            # Zapytanie do pobrania całkowitej liczby rekordów (bez paginacji)
            count_query = """
            SELECT COUNT(*) 
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            """
            
            if where_clauses:
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            # Pobierz całkowitą liczbę zamówień z filtrami
            cursor.execute(count_query, params)
            total_orders = cursor.fetchone()[0]
            
            # Oblicz całkowitą liczbę stron
            self.total_pages = (total_orders + self.records_per_page - 1) // self.records_per_page
            
            # Paginacja - dodaj LIMIT i OFFSET
            offset = self.current_page * self.records_per_page
            base_query += f" LIMIT {self.records_per_page} OFFSET {offset}"
            
            # Wykonaj główne zapytanie
            cursor.execute(base_query, params)
            orders = cursor.fetchall()
            
            # Odczyt i aktualizacja liczników dla zakładek statusów
            if orders:
                total_count = orders[0]['total_count']
                new_count = orders[0]['new_count']
                in_progress_count = orders[0]['in_progress_count']
                completed_count = orders[0]['completed_count']
                cancelled_count = orders[0]['cancelled_count']
                
                # Aktualizacja etykiet przycisków statusów
                self.status_tab_buttons["all"].setText(f"{_('Wszystkie')} ({total_count})")
                self.status_tab_buttons["new"].setText(f"{_('Nowe')} ({new_count})")
                self.status_tab_buttons["in_progress"].setText(f"{_('W realizacji')} ({in_progress_count})")
                self.status_tab_buttons["completed"].setText(f"{_('Zakończone')} ({completed_count})")
                self.status_tab_buttons["cancelled"].setText(f"{_('Anulowane')} ({cancelled_count})")
            else:
                # Jeśli nie ma zamówień, pobierz liczniki osobnym zapytaniem
                cursor.execute("""
                    SELECT 
                        COUNT(*) AS total_count,
                        SUM(CASE WHEN status = 'Nowe' THEN 1 ELSE 0 END) AS new_count,
                        SUM(CASE WHEN status = 'W realizacji' THEN 1 ELSE 0 END) AS in_progress_count,
                        SUM(CASE WHEN status = 'Zakończone' THEN 1 ELSE 0 END) AS completed_count,
                        SUM(CASE WHEN status = 'Anulowane' THEN 1 ELSE 0 END) AS cancelled_count
                    FROM orders
                """)
                counts = cursor.fetchone()
                
                if counts:
                    total_count = counts['total_count'] or 0
                    new_count = counts['new_count'] or 0
                    in_progress_count = counts['in_progress_count'] or 0
                    completed_count = counts['completed_count'] or 0
                    cancelled_count = counts['cancelled_count'] or 0
                    
                    # Aktualizacja etykiet przycisków statusów
                    self.status_tab_buttons["all"].setText(f"{_('Wszystkie')} ({total_count})")
                    self.status_tab_buttons["new"].setText(f"{_('Nowe')} ({new_count})")
                    self.status_tab_buttons["in_progress"].setText(f"{_('W realizacji')} ({in_progress_count})")
                    self.status_tab_buttons["completed"].setText(f"{_('Zakończone')} ({completed_count})")
                    self.status_tab_buttons["cancelled"].setText(f"{_('Anulowane')} ({cancelled_count})")
            
            # Wyczyść tabelę
            self.orders_table.setRowCount(0)
            
            # Wypełnij tabelę
            for order in orders:
                row_position = self.orders_table.rowCount()
                self.orders_table.insertRow(row_position)
                
                # Formatowanie danych
                order_id = str(order['id'])
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                client_name = order['client_name']
                services = order['services'] or "-"
                status = order['status']
                total_amount = f"{order['total_amount']:.2f} zł"
                
                # Dodawanie danych do komórek
                self.orders_table.setItem(row_position, 0, QTableWidgetItem(order_id))
                
                date_item = QTableWidgetItem(order_date)
                date_item.setTextAlignment(Qt.AlignCenter)
                self.orders_table.setItem(row_position, 1, date_item)
                
                self.orders_table.setItem(row_position, 2, QTableWidgetItem(client_name))
                self.orders_table.setItem(row_position, 3, QTableWidgetItem(services))
                
                # Status - obsługiwany przez delegata
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignCenter)
                self.orders_table.setItem(row_position, 4, status_item)
                
                # Kwota
                amount_item = QTableWidgetItem(total_amount)
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.orders_table.setItem(row_position, 5, amount_item)
                
                # Kolumna akcji - obsługiwana przez delegata
                self.orders_table.setItem(row_position, 6, QTableWidgetItem(""))
            
            # Aktualizacja informacji o paginacji
            displayed_count = len(orders)
            start_record = offset + 1 if displayed_count > 0 else 0
            end_record = offset + displayed_count
            
            self.records_info.setText(f"{_('Wyświetlanie')} {start_record}-{end_record} {_('z')} {total_orders} {_('zamówień')}")
            
            # Aktualizacja przycisków paginacji
            self.update_pagination_buttons()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania zamówień: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania zamówień: {e}",
                NotificationTypes.ERROR
            )
    
    def update_pagination_buttons(self):
        """
        Aktualizuje przyciski paginacji na podstawie aktualnej strony i całkowitej liczby stron.
        """
        # Resetowanie stylów przycisków
        self.page_1_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_2_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_3_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        
        # Określenie, które strony wyświetlić
        if self.total_pages <= 3:
            # Jeśli mamy 3 lub mniej stron, pokazujemy je wszystkie
            pages_to_show = range(1, self.total_pages + 1)
        else:
            # Jeśli mamy więcej stron, pokazujemy aktualną stronę i dwie następne
            if self.current_page == 0:
                pages_to_show = [1, 2, 3]
            elif self.current_page == self.total_pages - 1:
                pages_to_show = [self.total_pages - 2, self.total_pages - 1, self.total_pages]
            else:
                pages_to_show = [self.current_page + 1 - 1, self.current_page + 1, self.current_page + 1 + 1]
        
        # Aktualizacja przycisków
        buttons = [self.page_1_button, self.page_2_button, self.page_3_button]
        
        for i, button in enumerate(buttons):
            if i < len(pages_to_show):
                button.setText(str(pages_to_show[i]))
                button.setVisible(True)
                # Podświetlenie aktualnej strony
                if pages_to_show[i] == self.current_page + 1:
                    button.setStyleSheet(STYLES["CURRENT_PAGE_BUTTON"])
            else:
                button.setVisible(False)
        
        # Włącz/wyłącz przyciski nawigacji
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
    
    def go_to_page(self, page_number):
        """
        Przechodzi do wybranej strony.
        
        Args:
            page_number (int): Numer strony (0-based)
        """
        if 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self.load_orders()
    
    def next_page(self):
        """Przechodzi do następnej strony wyników."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_orders()

    def prev_page(self):
        """Przechodzi do poprzedniej strony wyników."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_orders()
    
    def filter_orders(self, text=""):
        """
        Filtruje zamówienia według wpisanego tekstu.
        
        Args:
            text (str): Tekst do filtrowania
        """
        # Zapisz tekst do filtrowania
        self.filter_text = text
        
        # Zastosuj aktualne filtry
        self.apply_filters()

    def apply_filters(self):
        """Stosuje filtry wyszukiwania i statusu do listy zamówień."""
        try:
            # Przetwarzanie dat
            date_from_text = self.date_from_input.text().strip()
            date_to_text = self.date_to_input.text().strip()
            
            if date_from_text:
                try:
                    # Konwersja formatu DD-MM-YYYY do YYYY-MM-DD dla bazy danych
                    date_obj = datetime.strptime(date_from_text, "%d-%m-%Y")
                    self.date_from = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    NotificationManager.get_instance().show_notification(
                        f"Nieprawidłowy format daty początkowej. Użyj formatu DD-MM-YYYY.",
                        NotificationTypes.WARNING
                    )
                    self.date_from = None
            else:
                self.date_from = None
            
            if date_to_text:
                try:
                    # Konwersja formatu DD-MM-YYYY do YYYY-MM-DD dla bazy danych
                    date_obj = datetime.strptime(date_to_text, "%d-%m-%Y")
                    self.date_to = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    NotificationManager.get_instance().show_notification(
                        f"Nieprawidłowy format daty końcowej. Użyj formatu DD-MM-YYYY.",
                        NotificationTypes.WARNING
                    )
                    self.date_to = None
            else:
                self.date_to = None
            
            # Resetuj paginację przy zmianie filtrów
            self.current_page = 0
            self.load_orders()
        except Exception as e:
            logger.error(f"Błąd podczas stosowania filtrów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas filtrowania: {e}",
                NotificationTypes.ERROR
            )

    def apply_sorting(self):
        """Stosuje wybrane sortowanie do listy zamówień."""
        self.load_orders()
    
    def filter_by_status(self):
        """Filtruje zamówienia po statusie."""
        sender = self.sender()
        status_type = sender.property("status_type")
        
        # Aktualizacja stanu aktywności przycisków
        for key, btn in self.status_tab_buttons.items():
            is_active = (key == status_type)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Ustawienie filtra statusu
        status_map = {
            "all": _("Wszystkie"),
            "new": _("Nowe"),
            "in_progress": _("W realizacji"),
            "completed": _("Zakończone"),
            "cancelled": _("Anulowane")
        }
        
        self.filtered_status = status_map.get(status_type, _("Wszystkie"))
        
        # Zastosuj filtr
        self.current_page = 0  # Reset paginacji
        self.load_orders()
        
        # Powiadomienie
        NotificationManager.get_instance().show_notification(
            f"Filtrowanie zamówień: {self.filtered_status}",
            NotificationTypes.INFO
        )
    
    def handle_view_order(self, row):
        """
        Obsługuje żądanie podglądu zamówienia z delegata akcji.
        
        Args:
            row (int): Wiersz zamówienia w tabeli
        """
        order_id = int(self.orders_table.item(row, 0).text())
        self.view_order(order_id)
    
    def handle_edit_order(self, row):
        """
        Obsługuje żądanie edycji zamówienia z delegata akcji.
        
        Args:
            row (int): Wiersz zamówienia w tabeli
        """
        order_id = int(self.orders_table.item(row, 0).text())
        self.edit_order(order_id)
    
    def view_order(self, order_id):
        """
        Wyświetla szczegóły zamówienia.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            # TODO: Zaimplementować szczegółowy widok zamówienia
            # Tymczasowo wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Wyświetlanie szczegółów zamówienia #{order_id}",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów zamówienia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania szczegółów zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def edit_order(self, order_id):
        """
        Edytuje wybrane zamówienie.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            dialog = OrderDialog(self.conn, order_id=order_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_orders()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"✏️ {_('Zamówienie')} #{order_id} {_('zaktualizowane pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                self.order_updated.emit(order_id)
        except Exception as e:
            logger.error(f"Błąd podczas edycji zamówienia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas edycji zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def show_more_actions(self, row):
        """
        Wyświetla menu z dodatkowymi akcjami dla zamówienia.
        
        Args:
            row (int): Wiersz zamówienia w tabeli
        """
        try:
            order_id = int(self.orders_table.item(row, 0).text())
            
            # Tworzenie menu
            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
            
            # Pobierz status zamówienia
            status = self.orders_table.item(row, 4).text()
            
            # Akcje zmiany statusu
            status_menu = menu.addMenu("🔄 " + _("Zmień status"))
            status_menu.setStyleSheet(STYLES["MENU"])
            
            statuses = [_("Nowe"), _("W realizacji"), _("Zakończone"), _("Anulowane")]
            for status_option in statuses:
                if status != status_option:
                    action = status_menu.addAction(status_option)
                    action.triggered.connect(lambda checked=False, oid=order_id, st=status_option: 
                                             self.change_order_status(oid, st))
            
            menu.addSeparator()
            
            # Opcja usunięcia
            delete_action = menu.addAction("🗑️ " + _("Usuń zamówienie"))
            delete_action.triggered.connect(lambda: self.delete_order(order_id))
            
            # Wyświetlenie menu w lokalizacji przycisku
            button_pos = self.orders_table.visualItemRect(self.orders_table.item(row, 6)).center()
            menu.exec(self.orders_table.viewport().mapToGlobal(button_pos))
            
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania menu akcji: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania menu akcji: {e}",
                NotificationTypes.ERROR
            )
    
    def show_context_menu(self, pos):
        """
        Wyświetla kontekstowe menu po kliknięciu prawym przyciskiem myszy.
        
        Args:
            pos (QPoint): Pozycja kursora
        """
        index = self.orders_table.indexAt(pos)
        if not index.isValid():
            return
        
        row = index.row()
        order_id = int(self.orders_table.item(row, 0).text())
        
        # Pobierz więcej informacji o zamówieniu dla wyświetlenia w menu
        client_name = self.orders_table.item(row, 2).text()
        
        # Tworzenie menu kontekstowego
        menu = QMenu(self)
        menu.setStyleSheet(STYLES["MENU"])
        
        # Akcje menu
        view_action = menu.addAction(f"👁️ {_('Szczegóły zamówienia')} #{order_id}")
        edit_action = menu.addAction(f"✏️ {_('Edytuj zamówienie')}")
        menu.addSeparator()
        
        # Opcje zmiany statusu
        status = self.orders_table.item(row, 4).text()
        status_menu = menu.addMenu(f"🔄 {_('Zmień status')}")
        status_menu.setStyleSheet(STYLES["MENU"])
        
        statuses = [_("Nowe"), _("W realizacji"), _("Zakończone"), _("Anulowane")]
        for status_option in statuses:
            if status != status_option:
                action = status_menu.addAction(status_option)
                action.triggered.connect(lambda checked=False, oid=order_id, st=status_option: 
                                         self.change_order_status(oid, st))
        
        menu.addSeparator()
        delete_action = menu.addAction(f"🗑️ {_('Usuń zamówienie')}")
        
        # Wyświetlenie menu i obsługa wybranej akcji
        action = menu.exec(self.orders_table.mapToGlobal(pos))
        
        if action == view_action:
            self.view_order(order_id)
        elif action == edit_action:
            self.edit_order(order_id)
        elif action == delete_action:
            self.delete_order(order_id)
    
    def add_order(self):
        """Otwiera dialog dodawania nowego zamówienia."""
        try:
            dialog = OrderDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę zamówień
                self.load_orders()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"➕ {_('Dodano nowe zamówienie pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał (jeśli dialog przekazuje ID nowego zamówienia)
                if hasattr(dialog, 'order_id'):
                    self.order_added.emit(dialog.order_id)
        except Exception as e:
            logger.error(f"Błąd podczas dodawania zamówienia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def change_order_status(self, order_id, new_status):
        """
        Zmienia status zamówienia.
        
        Args:
            order_id (int): ID zamówienia
            new_status (str): Nowy status zamówienia
        """
        try:
            cursor = self.conn.cursor()
            
            # Pobierz aktualny status
            cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            current_status = cursor.fetchone()['status']
            
            # Aktualizuj status
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id)
            )
            
            self.conn.commit()
            
            # Odśwież listę zamówień
            self.load_orders()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"🔄 {_('Status zamówienia')} #{order_id} {_('zmieniony z')} '{current_status}' {_('na')} '{new_status}'",
                NotificationTypes.SUCCESS
            )
            
            # Emituj sygnał
            self.order_updated.emit(order_id)
            
        except Exception as e:
            logger.error(f"Błąd podczas zmiany statusu zamówienia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zmiany statusu zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def delete_order(self, order_id):
        """
        Usuwa zamówienie.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            # Potwierdzenie usunięcia
            reply = QMessageBox.question(
                self, 
                _("Potwierdź usunięcie"), 
                _("Czy na pewno chcesz usunąć zamówienie #{}?\n\n"
                "Ta operacja usunie również wszystkie powiązane pozycje zamówienia.\n"
                "Ta operacja jest nieodwracalna.").format(order_id),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Usuń powiązane pozycje zamówienia
                    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
                    
                    # Usuń zamówienie
                    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                    
                    # Zatwierdź zmiany
                    self.conn.commit()
                    
                    # Odśwież listę zamówień
                    self.load_orders()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"🗑️ {_('Zamówienie')} #{order_id} {_('zostało usunięte')}",
                        NotificationTypes.SUCCESS
                    )
                    
                    # Emituj sygnał
                    self.order_deleted.emit(order_id)
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
        except Exception as e:
            logger.error(f"Błąd podczas usuwania zamówienia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas usuwania zamówienia: {e}",
                NotificationTypes.ERROR
            )
    
    def show_export_menu(self):
        """Wyświetla menu eksportu zamówień."""
        menu = QMenu(self)
        menu.setStyleSheet(STYLES["MENU"])
        
        export_actions = [
            ("📊 " + _("Raport podsumowujący"), self.generate_summary_report),
            ("📈 " + _("Analiza sprzedaży"), self.generate_sales_analysis),
            ("📉 " + _("Raport statusów"), self.generate_status_report)
        ]
        
        for label, slot in export_actions:
            action = QAction(label, self)
            action.triggered.connect(slot)
            menu.addAction(action)
        
        menu.addSeparator()
        
        export_excel_action = QAction("📥 " + _("Eksportuj do Excel"), self)
        export_excel_action.triggered.connect(self.export_to_excel)
        menu.addAction(export_excel_action)
        
        export_pdf_action = QAction("📄 " + _("Eksportuj do PDF"), self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        menu.addAction(export_pdf_action)
        
        # Wyświetlenie menu w lokalizacji przycisku
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))
    
    def generate_summary_report(self):
        """Generuje raport podsumowujący zamówienia."""
        try:
            NotificationManager.get_instance().show_notification(
                "Generowanie raportu podsumowującego...",
                NotificationTypes.INFO
            )
            
            # TODO: Zaimplementować generowanie raportu
            # Tymczasowo wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                "Funkcja generowania raportu podsumowującego będzie dostępna wkrótce.",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas generowania raportu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania raportu: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_sales_analysis(self):
        """Generuje analizę sprzedaży."""
        try:
            NotificationManager.get_instance().show_notification(
                "Generowanie analizy sprzedaży...",
                NotificationTypes.INFO
            )
            
            # TODO: Zaimplementować generowanie analizy sprzedaży
            # Tymczasowo wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                "Funkcja generowania analizy sprzedaży będzie dostępna wkrótce.",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas generowania analizy sprzedaży: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania analizy sprzedaży: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_status_report(self):
        """Generuje raport statusów zamówień."""
        try:
            NotificationManager.get_instance().show_notification(
                "Generowanie raportu statusów...",
                NotificationTypes.INFO
            )
            
            # TODO: Zaimplementować generowanie raportu statusów
            # Tymczasowo wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                "Funkcja generowania raportu statusów będzie dostępna wkrótce.",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas generowania raportu statusów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania raportu statusów: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_excel(self):
        """Eksportuje zamówienia do pliku Excel."""
        try:
            # Wybór pliku docelowego
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                _("Zapisz plik Excel"), 
                f"zamowienia_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Czy eksportować tylko widoczne/przefiltrowane zamówienia?
            export_mode = QMessageBox.question(
                self,
                _("Opcje eksportu"),
                _("Czy chcesz wyeksportować:\n\n"
                "• Tak: Tylko aktualnie przefiltrowane zamówienia\n"
                "• Nie: Wszystkie zamówienia w bazie danych\n"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if export_mode == QMessageBox.Cancel:
                return
            
            # Przygotuj zapytanie
            cursor = self.conn.cursor()
            base_query = """
            SELECT 
                o.id, 
                o.order_date, 
                c.name AS client_name, 
                GROUP_CONCAT(oi.name, ', ') AS services, 
                o.status, 
                o.total_amount,
                o.notes
            FROM 
                orders o
            JOIN 
                clients c ON o.client_id = c.id
            LEFT JOIN 
                order_items oi ON o.id = oi.order_id
            """
            
            params = []
            
            if export_mode == QMessageBox.Yes:
                # Eksportuj tylko przefiltrowane zamówienia
                where_clauses = []
                
                if self.filter_text:
                    filter_text = f"%{self.filter_text}%"
                    where_clauses.append("""(
                        c.name LIKE ? OR 
                        o.id LIKE ? OR 
                        oi.name LIKE ?
                    )""")
                    params.extend([filter_text, filter_text, filter_text])
                
                if self.date_from:
                    where_clauses.append("o.order_date >= ?")
                    params.append(self.date_from)
                
                if self.date_to:
                    where_clauses.append("o.order_date <= ?")
                    params.append(self.date_to)
                
                if self.filtered_status != _("Wszystkie"):
                    where_clauses.append("o.status = ?")
                    params.append(self.filtered_status)
                
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " GROUP BY o.id"
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Data (najnowsze)"):
                base_query += " ORDER BY o.order_date DESC"
            elif sort_field == _("Data (najstarsze)"):
                base_query += " ORDER BY o.order_date ASC"
            elif sort_field == _("Kwota (malejąco)"):
                base_query += " ORDER BY o.total_amount DESC"
            elif sort_field == _("Kwota (rosnąco)"):
                base_query += " ORDER BY o.total_amount ASC"
            
            # Pobierz dane
            cursor.execute(base_query, params)
            orders = cursor.fetchall()
            
            # Przygotuj dane do eksportu
            export_data = []
            headers = [
                _("ID"), _("Data"), _("Klient"), _("Usługi"), 
                _("Status"), _("Kwota"), _("Uwagi")
            ]
            
            for order in orders:
                # Formatowanie daty
                date_str = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                export_data.append([
                    order['id'],
                    date_str,
                    order['client_name'],
                    order['services'] or "",
                    order['status'],
                    order['total_amount'],
                    order['notes'] or ""
                ])
            
            # Wywołaj eksport do Excel
            export_data_to_excel(file_path, headers, export_data, _("Zamówienia"))
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"📥 {_('Wyeksportowano')} {len(orders)} {_('zamówień do pliku Excel')}",
                NotificationTypes.SUCCESS
            )
            
            # Informacja o zakończeniu
            QMessageBox.information(
                self,
                _("Eksport zakończony"),
                _("Pomyślnie wyeksportowano {} zamówień do pliku Excel:\n{}").format(
                    len(orders), file_path
                )
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu do Excel: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do Excel: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_pdf(self):
        """Eksportuje zamówienia do pliku PDF."""
        try:
            # Wybór pliku docelowego
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                _("Zapisz plik PDF"), 
                f"zamowienia_{datetime.now().strftime('%Y%m%d')}.pdf",
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Przygotuj zapytanie
            cursor = self.conn.cursor()
            base_query = """
            SELECT 
                o.id, 
                o.order_date, 
                c.name AS client_name, 
                GROUP_CONCAT(oi.name, ', ') AS services, 
                o.status, 
                o.total_amount
            FROM 
                orders o
            JOIN 
                clients c ON o.client_id = c.id
            LEFT JOIN 
                order_items oi ON o.id = oi.order_id
            """
            
            # Filtrowanie podobne jak w export_to_excel
            params = []
            where_clauses = []
            
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                where_clauses.append("""(
                    c.name LIKE ? OR 
                    o.id LIKE ? OR 
                    oi.name LIKE ?
                )""")
                params.extend([filter_text, filter_text, filter_text])
            
            if self.date_from:
                where_clauses.append("o.order_date >= ?")
                params.append(self.date_from)
            
            if self.date_to:
                where_clauses.append("o.order_date <= ?")
                params.append(self.date_to)
            
            if self.filtered_status != _("Wszystkie"):
                where_clauses.append("o.status = ?")
                params.append(self.filtered_status)
            
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " GROUP BY o.id"
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Data (najnowsze)"):
                base_query += " ORDER BY o.order_date DESC"
            elif sort_field == _("Data (najstarsze)"):
                base_query += " ORDER BY o.order_date ASC"
            elif sort_field == _("Kwota (malejąco)"):
                base_query += " ORDER BY o.total_amount DESC"
            elif sort_field == _("Kwota (rosnąco)"):
                base_query += " ORDER BY o.total_amount ASC"
            
            # Pobierz dane
            cursor.execute(base_query, params)
            orders = cursor.fetchall()
            
            # Przygotuj dane do eksportu
            export_data = []
            headers = [
                _("ID"), _("Data"), _("Klient"), _("Usługi"), 
                _("Status"), _("Kwota")
            ]
            
            for order in orders:
                # Formatowanie daty
                date_str = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                # Formatowanie kwoty
                amount_str = f"{order['total_amount']:.2f} zł"
                
                export_data.append([
                    order['id'],
                    date_str,
                    order['client_name'],
                    order['services'] or "",
                    order['status'],
                    amount_str
                ])
            
            # Wywołaj eksport do PDF
            export_data_to_pdf(file_path, headers, export_data, _("Zamówienia"))
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"📄 {_('Wyeksportowano')} {len(orders)} {_('zamówień do pliku PDF')}",
                NotificationTypes.SUCCESS
            )
            
            # Informacja o zakończeniu
            QMessageBox.information(
                self,
                _("Eksport zakończony"),
                _("Pomyślnie wyeksportowano {} zamówień do pliku PDF:\n{}").format(
                    len(orders), file_path
                )
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu do PDF: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do PDF: {e}",
                NotificationTypes.ERROR
            )
    
    def search(self, text):
        """
        Publiczna metoda do wyszukiwania zamówień, którą można wywołać z zewnątrz.
        
        Args:
            text (str): Tekst do wyszukiwania
        """
        self.search_input.setText(text)
        self.filter_orders(text)
    
    def refresh_data(self):
        """Odświeża dane w zakładce zamówień."""
        self.load_orders()
        
        # Powiadomienie
        NotificationManager.get_instance().show_notification(
            f"🔄 {_('Dane zamówień odświeżone')}",
            NotificationTypes.INFO
        )