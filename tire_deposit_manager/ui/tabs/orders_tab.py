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
    QStyledItemDelegate, QSpacerItem, QSizePolicy, QDialogButtonBox
)
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtCore import Qt, QEvent, Signal, QDate, QRect, QSettings

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
            
            # Po istniejącym menu, przed menu.exec():
            menu.addSeparator()

            # Dodaj menu komunikacji
            comm_menu = menu.addMenu("📱 " + _("Komunikacja"))
            comm_menu.setStyleSheet(STYLES["MENU"])

            # Email
            send_email_action = comm_menu.addAction("📧 " + _("Wyślij email"))
            send_email_action.triggered.connect(lambda: self.send_email_to_client(order_id))

            # SMS
            send_sms_action = comm_menu.addAction("📱 " + _("Wyślij SMS"))
            send_sms_action.triggered.connect(lambda: self.send_sms_to_client(order_id))            

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
        
        # Dodaj opcje komunikacji bezpośrednio do menu głównego (jak w deposits_tab.py)
        print_label_action = menu.addAction(f"🏷️ {_('Generuj etykietę')}")
        print_receipt_action = menu.addAction(f"📃 {_('Generuj potwierdzenie')}")
        send_email_action = menu.addAction(f"📧 {_('Wyślij powiadomienie email')}")
        send_sms_action = menu.addAction(f"📱 {_('Wyślij powiadomienie SMS')}")
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
        elif action == send_email_action:
            self.send_email_to_client(order_id)
        elif action == send_sms_action:
            self.send_sms_to_client(order_id)
        elif action == print_label_action:
            # Dodaj obsługę generowania etykiety (jeśli masz taką funkcję)
            NotificationManager.get_instance().show_notification(
                f"Funkcja generowania etykiety zostanie dostępna wkrótce.",
                NotificationTypes.INFO
            )
        elif action == print_receipt_action:
            # Dodaj obsługę generowania potwierdzenia (jeśli masz taką funkcję)
            NotificationManager.get_instance().show_notification(
                f"Funkcja generowania potwierdzenia zostanie dostępna wkrótce.",
                NotificationTypes.INFO
            )

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
        Usuwa zamówienie wraz ze wszystkimi powiązanymi rekordami.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            # Potwierdzenie usunięcia
            reply = QMessageBox.question(
                self,  # rodzic (self widget)
                _("Potwierdź usunięcie"),  # tytuł
                _("Czy na pewno chcesz usunąć zamówienie #{}?\n\n"
                "Ta operacja usunie również wszystkie powiązane pozycje zamówienia.\n"
                "Ta operacja jest nieodwracalna.").format(order_id),  # tekst
                QMessageBox.Yes | QMessageBox.No,  # standardowe przyciski
                QMessageBox.No  # domyślny przycisk
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Usuń logi emaili związane z zamówieniem
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS order_email_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id INTEGER,
                            email TEXT,
                            subject TEXT,
                            sent_date TEXT,
                            status TEXT,
                            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
                        )
                    """)
                    cursor.execute("DELETE FROM order_email_logs WHERE order_id = ?", (order_id,))
                    
                    # Usuń logi SMS związane z zamówieniem
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS order_sms_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id INTEGER,
                            phone_number TEXT,
                            content TEXT,
                            sent_date TEXT,
                            status TEXT,
                            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
                        )
                    """)
                    cursor.execute("DELETE FROM order_sms_logs WHERE order_id = ?", (order_id,))
                    
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
                    logger.error(f"Błąd podczas usuwania zamówienia (szczegóły): {e}")
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

    def send_email_to_client(self, order_id):
        """
        Wysyła email do klienta związany z zamówieniem.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            # Pobierz dane zamówienia
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT o.id, o.order_date, o.status, o.total_amount, o.notes,
                    c.name as client_name, c.email, c.phone_number
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order = cursor.fetchone()
            
            if not order:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono zamówienia o ID {order_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Sprawdź czy klient ma email
            if not order['email']:
                QMessageBox.warning(
                    self,
                    _("Brak adresu email"),
                    _("Klient nie posiada adresu email. Dodaj adres email do konta klienta przed wysłaniem wiadomości.")
                )
                return
            
            # Pobierz ustawienia email z QSettings
            settings = QSettings("TireDepositManager", "Settings")
            email_address = settings.value("email_address", "")
            email_password = settings.value("email_password", "")
            smtp_server = settings.value("smtp_server", "")
            smtp_port = settings.value("smtp_port", 587, type=int)
            use_ssl = settings.value("use_ssl", True, type=bool)
            
            # Sprawdź czy ustawienia email są skonfigurowane
            if not all([email_address, email_password, smtp_server, smtp_port]):
                QMessageBox.warning(
                    self,
                    _("Brak konfiguracji email"),
                    _("Konfiguracja email nie jest kompletna. Uzupełnij ustawienia w zakładce Ustawienia → Komunikacja.")
                )
                return
            
            # Pobierz szablony email
            try:
                import json
                import os
                from utils.paths import CONFIG_DIR
                
                templates_file = os.path.join(CONFIG_DIR, "templates.json")
                
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                else:
                    QMessageBox.warning(
                        self,
                        _("Brak szablonów"),
                        _("Nie znaleziono szablonów email. Skonfiguruj szablony w zakładce Ustawienia → Szablony.")
                    )
                    return
                
                # Ujednolicone mapowanie statusów na klucze szablonów - takie samo jak w order_dialog.py
                status = order['status']
                status_to_template_key = {
                    _("Nowe"): "order_nowe",
                    _("W realizacji"): "order_w_realizacji", 
                    _("Zakończone"): "order_zakończone",
                    _("Anulowane"): "order_nowe"  # Domyślnie używaj szablonu nowego zamówienia dla anulowanych
                }

                # Domyślnie używaj szablonu dla nowych zamówień, jeśli nie znajdziesz szablonu dla danego statusu
                template_key = status_to_template_key.get(status, "order_nowe")
                logger.info(f"Używany klucz szablonu dla statusu '{status}': {template_key}")

                # Dodaj kod diagnostyczny do wyświetlenia dostępnych szablonów
                if "email" in templates:
                    available_templates = list(templates["email"].keys())
                    logger.info(f"Dostępne szablony: {available_templates}")
                
                # Sprawdź czy szablon istnieje
                if "email" not in templates or template_key not in templates["email"]:
                    QMessageBox.warning(
                        self,
                        _("Brak szablonu"),
                        _("Nie znaleziono szablonu email dla wybranego statusu zamówienia. Sprawdź szablony w ustawieniach.")
                    )
                    return
                    
                logger.info(f"Znaleziono szablon: {template_key}")
                
                # Przygotuj dane do szablonu
                company_name = settings.value("company_name", "")
                company_address = settings.value("company_address", "")
                company_phone = settings.value("company_phone", "")
                company_email = settings.value("company_email", "")
                company_website = settings.value("company_website", "")
                
                # Pobierz pozycje zamówienia
                cursor.execute("""
                    SELECT name, quantity, price
                    FROM order_items
                    WHERE order_id = ?
                """, (order_id,))
                
                items = cursor.fetchall()
                
                # Przygotuj tabelę z pozycjami zamówienia
                items_table = """
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="background-color:#f8f9fa;">
                        <th style="padding:8px; border:1px solid #ddd; text-align:left;">Nazwa</th>
                        <th style="padding:8px; border:1px solid #ddd; text-align:center;">Ilość</th>
                        <th style="padding:8px; border:1px solid #ddd; text-align:right;">Cena</th>
                    </tr>
                """
                
                for item in items:
                    items_table += f"""
                    <tr>
                        <td style="padding:8px; border:1px solid #ddd;">{item['name']}</td>
                        <td style="padding:8px; border:1px solid #ddd; text-align:center;">{item['quantity']}</td>
                        <td style="padding:8px; border:1px solid #ddd; text-align:right;">{item['price']:.2f} zł</td>
                    </tr>
                    """
                
                items_table += "</table>"
                
                # Formatowanie daty
                from datetime import datetime
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                # Przygotuj mapowanie zmiennych
                template_vars = {
                    "order_id": order_id,
                    "client_name": order['client_name'],
                    "client_email": order['email'],
                    "order_date": order_date,
                    "status": order['status'],
                    "total_amount": f"{order['total_amount']:.2f} zł",
                    "items_table": items_table,
                    "notes": order['notes'] or "",
                    "company_name": company_name,
                    "company_address": company_address,
                    "company_phone": company_phone,
                    "company_email": company_email,
                    "company_website": company_website
                }
                
                # Pobierz szablon i podstaw zmienne
                email_template = templates["email"][template_key]
                subject = email_template["subject"]
                body = email_template["body"]
                
                # Podstawianie zmiennych w temacie i treści
                for key, value in template_vars.items():
                    subject = subject.replace("{" + key + "}", str(value))
                    body = body.replace("{" + key + "}", str(value))
                
                # Pokaż podgląd wiadomości
                preview_dialog = QDialog(self)
                preview_dialog.setWindowTitle(_("Podgląd wiadomości email"))
                preview_dialog.setMinimumSize(600, 400)
                
                layout = QVBoxLayout(preview_dialog)
                
                # Dodaj etykietę z informacjami
                info_label = QLabel(_("Wiadomość zostanie wysłana do: ") + order['email'])
                layout.addWidget(info_label)
                
                # Dodaj informację o użytym szablonie
                template_info = QLabel(_("Używany szablon: ") + template_key)
                layout.addWidget(template_info)
                
                # Dodaj pole edycji tematu
                subject_layout = QHBoxLayout()
                subject_layout.addWidget(QLabel(_("Temat:")))
                subject_edit = QLineEdit(subject)
                subject_layout.addWidget(subject_edit)
                layout.addLayout(subject_layout)
                
                # Dodaj podgląd treści (tylko do czytania)
                from PySide6.QtWebEngineWidgets import QWebEngineView
                preview = QWebEngineView()
                preview.setHtml(body)
                layout.addWidget(preview)
                
                # Przyciski
                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                    Qt.Horizontal, 
                    preview_dialog
                )
                buttons.accepted.connect(preview_dialog.accept)
                buttons.rejected.connect(preview_dialog.reject)
                layout.addWidget(buttons)
                
                # Wyświetl dialog podglądu
                if preview_dialog.exec() == QDialog.Accepted:
                    # Wyślij email
                    try:
                        import smtplib
                        from email.mime.text import MIMEText
                        from email.mime.multipart import MIMEMultipart
                        
                        # Aktualizuj temat (jeśli został zmieniony)
                        subject = subject_edit.text()
                        
                        # Przygotuj wiadomość
                        msg = MIMEMultipart()
                        msg['From'] = email_address
                        msg['To'] = order['email']
                        msg['Subject'] = subject
                        
                        msg.attach(MIMEText(body, 'html'))
                        
                        # Połącz z serwerem SMTP
                        if use_ssl:
                            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                        else:
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                        
                        # Logowanie
                        server.login(email_address, email_password)
                        
                        # Wysyłka wiadomości
                        server.send_message(msg)
                        
                        # Zamknięcie połączenia
                        server.quit()
                        
                        # Zapisz log wysłanego emaila
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS order_email_logs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                order_id INTEGER,
                                email TEXT,
                                subject TEXT,
                                sent_date TEXT,
                                status TEXT,
                                FOREIGN KEY (order_id) REFERENCES orders (id)
                            )
                        """)
                        
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO order_email_logs (order_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                            (order_id, order['email'], subject, current_date, "Wysłany")
                        )
                        self.conn.commit()
                        
                        NotificationManager.get_instance().show_notification(
                            f"📧 {_('Email wysłany pomyślnie do')}: {order['client_name']}",
                            NotificationTypes.SUCCESS
                        )
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas wysyłania email: {e}")
                        QMessageBox.critical(
                            self,
                            _("Błąd wysyłania"),
                            _("Nie udało się wysłać wiadomości email:\n\n") + str(e)
                        )
                
            except Exception as e:
                logger.error(f"Błąd podczas przygotowania email: {e}")
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas przygotowania wiadomości email:\n\n") + str(e)
                )
        
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania email: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd wysyłania email: {e}",
                NotificationTypes.ERROR
            )

    def send_sms_to_client(self, order_id):
        """
        Wysyła SMS do klienta związany z zamówieniem.
        
        Args:
            order_id (int): ID zamówienia
        """
        try:
            # Pobierz dane zamówienia
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT o.id, o.order_date, o.status, o.total_amount, o.notes,
                    c.name as client_name, c.email, c.phone_number
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order = cursor.fetchone()
            
            if not order:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono zamówienia o ID {order_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Sprawdź czy klient ma numer telefonu
            if not order['phone_number']:
                QMessageBox.warning(
                    self,
                    _("Brak numeru telefonu"),
                    _("Klient nie posiada numeru telefonu. Dodaj numer do konta klienta przed wysłaniem SMS.")
                )
                return
            
            # Formatuj numer telefonu
            from utils.sms_sender import format_phone_number
            formatted_phone = format_phone_number(order['phone_number'])
            
            # Pobierz ustawienia SMS z QSettings
            settings = QSettings("TireDepositManager", "Settings")
            api_key = settings.value("sms_api_key", "")
            sender = settings.value("sms_sender", "")
            enable_sms = settings.value("enable_sms", False, type=bool)
            
            # Sprawdź czy SMS są włączone
            if not enable_sms:
                QMessageBox.warning(
                    self,
                    _("SMS wyłączone"),
                    _("Wysyłanie SMS jest wyłączone. Włącz je w ustawieniach.")
                )
                return
            
            # Sprawdź czy ustawienia SMS są skonfigurowane
            if not all([api_key, sender]):
                QMessageBox.warning(
                    self,
                    _("Brak konfiguracji SMS"),
                    _("Konfiguracja SMS nie jest kompletna. Uzupełnij ustawienia w zakładce Ustawienia → Komunikacja.")
                )
                return
            
            # Pobierz szablony SMS
            try:
                import json
                import os
                from utils.paths import CONFIG_DIR
                
                templates_file = os.path.join(CONFIG_DIR, "templates.json")
                
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                else:
                    QMessageBox.warning(
                        self,
                        _("Brak szablonów"),
                        _("Nie znaleziono szablonów SMS. Skonfiguruj szablony w zakładce Ustawienia → Szablony.")
                    )
                    return
                    
                # Status zamówienia determinuje szablon
                status_to_template = {
                    _("Nowe"): "Nowe zamówienie",
                    _("W realizacji"): "Zamówienie w realizacji",
                    _("Zakończone"): "Zamówienie zakończone",
                    _("Anulowane"): "Nowe zamówienie"  # Domyślny szablon dla anulowanych
                }
                
                template_name = status_to_template.get(order['status'], "Nowe zamówienie")
                logger.info(f"Status zamówienia: '{order['status']}', wybrany szablon SMS: '{template_name}'")
                
                if "sms_order" not in templates or template_name not in templates["sms_order"]:
                    # Szablony domyślne, jeśli nie ma zapisanych
                    default_templates = {
                        "Nowe zamówienie": "Dziekujemy za zlozenie zamowienia {order_id}. Kwota: {amount} zl. O zmianach statusu bedziemy informowac. {company_name}",
                        "Zamówienie w realizacji": "Zamowienie {order_id} jest w realizacji. W razie pytan prosimy o kontakt: {company_phone}. {company_name}",
                        "Zamówienie zakończone": "Zamowienie {order_id} zostalo zrealizowane. Zapraszamy do odbioru. Dziekujemy za wspolprace! {company_name}"
                    }
                    template_content = default_templates.get(template_name, "")
                else:
                    template_content = templates["sms_order"][template_name]
                    
                # Przygotuj dane do szablonu
                company_name = settings.value("company_name", "")
                company_phone = settings.value("company_phone", "")
                
                # Formatowanie daty
                from datetime import datetime
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                # Przygotuj mapowanie zmiennych
                template_vars = {
                    "order_id": str(order_id),
                    "client_name": order['client_name'],
                    "date": order_date,
                    "status": order['status'],
                    "amount": f"{order['total_amount']:.2f}",
                    "company_name": company_name,
                    "company_phone": company_phone
                }
                
                # Podstawianie zmiennych w treści
                message = template_content
                for key, value in template_vars.items():
                    message = message.replace("{" + key + "}", str(value))
                
                # Pokaż podgląd wiadomości z możliwością edycji
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox
                
                preview_dialog = QDialog(self)
                preview_dialog.setWindowTitle(_("Podgląd SMS"))
                preview_dialog.setMinimumSize(400, 250)
                
                layout = QVBoxLayout(preview_dialog)
                
                # Dodaj etykietę z informacjami
                info_label = QLabel(_("SMS zostanie wysłany na numer: ") + order['phone_number'])
                layout.addWidget(info_label)
                
                # Dodaj pole edycji treści
                content_edit = QTextEdit(message)
                layout.addWidget(content_edit)
                
                # Dodaj licznik znaków
                char_counter = QLabel(f"0/160 znaków (1 SMS)")
                char_counter.setAlignment(Qt.AlignRight)
                layout.addWidget(char_counter)
                
                # Aktualizacja licznika znaków
                def update_char_counter():
                    text = content_edit.toPlainText()
                    count = len(text)
                    sms_count = (count + 159) // 160  # Zaokrąglenie w górę
                    
                    char_counter.setText(f"{count}/160 znaków ({sms_count} SMS)")
                    
                    # Zmień kolor, jeśli przekroczono limit jednego SMS-a
                    if count > 160:
                        char_counter.setStyleSheet("color: orange;")
                    elif count > 300:  # Ponad 2 SMS-y
                        char_counter.setStyleSheet("color: red;")
                    else:
                        char_counter.setStyleSheet("")
                
                content_edit.textChanged.connect(update_char_counter)
                update_char_counter()  # Inicjalne wywołanie
                
                # Przyciski
                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                    Qt.Horizontal, 
                    preview_dialog
                )
                buttons.accepted.connect(preview_dialog.accept)
                buttons.rejected.connect(preview_dialog.reject)
                layout.addWidget(buttons)
                
                # Wyświetl dialog podglądu
                if preview_dialog.exec() == QDialog.Accepted:
                    # Wyślij SMS
                    try:
                        from utils.sms_sender import SMSSender
                        
                        # Aktualizuj treść (jeśli została zmieniona)
                        message = content_edit.toPlainText()
                        
                        # Utwórz obiekt i wyślij SMS
                        sms_sender = SMSSender(api_key, sender)
                        success, result_message = sms_sender.send_sms(formatted_phone, message)
                        
                        # Zapisz log wysłanego SMS-a
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS order_sms_logs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                order_id INTEGER,
                                phone_number TEXT,
                                content TEXT,
                                sent_date TEXT,
                                status TEXT,
                                FOREIGN KEY (order_id) REFERENCES orders (id)
                            )
                        """)
                        
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        if success:
                            cursor.execute(
                                "INSERT INTO order_sms_logs (order_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                                (order_id, formatted_phone, message, current_date, "Wysłany")
                            )
                            self.conn.commit()
                            
                            NotificationManager.get_instance().show_notification(
                                f"📱 {_('SMS wysłany pomyślnie do')}: {order['client_name']}",
                                NotificationTypes.SUCCESS
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO order_sms_logs (order_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                                (order_id, formatted_phone, message, current_date, f"Błąd: {result_message}")
                            )
                            self.conn.commit()
                            
                            raise Exception(result_message)
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas wysyłania SMS: {e}")
                        QMessageBox.critical(
                            self,
                            _("Błąd wysyłania"),
                            _("Nie udało się wysłać wiadomości SMS:\n\n") + str(e)
                        )
                
            except Exception as e:
                logger.error(f"Błąd podczas przygotowania SMS: {e}")
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas przygotowania wiadomości SMS:\n\n") + str(e)
                )
        
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd wysyłania SMS: {e}",
                NotificationTypes.ERROR
            )

    def select_all_items(self, list_widget, checked=True):
        """Zaznacza lub odznacza wszystkie elementy na liście."""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if checked:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    def preview_mass_email(self, subject, body_html):
        """Wyświetla podgląd emaila w nowym oknie."""
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(_("Podgląd wiadomości email"))
        preview_dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(preview_dialog)
        
        # Temat
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel(_("Temat:")))
        subject_label = QLabel(subject)
        subject_label.setStyleSheet("font-weight: bold;")
        subject_layout.addWidget(subject_label)
        layout.addLayout(subject_layout)
        
        # Treść
        from PySide6.QtWebEngineWidgets import QWebEngineView
        preview = QWebEngineView()
        preview.setHtml(body_html)
        layout.addWidget(preview)
        
        # Przycisk zamknięcia
        close_btn = QPushButton(_("Zamknij"))
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)
        
        preview_dialog.exec()

    def send_email_notifications(self):
        """Wysyła powiadomienia email do klientów z zamówieniami."""
        try:
            # Sprawdź czy funkcja email jest skonfigurowana
            settings = QSettings("TireDepositManager", "Settings")
            email_address = settings.value("email_address", "")
            email_password = settings.value("email_password", "")
            smtp_server = settings.value("smtp_server", "")
            smtp_port = settings.value("smtp_port", 587, type=int)
            
            if not all([email_address, email_password, smtp_server, smtp_port]):
                QMessageBox.warning(
                    self,
                    _("Brak konfiguracji email"),
                    _("Konfiguracja email nie jest kompletna. Uzupełnij ustawienia w zakładce Ustawienia → Komunikacja.")
                )
                return
            
            # Pobierz listę zamówień z emailami klientów
            cursor = self.conn.cursor()
            
            # Buduj zapytanie w zależności od aktualnych filtrów
            query = """
            SELECT 
                o.id,
                c.name AS client_name,
                c.email,
                o.status,
                o.order_date,
                o.total_amount
            FROM 
                orders o
            JOIN 
                clients c ON o.client_id = c.id
            WHERE 
                c.email IS NOT NULL AND c.email != ''
            """
            
            params = []
            
            # Dodaj filtr statusu jeśli potrzeba
            if self.filtered_status != _("Wszystkie"):
                query += " AND o.status = ?"
                params.append(self.filtered_status)
            
            # Dodaj filtry tekstowe jeśli istnieją
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                query += " AND (c.name LIKE ? OR o.id LIKE ?)"
                params.extend([filter_text, filter_text])
            
            # Wykonaj zapytanie
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            orders = cursor.fetchall()
            
            # Jeśli nie ma zamówień z emailami klientów
            if not orders:
                QMessageBox.information(
                    self,
                    _("Brak zamówień"),
                    _("Nie znaleziono zamówień z przypisanymi adresami email.")
                )
                return
            
            # Dialog konfiguracji masowej wysyłki email
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QCheckBox, QListWidget, QListWidgetItem, QApplication
            
            config_dialog = QDialog(self)
            config_dialog.setWindowTitle(_("Wysyłanie powiadomień email"))
            config_dialog.setMinimumSize(700, 600)
            
            layout = QVBoxLayout(config_dialog)
            
            # Wybór szablonu
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel(_("Wybierz szablon email:")))
            
            template_combo = QComboBox()
            template_combo.addItems([_("Nowe zamówienie"), _("Zamówienie w realizacji"), _("Zamówienie zakończone")])
            
            # Ustaw domyślny szablon w zależności od statusu
            default_template = _("Nowe zamówienie")
            if self.filtered_status == _("W realizacji"):
                default_template = _("Zamówienie w realizacji")
            elif self.filtered_status == _("Zakończone"):
                default_template = _("Zamówienie zakończone")
                
            index = template_combo.findText(default_template)
            if index >= 0:
                template_combo.setCurrentIndex(index)
            template_layout.addWidget(template_combo, 1)
            
            layout.addLayout(template_layout)
            
            # Temat wiadomości
            subject_layout = QHBoxLayout()
            subject_layout.addWidget(QLabel(_("Temat:")))
            subject_edit = QLineEdit()
            subject_layout.addWidget(subject_edit)
            layout.addLayout(subject_layout)
            
            # Podgląd treści
            content_label = QLabel(_("Podgląd treści:"))
            layout.addWidget(content_label)
            
            from PySide6.QtWebEngineWidgets import QWebEngineView
            email_preview = QWebEngineView()
            email_preview.setMinimumHeight(200)
            layout.addWidget(email_preview)
            
            # Lista zamówień do wysłania
            orders_label = QLabel(f"{_('Znaleziono')} {len(orders)} {_('zamówień z adresami email:')}")
            layout.addWidget(orders_label)
            
            orders_list = QListWidget()
            orders_list.setSelectionMode(QListWidget.ExtendedSelection)
            layout.addWidget(orders_list)
            
            # Wypełnij listę zamówień
            for order in orders:
                order_id = order['id']
                status = order['status']
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                item = QListWidgetItem(f"{order_id} - {order['client_name']} - {order['email']} - {status} - {order_date}")
                item.setData(Qt.UserRole, order_id)
                orders_list.addItem(item)
                item.setCheckState(Qt.Checked)  # Domyślnie zaznaczone
            
                # Opcje
            options_layout = QHBoxLayout()
            
            select_all_btn = QPushButton(_("Zaznacz wszystkie"))
            select_all_btn.clicked.connect(lambda: self.select_all_items(orders_list, True))
            options_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton(_("Odznacz wszystkie"))
            deselect_all_btn.clicked.connect(lambda: self.select_all_items(orders_list, False))
            options_layout.addWidget(deselect_all_btn)
            
            options_layout.addStretch()
            
            layout.addLayout(options_layout)
            
            # Funkcja aktualizacji szablonu przy zmianie wyboru
            def update_template():
                # Mapowanie z UI na klucze szablonów
                template_map = {
                    _("Nowe zamówienie"): "order_nowe",
                    _("Zamówienie w realizacji"): "order_w_realizacji",
                    _("Zamówienie zakończone"): "order_zakończone",
                }
                
                template_name = template_combo.currentText()
                template_key = template_map.get(template_name, "order_nowe")
                
                # Pobierz szablon
                import json
                import os
                from utils.paths import CONFIG_DIR
                
                templates_file = os.path.join(CONFIG_DIR, "templates.json")
                
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                        
                    if "email" in templates and template_key in templates["email"]:
                        template = templates["email"][template_key]
                        subject = template.get("subject", "")
                        body = template.get("body", "")
                        
                        # Ustaw temat
                        subject_edit.setText(subject)
                        
                        # Pokaż podgląd z przykładowymi danymi
                        company_name = settings.value("company_name", "")
                        company_address = settings.value("company_address", "")
                        company_phone = settings.value("company_phone", "")
                        company_email = settings.value("company_email", "")
                        company_website = settings.value("company_website", "")
                        
                        # Przykładowe dane zamówienia
                        example_order_id = "123"
                        example_date = datetime.now().strftime("%d-%m-%Y")
                        example_items_table = """
                        <table style="width:100%; border-collapse: collapse;">
                            <tr style="background-color:#f8f9fa;">
                                <th style="padding:8px; border:1px solid #ddd; text-align:left;">Nazwa</th>
                                <th style="padding:8px; border:1px solid #ddd; text-align:center;">Ilość</th>
                                <th style="padding:8px; border:1px solid #ddd; text-align:right;">Cena</th>
                            </tr>
                            <tr>
                                <td style="padding:8px; border:1px solid #ddd;">Przykładowy produkt</td>
                                <td style="padding:8px; border:1px solid #ddd; text-align:center;">2</td>
                                <td style="padding:8px; border:1px solid #ddd; text-align:right;">150.00 zł</td>
                            </tr>
                        </table>
                        """
                        
                        # Zastąp zmienne w szablonie
                        example_data = {
                            "order_id": example_order_id,
                            "client_name": "Jan Kowalski",
                            "client_email": "jan.kowalski@example.com",
                            "order_date": example_date,
                            "status": template_name,
                            "total_amount": "300.00 zł",
                            "items_table": example_items_table,
                            "notes": "Przykładowa uwaga",
                            "company_name": company_name,
                            "company_address": company_address,
                            "company_phone": company_phone,
                            "company_email": company_email,
                            "company_website": company_website
                        }
                        
                        for key, value in example_data.items():
                            body = body.replace("{" + key + "}", str(value))
                        
                        # Wyświetl podgląd
                        email_preview.setHtml(body)
            
            template_combo.currentIndexChanged.connect(update_template)
            update_template()  # Załaduj początkowy szablon
            
            # Przyciski
            buttons_layout = QHBoxLayout()
            
            cancel_btn = QPushButton(_("Anuluj"))
            cancel_btn.clicked.connect(config_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            buttons_layout.addStretch()
            
            preview_btn = QPushButton(_("Podgląd"))
            preview_btn.clicked.connect(lambda: self.preview_mass_email(subject_edit.text(), email_preview.page().toHtml()))
            buttons_layout.addWidget(preview_btn)
            
            send_btn = QPushButton(_("Wyślij powiadomienia"))
            send_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            # Funkcja wysyłania emaili
            def send_mass_email():
                selected_items = []
                
                # Zbierz zaznaczone zamówienia
                for i in range(orders_list.count()):
                    item = orders_list.item(i)
                    if item.checkState() == Qt.Checked:
                        order_id = item.data(Qt.UserRole)
                        selected_items.append(order_id)
                
                if not selected_items:
                    QMessageBox.warning(
                        self,
                        _("Brak zaznaczonych zamówień"),
                        _("Zaznacz przynajmniej jedno zamówienie do wysłania powiadomienia.")
                    )
                    return
                    
                # Potwierdź wysyłkę
                reply = QMessageBox.question(
                    self,
                    _("Potwierdź wysyłkę"),
                    f"{_('Czy na pewno chcesz wysłać')} {len(selected_items)} {_('powiadomień email?')}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
                    
                # Zamknij dialog konfiguracji
                config_dialog.accept()
                
                # Pobierz dane dla emaili
                subject = subject_edit.text()
                
                # Mapowanie z UI na klucze szablonów
                template_map = {
                    _("Nowe zamówienie"): "order_nowe",
                    _("Zamówienie w realizacji"): "order_w_realizacji",
                    _("Zamówienie zakończone"): "order_zakończone",
                }
                
                template_name = template_combo.currentText()
                template_key = template_map.get(template_name, "order_nowe")
                
                # Pobierz szablon
                import json
                import os
                from utils.paths import CONFIG_DIR
                
                templates_file = os.path.join(CONFIG_DIR, "templates.json")
                
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    
                    if "email" not in templates or template_key not in templates["email"]:
                        QMessageBox.warning(
                            self,
                            _("Brak szablonu"),
                            _("Nie znaleziono odpowiedniego szablonu email. Sprawdź ustawienia szablonów.")
                        )
                        return
                        
                    template = templates["email"][template_key]
                    template_body = template.get("body", "")
                    
                    # Konfiguracja SMTP
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    # Pobierz dane firmy
                    company_name = settings.value("company_name", "")
                    company_address = settings.value("company_address", "")
                    company_phone = settings.value("company_phone", "")
                    company_email = settings.value("company_email", "")
                    company_website = settings.value("company_website", "")
                    
                    # Pokaż dialog postępu
                    progress_dialog = QDialog(self)
                    progress_dialog.setWindowTitle(_("Wysyłanie emaili"))
                    progress_dialog.setMinimumWidth(400)
                    
                    progress_layout = QVBoxLayout(progress_dialog)
                    progress_layout.addWidget(QLabel(f"{_('Wysyłanie')} {len(selected_items)} {_('powiadomień email...')}"))
                    
                    progress_label = QLabel(_("Przygotowywanie..."))
                    progress_layout.addWidget(progress_label)
                    
                    progress_btn = QPushButton(_("Anuluj"))
                    progress_btn.clicked.connect(progress_dialog.reject)
                    progress_layout.addWidget(progress_btn)
                    
                    progress_dialog.show()
                    
                    # Liczniki
                    success_count = 0
                    fail_count = 0
                    
                    # Połącz z serwerem SMTP
                    try:
                        if settings.value("use_ssl", True, type=bool):
                            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                        else:
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                        
                        # Logowanie
                        server.login(email_address, email_password)
                        
                        # Pętla wysyłania
                        for i, order_id in enumerate(selected_items):
                            try:
                                # Pobierz dane zamówienia
                                cursor.execute("""
                                    SELECT o.id, o.order_date, o.status, o.total_amount, o.notes,
                                        c.name as client_name, c.email
                                    FROM orders o
                                    JOIN clients c ON o.client_id = c.id
                                    WHERE o.id = ?
                                """, (order_id,))
                                
                                order = cursor.fetchone()
                                
                                if not order or not order['email']:
                                    continue
                                    
                                # Aktualizacja etykiety postępu
                                progress_label.setText(f"{_('Wysyłanie')} ({i+1}/{len(selected_items)}): {order['client_name']}")
                                QApplication.processEvents()  # Odśwież UI
                                
                                if progress_dialog.result() == QDialog.Rejected:
                                    break  # Anulowano
                                
                                # Pobierz pozycje zamówienia
                                cursor.execute("""
                                    SELECT name, quantity, price
                                    FROM order_items
                                    WHERE order_id = ?
                                """, (order_id,))
                                
                                items = cursor.fetchall()
                                
                                # Przygotuj tabelę z pozycjami zamówienia
                                items_table = """
                                <table style="width:100%; border-collapse: collapse;">
                                    <tr style="background-color:#f8f9fa;">
                                        <th style="padding:8px; border:1px solid #ddd; text-align:left;">Nazwa</th>
                                        <th style="padding:8px; border:1px solid #ddd; text-align:center;">Ilość</th>
                                        <th style="padding:8px; border:1px solid #ddd; text-align:right;">Cena</th>
                                    </tr>
                                """
                                
                                for item in items:
                                    items_table += f"""
                                    <tr>
                                        <td style="padding:8px; border:1px solid #ddd;">{item['name']}</td>
                                        <td style="padding:8px; border:1px solid #ddd; text-align:center;">{item['quantity']}</td>
                                        <td style="padding:8px; border:1px solid #ddd; text-align:right;">{item['price']:.2f} zł</td>
                                    </tr>
                                    """
                                
                                items_table += "</table>"
                                
                                # Formatowanie daty
                                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                                
                                # Dane do szablonu
                                template_data = {
                                    "order_id": order_id,
                                    "client_name": order['client_name'],
                                    "client_email": order['email'],
                                    "order_date": order_date,
                                    "status": order['status'],
                                    "total_amount": f"{order['total_amount']:.2f} zł",
                                    "items_table": items_table,
                                    "notes": order['notes'] or "",
                                    "company_name": company_name,
                                    "company_address": company_address,
                                    "company_phone": company_phone,
                                    "company_email": company_email,
                                    "company_website": company_website
                                }
                                
                                # Wypełnij szablon danymi
                                body = template_body
                                this_subject = subject
                                
                                for key, value in template_data.items():
                                    body = body.replace("{" + key + "}", str(value))
                                    this_subject = this_subject.replace("{" + key + "}", str(value))
                                
                                # Przygotuj wiadomość
                                msg = MIMEMultipart()
                                msg['From'] = email_address
                                msg['To'] = order['email']
                                msg['Subject'] = this_subject
                                
                                msg.attach(MIMEText(body, 'html'))
                                
                                # Wysyłka wiadomości
                                server.send_message(msg)
                                
                                # Zapisz log wysłanego emaila
                                cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS order_email_logs (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        order_id INTEGER,
                                        email TEXT,
                                        subject TEXT,
                                        sent_date TEXT,
                                        status TEXT,
                                        FOREIGN KEY (order_id) REFERENCES orders (id)
                                    )
                                """)
                                
                                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute(
                                    "INSERT INTO order_email_logs (order_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                                    (order_id, order['email'], this_subject, current_date, "Wysłany")
                                )
                                self.conn.commit()
                                
                                success_count += 1
                                
                            except Exception as e:
                                logger.error(f"Błąd podczas wysyłania emaila do {order.get('client_name', '')}: {e}")
                                fail_count += 1
                                
                                # Zapisz log błędu
                                try:
                                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    cursor.execute(
                                        "INSERT INTO order_email_logs (order_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                                        (order_id, order.get('email', ''), subject, current_date, f"Błąd: {e}")
                                    )
                                    self.conn.commit()
                                except:
                                    pass
                        
                        # Zamknij połączenie SMTP
                        server.quit()
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas konfiguracji SMTP: {e}")
                        QMessageBox.critical(
                            self,
                            _("Błąd połączenia"),
                            _("Nie udało się nawiązać połączenia z serwerem SMTP:\n\n") + str(e)
                        )
                        progress_dialog.accept()
                        return
                    
                    # Zamknij dialog postępu
                    progress_dialog.accept()
                    
                    # Pokaż podsumowanie
                    QMessageBox.information(
                        self,
                        _("Podsumowanie wysyłki email"),
                        f"{_('Wysłano')}: {success_count} {_('powiadomień')}\n"
                        f"{_('Nieudane')}: {fail_count} {_('powiadomień')}\n\n"
                        f"{_('Szczegóły można znaleźć w logach systemu.')}"
                    )
                    
                    # Odśwież widok
                    self.load_orders()
                    
            send_btn.clicked.connect(send_mass_email)
            buttons_layout.addWidget(send_btn)
            
            layout.addLayout(buttons_layout)
            
            # Wyświetl dialog
            config_dialog.exec()
        
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomień email: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania powiadomień email: {e}",
                NotificationTypes.ERROR
            )

    def send_sms_notifications(self):
        """Wysyła powiadomienia SMS do klientów z zamówieniami."""
        try:
            # Sprawdź czy funkcja SMS jest skonfigurowana
            settings = QSettings("TireDepositManager", "Settings")
            api_key = settings.value("sms_api_key", "")
            sender = settings.value("sms_sender", "")
            enable_sms = settings.value("enable_sms", False, type=bool)
            
            if not all([api_key, sender]) or not enable_sms:
                QMessageBox.warning(
                    self,
                    _("Brak konfiguracji SMS"),
                    _("Konfiguracja SMS nie jest kompletna lub wysyłanie SMS jest wyłączone. Sprawdź ustawienia w zakładce Ustawienia → Komunikacja.")
                )
                return
            
            # Pobierz listę zamówień z numerami telefonów klientów
            cursor = self.conn.cursor()
            
            # Buduj zapytanie w zależności od aktualnych filtrów
            query = """
            SELECT 
                o.id,
                c.name AS client_name,
                c.phone_number,
                o.status,
                o.order_date,
                o.total_amount
            FROM 
                orders o
            JOIN 
                clients c ON o.client_id = c.id
            WHERE 
                c.phone_number IS NOT NULL AND c.phone_number != ''
            """
            
            params = []
            
            # Dodaj filtr statusu jeśli potrzeba
            if self.filtered_status != _("Wszystkie"):
                query += " AND o.status = ?"
                params.append(self.filtered_status)
            
            # Dodaj filtry tekstowe jeśli istnieją
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                query += " AND (c.name LIKE ? OR o.id LIKE ?)"
                params.extend([filter_text, filter_text])
            
            # Wykonaj zapytanie
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            orders = cursor.fetchall()
            
            # Jeśli nie ma zamówień z numerami telefonów
            if not orders:
                QMessageBox.information(
                    self,
                    _("Brak zamówień"),
                    _("Nie znaleziono zamówień z przypisanymi numerami telefonów.")
                )
                return
            
            # Dialog konfiguracji masowej wysyłki SMS
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QCheckBox, QListWidget, QListWidgetItem, QApplication
            
            config_dialog = QDialog(self)
            config_dialog.setWindowTitle(_("Wysyłanie powiadomień SMS"))
            config_dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(config_dialog)
            
            # Wybór szablonu
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel(_("Wybierz szablon SMS:")))
            
            template_combo = QComboBox()
            template_combo.addItems([_("Nowe zamówienie"), _("Zamówienie w realizacji"), _("Zamówienie zakończone")])
            
            # Ustaw domyślny szablon w zależności od statusu
            default_template = _("Nowe zamówienie")
            if self.filtered_status == _("W realizacji"):
                default_template = _("Zamówienie w realizacji")
            elif self.filtered_status == _("Zakończone"):
                default_template = _("Zamówienie zakończone")
                
            index = template_combo.findText(default_template)
            if index >= 0:
                template_combo.setCurrentIndex(index)
            template_layout.addWidget(template_combo, 1)
            
            layout.addLayout(template_layout)
            
            # Treść wiadomości
            content_label = QLabel(_("Treść wiadomości:"))
            layout.addWidget(content_label)
            
            message_edit = QTextEdit()
            message_edit.setMinimumHeight(100)
            layout.addWidget(message_edit)
            
            # Licznik znaków
            char_counter = QLabel("0/160 znaków (1 SMS)")
            char_counter.setAlignment(Qt.AlignRight)
            layout.addWidget(char_counter)
            
            # Aktualizacja licznika znaków
            def update_counter():
                text = message_edit.toPlainText()
                count = len(text)
                sms_count = (count + 159) // 160  # Zaokrąglenie w górę
                
                if count > 160:
                    char_counter.setStyleSheet("color: orange;")
                elif count > 300:
                    char_counter.setStyleSheet("color: red;")
                else:
                    char_counter.setStyleSheet("")
                    
                char_counter.setText(f"{count}/160 znaków ({sms_count} SMS)")
            
            message_edit.textChanged.connect(update_counter)
            
            # Aktualizacja szablonu przy zmianie wyboru
            def update_template():
                template_name = ""
                if template_combo.currentText() == _("Nowe zamówienie"):
                    template_name = "Nowe zamówienie"
                elif template_combo.currentText() == _("Zamówienie w realizacji"):
                    template_name = "Zamówienie w realizacji"
                elif template_combo.currentText() == _("Zamówienie zakończone"):
                    template_name = "Zamówienie zakończone"
                
                # Pobierz szablon SMS
                import json
                import os
                from utils.paths import CONFIG_DIR
                
                templates_file = os.path.join(CONFIG_DIR, "templates.json")
                
                # Domyślne szablony, jeśli nie ma zapisanych
                default_templates = {
                    "Nowe zamówienie": "Dziekujemy za zlozenie zamowienia {order_id}. Kwota: {amount} zl. O zmianach statusu bedziemy informowac. {company_name}",
                    "Zamówienie w realizacji": "Zamowienie {order_id} jest w realizacji. W razie pytan prosimy o kontakt: {company_phone}. {company_name}",
                    "Zamówienie zakończone": "Zamowienie {order_id} zostalo zrealizowane. Zapraszamy do odbioru. Dziekujemy za wspolprace! {company_name}"
                }
                
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    
                    # Sprawdź czy szablon istnieje
                    if "sms_order" in templates and template_name in templates["sms_order"]:
                        template_content = templates["sms_order"][template_name]
                    else:
                        template_content = default_templates.get(template_name, "")
                else:
                    template_content = default_templates.get(template_name, "")
                
                # Ustaw treść
                message_edit.setPlainText(template_content)
                update_counter()
                
            template_combo.currentIndexChanged.connect(update_template)
            update_template()  # Załaduj początkowy szablon
            
            # Lista zamówień do wysłania
            orders_label = QLabel(f"{_('Znaleziono')} {len(orders)} {_('zamówień z numerami telefonów:')}")
            layout.addWidget(orders_label)
            
            orders_list = QListWidget()
            orders_list.setSelectionMode(QListWidget.ExtendedSelection)
            layout.addWidget(orders_list)
            
            # Wypełnij listę zamówień
            for order in orders:
                order_id = order['id']
                status = order['status']
                order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                item = QListWidgetItem(f"{order_id} - {order['client_name']} - {order['phone_number']} - {status} - {order_date}")
                item.setData(Qt.UserRole, order_id)
                orders_list.addItem(item)
                item.setCheckState(Qt.Checked)  # Domyślnie zaznaczone
            
            # Opcje
            options_layout = QHBoxLayout()
            
            select_all_btn = QPushButton(_("Zaznacz wszystkie"))
            select_all_btn.clicked.connect(lambda: self.select_all_items(orders_list, True))
            options_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton(_("Odznacz wszystkie"))
            deselect_all_btn.clicked.connect(lambda: self.select_all_items(orders_list, False))
            options_layout.addWidget(deselect_all_btn)
            
            options_layout.addStretch()
            
            layout.addLayout(options_layout)
            
            # Przyciski
            buttons_layout = QHBoxLayout()
            
            cancel_btn = QPushButton(_("Anuluj"))
            cancel_btn.clicked.connect(config_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            buttons_layout.addStretch()
            
            preview_btn = QPushButton(_("Podgląd"))
            preview_btn.clicked.connect(lambda: self.preview_mass_sms(message_edit.toPlainText(), orders[0] if orders else None))
            buttons_layout.addWidget(preview_btn)
            
            send_btn = QPushButton(_("Wyślij powiadomienia"))
            send_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            # Funkcja wysyłania SMS-ów
            def send_mass_sms():
                selected_items = []
                
                # Zbierz zaznaczone zamówienia
                for i in range(orders_list.count()):
                    item = orders_list.item(i)
                    if item.checkState() == Qt.Checked:
                        order_id = item.data(Qt.UserRole)
                        for order in orders:
                            if order['id'] == order_id:
                                selected_items.append(order)
                                break
                
                if not selected_items:
                    QMessageBox.warning(
                        self,
                        _("Brak zaznaczonych zamówień"),
                        _("Zaznacz przynajmniej jedno zamówienie do wysłania powiadomienia.")
                    )
                    return
                    
                # Potwierdź wysyłkę
                reply = QMessageBox.question(
                    self,
                    _("Potwierdź wysyłkę"),
                    f"{_('Czy na pewno chcesz wysłać')} {len(selected_items)} {_('powiadomień SMS?')}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
                    
                # Zamknij dialog konfiguracji
                config_dialog.accept()
                
                # Inicjalizuj SMSSender
                from utils.sms_sender import SMSSender, format_phone_number
                sms_sender_obj = SMSSender(api_key, sender)
                
                # Pobierz dane firmy
                company_name = settings.value("company_name", "")
                company_address = settings.value("company_address", "")
                company_phone = settings.value("company_phone", "")
                
                # Liczniki
                success_count = 0
                fail_count = 0
                
                # Pokaż dialog postępu
                progress_dialog = QDialog(self)
                progress_dialog.setWindowTitle(_("Wysyłanie SMS-ów"))
                progress_dialog.setMinimumWidth(400)
                
                progress_layout = QVBoxLayout(progress_dialog)
                progress_layout.addWidget(QLabel(f"{_('Wysyłanie')} {len(selected_items)} {_('powiadomień SMS...')}"))
                
                progress_label = QLabel(_("Przygotowywanie..."))
                progress_layout.addWidget(progress_label)
                
                progress_btn = QPushButton(_("Anuluj"))
                progress_btn.clicked.connect(progress_dialog.reject)
                progress_layout.addWidget(progress_btn)
                
                progress_dialog.show()
                
                # Pętla wysyłania
                for i, order in enumerate(selected_items):
                    try:
                        # Aktualizacja etykiety postępu
                        progress_label.setText(f"{_('Wysyłanie')} ({i+1}/{len(selected_items)}): {order['client_name']}")
                        QApplication.processEvents()  # Odśwież UI
                        
                        if progress_dialog.result() == QDialog.Rejected:
                            break  # Anulowano
                        
                        # Formatowanie daty
                        order_date = datetime.strptime(order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                        
                        # Dane do szablonu
                        template_data = {
                            "order_id": str(order['id']),
                            "client_name": order['client_name'],
                            "date": order_date,
                            "status": order['status'],
                            "amount": f"{order['total_amount']:.2f}",
                            "company_name": company_name,
                            "company_phone": company_phone
                        }
                        
                        # Wypełnij szablon danymi
                        message_content = message_edit.toPlainText()
                        for key, value in template_data.items():
                            message_content = message_content.replace("{" + key + "}", str(value))
                        
                        # Wyślij SMS
                        formatted_phone = format_phone_number(order['phone_number'])
                        success, result_message = sms_sender_obj.send_sms(formatted_phone, message_content)
                        
                        # Zapisz log
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS order_sms_logs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                order_id INTEGER,
                                phone_number TEXT,
                                content TEXT,
                                sent_date TEXT,
                                status TEXT,
                                FOREIGN KEY (order_id) REFERENCES orders (id)
                            )
                        """)
                        
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        if success:
                            success_count += 1
                            status = "Wysłany"
                        else:
                            fail_count += 1
                            status = f"Błąd: {result_message}"
                        
                        cursor.execute(
                            "INSERT INTO order_sms_logs (order_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                            (order['id'], formatted_phone, message_content, current_date, status)
                        )
                        self.conn.commit()
                        
                    except Exception as e:
                        logger.error(f"Błąd podczas wysyłania SMS: {e}")
                        fail_count += 1
                
                # Zamknij dialog postępu
                progress_dialog.accept()
                
                # Pokaż podsumowanie
                QMessageBox.information(
                    self,
                    _("Podsumowanie wysyłki SMS"),
                    f"{_('Wysłano')}: {success_count} {_('powiadomień')}\n"
                    f"{_('Nieudane')}: {fail_count} {_('powiadomień')}\n\n"
                    f"{_('Szczegóły można znaleźć w logach systemu.')}"
                )
                
                # Odśwież widok
                self.load_orders()
            
            send_btn.clicked.connect(send_mass_sms)
            buttons_layout.addWidget(send_btn)
            
            layout.addLayout(buttons_layout)
            
            # Wyświetl dialog
            config_dialog.exec()
        
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomień SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania powiadomień SMS: {e}",
                NotificationTypes.ERROR
            )

    def preview_mass_sms(self, template, example_order=None):
        """Wyświetla podgląd SMS-a z podstawieniem danych przykładowego zamówienia."""
        try:
            if not example_order:
                QMessageBox.warning(
                    self,
                    _("Brak danych"),
                    _("Nie można wygenerować podglądu. Brak danych zamówienia.")
                )
                return
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "")
            company_phone = settings.value("company_phone", "")
            
            # Formatowanie daty
            order_date = datetime.strptime(example_order['order_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            
            # Dane do szablonu
            template_data = {
                "order_id": str(example_order['id']),
                "client_name": example_order['client_name'],
                "date": order_date,
                "status": example_order['status'],
                "amount": f"{example_order['total_amount']:.2f}",
                "company_name": company_name,
                "company_phone": company_phone
            }
            
            # Wypełnij szablon danymi
            message_content = template
            for key, value in template_data.items():
                message_content = message_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            QMessageBox.information(
                self,
                _("Podgląd SMS-a (przykład)"),
                f"{_('Dla zamówienia')}: {example_order['id']} - {example_order['client_name']}\n\n"
                f"{_('Treść')}: {message_content}\n\n"
                f"{_('Długość')}: {len(message_content)} {_('znaków')}\n"
                f"{_('SMS-ów')}: {(len(message_content) + 159) // 160}"
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania podglądu SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania podglądu SMS: {e}",
                NotificationTypes.ERROR
            )
                    
            send_btn.clicked.connect(send_mass_email)
            buttons_layout.addWidget(send_btn)
            
            layout.addLayout(buttons_layout)
            
            # Wyświetl dialog
            config_dialog.exec()