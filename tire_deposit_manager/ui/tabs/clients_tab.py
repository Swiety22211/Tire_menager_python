#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka zarządzania klientami w aplikacji.
Wyświetla listę klientów, umożliwia dodawanie, edycję i usuwanie.
Dodatkowo umożliwia przypisywanie pojazdów do klientom.
"""

import os
import logging
import csv
import smtplib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QMenu,
    QComboBox, QFrame, QTabWidget, QSplitter, QToolButton, QScrollArea,
    QSpacerItem, QSizePolicy, QStyledItemDelegate, QFileDialog
)
from PySide6.QtCore import Qt, QEvent, Signal, QRect
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter, QPen, QBrush
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from utils.settings import Settings
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.client_details_dialog import ClientDetailsDialog
from ui.dialogs.vehicle_dialog import VehicleDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR
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
    "EMAIL_BUTTON": """
        QPushButton#emailButton {
            background-color: #4dabf7;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton#emailButton:hover {
            background-color: #339af0;
        }
    """
}


class StatusDelegate(QStyledItemDelegate):
    """
    Delegat do stylizowania komórek statusu w tabeli klientów.
    """
    def paint(self, painter, option, index):
        status = index.data()
        
        if status == _("Stały"):
            background_color = QColor("#51cf66")
            text_color = QColor(255, 255, 255)
        elif status == _("Nowy"):
            background_color = QColor("#ffa94d")
            text_color = QColor(255, 255, 255)
        elif status == _("Firma"):
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

        delete_rect = QRect(
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
        painter.drawText(delete_rect, Qt.AlignCenter, "🗑️")

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

            delete_rect = QRect(
                int(x3), 
                int(y_center - button_height/2),
                int(button_width), 
                int(button_height)
            )

            if view_rect.contains(event.pos()):
                self.parent().view_client_requested.emit(index.row())
                return True
            elif edit_rect.contains(event.pos()):
                self.parent().edit_client_requested.emit(index.row())
                return True
            elif delete_rect.contains(event.pos()):
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Opcje wyglądu
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            _("ID"), _("Nazwisko i imię"), _("Telefon"), _("Email"), 
            _("Nr rejestracyjny"), _("Pojazdy"), _("Typ"), _("Akcje")
        ])
        
        # Ustawienie rozciągania kolumn - zoptymalizowane dla responsywności
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Domyślnie interaktywne
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nazwisko i imię
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Telefon
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Email
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Nr rejestracyjny
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Pojazdy
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Typ
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)  # Akcje
        self.setColumnWidth(7, 190)  # Stała szerokość kolumny akcji
        
        # Delegaty
        self.setItemDelegateForColumn(6, StatusDelegate(self))  # Kolumna "Typ"
        self.setItemDelegateForColumn(7, ActionButtonDelegate(self))  # Kolumna "Akcje"
        
        # Wysokość wiersza
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Ustawienie reguł stylów dla trybu ciemnego
        self.setStyleSheet(STYLES["TABLE_WIDGET"])


class ClientsTab(QWidget):
    """
    Zakładka zarządzania klientami w aplikacji.
    Wyświetla listę klientów, umożliwia dodawanie, edycję i usuwanie.
    Dodatkowo umożliwia przypisywanie pojazdów do klientów.
    """
    
    # Sygnały związane z obsługą klientów
    client_added = Signal(int)  # Emitowany po dodaniu klienta (parametr: client_id)
    client_updated = Signal(int)  # Emitowany po aktualizacji klienta (parametr: client_id)
    client_deleted = Signal(int)  # Emitowany po usunięciu klienta (parametr: client_id)
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki klientów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.filtered_type = _("Wszyscy")
        self.records_per_page = 20  # Liczba rekordów na stronę dla paginacji
        self.current_page = 0  # Aktualna strona
        self.filter_text = ""  # Tekst wyszukiwania
        self.total_pages = 0  # Całkowita liczba stron
        
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
        header_layout.setSpacing(10)
        
        # Tytuł zakładki klientów
        title_label = QLabel(_("Zarządzanie Klientami"))
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        # Elastyczny odstęp
        header_layout.addStretch(1)

        # Przycisk wysyłania emaili
        self.email_button = QPushButton("📧 " + _("Wyślij Email"))
        self.email_button.setObjectName("emailButton")
        self.email_button.setFixedHeight(40)
        self.email_button.setMinimumWidth(130)
        self.email_button.setStyleSheet(STYLES["EMAIL_BUTTON"])
        self.email_button.clicked.connect(self.send_email_to_clients)
        header_layout.addWidget(self.email_button)
        
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
        search_box.setFixedHeight(40)
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
        self.search_input.setPlaceholderText(_("Szukaj według nazwiska, telefonu lub nr rejestracyjnego..."))
        self.search_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        self.search_input.textChanged.connect(self.filter_clients)
        search_box_layout.addWidget(self.search_input)
        
        search_layout.addWidget(search_box, 1)  # Rozciągnij pole wyszukiwania
        
        # Combobox sortowania
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(5)
        
        sort_label = QLabel(_("Sortuj:"))
        sort_label.setMinimumWidth(50)
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("filterCombo")
        self.sort_combo.setFixedHeight(40)
        self.sort_combo.setMinimumWidth(150)
        self.sort_combo.addItems([_("Nazwisko"), _("Data dodania"), _("Liczba pojazdów")])
        self.sort_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.sort_combo.currentTextChanged.connect(self.apply_sorting)
        sort_layout.addWidget(self.sort_combo)
        
        search_layout.addLayout(sort_layout)
        
        # Przycisk filtrowania z emotikoną
        self.filter_button = QPushButton("🔍 " + _("Filtruj"))
        self.filter_button.setObjectName("filterButton")
        self.filter_button.setFixedHeight(40)
        self.filter_button.setMinimumWidth(100)
        self.filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.filter_button.clicked.connect(self.apply_filters)
        search_layout.addWidget(self.filter_button)
        
        main_layout.addWidget(search_panel)
        
        # Zakładki statusów klientów
        self.tabs_widget = QTabWidget()
        self.tabs_widget.setObjectName("clientTypeTabs")
        self.tabs_widget.setTabPosition(QTabWidget.North)
        self.tabs_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs_widget.setStyleSheet(STYLES["TABS"])
        
        # Tworzenie zakładek
        self.all_tab = QWidget()
        self.individual_tab = QWidget()
        self.company_tab = QWidget()
        self.regular_tab = QWidget()
        self.new_tab = QWidget()
        
        # Dodanie zakładek do widgetu
        self.tabs_widget.addTab(self.all_tab, _("Wszyscy (0)"))
        self.tabs_widget.addTab(self.individual_tab, _("Indywidualni (0)"))
        self.tabs_widget.addTab(self.company_tab, _("Firmowi (0)"))
        self.tabs_widget.addTab(self.regular_tab, _("Stali (0)"))
        self.tabs_widget.addTab(self.new_tab, _("Nowi (0)"))
        
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
        pagination_layout.setSpacing(10)
        
        # Informacja o liczbie wyświetlanych rekordów
        self.records_info = QLabel(_("Wyświetlanie 0 z 0 rekordów"))
        self.records_info.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        pagination_layout.addWidget(self.records_info)
        
        pagination_layout.addStretch(1)
        
        # Przyciski nawigacji z emotikonami
        self.prev_button = QPushButton("⬅️")
        self.prev_button.setFixedSize(40, 40)
        self.prev_button.setStyleSheet(STYLES["NAV_BUTTON"])
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_1_button = QPushButton("1")
        self.page_1_button.setFixedSize(40, 40)
        self.page_1_button.setObjectName("currentPageButton")
        self.page_1_button.setStyleSheet(STYLES["CURRENT_PAGE_BUTTON"])
        self.page_1_button.clicked.connect(lambda: self.go_to_page(int(self.page_1_button.text()) - 1))
        pagination_layout.addWidget(self.page_1_button)
        
        self.page_2_button = QPushButton("2")
        self.page_2_button.setFixedSize(40, 40)
        self.page_2_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_2_button.clicked.connect(lambda: self.go_to_page(int(self.page_2_button.text()) - 1))
        pagination_layout.addWidget(self.page_2_button)
        
        self.page_3_button = QPushButton("3")
        self.page_3_button.setFixedSize(40, 40)
        self.page_3_button.setStyleSheet(STYLES["PAGE_BUTTON"])
        self.page_3_button.clicked.connect(lambda: self.go_to_page(int(self.page_3_button.text()) - 1))
        pagination_layout.addWidget(self.page_3_button)
        
        self.next_button = QPushButton("➡️")
        self.next_button.setFixedSize(40, 40)
        self.next_button.setStyleSheet(STYLES["NAV_BUTTON"])
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        pagination_layout.addStretch(1)
        
        # Przycisk "Dodaj klienta" (przeniesiony na dół)
        self.add_button = QPushButton("➕ " + _("Dodaj Klienta"))
        self.add_button.setObjectName("addButton")
        self.add_button.setFixedHeight(40)
        self.add_button.setMinimumWidth(150)
        self.add_button.setStyleSheet(STYLES["ADD_BUTTON"])
        self.add_button.clicked.connect(self.add_client)
        pagination_layout.addWidget(self.add_button)
        
        # Przyciski importu/eksportu z emotikonami
        self.import_button = QPushButton("📥 " + _("Import klientów"))
        self.import_button.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.import_button.clicked.connect(self.import_clients)
        pagination_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("📤 " + _("Eksport listy"))
        self.export_button.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.export_button.clicked.connect(self.export_clients)
        pagination_layout.addWidget(self.export_button)
        
        main_layout.addLayout(pagination_layout)

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
        
        # Pobierz kolor tła z CSS style
        # Klucz koloru tła znajduje się po "background-color: " i przed ";"
        background_color = ""
        for line in style.split("\n"):
            if "background-color:" in line:
                background_color = line.split("background-color:")[1].split(";")[0].strip()
                break
        
        # Tytuł z ikoną - teraz z tym samym kolorem tła
        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)
        
        icon_label = QLabel(icon)
        if background_color:
            icon_label.setStyleSheet(f"font-size: 16px; background-color: {background_color};")
        else:
            icon_label.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        if background_color:
            title_label.setStyleSheet(f"{STYLES['STAT_TITLE']} background-color: {background_color};")
        else:
            title_label.setStyleSheet(STYLES["STAT_TITLE"])
        title_layout.addWidget(title_label)
        
        title_layout.addStretch(1)
        
        layout.addLayout(title_layout)
        
        # Wartość - również z tym samym kolorem tła
        value_label = QLabel(value)
        if background_color:
            value_label.setStyleSheet(f"{STYLES['STAT_LABEL']} background-color: {background_color};")
        else:
            value_label.setStyleSheet(STYLES["STAT_LABEL"])
        layout.addWidget(value_label)
        
        # Zapisanie referencji do etykiety wartości
        card.value_label = value_label
        
        return card

    def update_statistics(self):
        """
        Aktualizuje statystyki klientów na podstawie danych z bazy.
        """
        try:
            cursor = self.conn.cursor()
            
            # Optymalizacja: pobierz wszystkie statystyki jednym zapytaniem
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN client_type = 'Indywidualny' THEN 1 ELSE 0 END) as individual,
                    SUM(CASE WHEN client_type = 'Firma' THEN 1 ELSE 0 END) as company
                FROM clients
            """)
            
            result = cursor.fetchone()
            if result:
                self.statistics['total'] = result[0] or 0
                self.statistics['individual'] = result[1] or 0
                self.statistics['company'] = result[2] or 0
                
                # Aktualizacja wartości na widżetach
                self.all_clients_card.value_label.setText(str(self.statistics['total']))
                self.individual_clients_card.value_label.setText(str(self.statistics['individual']))
                self.company_clients_card.value_label.setText(str(self.statistics['company']))
            
            # Pobierz liczbę aktywnych depozytów (zakładam, że masz tabelę 'deposits' z polem 'active')
            # Jeśli struktura bazy jest inna, dostosuj to zapytanie
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM deposits WHERE active = 1
                """)
                active_deposits = cursor.fetchone()[0] or 0
                self.statistics['active_deposits'] = active_deposits
                self.active_deposits_card.value_label.setText(str(active_deposits))
            except Exception as e:
                # Jeśli tabela depozytów nie istnieje lub ma inną strukturę
                logger.warning(f"Nie można pobrać statystyk depozytów: {e}")
                self.statistics['active_deposits'] = 0
                self.active_deposits_card.value_label.setText("0")
            
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji statystyk: {e}")
    
    def send_email_to_clients(self):
        """
        Otwiera dialog do wysyłania emaili do wybranych klientów.
        """
        # Sprawdź, czy są zaznaczeni klienci
        current_tab = self.tabs_widget.currentWidget()
        table = current_tab.clients_table
        selected_items = table.selectedItems()
        selected_rows = set()
        
        for item in selected_items:
            selected_rows.add(item.row())
        
        # Przygotuj listę klientów
        selected_clients = []
        for row in selected_rows:
            client_id = int(table.item(row, 0).text())
            client_name = table.item(row, 1).text()
            client_email = table.item(row, 3).text()
            
            # Sprawdź, czy email jest dostępny
            if client_email and "@" in client_email:
                selected_clients.append({
                    'id': client_id,
                    'name': client_name,
                    'email': client_email
                })
        
        if not selected_clients:
            # Jeśli nie ma zaznaczonych klientów lub nie mają emaili, pokaż opcję wyboru wszystkich
            reply = QMessageBox.question(
                self,
                _("Brak zaznaczonych klientów"),
                _("Nie zaznaczono klientów z adresami email. Czy chcesz wysłać email do wszystkich klientów, którzy posiadają adresy email?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Pobierz wszystkich klientów z emailami
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT id, name, email FROM clients 
                        WHERE email IS NOT NULL AND email <> '' 
                        ORDER BY name
                    """)
                    
                    clients = cursor.fetchall()
                    for client in clients:
                        client_id, client_name, client_email = client
                        if "@" in client_email:
                            selected_clients.append({
                                'id': client_id,
                                'name': client_name,
                                'email': client_email
                            })
                except Exception as e:
                    logger.error(f"Błąd podczas pobierania listy klientów: {e}")
                    QMessageBox.critical(
                        self,
                        _("Błąd"),
                        f"{_('Wystąpił błąd podczas pobierania listy klientów')}:\n{str(e)}"
                    )
                    return
            else:
                return
        
        if not selected_clients:
            QMessageBox.warning(
                self,
                _("Brak adresów email"),
                _("Nie znaleziono klientów z poprawnymi adresami email.")
            )
            return
        
        # Wyświetl dialog do wysyłania emaili
        self.show_email_dialog(selected_clients)
    
    def show_email_dialog(self, clients):
        """
        Wyświetla dialog do wysyłania emaili.
        
        Args:
            clients (list): Lista słowników z danymi klientów (id, name, email)
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(_("Wyślij Email do Klientów"))
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
        # Układ główny
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Etykieta z informacją o liczbie odbiorców
        recipients_label = QLabel(_("Wybrani odbiorcy: {}").format(len(clients)))
        recipients_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(recipients_label)
        
        # Lista odbiorców (rozwijana)
        recipients_frame = QFrame()
        recipients_frame.setFrameShape(QFrame.StyledPanel)
        recipients_frame.setMaximumHeight(150)
        recipients_scroll = QScrollArea()
        recipients_scroll.setWidget(recipients_frame)
        recipients_scroll.setWidgetResizable(True)
        
        recipients_layout = QVBoxLayout(recipients_frame)
        for client in clients:
            client_label = QLabel(f"{client['name']} <{client['email']}>")
            recipients_layout.addWidget(client_label)
        
        layout.addWidget(recipients_scroll)
        
        # Pole tematu
        subject_layout = QHBoxLayout()
        subject_label = QLabel(_("Temat:"))
        subject_label.setFixedWidth(80)
        subject_layout.addWidget(subject_label)
        
        subject_input = QLineEdit()
        subject_layout.addWidget(subject_input)
        layout.addLayout(subject_layout)
        
        # Pole treści
        content_label = QLabel(_("Treść wiadomości:"))
        layout.addWidget(content_label)
        
        email_content = QTextEdit()
        email_content.setMinimumHeight(200)
        layout.addWidget(email_content)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        cancel_button = QPushButton(_("Anuluj"))
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        send_button = QPushButton(_("Wyślij"))
        send_button.setStyleSheet("""
            background-color: #40c057;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 20px;
        """)
        send_button.clicked.connect(lambda: self.send_emails(
            clients,
            subject_input.text(),
            email_content.toPlainText(),
            dialog
        ))
        buttons_layout.addWidget(send_button)
        
        layout.addLayout(buttons_layout)
        
        # Wyświetl dialog
        dialog.exec()
    
    def send_emails(self, clients, subject, content, dialog):
        """
        Wysyła emaile do wybranych klientów.
        
        Args:
            clients (list): Lista słowników z danymi klientów
            subject (str): Temat wiadomości
            content (str): Treść wiadomości
            dialog (QDialog): Dialog, który należy zamknąć po wysłaniu
        """
        # Walidacja pól
        if not subject.strip():
            QMessageBox.warning(
                dialog,
                _("Brak tematu"),
                _("Proszę podać temat wiadomości.")
            )
            return
        
        if not content.strip():
            QMessageBox.warning(
                dialog,
                _("Brak treści"),
                _("Proszę podać treść wiadomości.")
            )
            return
        
        # Pobranie ustawień SMTP
        try:
            settings = Settings.get_instance()
            smtp_server = settings.get_setting("smtp_server", "")
            smtp_port = int(settings.get_setting("smtp_port", "587"))
            smtp_user = settings.get_setting("smtp_user", "")
            smtp_password = settings.get_setting("smtp_password", "")
            sender_email = settings.get_setting("sender_email", "")
            
            if not all([smtp_server, smtp_port, smtp_user, smtp_password, sender_email]):
                QMessageBox.warning(
                    dialog,
                    _("Brak konfiguracji SMTP"),
                    _("Proszę skonfigurować ustawienia SMTP w opcjach aplikacji.")
                )
                return
        except Exception as e:
            logger.error(f"Błąd podczas pobierania ustawień SMTP: {e}")
            QMessageBox.critical(
                dialog,
                _("Błąd"),
                f"{_('Wystąpił błąd podczas pobierania ustawień SMTP')}:\n{str(e)}"
            )
            return
        
        # Przygotowanie do wysyłania
        progress_dialog = QProgressDialog(_("Wysyłanie emaili..."), _("Anuluj"), 0, len(clients), dialog)
        progress_dialog.setWindowTitle(_("Postęp wysyłania"))
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        try:
            # Nawiązanie połączenia z serwerem SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            
            # Wysyłanie emaili
            for i, client in enumerate(clients):
                if progress_dialog.wasCanceled():
                    break
                
                try:
                    # Przygotowanie wiadomości
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = client['email']
                    msg['Subject'] = subject
                    
                    # Dodanie treści wiadomości
                    msg.attach(MIMEText(content, 'plain'))
                    
                    # Wysłanie wiadomości
                    server.sendmail(sender_email, client['email'], msg.as_string())
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"{client['name']} ({client['email']}): {str(e)}"
                    error_messages.append(error_msg)
                    logger.error(f"Błąd wysyłania emaila do {client['email']}: {e}")
                
                # Aktualizacja paska postępu
                progress_dialog.setValue(i + 1)
            
            # Zamknięcie połączenia SMTP
            server.quit()
            
        except Exception as e:
            logger.error(f"Błąd połączenia z serwerem SMTP: {e}")
            QMessageBox.critical(
                dialog,
                _("Błąd SMTP"),
                f"{_('Wystąpił błąd podczas łączenia z serwerem SMTP')}:\n{str(e)}"
            )
            progress_dialog.cancel()
            return
        
        # Zamknięcie okna postępu
        progress_dialog.setValue(len(clients))
        
        # Zamknięcie dialogu wysyłania
        dialog.accept()
        
        # Podsumowanie wysyłania
        if error_count > 0:
            # Pokaż informację o błędach
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle(_("Raport wysyłania"))
            error_dialog.setMinimumWidth(500)
            error_dialog.setMinimumHeight(300)
            
            error_layout = QVBoxLayout(error_dialog)
            
            summary_label = QLabel(
                _("Wysłano {} wiadomości. Wystąpiło {} błędów.").format(
                    success_count, error_count
                )
            )
            summary_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            error_layout.addWidget(summary_label)
            
            errors_label = QLabel(_("Szczegóły błędów:"))
            error_layout.addWidget(errors_label)
            
            errors_text = QTextEdit()
            errors_text.setReadOnly(True)
            errors_text.setPlainText("\n".join(error_messages))
            error_layout.addWidget(errors_text)
            
            close_button = QPushButton(_("Zamknij"))
            close_button.clicked.connect(error_dialog.accept)
            error_layout.addWidget(close_button, 0, Qt.AlignRight)
            
            error_dialog.exec()
        else:
            # Powiadomienie o sukcesie
            NotificationManager.get_instance().show_notification(
                f"📧 {_('Pomyślnie wysłano')} {success_count} {_('wiadomości email')}",
                NotificationTypes.SUCCESS
            )
        
    def load_clients(self):
        """
        Ładuje listę klientów z bazy danych i wyświetla w odpowiednich zakładkach.
        """
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie parametrów zapytania
            params = []
            
            # Bazowe zapytanie zoptymalizowane - używa jednego JOIN i podzapytań
            base_query = """
            SELECT 
                c.id, 
                c.name, 
                c.phone_number, 
                c.email, 
                c.client_type, 
                c.discount,
                v.registration_number as reg_number,
                (SELECT COUNT(*) FROM vehicles WHERE client_id = c.id) as vehicle_count
            FROM 
                clients c
            LEFT JOIN 
                (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                ON c.id = fv.client_id
            LEFT JOIN
                vehicles v ON fv.first_vehicle_id = v.id
            """
            
            # Warunki filtrowania
            where_clauses = []
            
            # Filtrowanie po tekście
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                where_clauses.append("""(
                    c.name LIKE ? OR 
                    c.phone_number LIKE ? OR 
                    v.registration_number LIKE ?
                )""")
                params.extend([filter_text, filter_text, filter_text])
            
            # Filtrowanie po typie klienta
            if self.filtered_type != _("Wszyscy"):
                if self.filtered_type == _("Indywidualni"):
                    where_clauses.append("c.client_type = 'Indywidualny'")
                elif self.filtered_type == _("Firmowi"):
                    where_clauses.append("c.client_type = 'Firma'")
                elif self.filtered_type == _("Stali"):
                    where_clauses.append("c.discount > 0")
                elif self.filtered_type == _("Nowi"):
                    where_clauses.append("c.discount = 0")
            
            # Dodanie warunków WHERE
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Nazwisko"):
                base_query += " ORDER BY c.name"
            elif sort_field == _("Data dodania"):
                base_query += " ORDER BY c.id DESC"
            elif sort_field == _("Liczba pojazdów"):
                base_query += " ORDER BY vehicle_count DESC, c.name"
            
            # Zapytanie do pobrania całkowitej liczby rekordów (bez paginacji)
            count_query = """
            SELECT COUNT(*) 
            FROM clients c
            LEFT JOIN 
                (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                ON c.id = fv.client_id
            LEFT JOIN
                vehicles v ON fv.first_vehicle_id = v.id
            """
            
            if where_clauses:
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            # Pobierz całkowitą liczbę klientów z filtrami
            cursor.execute(count_query, params)
            total_clients = cursor.fetchone()[0]
            
            # Oblicz całkowitą liczbę stron
            self.total_pages = (total_clients + self.records_per_page - 1) // self.records_per_page
            
            # Paginacja - dodaj LIMIT i OFFSET
            offset = self.current_page * self.records_per_page
            base_query += f" LIMIT {self.records_per_page} OFFSET {offset}"
            
            # Wykonaj główne zapytanie
            cursor.execute(base_query, params)
            clients = cursor.fetchall()
            
            # Pobierz liczby klientów dla poszczególnych zakładek - optymalizacja: 
            # jedno zapytanie zamiast czterech oddzielnych
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN client_type = 'Indywidualny' THEN 1 ELSE 0 END) as individual_count,
                    SUM(CASE WHEN client_type = 'Firma' THEN 1 ELSE 0 END) as company_count,
                    SUM(CASE WHEN discount > 0 THEN 1 ELSE 0 END) as regular_count,
                    SUM(CASE WHEN discount = 0 THEN 1 ELSE 0 END) as new_count
                FROM clients
            """)
            
            counts = cursor.fetchone()
            individual_count, company_count, regular_count, new_count = counts
            
            # Aktualizacja liczby klientów w zakładkach
            self.tabs_widget.setTabText(0, f"{_('Wszyscy')} ({total_clients})")
            self.tabs_widget.setTabText(1, f"{_('Indywidualni')} ({individual_count})")
            self.tabs_widget.setTabText(2, f"{_('Firmowi')} ({company_count})")
            self.tabs_widget.setTabText(3, f"{_('Stali')} ({regular_count})")
            self.tabs_widget.setTabText(4, f"{_('Nowi')} ({new_count})")
            
            # Wyczyść wszystkie tabele
            for tab in [self.all_tab, self.individual_tab, self.company_tab, self.regular_tab, self.new_tab]:
                tab.clients_table.setRowCount(0)
            
            # Wypełnij tabele
            for client in clients:
                client_id, name, phone, email, client_type, discount, reg_number, vehicle_count = client
                
                # Dodaj klienta do tabeli "Wszyscy"
                self.add_client_to_table(
                    self.all_tab.clients_table, client_id, name, phone, email, 
                    reg_number or "-", vehicle_count, client_type, discount
                )
                
                # Dodaj klienta do odpowiedniej tabeli typu
                if client_type == "Indywidualny":
                    self.add_client_to_table(
                        self.individual_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                elif client_type == "Firma":
                    self.add_client_to_table(
                        self.company_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                
                # Dodaj klienta do odpowiedniej tabeli statusu
                if discount is not None and discount > 0:
                    self.add_client_to_table(
                        self.regular_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                else:
                    self.add_client_to_table(
                        self.new_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
            
            # Aktualizacja informacji o paginacji
            displayed_count = len(clients)
            start_record = offset + 1 if displayed_count > 0 else 0
            end_record = offset + displayed_count
            
            self.records_info.setText(f"{_('Wyświetlanie')} {start_record}-{end_record} {_('z')} {total_clients} {_('rekordów')}")
            
            # Aktualizacja przycisków paginacji
            self.update_pagination_buttons()
            
            # Aktualizacja statystyk w kartach
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania klientów: {e}")
            QMessageBox.critical(self, _("Błąd"), f"{_('Wystąpił błąd podczas ładowania klientów')}:\n{str(e)}")

    def setup_tab_content(self, tab):
        """
        Ustawia zawartość zakładki z tabelą klientów.
        
        Args:
            tab (QWidget): Zakładka, dla której ustawiamy zawartość
        """
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 10, 0, 0)
        tab_layout.setSpacing(0)
        
        # Tworzenie tabeli klientów
        clients_table = ClientsTable()
        clients_table.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, clients_table))
        clients_table.doubleClicked.connect(self.on_table_double_clicked)
        
        # Podłączenie sygnałów akcji
        clients_table.view_client_requested.connect(self.handle_view_client)
        clients_table.edit_client_requested.connect(self.handle_edit_client)
        clients_table.delete_client_requested.connect(self.handle_delete_client)
        
        # Zapisanie referencji do tabeli jako atrybut tab
        tab.clients_table = clients_table
        
        tab_layout.addWidget(clients_table)
    
    def on_table_double_clicked(self, index):
        """
        Obsługuje podwójne kliknięcie w tabelę.
        
        Args:
            index (QModelIndex): Indeks klikniętej komórki
        """
        current_tab = self.tabs_widget.currentWidget()
        table = current_tab.clients_table
        row = index.row()
        client_id = int(table.item(row, 0).text())
        self.view_client_details(client_id=client_id)
    
    def load_clients(self):
        """
        Ładuje listę klientów z bazy danych i wyświetla w odpowiednich zakładkach.
        Zoptymalizowana wersja funkcji, która używa mniejszej liczby zapytań do bazy danych.
        """
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie parametrów zapytania
            params = []
            
            # Bazowe zapytanie zoptymalizowane - używa jednego JOIN i podzapytań
            base_query = """
            SELECT 
                c.id, 
                c.name, 
                c.phone_number, 
                c.email, 
                c.client_type, 
                c.discount,
                v.registration_number as reg_number,
                (SELECT COUNT(*) FROM vehicles WHERE client_id = c.id) as vehicle_count
            FROM 
                clients c
            LEFT JOIN 
                (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                ON c.id = fv.client_id
            LEFT JOIN
                vehicles v ON fv.first_vehicle_id = v.id
            """
            
            # Warunki filtrowania
            where_clauses = []
            
            # Filtrowanie po tekście
            if self.filter_text:
                filter_text = f"%{self.filter_text}%"
                where_clauses.append("""(
                    c.name LIKE ? OR 
                    c.phone_number LIKE ? OR 
                    v.registration_number LIKE ?
                )""")
                params.extend([filter_text, filter_text, filter_text])
            
            # Filtrowanie po typie klienta
            if self.filtered_type != _("Wszyscy"):
                if self.filtered_type == _("Indywidualni"):
                    where_clauses.append("c.client_type = 'Indywidualny'")
                elif self.filtered_type == _("Firmowi"):
                    where_clauses.append("c.client_type = 'Firma'")
                elif self.filtered_type == _("Stali"):
                    where_clauses.append("c.discount > 0")
                elif self.filtered_type == _("Nowi"):
                    where_clauses.append("c.discount = 0")
            
            # Dodanie warunków WHERE
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Nazwisko"):
                base_query += " ORDER BY c.name"
            elif sort_field == _("Data dodania"):
                base_query += " ORDER BY c.id DESC"
            elif sort_field == _("Liczba pojazdów"):
                base_query += " ORDER BY vehicle_count DESC, c.name"
            
            # Zapytanie do pobrania całkowitej liczby rekordów (bez paginacji)
            count_query = """
            SELECT COUNT(*) 
            FROM clients c
            LEFT JOIN 
                (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                ON c.id = fv.client_id
            LEFT JOIN
                vehicles v ON fv.first_vehicle_id = v.id
            """
            
            if where_clauses:
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            # Pobierz całkowitą liczbę klientów z filtrami
            cursor.execute(count_query, params)
            total_clients = cursor.fetchone()[0]
            
            # Oblicz całkowitą liczbę stron
            self.total_pages = (total_clients + self.records_per_page - 1) // self.records_per_page
            
            # Paginacja - dodaj LIMIT i OFFSET
            offset = self.current_page * self.records_per_page
            base_query += f" LIMIT {self.records_per_page} OFFSET {offset}"
            
            # Wykonaj główne zapytanie
            cursor.execute(base_query, params)
            clients = cursor.fetchall()
            
            # Pobierz liczby klientów dla poszczególnych zakładek - optymalizacja: 
            # jedno zapytanie zamiast czterech oddzielnych
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN client_type = 'Indywidualny' THEN 1 ELSE 0 END) as individual_count,
                    SUM(CASE WHEN client_type = 'Firma' THEN 1 ELSE 0 END) as company_count,
                    SUM(CASE WHEN discount > 0 THEN 1 ELSE 0 END) as regular_count,
                    SUM(CASE WHEN discount = 0 THEN 1 ELSE 0 END) as new_count
                FROM clients
            """)
            
            counts = cursor.fetchone()
            individual_count, company_count, regular_count, new_count = counts
            
            # Aktualizacja liczby klientów w zakładkach
            self.tabs_widget.setTabText(0, f"{_('Wszyscy')} ({total_clients})")
            self.tabs_widget.setTabText(1, f"{_('Indywidualni')} ({individual_count})")
            self.tabs_widget.setTabText(2, f"{_('Firmowi')} ({company_count})")
            self.tabs_widget.setTabText(3, f"{_('Stali')} ({regular_count})")
            self.tabs_widget.setTabText(4, f"{_('Nowi')} ({new_count})")
            
            # Wyczyść wszystkie tabele
            for tab in [self.all_tab, self.individual_tab, self.company_tab, self.regular_tab, self.new_tab]:
                tab.clients_table.setRowCount(0)
            
            # Wypełnij tabele
            for client in clients:
                client_id, name, phone, email, client_type, discount, reg_number, vehicle_count = client
                
                # Dodaj klienta do tabeli "Wszyscy"
                self.add_client_to_table(
                    self.all_tab.clients_table, client_id, name, phone, email, 
                    reg_number or "-", vehicle_count, client_type, discount
                )
                
                # Dodaj klienta do odpowiedniej tabeli typu
                if client_type == "Indywidualny":
                    self.add_client_to_table(
                        self.individual_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                elif client_type == "Firma":
                    self.add_client_to_table(
                        self.company_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                
                # Dodaj klienta do odpowiedniej tabeli statusu
                if discount is not None and discount > 0:
                    self.add_client_to_table(
                        self.regular_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
                else:
                    self.add_client_to_table(
                        self.new_tab.clients_table, client_id, name, phone, email, 
                        reg_number or "-", vehicle_count, client_type, discount
                    )
            
            # Aktualizacja informacji o paginacji
            displayed_count = len(clients)
            start_record = offset + 1 if displayed_count > 0 else 0
            end_record = offset + displayed_count
            
            self.records_info.setText(f"{_('Wyświetlanie')} {start_record}-{end_record} {_('z')} {total_clients} {_('rekordów')}")
            
            # Aktualizacja przycisków paginacji
            self.update_pagination_buttons()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania klientów: {e}")
            QMessageBox.critical(self, _("Błąd"), f"{_('Wystąpił błąd podczas ładowania klientów')}:\n{str(e)}")
    
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
            self.load_clients()

    def view_client_details(self, index=None, client_id=None):
        """
        Wyświetla szczegóły klienta.
        
        Args:
            index (QModelIndex, optional): Indeks w tabeli
            client_id (int, optional): ID klienta
        """
        try:
            # Jeśli nie podano client_id, pobierz z zaznaczonego wiersza lub indeksu
            if client_id is None:
                if isinstance(index, int):
                    # Jeśli przekazano int zamiast QModelIndex, zakładamy że to client_id
                    client_id = index
                else:
                    current_tab = self.tabs_widget.currentWidget()
                    table = current_tab.clients_table
                    
                    if index is not None:
                        row = index.row()
                    else:
                        selected_items = table.selectedItems()
                        if not selected_items:
                            QMessageBox.warning(self, _("Ostrzeżenie"), _("Wybierz klienta do wyświetlenia."))
                            return
                        row = selected_items[0].row()
                    
                    client_id = int(table.item(row, 0).text())
            
            # Otwórz dialog szczegółów
            dialog = ClientDetailsDialog(self.conn, client_id, parent=self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów klienta: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Nie można wyświetlić szczegółów klienta')}:\n{str(e)}"
            )
    
    def handle_view_client(self, row):
        """
        Obsługuje żądanie podglądu klienta z delegata akcji.
        
        Args:
            row (int): Wiersz klienta w tabeli
        """
        current_tab = self.tabs_widget.currentWidget()
        table = current_tab.clients_table
        client_id = int(table.item(row, 0).text())
        self.view_client_details(client_id=client_id)
    
    def filter_clients(self, text=""):
        """
        Filtruje klientów według wpisanego tekstu.
        
        Args:
            text (str): Tekst do filtrowania
        """
        # Zapisz tekst do filtrowania
        self.filter_text = text
        
        # Zastosuj aktualne filtry po krótkim opóźnieniu, aby nie wykonywać zapytań przy każdym znaku
        # Tutaj można by zastosować timer, ale dla uproszczenia stosujemy bezpośrednie wywołanie
        self.apply_filters()

    def apply_filters(self):
        """Stosuje filtry wyszukiwania i typu klienta do listy klientów."""
        # Resetuj paginację przy zmianie filtrów
        self.current_page = 0
        self.load_clients()

    def change_client_type_filter(self, client_type):
        """
        Zmienia filtr typu klienta.
        
        Args:
            client_type (str): Typ klienta do filtrowania
        """
        self.filtered_type = client_type
        
        # Zmień aktywną zakładkę
        tab_map = {
            _("Wszyscy"): 0,
            _("Indywidualni"): 1,
            _("Firmowi"): 2,
            _("Stali"): 3,
            _("Nowi"): 4
        }
        
        if client_type in tab_map:
            self.tabs_widget.setCurrentIndex(tab_map[client_type])
        
        # Załaduj klientów z nowym filtrem
        self.apply_filters()

    def apply_sorting(self):
        """Stosuje wybrane sortowanie do listy klientów."""
        self.load_clients()

    def next_page(self):
        """Przechodzi do następnej strony wyników."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_clients()

    def prev_page(self):
        """Przechodzi do poprzedniej strony wyników."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_clients()
    
    def tab_changed(self, index):
        """
        Obsługa zmiany zakładki.
        
        Args:
            index (int): Indeks zakładki
        """
        # Mapowanie indeksu zakładki na typ klienta
        type_map = {
            0: _("Wszyscy"),
            1: _("Indywidualni"), 
            2: _("Firmowi"),
            3: _("Stali"), 
            4: _("Nowi")
        }
        
        if index in type_map:
            # Aktualizuj combobox typu i filtr
            self.filtered_type = type_map[index]
            
            # Załaduj klientów
            self.load_clients()
    
    def add_client_to_table(self, table, client_id, name, phone, email, reg_number, vehicle_count, client_type, discount):
        """
        Dodaje klienta do konkretnej tabeli w zakładce.
        
        Args:
            table (QTableWidget): Tabela, do której dodajemy klienta
            client_id (int): ID klienta
            name (str): Nazwa klienta
            phone (str): Numer telefonu
            email (str): Adres email
            reg_number (str): Numer rejestracyjny pierwszego pojazdu
            vehicle_count (int): Liczba pojazdów
            client_type (str): Typ klienta
            discount (float): Wartość rabatu
        """
        row = table.rowCount()
        table.insertRow(row)
        
        # ID
        id_item = QTableWidgetItem(str(client_id))
        id_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 0, id_item)
        
        # Nazwa
        table.setItem(row, 1, QTableWidgetItem(name or ""))
        
        # Telefon
        phone_item = QTableWidgetItem(phone if phone else "-")
        phone_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 2, phone_item)
        
        # Email
        email_item = QTableWidgetItem(email if email else "-")
        table.setItem(row, 3, email_item)
        
        # Nr rejestracyjny
        reg_item = QTableWidgetItem(reg_number or "-")
        reg_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 4, reg_item)
        
        # Liczba pojazdów
        vehicles_item = QTableWidgetItem(str(vehicle_count))
        vehicles_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 5, vehicles_item)
        
        # Typ klienta
        client_type_display = _("Nowy")
        if discount is not None and discount > 0:
            client_type_display = _("Stały")
        if client_type == "Firma":
            client_type_display = _("Firma")
            
        type_item = QTableWidgetItem(client_type_display)
        type_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 6, type_item)
        
        # Akcje (puste - renderowane przez delegata)
        table.setItem(row, 7, QTableWidgetItem(""))
    
    def show_context_menu(self, pos, table=None):
        """
        Wyświetla menu kontekstowe dla tabeli klientów.
        
        Args:
            pos (QPoint): Pozycja kliknięcia
            table (QTableWidget, optional): Tabela, dla której pokazujemy menu
        """
        # Jeśli nie podano tabeli, użyj aktywnej zakładki
        if table is None:
            current_tab = self.tabs_widget.currentWidget()
            table = current_tab.clients_table
        
        selected_items = table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        client_id = int(table.item(row, 0).text())
        client_name = table.item(row, 1).text()
        
        # Tworzenie menu kontekstowego
        menu = QMenu(self)
        menu.setStyleSheet(STYLES["MENU"])
        
        # Akcje menu
        view_action = menu.addAction(f"👁️ {_('Szczegóły klienta')}")
        edit_action = menu.addAction(f"✏️ {_('Edytuj klienta')}")
        menu.addSeparator()
        add_vehicle_action = menu.addAction(f"🚗 {_('Dodaj pojazd')}")
        
        # Dodanie podmenu pojazdów, jeśli klient ma jakiś pojazd
        # Pobierz pojazdy klienta - zoptymalizowane zapytanie
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, make, model, registration_number
            FROM vehicles
            WHERE client_id = ?
            ORDER BY make, model
        """, (client_id,))
        
        vehicles = cursor.fetchall()
        
        if vehicles:
            menu.addSeparator()
            vehicles_menu = menu.addMenu(f"🚗 {_('Zarządzaj pojazdami')}")
            vehicles_menu.setStyleSheet(STYLES["MENU"])
            
            for vehicle in vehicles:
                vehicle_id, make, model, reg_number = vehicle
                vehicle_text = f"{make or ''} {model or ''}"
                if reg_number:
                    vehicle_text += f" ({reg_number})"
                
                vehicle_menu = vehicles_menu.addMenu(vehicle_text)
                vehicle_menu.setStyleSheet(STYLES["MENU"])
                
                edit_vehicle_action = vehicle_menu.addAction(f"✏️ {_('Edytuj pojazd')}")
                
                # Używamy lokalnych zmiennych dla uniknięcia problemów z domknięciami
                def create_edit_handler(vehicle_id=vehicle_id, client_id=client_id, client_name=client_name):
                    return lambda: self.edit_vehicle(vehicle_id, client_id, client_name)
                
                edit_vehicle_action.triggered.connect(create_edit_handler())
                
                delete_vehicle_action = vehicle_menu.addAction(f"🗑️ {_('Usuń pojazd')}")
                
                def create_delete_handler(vehicle_id=vehicle_id, client_id=client_id, client_name=client_name, vehicle_text=vehicle_text):
                    return lambda: self.delete_vehicle(vehicle_id, client_id, client_name, vehicle_text)
                
                delete_vehicle_action.triggered.connect(create_delete_handler())
        
        menu.addSeparator()
        delete_action = menu.addAction(f"🗑️ {_('Usuń klienta')}")
        
        # Wyświetlenie menu i przetwarzanie wybranej akcji
        action = menu.exec(table.mapToGlobal(pos))
        
        if action == view_action:
            self.view_client_details(client_id=client_id)
        elif action == edit_action:
            self.edit_client(client_id=client_id)
        elif action == add_vehicle_action:
            self.add_vehicle_to_client(client_id, client_name)
        elif action == delete_action:
            self.handle_delete_client(row)
    
    def add_client(self):
        """Otwiera dialog dodawania nowego klienta."""
        try:
            dialog = ClientDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"➕ {_('Dodano nowego klienta pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                if hasattr(dialog, 'client_id'):
                    self.client_added.emit(dialog.client_id)
        except Exception as e:
            logger.error(f"Błąd podczas dodawania klienta: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Nie można dodać klienta')}:\n{str(e)}"
            )

    def edit_client(self, client_id=None):
        """
        Edytuje istniejącego klienta.
        
        Args:
            client_id (int, optional): ID klienta do edycji
        """
        try:
            # Jeśli nie podano client_id, pobierz z zaznaczonego wiersza
            if client_id is None:
                current_tab = self.tabs_widget.currentWidget()
                table = current_tab.clients_table
                selected_items = table.selectedItems()
                if not selected_items:
                    QMessageBox.warning(self, _("Ostrzeżenie"), _("Wybierz klienta do edycji."))
                    return
                
                row = selected_items[0].row()
                client_id = int(table.item(row, 0).text())
            
            # Otwórz dialog edycji
            dialog = ClientDialog(self.conn, client_id=client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"✏️ {_('Dane klienta zaktualizowane pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                self.client_updated.emit(client_id)
        except Exception as e:
            logger.error(f"Błąd podczas edycji klienta: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Nie można edytować klienta')}:\n{str(e)}"
            )
    
    def handle_edit_client(self, row):
        """
        Obsługuje żądanie edycji klienta z delegata akcji.
        
        Args:
            row (int): Wiersz klienta w tabeli
        """
        current_tab = self.tabs_widget.currentWidget()
        table = current_tab.clients_table
        client_id = int(table.item(row, 0).text())
        self.edit_client(client_id=client_id)

    def handle_delete_client(self, row):
        """
        Obsługuje żądanie usunięcia klienta z delegata akcji.
        
        Args:
            row (int): Wiersz klienta w tabeli
        """
        try:
            current_tab = self.tabs_widget.currentWidget()
            table = current_tab.clients_table
            
            client_id = int(table.item(row, 0).text())
            client_name = table.item(row, 1).text()
            
            # Potwierdzenie usunięcia
            reply = QMessageBox.question(
                self, 
                _("Potwierdź usunięcie"), 
                _("Czy na pewno chcesz usunąć klienta {}?\n\n"
                "Ta operacja usunie również wszystkie powiązane pojazdy i dane.\n"
                "Ta operacja jest nieodwracalna.").format(client_name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Usuń powiązane pojazdy
                    cursor.execute("DELETE FROM vehicles WHERE client_id = ?", (client_id,))
                    
                    # Usuń klienta
                    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                    
                    # Zatwierdź zmiany
                    self.conn.commit()
                    
                    # Odśwież listę klientów
                    self.load_clients()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"🗑️ {_('Klient')} {client_name} {_('został usunięty')}",
                        NotificationTypes.SUCCESS
                    )
                    
                    # Emituj sygnał
                    self.client_deleted.emit(client_id)
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
        except Exception as e:
            logger.error(f"Błąd podczas usuwania klienta: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Wystąpił błąd podczas usuwania klienta')}:\n{str(e)}"
            )

    def export_clients(self):
        """
        Eksportuje listę klientów do pliku CSV.
        Eksportuje aktualnie przefiltrowaną listę lub wszystkich klientów.
        """
        try:
            # Wybór pliku docelowego
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                _("Zapisz plik CSV"),
                f"klienci_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return  # Anulowano wybór pliku
            
            # Czy eksportować tylko widocznych klientów?
            export_mode = QMessageBox.question(
                self,
                _("Opcje eksportu"),
                _("Czy chcesz wyeksportować:\n\n"
                "• Tak: Tylko aktualnie przefiltrowanych klientów\n"
                "• Nie: Wszystkich klientów w bazie danych\n"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if export_mode == QMessageBox.Cancel:
                return
            
            cursor = self.conn.cursor()
            
            # Bazowe zapytanie
            if export_mode == QMessageBox.Yes:
                # Eksportuj tylko przefiltrowanych klientów
                base_query = """
                SELECT 
                    c.id, c.name, c.phone_number, c.email, c.client_type, c.discount, c.notes,
                    v.make as vehicle_make, v.model as vehicle_model, v.registration_number
                FROM 
                    clients c
                LEFT JOIN 
                    (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                    ON c.id = fv.client_id
                LEFT JOIN
                    vehicles v ON fv.first_vehicle_id = v.id
                """
                
                # Dodaj warunki filtrowania
                where_clauses = []
                params = []
                
                if self.filter_text:
                    filter_text = f"%{self.filter_text}%"
                    where_clauses.append("""(
                        c.name LIKE ? OR 
                        c.phone_number LIKE ? OR 
                        v.registration_number LIKE ?
                    )""")
                    params.extend([filter_text, filter_text, filter_text])
                
                if self.filtered_type != _("Wszyscy"):
                    if self.filtered_type == _("Indywidualni"):
                        where_clauses.append("c.client_type = 'Indywidualny'")
                    elif self.filtered_type == _("Firmowi"):
                        where_clauses.append("c.client_type = 'Firma'")
                    elif self.filtered_type == _("Stali"):
                        where_clauses.append("c.discount > 0")
                    elif self.filtered_type == _("Nowi"):
                        where_clauses.append("c.discount = 0")
                
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)
            else:
                # Eksportuj wszystkich klientów
                base_query = """
                SELECT 
                    c.id, c.name, c.phone_number, c.email, c.client_type, c.discount, c.notes,
                    v.make as vehicle_make, v.model as vehicle_model, v.registration_number
                FROM 
                    clients c
                LEFT JOIN 
                    (SELECT client_id, MIN(id) as first_vehicle_id FROM vehicles GROUP BY client_id) fv
                    ON c.id = fv.client_id
                LEFT JOIN
                    vehicles v ON fv.first_vehicle_id = v.id
                """
                params = []
            
            # Sortowanie
            sort_field = self.sort_combo.currentText()
            if sort_field == _("Nazwisko"):
                base_query += " ORDER BY c.name"
            elif sort_field == _("Data dodania"):
                base_query += " ORDER BY c.id DESC"
            elif sort_field == _("Liczba pojazdów"):
                base_query += " ORDER BY (SELECT COUNT(*) FROM vehicles WHERE client_id = c.id) DESC, c.name"
            
            # Pobierz dane
            cursor.execute(base_query, params)
            clients = cursor.fetchall()
            
            # Eksport do CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'name', 'phone_number', 'email', 'client_type', 'discount', 'notes',
                    'vehicle_make', 'vehicle_model', 'registration_number'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for client in clients:
                    writer.writerow({
                        'id': client[0],
                        'name': client[1],
                        'phone_number': client[2] or '',
                        'email': client[3] or '',
                        'client_type': client[4],
                        'discount': client[5],
                        'notes': client[6] or '',
                        'vehicle_make': client[7] or '',
                        'vehicle_model': client[8] or '',
                        'registration_number': client[9] or ''
                    })
                
            # Powiadomienie
            exported_count = len(clients)
            NotificationManager.get_instance().show_notification(
                f"📤 {_('Wyeksportowano')} {exported_count} {_('klientów')}",
                NotificationTypes.SUCCESS
            )
            
            # Informacja o zakończeniu
            QMessageBox.information(
                self,
                _("Eksport zakończony"),
                _("Pomyślnie wyeksportowano {} klientów do pliku:\n{}").format(
                    exported_count, file_path
                )
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas eksportu klientów: {e}")
            QMessageBox.critical(
                self,
                _("Błąd eksportu"),
                f"{_('Wystąpił błąd podczas eksportu klientów')}:\n{str(e)}"
            )
    
    def import_clients(self):
        """
        Importuje klientów z pliku CSV.
        Pozwala na wybór pliku CSV i zaimportowanie nowych klientów do bazy danych.
        """
        try:
            # Wybór pliku
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                _("Wybierz plik CSV do importu"),
                "",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return  # Anulowano wybór pliku
            
            # Potwierdzenie importu
            reply = QMessageBox.question(
                self,
                _("Potwierdź import"),
                _("Czy na pewno chcesz zaimportować klientów z pliku {}?\n\n"
                  "Zalecane jest wykonanie kopii zapasowej bazy danych przed importem.").format(os.path.basename(file_path)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Odczyt pliku CSV
            imported_count = 0
            skipped_count = 0
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                if not reader.fieldnames:
                    raise ValueError(_("Nieprawidłowy format pliku CSV. Brak nagłówków."))
                
                required_fields = ['name', 'phone_number', 'email', 'client_type']
                missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                
                if missing_fields:
                    raise ValueError(_("Brakujące wymagane pola w CSV: {}").format(", ".join(missing_fields)))
                
                cursor = self.conn.cursor()
                
                for row_num, row in enumerate(reader, start=2):  # Start from 2 as row 1 is headers
                    try:
                        # Sprawdzenie czy klient już istnieje (po emailu lub telefonie)
                        cursor.execute(
                            "SELECT id FROM clients WHERE email = ? OR phone_number = ?",
                            (row.get('email', ''), row.get('phone_number', ''))
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            skipped_count += 1
                            continue
                        
                        # Przygotowanie danych do wstawienia
                        name = row.get('name', '').strip()
                        phone = row.get('phone_number', '').strip()
                        email = row.get('email', '').strip()
                        client_type = row.get('client_type', 'Indywidualny').strip()
                        discount = float(row.get('discount', 0)) if row.get('discount') else 0
                        notes = row.get('notes', '').strip()
                        
                        # Walidacja
                        if not name:
                            raise ValueError(_("Brak wymaganego pola 'name'"))
                        
                        if client_type not in ['Indywidualny', 'Firma']:
                            client_type = 'Indywidualny'
                        
                        # Wstawienie nowego klienta
                        cursor.execute(
                            """
                            INSERT INTO clients (name, phone_number, email, client_type, discount, notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (name, phone, email, client_type, discount, notes)
                        )
                        
                        client_id = cursor.lastrowid
                        imported_count += 1
                        
                        # Sprawdź, czy istnieją dane o pojazdach
                        if 'vehicle_make' in row and 'vehicle_model' in row and row.get('vehicle_make'):
                            reg_number = row.get('vehicle_registration', '').strip()
                            make = row.get('vehicle_make', '').strip()
                            model = row.get('vehicle_model', '').strip()
                            
                            if make and model:
                                cursor.execute(
                                    """
                                    INSERT INTO vehicles (client_id, make, model, registration_number)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (client_id, make, model, reg_number)
                                )
                        
                    except Exception as e:
                        errors.append(f"{_('Wiersz')} {row_num}: {str(e)}")
                
                self.conn.commit()
            
            # Informacja o rezultacie
            if errors:
                message = _("Import zakończony z błędami:\n\n")
                message += "\n".join(errors[:10])  # Pokaż tylko 10 pierwszych błędów
                if len(errors) > 10:
                    message += f"\n{_('...oraz')} {len(errors) - 10} {_('więcej błędów.')}"
                message += f"\n\n{_('Zaimportowano:')} {imported_count}\n{_('Pominięto:')} {skipped_count}"
                QMessageBox.warning(self, _("Import z błędami"), message)
            else:
                QMessageBox.information(
                    self,
                    _("Import zakończony"),
                    _("Pomyślnie zaimportowano {} klientów.\nPominięto {} istniejących klientów.").format(
                        imported_count, skipped_count
                    )
                )
            
            # Odśwież listę klientów
            self.load_clients()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"📥 {_('Zaimportowano')} {imported_count} {_('klientów')}",
                NotificationTypes.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas importu klientów: {e}")
            QMessageBox.critical(
                self,
                _("Błąd importu"),
                f"{_('Wystąpił błąd podczas importu klientów')}:\n{str(e)}"
            )
            if hasattr(self.conn, 'rollback'):
                self.conn.rollback()

    def delete_vehicle(self, vehicle_id, client_id, client_name, vehicle_info):
        """
        Usuwa pojazd klienta.
        
        Args:
            vehicle_id (int): ID pojazdu
            client_id (int): ID klienta
            client_name (str): Nazwa klienta
            vehicle_info (str): Informacje o pojeździe (np. marka, model)
        """
        try:
            reply = QMessageBox.question(
                self, 
                _("Potwierdź usunięcie"), 
                _("Czy na pewno chcesz usunąć pojazd {} klienta {}?\n\n"
                  "Ta operacja jest nieodwracalna.").format(vehicle_info, client_name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Usuń pojazd
                    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
                    
                    # Zatwierdź zmiany
                    self.conn.commit()
                    
                    # Odśwież listę klientów
                    self.load_clients()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"🗑️ {_('Usunięto pojazd')}: {vehicle_info}",
                        NotificationTypes.SUCCESS
                    )
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
        except Exception as e:
            logger.error(f"Błąd podczas usuwania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Wystąpił błąd podczas usuwania pojazdu')}:\n{str(e)}"
            )
    
    def search(self, text):
        """
        Publiczna metoda do wyszukiwania klientów, którą można wywołać z zewnątrz.
        
        Args:
            text (str): Tekst do wyszukiwania
        """
        self.search_input.setText(text)
        self.filter_clients(text)
        
    def refresh_data(self):
        """Odświeża dane w zakładce klientów."""
        self.load_clients()
        
        # Powiadomienie
        NotificationManager.get_instance().show_notification(
            f"🔄 {_('Dane klientów odświeżone')}",
            NotificationTypes.INFO
        )
    
    def add_vehicle_to_client(self, client_id, client_name):
        """
        Dodaje nowy pojazd do wybranego klienta.
        
        Args:
            client_id (int): ID klienta
            client_name (str): Nazwa klienta
        """
        try:
            # Bezpośredni import wewnątrz metody
            from ui.dialogs.vehicle_dialog import VehicleDialog
            
            dialog = VehicleDialog(self.conn, client_id=client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów, aby pokazać nowy pojazd
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"🚗 {_('Dodano nowy pojazd dla klienta')}: {client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas dodawania pojazdu: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Nie można dodać pojazdu')}:\n{str(e)}"
            )

    def edit_vehicle(self, vehicle_id, client_id, client_name):
        """
        Edytuje istniejący pojazd klienta.
        
        Args:
            vehicle_id (int): ID pojazdu
            client_id (int): ID klienta
            client_name (str): Nazwa klienta
        """
        try:
            # Bezpośredni import wewnątrz metody
            from ui.dialogs.vehicle_dialog import VehicleDialog
            # Sprawdzenie, czy dialog VehicleDialog przyjmuje parametr vehicle_id
            import inspect
            vehicle_dialog_params = inspect.signature(VehicleDialog.__init__).parameters
            
            if 'vehicle_id' in vehicle_dialog_params:
                dialog = VehicleDialog(self.conn, client_id=client_id, vehicle_id=vehicle_id, parent=self)
            else:
                # Pobierz dane pojazdu ręcznie i przekaż je do konstruktora
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT make, model, registration_number, year, vin 
                    FROM vehicles 
                    WHERE id = ?
                """, (vehicle_id,))
                vehicle_data = cursor.fetchone()
                
                if vehicle_data:
                    make, model, reg_number, year, vin = vehicle_data
                    logger.info(f"Pobrano dane pojazdu ID={vehicle_id}: {make} {model} {reg_number}")
                    dialog = VehicleDialog(self.conn, client_id=client_id, parent=self)
                    dialog.set_vehicle_data(make, model, reg_number, year, vin)
                else:
                    logger.warning(f"Nie znaleziono pojazdu o ID={vehicle_id}")
                    QMessageBox.warning(
                        self, 
                        _("Ostrzeżenie"), 
                        _("Nie można znaleźć danych pojazdu.")
                    )
                    return
                
            if dialog.exec() == QDialog.Accepted:
                # Odśwież listę klientów, aby pokazać zaktualizowany pojazd
                self.load_clients()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"🚗 {_('Zaktualizowano pojazd dla klienta')}: {client_name}",
                    NotificationTypes.SUCCESS
                )
        except Exception as e:
            logger.error(f"Błąd podczas edycji pojazdu: {e}")
            QMessageBox.critical(
                self, 
                _("Błąd"), 
                f"{_('Nie można edytować pojazdu')}:\n{str(e)}"
            )
