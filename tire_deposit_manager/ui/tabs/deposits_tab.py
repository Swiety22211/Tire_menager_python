#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zakładki depozytów w aplikacji Menadżer Serwisu Opon.
Obsługuje wyświetlanie, filtrowanie i zarządzanie depozytami opon klientów.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QAbstractItemView, QDialog, QFileDialog,
    QFrame, QSplitter, QToolButton, QScrollArea, QMessageBox,
    QStyledItemDelegate, QSpacerItem, QSizePolicy, QTabWidget
)
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPainter, QPixmap
from PySide6.QtCore import Qt, QEvent, Signal, QDate, QRect, QSettings
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtWebEngineWidgets import QWebEngineView

from ui.dialogs.deposit_dialog import DepositDialog
from ui.dialogs.deposit_release_dialog import DepositReleaseDialog
from utils.exporter import export_data_to_excel, export_data_to_pdf
from utils.paths import ICONS_DIR
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireDepositManager")

# Wspólne style CSS - scentralizowane do łatwego zarządzania
# Dodaj te style do istniejącego słownika STYLES w pliku deposits_tab.py
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
    "RELEASE_BUTTON": """
        QPushButton#releaseButton {
            background-color: #ffa94d;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 5px 15px;
        }
        QPushButton#releaseButton:hover {
            background-color: #ff922b;
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
    "SUMMARY_CARD": """
        QFrame {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 5px;
        }
        QLabel {
            color: #212529;
        }
    """,
    # Dodaj brakujące style kart statystycznych
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
    """
}


class StatusDelegate(QStyledItemDelegate):
    """
    Delegat do stylizowania komórek statusu w tabeli depozytów.
    """
    def paint(self, painter, option, index):
        if not index.isValid():
            return super().paint(painter, option, index)
            
        status = index.data()
        
        # Zapisz stan paintera przed rozpoczęciem własnego rysowania
        painter.save()
        
        try:
            # Określenie kolorów w zależności od statusu
            if status == _("Aktywny"):
                background_color = QColor("#51cf66")  # Zielony
                text_color = QColor(255, 255, 255)
            elif status == _("Do odbioru"):
                background_color = QColor("#ffa94d")  # Pomarańczowy
                text_color = QColor(255, 255, 255)
            elif status == _("Zaległy"):
                background_color = QColor("#fa5252")  # Czerwony
                text_color = QColor(255, 255, 255)
            elif status == _("Rezerwacja"):
                background_color = QColor("#4dabf7")  # Niebieski
                text_color = QColor(255, 255, 255)
            elif status == _("Wydany"):
                background_color = QColor("#adb5bd")  # Szary
                text_color = QColor(255, 255, 255)
            else:
                # Domyślne kolory
                background_color = QColor("#2c3034")
                text_color = QColor(255, 255, 255)
            
            # Włącz antyaliasing dla gładszych krawędzi
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Wyczyść tło
            painter.setBrush(background_color)
            painter.setPen(Qt.NoPen)
            
            # Rysowanie zaokrąglonego prostokąta
            painter.drawRoundedRect(option.rect.adjusted(4, 4, -4, -4), 10, 10)
            
            # Rysowanie tekstu
            painter.setPen(text_color)
            painter.drawText(
                option.rect, 
                Qt.AlignCenter, 
                status
            )
        except Exception as e:
            logger.error(f"Błąd podczas rysowania statusu: {e}")
        finally:
            # Zawsze przywracaj stan paintera, nawet jeśli wystąpi błąd
            painter.restore()


class ActionButtonDelegate(QStyledItemDelegate):
    """
    Delegat do wyświetlania przycisków akcji z emotikonami w tabeli.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            return super().paint(painter, option, index)
            
        # Zapisz stan paintera
        painter.save()
        
        try:
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
        except Exception as e:
            logger.error(f"Błąd podczas rysowania przycisku akcji: {e}")
        finally:
            # Zawsze przywracaj stan paintera
            painter.restore()

    def editorEvent(self, event, model, option, index):
        try:
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
        except Exception as e:
            logger.error(f"Błąd podczas obsługi zdarzenia edytora: {e}")

        return super().editorEvent(event, model, option, index)


class DepositsTable(QTableWidget):
    """
    Tabela depozytów opon z obsługą akcji.
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
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            _("ID"), _("Klient"), _("Dane kontaktowe"), 
            _("Data przyjęcia"), _("Data odbioru"), _("Rozmiar/Typ"), 
            _("Lokalizacja"), _("Status"), _("Akcje")
        ])
        
        # Ustawienie rozciągania kolumn
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Domyślnie interaktywne
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Klient
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Dane kontaktowe
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Data przyjęcia
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Data odbioru
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Rozmiar/Typ
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Lokalizacja
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Status
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Akcje
        self.setColumnWidth(8, 50)  # Stała szerokość kolumny akcji
        
        # Delegaty
        self.setItemDelegateForColumn(7, StatusDelegate(self))  # Status
        self.setItemDelegateForColumn(8, ActionButtonDelegate(self))  # Akcje
        
        # Wysokość wiersza
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Ustawienie reguł stylów dla trybu ciemnego
        self.setStyleSheet(STYLES["TABLE_WIDGET"])


class DepositsTab(QWidget):
    """Zakładka depozytów w aplikacji Menadżer Serwisu Opon"""
    
    # Sygnały
    deposit_added = Signal(int)  # Emitowany po dodaniu depozytu
    deposit_released = Signal(int)  # Emitowany po wydaniu depozytu
    deposit_updated = Signal(int)  # Emitowany po aktualizacji depozytu
    deposit_deleted = Signal(int)  # Emitowany po usunięciu depozytu
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki depozytów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.current_tab_index = 0  # Aktywna zakładka (0 - Aktywne, 1 - Historia, 2 - Do odbioru, 3 - Mapa magazynu)
        self.current_status_filter = _("Wszystkie")  # Filtr statusu
        self.current_season_filter = _("Wszystkie")  # Filtr sezonu
        self.filter_text = ""  # Tekst wyszukiwania
        self.current_page = 0  # Aktywna strona paginacji
        self.records_per_page = 20  # Liczba rekordów na stronę
        self.total_pages = 0  # Całkowita liczba stron
        
        # Statystyki depozytów
        self.total_deposits = 0
        self.active_deposits = 0
        self.pending_deposits = 0
        self.overdue_deposits = 0
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie danych
        self.load_statistics()
        self.load_deposits()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki depozytów."""
        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Tytuł zakładki depozytów
        title_label = QLabel(_("Zarządzanie Depozytami"))
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        # Elastyczny odstęp
        header_layout.addStretch(1)
        
        # Przyciski akcji w nagłówku
        self.add_deposit_btn = QPushButton("+ " + _("Nowy depozyt"))
        self.add_deposit_btn.setObjectName("addButton")
        self.add_deposit_btn.setFixedHeight(40)
        self.add_deposit_btn.setMinimumWidth(150)
        self.add_deposit_btn.setStyleSheet(STYLES["ADD_BUTTON"])
        self.add_deposit_btn.clicked.connect(self.add_deposit)
        header_layout.addWidget(self.add_deposit_btn)
        
        self.release_deposit_btn = QPushButton("+ " + _("Wydanie depozytu"))
        self.release_deposit_btn.setObjectName("releaseButton")
        self.release_deposit_btn.setFixedHeight(40)
        self.release_deposit_btn.setMinimumWidth(150)
        self.release_deposit_btn.setStyleSheet(STYLES["RELEASE_BUTTON"])
        self.release_deposit_btn.clicked.connect(self.release_deposit)
        header_layout.addWidget(self.release_deposit_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Panel statystyk - nowa sekcja
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # Karta statystyczna: Łączna liczba depozytów
        self.total_deposits_card = self.create_stat_card(
            "📦", _("Łączna liczba"), "0", 
            STYLES["STAT_CARD_BLUE"]
        )
        stats_layout.addWidget(self.total_deposits_card)
        
        # Karta statystyczna: Aktywne
        self.active_deposits_card = self.create_stat_card(
            "✅", _("Aktywne"), "0", 
            STYLES["STAT_CARD_GREEN"]
        )
        stats_layout.addWidget(self.active_deposits_card)
        
        # Karta statystyczna: Do odbioru
        self.pending_deposits_card = self.create_stat_card(
            "🔔", _("Do odbioru"), "0", 
            STYLES["STAT_CARD_ORANGE"]
        )
        stats_layout.addWidget(self.pending_deposits_card)
        
        # Karta statystyczna: Zaległe
        self.overdue_deposits_card = self.create_stat_card(
            "⚠️", _("Zaległe"), "0", 
            STYLES["STAT_CARD_LIGHT_BLUE"]
        )
        stats_layout.addWidget(self.overdue_deposits_card)
        
        main_layout.addLayout(stats_layout)
        
        # Zakładki typów widoku
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(STYLES["TABS"])
        
        # Tworzenie zakładek
        self.active_tab = QWidget()
        self.history_tab = QWidget()
        self.pending_tab = QWidget()
        self.warehouse_map_tab = QWidget()
        
        # Dodanie zakładek do widgetu
        self.tabs.addTab(self.active_tab, _("Aktywne"))
        self.tabs.addTab(self.history_tab, _("Historia"))
        self.tabs.addTab(self.pending_tab, _("Do odbioru"))
        self.tabs.addTab(self.warehouse_map_tab, _("Mapa magazynu"))
        
        # Połączenie zmiany zakładki z odpowiednim filtrowaniem
        self.tabs.currentChanged.connect(self.tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # Konfiguracja zakładek
        self.setup_active_tab()
        self.setup_history_tab()
        self.setup_pending_tab()
        self.setup_warehouse_map_tab()
        
        # Panel przycisków akcji masowych
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.generate_labels_btn = QPushButton(_("Generuj etykiety dla wybranych depozytów"))
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

        self.send_email_btn = QPushButton(_("Powiadomienia Email"))
        self.send_email_btn.setFixedHeight(40)
        self.send_email_btn.setStyleSheet("""
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
        self.send_email_btn.clicked.connect(self.send_email_notifications)
        actions_layout.addWidget(self.send_email_btn)

        self.export_list_btn = QPushButton(_("Eksportuj listę depozytów"))
        self.export_list_btn.setFixedHeight(40)
        self.export_list_btn.setStyleSheet("""
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
        self.export_list_btn.clicked.connect(self.export_deposits_list)
        actions_layout.addWidget(self.export_list_btn)

        main_layout.addLayout(actions_layout)

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

    def load_statistics(self):
        """Ładuje statystyki depozytów z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz całkowitą liczbę depozytów
            cursor.execute("SELECT COUNT(*) FROM deposits")
            self.total_deposits = cursor.fetchone()[0]
            
            # Pobierz liczbę aktywnych depozytów
            cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
            self.active_deposits = cursor.fetchone()[0]
            
            # Pobierz liczbę depozytów do odbioru w tym tygodniu
            today = datetime.now()
            week_later = today + timedelta(days=7)
            cursor.execute(
                "SELECT COUNT(*) FROM deposits WHERE status = 'Do odbioru' AND pickup_date BETWEEN ? AND ?",
                (today.strftime("%Y-%m-%d"), week_later.strftime("%Y-%m-%d"))
            )
            self.pending_deposits = cursor.fetchone()[0]
            
            # Pobierz liczbę zaległych depozytów
            cursor.execute(
                "SELECT COUNT(*) FROM deposits WHERE status = 'Zaległy' OR (status = 'Do odbioru' AND pickup_date < ?)",
                (today.strftime("%Y-%m-%d"),)
            )
            self.overdue_deposits = cursor.fetchone()[0]
            
            # Aktualizuj etykiety w interfejsie
            self.total_deposits_card.value_label.setText(f"{self.total_deposits}")
            self.active_deposits_card.value_label.setText(f"{self.active_deposits}")
            self.pending_deposits_card.value_label.setText(f"{self.pending_deposits}")
            self.overdue_deposits_card.value_label.setText(f"{self.overdue_deposits}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania statystyk depozytów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania statystyk: {e}",
                NotificationTypes.ERROR
            )
    
    def setup_active_tab(self):
        """Konfiguracja zakładki aktywnych depozytów."""
        layout = QVBoxLayout(self.active_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
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
        self.search_input.setPlaceholderText(_("Szukaj według klienta lub numeru..."))
        self.search_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        self.search_input.textChanged.connect(self.filter_deposits)
        search_box_layout.addWidget(self.search_input)
        
        search_layout.addWidget(search_box, 1)  # Rozciągnij pole wyszukiwania
        
        # Filtr statusu
        status_layout = QHBoxLayout()
        status_layout.setSpacing(5)
        
        status_label = QLabel(_("Status:"))
        status_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("filterCombo")
        self.status_combo.setFixedHeight(40)
        self.status_combo.setMinimumWidth(120)
        self.status_combo.addItems([
            _("Wszystkie"), 
            _("Aktywny"), 
            _("Do odbioru"), 
            _("Zaległy"),
            _("Rezerwacja")
        ])
        self.status_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.status_combo.currentTextChanged.connect(self.apply_filters)
        search_layout.addWidget(self.status_combo)
        
        # Filtr sezonu
        season_layout = QHBoxLayout()
        season_layout.setSpacing(5)
        
        season_label = QLabel(_("Sezon:"))
        season_layout.addWidget(season_label)
        
        self.season_combo = QComboBox()
        self.season_combo.setObjectName("filterCombo")
        self.season_combo.setFixedHeight(40)
        self.season_combo.setMinimumWidth(120)
        self.season_combo.addItems([
            _("Wszystkie"), 
            _("Letnie"), 
            _("Zimowe"), 
            _("Całoroczne")
        ])
        self.season_combo.setStyleSheet(STYLES["COMBO_BOX"])
        self.season_combo.currentTextChanged.connect(self.apply_filters)
        search_layout.addWidget(self.season_combo)
        
        # Przycisk filtrowania
        self.filter_button = QPushButton(_("Filtruj"))
        self.filter_button.setObjectName("filterButton")
        self.filter_button.setFixedHeight(40)
        self.filter_button.setMinimumWidth(100)
        self.filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.filter_button.clicked.connect(self.apply_filters)
        search_layout.addWidget(self.filter_button)
        
        layout.addWidget(search_panel)
        
        # Tabela depozytów
        self.active_deposits_table = DepositsTable()
        self.active_deposits_table.customContextMenuRequested.connect(self.show_context_menu)
        self.active_deposits_table.doubleClicked.connect(self.on_table_double_clicked)
        self.active_deposits_table.action_requested.connect(self.show_deposit_actions)
        layout.addWidget(self.active_deposits_table)
        
        # Panel nawigacji stron
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(10)
        
        # Informacja o liczbie wyświetlanych rekordów
        self.records_info = QLabel(_("Wyświetlanie 0 z 0 depozytów"))
        self.records_info.setStyleSheet("color: #bdc3c7; font-size: 13px;")
        pagination_layout.addWidget(self.records_info)
        
        pagination_layout.addStretch(1)
        
        # Przyciski nawigacji
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
        
        layout.addLayout(pagination_layout)
    
    def setup_history_tab(self):
        """Konfiguracja zakładki historii depozytów."""
        layout = QVBoxLayout(self.history_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Panel wyszukiwania i filtrów (podobny do aktywnych)
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        search_panel.setStyleSheet(STYLES["SEARCH_PANEL"])
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(10)
        
        # Pole wyszukiwania dla historii
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
        
        self.history_search_input = QLineEdit()
        self.history_search_input.setObjectName("searchField")
        self.history_search_input.setPlaceholderText(_("Szukaj w historii depozytów..."))
        self.history_search_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        # Podłączenie można dodać później
        search_box_layout.addWidget(self.history_search_input)
        
        search_layout.addWidget(search_box, 1)  # Rozciągnij pole wyszukiwania
        
        # Filtry dat
        date_layout = QHBoxLayout()
        date_layout.setSpacing(5)
        
        date_from_label = QLabel(_("Od:"))
        date_layout.addWidget(date_from_label)
        
        self.date_from_input = QLineEdit()
        self.date_from_input.setObjectName("dateField")
        self.date_from_input.setPlaceholderText(_("DD-MM-YYYY"))
        self.date_from_input.setFixedWidth(100)
        self.date_from_input.setFixedHeight(40)
        self.date_from_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        date_layout.addWidget(self.date_from_input)
        
        date_to_label = QLabel(_("Do:"))
        date_layout.addWidget(date_to_label)
        
        self.date_to_input = QLineEdit()
        self.date_to_input.setObjectName("dateField")
        self.date_to_input.setPlaceholderText(_("DD-MM-YYYY"))
        self.date_to_input.setFixedWidth(100)
        self.date_to_input.setFixedHeight(40)
        self.date_to_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        date_layout.addWidget(self.date_to_input)
        
        search_layout.addLayout(date_layout)
        
        # Przycisk filtrowania
        self.history_filter_button = QPushButton(_("Filtruj"))
        self.history_filter_button.setObjectName("filterButton")
        self.history_filter_button.setFixedHeight(40)
        self.history_filter_button.setMinimumWidth(100)
        self.history_filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        # Podłączenie można dodać później
        search_layout.addWidget(self.history_filter_button)
        
        layout.addWidget(search_panel)
        
        # Tabela historii depozytów
        self.history_deposits_table = DepositsTable()
        layout.addWidget(self.history_deposits_table)
        
        # Dodanie informacji
        info_label = QLabel(_("Historia zawiera wszystkie wydane depozyty, które zostały odebrane przez klientów."))
        info_label.setStyleSheet("color: #bdc3c7; font-style: italic;")
        layout.addWidget(info_label)
    
    def setup_pending_tab(self):
        """Konfiguracja zakładki depozytów do odbioru."""
        layout = QVBoxLayout(self.pending_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Panel wyszukiwania i filtrów (uproszczony)
        search_panel = QFrame()
        search_panel.setObjectName("searchPanel")
        search_panel.setMinimumHeight(60)
        search_panel.setMaximumHeight(60)
        search_panel.setStyleSheet(STYLES["SEARCH_PANEL"])
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(10)
        
        # Pole wyszukiwania dla depozytów do odbioru
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
        
        self.pending_search_input = QLineEdit()
        self.pending_search_input.setObjectName("searchField")
        self.pending_search_input.setPlaceholderText(_("Szukaj depozytów do odbioru..."))
        self.pending_search_input.setStyleSheet(STYLES["SEARCH_FIELD"])
        # Podłączenie można dodać później
        search_box_layout.addWidget(self.pending_search_input)
        
        search_layout.addWidget(search_box, 1)  # Rozciągnij pole wyszukiwania
        
        # Filtry pilności
        urgency_layout = QHBoxLayout()
        urgency_layout.setSpacing(5)
        
        urgency_label = QLabel(_("Pilność:"))
        urgency_layout.addWidget(urgency_label)
        
        self.urgency_combo = QComboBox()
        self.urgency_combo.setObjectName("filterCombo")
        self.urgency_combo.setFixedHeight(40)
        self.urgency_combo.setMinimumWidth(150)
        self.urgency_combo.addItems([
            _("Wszystkie"), 
            _("W tym tygodniu"), 
            _("W przyszłym tygodniu"), 
            _("Zaległe")
        ])
        self.urgency_combo.setStyleSheet(STYLES["COMBO_BOX"])
        # Podłączenie można dodać później
        urgency_layout.addWidget(self.urgency_combo)
        
        search_layout.addLayout(urgency_layout)
        
        # Przycisk filtrowania
        self.pending_filter_button = QPushButton(_("Filtruj"))
        self.pending_filter_button.setObjectName("filterButton")
        self.pending_filter_button.setFixedHeight(40)
        self.pending_filter_button.setMinimumWidth(100)
        self.pending_filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        # Podłączenie można dodać później
        search_layout.addWidget(self.pending_filter_button)
        
        layout.addWidget(search_panel)
        
        # Tabela depozytów do odbioru
        self.pending_deposits_table = DepositsTable()
        self.pending_deposits_table.customContextMenuRequested.connect(self.show_context_menu)
        self.pending_deposits_table.doubleClicked.connect(self.on_table_double_clicked)
        self.pending_deposits_table.action_requested.connect(self.show_deposit_actions)
        layout.addWidget(self.pending_deposits_table)
        
        # Przyciski akcji masowych specyficznych dla tej zakładki
        actions_layout = QHBoxLayout()
        
        self.notify_all_btn = QPushButton(_("Powiadom wszystkich klientów"))
        self.notify_all_btn.setFixedHeight(40)
        self.notify_all_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        actions_layout.addWidget(self.notify_all_btn)
        
        self.print_list_btn = QPushButton(_("Drukuj listę do odbioru"))
        self.print_list_btn.setFixedHeight(40)
        self.print_list_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        actions_layout.addWidget(self.print_list_btn)
        
        # Dodanie nowych przycisków dla SMS i Email
        self.send_all_email_btn = QPushButton(_("📧 Wyślij powiadomienia Email"))
        self.send_all_email_btn.setFixedHeight(40)
        self.send_all_email_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.send_all_email_btn.clicked.connect(self.send_email_notifications)
        actions_layout.addWidget(self.send_all_email_btn)
        
        self.send_all_sms_btn = QPushButton(_("📱 Wyślij powiadomienia SMS"))
        self.send_all_sms_btn.setFixedHeight(40)
        self.send_all_sms_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        self.send_all_sms_btn.clicked.connect(self.send_sms_notifications)
        actions_layout.addWidget(self.send_all_sms_btn)
        
        layout.addLayout(actions_layout)
    
    
    def load_deposits(self):
        """Ładuje depozyty z bazy danych z uwzględnieniem aktywnej zakładki i filtrów."""
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie parametrów zapytania
            params = []
            
            # Bazowe zapytanie w zależności od aktywnej zakładki
            if self.current_tab_index == 0:  # Aktywne
                base_query = """
                SELECT 
                    d.id, 
                    c.name AS client_name, 
                    c.phone_number || '\n' || c.email AS contact_info,
                    d.deposit_date,
                    d.pickup_date,
                    d.tire_size || ' ' || d.tire_type AS tire_info,
                    d.location,
                    d.status
                FROM 
                    deposits d
                JOIN 
                    clients c ON d.client_id = c.id
                WHERE 
                    d.status IN ('Aktywny', 'Do odbioru', 'Zaległy', 'Rezerwacja')
                """
            elif self.current_tab_index == 1:  # Historia
                base_query = """
                SELECT 
                    d.id, 
                    c.name AS client_name, 
                    c.phone_number || '\n' || c.email AS contact_info,
                    d.deposit_date,
                    d.pickup_date,
                    d.tire_size || ' ' || d.tire_type AS tire_info,
                    d.location,
                    d.status
                FROM 
                    deposits d
                JOIN 
                    clients c ON d.client_id = c.id
                WHERE 
                    d.status = 'Wydany'
                """
            elif self.current_tab_index == 2:  # Do odbioru
                base_query = """
                SELECT 
                    d.id, 
                    c.name AS client_name, 
                    c.phone_number || '\n' || c.email AS contact_info,
                    d.deposit_date,
                    d.pickup_date,
                    d.tire_size || ' ' || d.tire_type AS tire_info,
                    d.location,
                    d.status
                FROM 
                    deposits d
                JOIN 
                    clients c ON d.client_id = c.id
                WHERE 
                    d.status = 'Do odbioru'
                """
            else:  # Mapa magazynu lub inna
                return  # Obsługa mapy magazynu będzie realizowana osobno
            
            # Dodatkowe filtry specyficzne dla aktywnej zakładki
            where_clauses = []
            
            if self.current_tab_index == 0:  # Aktywne
                # Filtrowanie po tekście
                if self.filter_text:
                    filter_text = f"%{self.filter_text}%"
                    where_clauses.append("""(
                        c.name LIKE ? OR 
                        d.id LIKE ? OR 
                        c.phone_number LIKE ?
                    )""")
                    params.extend([filter_text, filter_text, filter_text])
                
                # Filtrowanie po statusie
                if self.current_status_filter != _("Wszystkie"):
                    where_clauses.append("d.status = ?")
                    params.append(self.current_status_filter)
                
                # Filtrowanie po sezonie
                if self.current_season_filter != _("Wszystkie"):
                    where_clauses.append("d.tire_type LIKE ?")
                    params.append(f"%{self.current_season_filter}%")
            
            # Dodanie warunków WHERE
            if where_clauses:
                if "WHERE" in base_query:
                    base_query += " AND " + " AND ".join(where_clauses)
                else:
                    base_query += " WHERE " + " AND ".join(where_clauses)
            
            # Sortowanie - domyślnie po ID
            base_query += " ORDER BY d.id DESC"
            
            # Obliczenie całkowitej liczby rekordów (do paginacji)
            count_query = f"SELECT COUNT(*) FROM ({base_query})"
            cursor.execute(count_query, params)
            total_deposits = cursor.fetchone()[0]
            
            # Obliczenie liczby stron
            self.total_pages = (total_deposits + self.records_per_page - 1) // self.records_per_page
            
            # Dodanie paginacji
            offset = self.current_page * self.records_per_page
            base_query += f" LIMIT {self.records_per_page} OFFSET {offset}"
            
            # Wykonanie zapytania
            cursor.execute(base_query, params)
            deposits = cursor.fetchall()
            
            # Czyszczenie i wypełnianie odpowiedniej tabeli w zależności od aktywnej zakładki
            if self.current_tab_index == 0:
                table = self.active_deposits_table
            elif self.current_tab_index == 1:
                table = self.history_deposits_table
            elif self.current_tab_index == 2:
                table = self.pending_deposits_table
            else:
                return  # Brak tabeli dla mapy magazynu
            
            table.setRowCount(0)
            
            # Wypełnianie tabeli danymi
            for deposit in deposits:
                row_position = table.rowCount()
                table.insertRow(row_position)
                
                # Formatowanie ID (zwykle w formacie Dxxx)
                deposit_id = f"D{str(deposit['id']).zfill(3)}"
                
                # Formatowanie dat
                deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                # Dodanie danych do komórek
                table.setItem(row_position, 0, QTableWidgetItem(deposit_id))
                table.setItem(row_position, 1, QTableWidgetItem(deposit['client_name']))
                table.setItem(row_position, 2, QTableWidgetItem(deposit['contact_info']))
                table.setItem(row_position, 3, QTableWidgetItem(deposit_date))
                table.setItem(row_position, 4, QTableWidgetItem(pickup_date))
                table.setItem(row_position, 5, QTableWidgetItem(deposit['tire_info']))
                table.setItem(row_position, 6, QTableWidgetItem(deposit['location']))
                
                # Status - obsługiwany przez delegata
                status_item = QTableWidgetItem(deposit['status'])
                status_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_position, 7, status_item)
                
                # Kolumna akcji - obsługiwana przez delegata
                table.setItem(row_position, 8, QTableWidgetItem(""))
            
            # Aktualizacja informacji o paginacji
            displayed_count = len(deposits)
            start_record = offset + 1 if displayed_count > 0 else 0
            end_record = offset + displayed_count
            
            self.records_info.setText(f"{_('Wyświetlanie')} {start_record}-{end_record} {_('z')} {total_deposits} {_('depozytów')}")
            
            # Aktualizacja przycisków paginacji
            self.update_pagination_buttons()
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania depozytów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas ładowania depozytów: {e}",
                NotificationTypes.ERROR
            )
    
    def update_pagination_buttons(self):
        """Aktualizuje przyciski paginacji."""
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
        """Przechodzi do wybranej strony."""
        if 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self.load_deposits()
    
    def next_page(self):
        """Przechodzi do następnej strony wyników."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_deposits()

    def prev_page(self):
        """Przechodzi do poprzedniej strony wyników."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_deposits()
    
    def setup_warehouse_map_tab(self):
        """Konfiguracja zakładki mapy magazynu."""
        layout = QVBoxLayout(self.warehouse_map_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Informacja o funkcjonalności
        info_label = QLabel(_("Mapa magazynu pozwala wizualnie zarządzać przestrzenią magazynową i lokalizacją depozytów."))
        info_label.setStyleSheet("color: white;")
        layout.addWidget(info_label)
        
        # Placeholder na mapę magazynu (do rozbudowy w przyszłości)
        warehouse_view = QFrame()
        warehouse_view.setMinimumHeight(400)
        warehouse_view.setStyleSheet("background-color: #343a40; border-radius: 5px;")
        warehouse_layout = QVBoxLayout(warehouse_view)
        
        placeholder_label = QLabel(_("Funkcjonalność mapy magazynu będzie dostępna wkrótce."))
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: #adb5bd; font-style: italic;")
        warehouse_layout.addWidget(placeholder_label)
        
        layout.addWidget(warehouse_view)
        
        # Przyciski akcji dla mapy magazynu
        actions_layout = QHBoxLayout()
        
        self.configure_map_btn = QPushButton(_("Konfiguruj mapę magazynu"))
        self.configure_map_btn.setFixedHeight(40)
        self.configure_map_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        actions_layout.addWidget(self.configure_map_btn)
        
        self.optimize_btn = QPushButton(_("Optymalizuj rozmieszczenie"))
        self.optimize_btn.setFixedHeight(40)
        self.optimize_btn.setStyleSheet(STYLES["UTILITY_BUTTON"])
        actions_layout.addWidget(self.optimize_btn)
        
        layout.addLayout(actions_layout)
        self.load_deposits()
    
    def tab_changed(self, index):
        """Obsługuje zmianę aktywnej zakładki."""
        self.current_tab_index = index
        self.current_page = 0  # Reset paginacji przy zmianie zakładki
        self.load_deposits()
    
    def filter_deposits(self, text=""):
        """Filtruje depozyty wg wpisanego tekstu."""
        self.filter_text = text
        self.current_page = 0  # Reset paginacji przy zmianie filtra
        self.apply_filters()
    
    def apply_filters(self):
        """Stosuje filtry do listy depozytów."""
        try:
            # Aktualizacja filtrów
            self.current_status_filter = self.status_combo.currentText()
            self.current_season_filter = self.season_combo.currentText()
            
            # Reset paginacji
            self.current_page = 0
            
            # Odświeżenie danych
            self.load_deposits()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Filtrowanie depozytów wg kryteriów: {self.current_status_filter}, {self.current_season_filter}",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas stosowania filtrów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas filtrowania: {e}",
                NotificationTypes.ERROR
            )
    
    def on_table_double_clicked(self, index):
        """Obsługuje podwójne kliknięcie w tabelę."""
        try:
            # Pobranie ID depozytu z tabeli
            row = index.row()
            
            if self.current_tab_index == 0:
                table = self.active_deposits_table
            elif self.current_tab_index == 1:
                table = self.history_deposits_table
            elif self.current_tab_index == 2:
                table = self.pending_deposits_table
            else:
                return
            
            deposit_id_str = table.item(row, 0).text()
            deposit_id = int(deposit_id_str.replace('D', ''))
            
            # Otwórz dialog z podglądem/edycją depozytu
            self.view_deposit_details(deposit_id)
        
        except Exception as e:
            logger.error(f"Błąd podczas obsługi podwójnego kliknięcia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas otwierania szczegółów depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def view_deposit_details(self, deposit_id):
        """Wyświetla szczegóły depozytu."""
        try:
            # Tutaj można zaimplementować dialog z podglądem depozytu
            # Jako tymczasowe rozwiązanie wyświetlimy powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Wyświetlanie szczegółów depozytu #{deposit_id}",
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania szczegółów depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def show_context_menu(self, pos):
        """Wyświetla menu kontekstowe dla depozytu."""
        try:
            # Pobranie tabeli i indeksu wiersza
            if self.current_tab_index == 0:
                table = self.active_deposits_table
            elif self.current_tab_index == 1:
                table = self.history_deposits_table
            elif self.current_tab_index == 2:
                table = self.pending_deposits_table
            else:
                return
            
            index = table.indexAt(pos)
            if not index.isValid():
                return
            
            row = index.row()
            deposit_id_str = table.item(row, 0).text()
            deposit_id = int(deposit_id_str.replace('D', ''))
            client_name = table.item(row, 1).text()
            status = table.item(row, 7).text()
            
            # Tworzenie menu kontekstowego
            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
            
            # Akcje menu
            view_action = menu.addAction(f"👁️ {_('Szczegóły depozytu')} #{deposit_id_str}")
            edit_action = menu.addAction(f"✏️ {_('Edytuj depozyt')}")
            menu.addSeparator()
            
            # Dodanie nowych opcji do menu
            print_label_action = menu.addAction(f"🏷️ {_('Generuj etykietę')}")
            print_receipt_action = menu.addAction(f"📃 {_('Generuj potwierdzenie przyjęcia')}")
            send_email_action = menu.addAction(f"📧 {_('Wyślij powiadomienie email')}")
            send_sms_action = menu.addAction(f"📱 {_('Wyślij powiadomienie SMS')}")
            menu.addSeparator()
            
            # Podmenu zmiany statusu
            status_menu = menu.addMenu(f"🔄 {_('Zmień status')}")
            status_menu.setStyleSheet(STYLES["MENU"])
            
            statuses = [_("Aktywny"), _("Do odbioru"), _("Zaległy"), _("Rezerwacja")]
            for status_option in statuses:
                if status != status_option:
                    action = status_menu.addAction(status_option)
                    action.triggered.connect(lambda checked=False, did=deposit_id, st=status_option: 
                                        self.change_deposit_status(did, st))
            
            # Opcja wydania depozytu
            menu.addSeparator()
            release_action = menu.addAction(f"📤 {_('Wydaj depozyt')}")
            
            # Opcja usunięcia tylko gdy depozyt nie ma statusu "Wydany"
            if status != _("Wydany"):
                menu.addSeparator()
                delete_action = menu.addAction(f"🗑️ {_('Usuń depozyt')}")
            else:
                delete_action = None
            
            # Wyświetlenie menu i obsługa wybranej akcji
            action = menu.exec(table.mapToGlobal(pos))
            
            if action == view_action:
                self.view_deposit_details(deposit_id)
            elif action == edit_action:
                self.edit_deposit(deposit_id)
            elif action == release_action:
                self.release_deposit(deposit_id=deposit_id)
            elif action == delete_action:
                self.delete_deposit(deposit_id)
            elif action == print_label_action:
                self.generate_deposit_label(deposit_id)
            elif action == print_receipt_action:
                self.generate_deposit_receipt(deposit_id)
            elif action == send_email_action:
                self.send_deposit_email_notification(deposit_id)
            elif action == send_sms_action:
                self.send_deposit_sms_notification(deposit_id)
        
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania menu kontekstowego: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania menu: {e}",
                NotificationTypes.ERROR
            )

    def show_deposit_actions(self, row):
        """Wyświetla menu akcji dla depozytu po kliknięciu przycisku w tabeli."""
        try:
            # Pobranie tabeli
            if self.current_tab_index == 0:
                table = self.active_deposits_table
            elif self.current_tab_index == 1:
                table = self.history_deposits_table
            elif self.current_tab_index == 2:
                table = self.pending_deposits_table
            else:
                return
            
            deposit_id_str = table.item(row, 0).text()
            deposit_id = int(deposit_id_str.replace('D', ''))
            
            # Tworzenie menu
            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
            
            # Akcje menu
            view_action = menu.addAction(f"👁️ {_('Szczegóły')}")
            edit_action = menu.addAction(f"✏️ {_('Edytuj')}")
            menu.addSeparator()
            email_action = menu.addAction(f"📧 {_('Email')}")
            sms_action = menu.addAction(f"📱 {_('SMS')}")
            menu.addSeparator()
            release_action = menu.addAction(f"📤 {_('Wydaj')}")
            
            # Status depozytu
            status = table.item(row, 7).text()
            
            # Opcja usunięcia tylko gdy depozyt nie ma statusu "Wydany"
            if status != _("Wydany"):
                menu.addSeparator()
                delete_action = menu.addAction(f"🗑️ {_('Usuń')}")
            else:
                delete_action = None
            
            # Wyświetlenie menu w lokalizacji przycisku
            button_pos = table.visualItemRect(table.item(row, 8)).center()
            action = menu.exec(table.viewport().mapToGlobal(button_pos))
            
            if action == view_action:
                self.view_deposit_details(deposit_id)
            elif action == edit_action:
                self.edit_deposit(deposit_id)
            elif action == email_action:
                self.send_deposit_email_notification(deposit_id)
            elif action == sms_action:
                self.send_deposit_sms_notification(deposit_id)
            elif action == release_action:
                self.release_deposit(deposit_id=deposit_id)
            elif action == delete_action and delete_action is not None:
                self.delete_deposit(deposit_id)
        
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania menu akcji: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wyświetlania menu akcji: {e}",
                NotificationTypes.ERROR
            )

    
    def add_deposit(self):
        """Otwiera dialog dodawania nowego depozytu."""
        try:
            dialog = DepositDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież statystyki i listę depozytów
                self.load_statistics()
                self.load_deposits()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"➕ {_('Dodano nowy depozyt pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                if hasattr(dialog, 'deposit_id'):
                    self.deposit_added.emit(dialog.deposit_id)
        except Exception as e:
            logger.error(f"Błąd podczas dodawania depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas dodawania depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def edit_deposit(self, deposit_id):
        """Edytuje istniejący depozyt."""
        try:
            dialog = DepositDialog(self.conn, deposit_id=deposit_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież dane
                self.load_statistics()
                self.load_deposits()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    f"✏️ {_('Depozyt')} #{deposit_id} {_('zaktualizowany pomyślnie')}",
                    NotificationTypes.SUCCESS
                )
                
                # Emituj sygnał
                self.deposit_updated.emit(deposit_id)
        except Exception as e:
            logger.error(f"Błąd podczas edycji depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas edycji depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def release_deposit(self, deposit_id=None):
        """Otwiera dialog wydawania depozytu."""
        try:
            dialog = DepositReleaseDialog(self.conn, deposit_id=deposit_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Odśwież dane
                self.load_statistics()
                self.load_deposits()
                
                # Powiadomienie
                if deposit_id:
                    NotificationManager.get_instance().show_notification(
                        f"📤 {_('Depozyt')} #{deposit_id} {_('został wydany pomyślnie')}",
                        NotificationTypes.SUCCESS
                    )
                else:
                    NotificationManager.get_instance().show_notification(
                        f"📤 {_('Depozyt został wydany pomyślnie')}",
                        NotificationTypes.SUCCESS
                    )
                
                # Emituj sygnał
                if hasattr(dialog, 'deposit_id'):
                    self.deposit_released.emit(dialog.deposit_id)
        except Exception as e:
            logger.error(f"Błąd podczas wydawania depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wydawania depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def change_deposit_status(self, deposit_id, new_status):
        """Zmienia status depozytu."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz aktualny status
            cursor.execute("SELECT status FROM deposits WHERE id = ?", (deposit_id,))
            current_status = cursor.fetchone()['status']
            
            # Aktualizuj status
            cursor.execute(
                "UPDATE deposits SET status = ? WHERE id = ?",
                (new_status, deposit_id)
            )
            
            self.conn.commit()
            
            # Odśwież dane
            self.load_statistics()
            self.load_deposits()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"🔄 {_('Status depozytu')} #{deposit_id} {_('zmieniony z')} '{current_status}' {_('na')} '{new_status}'",
                NotificationTypes.SUCCESS
            )
            
            # Emituj sygnał
            self.deposit_updated.emit(deposit_id)
            
        except Exception as e:
            logger.error(f"Błąd podczas zmiany statusu depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas zmiany statusu depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def identify_foreign_key_tables(self):
        """Identyfikuje tabele powiązane kluczem obcym z tabelą deposits."""
        try:
            cursor = self.conn.cursor()
            # Znajdź wszystkie tabele w bazie danych
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            related_tables = []
            for table in tables:
                # Sprawdź każdą tabelę czy ma powiązanie z deposits
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                for fk in cursor.fetchall():
                    if fk[2] == 'deposits':  # jeśli tabela ma klucz obcy do deposits
                        related_tables.append({
                            'table': table,
                            'from': fk[3],  # kolumna w tej tabeli
                            'to': fk[4]     # kolumna w tabeli deposits
                        })
            
            print("Tabele powiązane z deposits:", related_tables)
            return related_tables
        except Exception as e:
            print(f"Błąd podczas identyfikacji tabel: {e}")
            return []

    def delete_deposit(self, deposit_id):
        """Usuwa depozyt."""
        try:
            # Potwierdzenie usunięcia
            reply = QMessageBox.question(
                self, 
                _("Potwierdź usunięcie"), 
                _("Czy na pewno chcesz usunąć depozyt #{}?\n\n"
                "Ta operacja jest nieodwracalna.").format(deposit_id),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                
                try:
                    # Rozpocznij transakcję
                    self.conn.execute("BEGIN")
                    
                    # Znajdź powiązane tabele
                    related_tables = self.identify_foreign_key_tables()
                    
                    # Usuń powiązane rekordy ze wszystkich powiązanych tabel
                    for related in related_tables:
                        cursor.execute(f"DELETE FROM {related['table']} WHERE {related['from']} = ?", (deposit_id,))
                        print(f"Usunięto powiązane rekordy z tabeli {related['table']}")
                    
                    # Sprawdź czy są rekordy w email_logs
                    cursor.execute("DELETE FROM email_logs WHERE deposit_id = ?", (deposit_id,))
                    
                    # Na końcu usuń depozyt
                    cursor.execute("DELETE FROM deposits WHERE id = ?", (deposit_id,))
                    
                    # Zatwierdź zmiany
                    self.conn.commit()
                    
                    # Odśwież dane
                    self.load_statistics()
                    self.load_deposits()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        f"🗑️ {_('Depozyt')} #{deposit_id} {_('został usunięty')}",
                        NotificationTypes.SUCCESS
                    )
                    
                    # Emituj sygnał
                    self.deposit_deleted.emit(deposit_id)
                except Exception as e:
                    # W przypadku błędu, cofnij transakcję
                    self.conn.rollback()
                    raise e
        except Exception as e:
            logger.error(f"Błąd podczas usuwania depozytu: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas usuwania depozytu: {e}",
                NotificationTypes.ERROR
            )
    
    def generate_labels(self):
        """Generuje etykiety dla wybranych depozytów."""
        try:
            # Implementacja generowania etykiet
            # Jako tymczasowe rozwiązanie wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Funkcja generowania etykiet będzie dostępna wkrótce."),
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiet: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania etykiet: {e}",
                NotificationTypes.ERROR
            )
    
    def send_email_notifications(self):
        """Wysyła powiadomienia Email do klientów."""
        try:
            # Implementacja wysyłania Email
            # Jako tymczasowe rozwiązanie wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Funkcja wysyłania powiadomień Email będzie dostępna wkrótce."),
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomień Email: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas wysyłania powiadomień Email: {e}",
                NotificationTypes.ERROR
            )
    
    def export_deposits_list(self):
        """Eksportuje listę depozytów do pliku."""
        try:
            # Opcje eksportu: Excel, PDF, CSV
            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
            
            excel_action = menu.addAction(_("Eksportuj do Excel"))
            pdf_action = menu.addAction(_("Eksportuj do PDF"))
            csv_action = menu.addAction(_("Eksportuj do CSV"))
            
            # Wyświetlenie menu
            action = menu.exec(self.export_list_btn.mapToGlobal(self.export_list_btn.rect().bottomLeft()))
            
            if action == excel_action:
                self.export_to_excel()
            elif action == pdf_action:
                self.export_to_pdf()
            elif action == csv_action:
                self.export_to_csv()
        
        except Exception as e:
            logger.error(f"Błąd podczas eksportu listy depozytów: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas eksportu listy: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_excel(self):
        """Eksportuje listę depozytów do pliku Excel."""
        try:
            # Wybór pliku docelowego
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                _("Zapisz plik Excel"), 
                f"depozyty_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Czy eksportować tylko widoczne/przefiltrowane depozyty?
            export_mode = QMessageBox.question(
                self,
                _("Opcje eksportu"),
                _("Czy chcesz wyeksportować:\n\n"
                "• Tak: Tylko aktualnie przefiltrowane depozyty\n"
                "• Nie: Wszystkie depozyty w bazie danych\n"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if export_mode == QMessageBox.Cancel:
                return
            
            # Przygotuj zapytanie
            cursor = self.conn.cursor()
            
            if export_mode == QMessageBox.Yes:
                # Eksportuj tylko przefiltrowane depozyty
                # Używamy tego samego zapytania co w load_deposits, ale bez paginacji
                if self.current_tab_index == 0:  # Aktywne
                    base_query = """
                    SELECT 
                        d.id, 
                        c.name AS client_name, 
                        c.phone_number,
                        c.email,
                        d.deposit_date,
                        d.pickup_date,
                        d.tire_size,
                        d.tire_type,
                        d.quantity,
                        d.location,
                        d.status,
                        d.notes
                    FROM 
                        deposits d
                    JOIN 
                        clients c ON d.client_id = c.id
                    WHERE 
                        d.status IN ('Aktywny', 'Do odbioru', 'Zaległy', 'Rezerwacja')
                    """
                    
                    # Dodatkowe filtry
                    params = []
                    where_clauses = []
                    
                    if self.filter_text:
                        filter_text = f"%{self.filter_text}%"
                        where_clauses.append("""(
                            c.name LIKE ? OR 
                            d.id LIKE ? OR 
                            c.phone_number LIKE ?
                        )""")
                        params.extend([filter_text, filter_text, filter_text])
                    
                    if self.current_status_filter != _("Wszystkie"):
                        where_clauses.append("d.status = ?")
                        params.append(self.current_status_filter)
                    
                    if self.current_season_filter != _("Wszystkie"):
                        where_clauses.append("d.tire_type LIKE ?")
                        params.append(f"%{self.current_season_filter}%")
                    
                    # Dodanie warunków WHERE
                    if where_clauses:
                        base_query += " AND " + " AND ".join(where_clauses)
                    
                elif self.current_tab_index == 1:  # Historia
                    base_query = """
                    SELECT 
                        d.id, 
                        c.name AS client_name, 
                        c.phone_number,
                        c.email,
                        d.deposit_date,
                        d.pickup_date,
                        d.tire_size,
                        d.tire_type,
                        d.quantity,
                        d.location,
                        d.status,
                        d.notes
                    FROM 
                        deposits d
                    JOIN 
                        clients c ON d.client_id = c.id
                    WHERE 
                        d.status = 'Wydany'
                    """
                    params = []
                    
                elif self.current_tab_index == 2:  # Do odbioru
                    base_query = """
                    SELECT 
                        d.id, 
                        c.name AS client_name, 
                        c.phone_number,
                        c.email,
                        d.deposit_date,
                        d.pickup_date,
                        d.tire_size,
                        d.tire_type,
                        d.quantity,
                        d.location,
                        d.status,
                        d.notes
                    FROM 
                        deposits d
                    JOIN 
                        clients c ON d.client_id = c.id
                    WHERE 
                        d.status = 'Do odbioru'
                    """
                    params = []
                    
                else:  # Mapa magazynu lub inna
                    NotificationManager.get_instance().show_notification(
                        _("Eksport z tej zakładki nie jest obsługiwany."),
                        NotificationTypes.WARNING
                    )
                    return
            else:
                # Eksportuj wszystkie depozyty
                base_query = """
                SELECT 
                    d.id, 
                    c.name AS client_name, 
                    c.phone_number,
                    c.email,
                    d.deposit_date,
                    d.pickup_date,
                    d.tire_size,
                    d.tire_type,
                    d.quantity,
                    d.location,
                    d.status,
                    d.notes
                FROM 
                    deposits d
                JOIN 
                    clients c ON d.client_id = c.id
                """
                params = []
            
            # Sortowanie
            base_query += " ORDER BY d.id DESC"
            
            # Wykonanie zapytania
            cursor.execute(base_query, params)
            deposits = cursor.fetchall()
            
            # Przygotowanie danych do eksportu
            headers = [
                _("ID"), _("Klient"), _("Telefon"), _("Email"), 
                _("Data przyjęcia"), _("Data odbioru"), _("Rozmiar"), 
                _("Typ"), _("Ilość"), _("Lokalizacja"), _("Status"), _("Uwagi")
            ]
            
            data = []
            for deposit in deposits:
                data.append([
                    f"D{str(deposit['id']).zfill(3)}",
                    deposit['client_name'],
                    deposit['phone_number'],
                    deposit['email'],
                    datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y"),
                    deposit['tire_size'],
                    deposit['tire_type'],
                    deposit['quantity'],
                    deposit['location'],
                    deposit['status'],
                    deposit['notes'] or ""
                ])
            
            # Eksport do Excel
            export_data_to_excel(file_path, headers, data, _("Depozyty"))
            
            NotificationManager.get_instance().show_notification(
                f"📊 {_('Wyeksportowano')} {len(deposits)} {_('depozytów do pliku Excel')}",
                NotificationTypes.SUCCESS
            )
        
        except Exception as e:
            logger.error(f"Błąd podczas eksportu do Excel: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do Excel: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_pdf(self):
        """Eksportuje listę depozytów do pliku PDF."""
        try:
            # Implementacja eksportu do PDF analogiczna do Excel
            # Jako tymczasowe rozwiązanie wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Funkcja eksportu do PDF będzie dostępna wkrótce."),
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas eksportu do PDF: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do PDF: {e}",
                NotificationTypes.ERROR
            )
    
    def export_to_csv(self):
        """Eksportuje listę depozytów do pliku CSV."""
        try:
            # Implementacja eksportu do CSV analogiczna do Excel
            # Jako tymczasowe rozwiązanie wyświetlamy powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Funkcja eksportu do CSV będzie dostępna wkrótce."),
                NotificationTypes.INFO
            )
        except Exception as e:
            logger.error(f"Błąd podczas eksportu do CSV: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd eksportu do CSV: {e}",
                NotificationTypes.ERROR
            )
    
    def refresh_data(self):
        """Odświeża dane w zakładce depozytów."""
        self.load_statistics()
        self.load_deposits()
        
        # Powiadomienie
        NotificationManager.get_instance().show_notification(
            f"🔄 {_('Dane depozytów odświeżone')}",
            NotificationTypes.INFO
        )

    def generate_deposit_label(self, deposit_id):
        """Generuje etykietę dla wybranego depozytu."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane depozytu
            query = """
            SELECT 
                d.id,
                c.name AS client_name,
                d.tire_size,
                d.tire_type,
                d.quantity,
                d.location,
                d.status,
                d.deposit_date,
                d.pickup_date
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                d.id = ?
            """
            
            cursor.execute(query, (deposit_id,))
            deposit = cursor.fetchone()
            
            if not deposit:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono depozytu o ID {deposit_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Formatowanie ID depozytu
            deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
            
            # Formatowanie dat
            deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            current_date = datetime.now().strftime("%d-%m-%Y")
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            company_email = settings.value("company_email", "")
            company_website = settings.value("company_website", "")
            
            # Przygotowanie danych do szablonu
            template_data = {
                "deposit_id": deposit_id_str,
                "client_name": deposit['client_name'],
                "phone_number": deposit['phone_number'] or "",
                "email": deposit['email'] or "",
                "tire_size": deposit['tire_size'],
                "tire_type": deposit['tire_type'],
                "quantity": str(deposit['quantity']),
                "location": deposit['location'],
                "deposit_date": deposit_date,
                "pickup_date": pickup_date,
                "current_date": current_date,
                "notes": deposit['notes'] or "",
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone,
                "company_email": company_email,
                "company_website": company_website
            }
            
            # Pobierz szablon potwierdzenia
            template = self.get_receipt_template()
            
            # Wypełnij szablon danymi
            html_content = template
            for key, value in template_data.items():
                html_content = html_content.replace("{" + key + "}", value)
            
            # Wyświetl podgląd wydruku
            self.print_html_preview(html_content, "Podgląd potwierdzenia przyjęcia depozytu")
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Wygenerowano potwierdzenie przyjęcia dla depozytu {deposit_id_str}",
                NotificationTypes.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania potwierdzenia: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania potwierdzenia: {e}",
                NotificationTypes.ERROR
            )

    def send_deposit_email_notification(self, deposit_id):
        """Wysyła powiadomienie email dla depozytu."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane depozytu
            query = """
            SELECT 
                d.id,
                c.name AS client_name,
                c.email,
                c.phone_number,
                d.tire_size,
                d.tire_type,
                d.quantity,
                d.status,
                d.location,
                d.deposit_date,
                d.pickup_date,
                d.notes
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                d.id = ?
            """
            
            cursor.execute(query, (deposit_id,))
            deposit = cursor.fetchone()
            
            if not deposit:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono depozytu o ID {deposit_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Formatowanie ID depozytu
            deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
            
            # Sprawdź, czy klient ma adres email
            if not deposit['email']:
                NotificationManager.get_instance().show_notification(
                    f"Klient {deposit['client_name']} nie ma podanego adresu email",
                    NotificationTypes.WARNING
                )
                return
            
            # Formatowanie dat
            deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            current_date = datetime.now().strftime("%d-%m-%Y")
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            company_email = settings.value("company_email", "")
            company_website = settings.value("company_website", "")
            
            # Przygotowanie danych do szablonu
            template_data = {
                "deposit_id": deposit_id_str,
                "client_name": deposit['client_name'],
                "phone_number": deposit['phone_number'] or "",
                "email": deposit['email'],
                "tire_size": deposit['tire_size'],
                "tire_type": deposit['tire_type'],
                "quantity": str(deposit['quantity']),
                "location": deposit['location'],
                "deposit_date": deposit_date,
                "pickup_date": pickup_date,
                "status": deposit['status'],
                "notes": deposit['notes'] or "",
                "current_date": current_date,
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone,
                "company_email": company_email,
                "company_website": company_website
            }
            
            # Wybierz odpowiedni szablon email w zależności od statusu
            template_key = "general"
            status = deposit['status']
            
            if status == "Aktywny":
                template_key = "active"
            elif status == "Do odbioru":
                template_key = "pickup"
            elif status == "Zaległy":
                template_key = "overdue"
            
            # Pobierz szablon email i temat
            email_template = self.get_email_template(template_key)
            email_subject = email_template.get("subject", "Informacja o depozycie opon")
            email_body = email_template.get("body", "")
            
            # Wypełnij szablon danymi
            for key, value in template_data.items():
                email_subject = email_subject.replace("{" + key + "}", value)
                email_body = email_body.replace("{" + key + "}", value)
            
            # Pokaż okno podglądu przed wysłaniem
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
            
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Podgląd wiadomości email")
            preview_dialog.setMinimumSize(800, 600)
            
            preview_layout = QVBoxLayout(preview_dialog)
            
            # Adresat
            to_layout = QHBoxLayout()
            to_layout.addWidget(QLabel("Do:"))
            to_field = QLineEdit(deposit['email'])
            to_field.setReadOnly(True)
            to_layout.addWidget(to_field)
            preview_layout.addLayout(to_layout)
            
            # Temat
            subject_layout = QHBoxLayout()
            subject_layout.addWidget(QLabel("Temat:"))
            subject_field = QLineEdit(email_subject)
            subject_field.setReadOnly(False)  # Możliwość edycji tematu
            subject_layout.addWidget(subject_field)
            preview_layout.addLayout(subject_layout)
            
            # Treść HTML
            content_label = QLabel("Treść:")
            preview_layout.addWidget(content_label)
            
            email_view = QWebEngineView()
            email_view.setHtml(email_body)
            email_view.setMinimumHeight(400)
            preview_layout.addWidget(email_view)
            
            # Przyciski
            buttons_layout = QHBoxLayout()
            cancel_btn = QPushButton("Anuluj")
            cancel_btn.clicked.connect(preview_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            buttons_layout.addStretch(1)
            
            send_btn = QPushButton("Wyślij email")
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
            send_btn.clicked.connect(lambda: self.confirm_send_email(deposit_id_str, deposit['email'], subject_field.text(), email_body, preview_dialog))
            buttons_layout.addWidget(send_btn)
            
            preview_layout.addLayout(buttons_layout)
            
            preview_dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania powiadomienia email: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas przygotowania powiadomienia email: {e}",
                NotificationTypes.ERROR
            )

    def confirm_send_email(self, deposit_id, email, subject, body, dialog):
        """Potwierdza wysłanie emaila."""
        try:
            # Pobierz ustawienia SMTP
            settings = QSettings("TireDepositManager", "Settings")
            smtp_server = settings.value("smtp_server", "")
            smtp_port = settings.value("smtp_port", 587, type=int)
            use_ssl = settings.value("use_ssl", True, type=bool)
            email_address = settings.value("email_address", "")
            email_password = settings.value("email_password", "")
            
            # Sprawdź czy mamy wszystkie potrzebne dane
            if not smtp_server or not email_address or not email_password:
                QMessageBox.warning(
                    self,
                    "Brak konfiguracji SMTP",
                    "Brakuje danych konfiguracyjnych serwera SMTP. Przejdź do Ustawienia > Komunikacja, aby skonfigurować wysyłanie emaili."
                )
                return
            
            # Zamknij dialog podglądu
            dialog.accept()
            
            # Pokazujemy komunikat, że wysyłamy email
            # Używamy NotificationManager zamiast QMessageBox, żeby nie blokować interfejsu
            NotificationManager.get_instance().show_notification(
                f"Wysyłanie emaila do {email}...",
                NotificationTypes.INFO
            )
            
            # FAKTYCZNE WYSYŁANIE EMAILA
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                # Przygotuj wiadomość
                msg = MIMEMultipart()
                msg['From'] = email_address
                msg['To'] = email
                msg['Subject'] = subject
                
                # Dodanie treści HTML
                msg.attach(MIMEText(body, 'html'))
                
                # Utworzenie sesji SMTP
                logger.info(f"Próba połączenia z serwerem SMTP: {smtp_server}:{smtp_port}")
                
                session = smtplib.SMTP(smtp_server, smtp_port)
                session.set_debuglevel(1)  # Włącz debugowanie SMTP
                
                # Dla większości serwerów konieczne jest rozpoczęcie sesji TLS
                if use_ssl:
                    logger.info("Uruchamianie TLS...")
                    session.starttls()
                
                # Logowanie do serwera SMTP
                logger.info(f"Próba logowania do serwera SMTP jako {email_address}")
                session.login(email_address, email_password)
                
                # Wysłanie wiadomości
                logger.info(f"Wysyłanie wiadomości do {email}")
                session.sendmail(email_address, email, msg.as_string())
                
                # Zakończenie sesji
                logger.info("Zamykanie sesji SMTP")
                session.quit()
                
                # Powiadomienie o sukcesie
                NotificationManager.get_instance().show_notification(
                    f"Email został pomyślnie wysłany do {email}",
                    NotificationTypes.SUCCESS
                )
                
                # Zapisz informację o wysłanym emailu w bazie danych
                cursor = self.conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deposit_id INTEGER,
                        email TEXT,
                        subject TEXT,
                        sent_date TEXT,
                        status TEXT,
                        FOREIGN KEY (deposit_id) REFERENCES deposits (id)
                    )
                """)
                
                # Zapisz log wysłanego emaila
                from datetime import datetime
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO email_logs (deposit_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                    (deposit_id.replace('D', ''), email, subject, current_date, "Wysłany")
                )
                self.conn.commit()
                
                logger.info(f"Wysłano email dla depozytu {deposit_id} do {email}")
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Błąd uwierzytelniania SMTP: {e}")
                NotificationManager.get_instance().show_notification(
                    f"Błąd logowania do serwera SMTP: {e}",
                    NotificationTypes.ERROR
                )
                
                # Zapisz log błędu
                cursor = self.conn.cursor()
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO email_logs (deposit_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                    (deposit_id.replace('D', ''), email, subject, current_date, f"Błąd: {e}")
                )
                self.conn.commit()
                
            except smtplib.SMTPException as e:
                logger.error(f"Błąd SMTP: {e}")
                NotificationManager.get_instance().show_notification(
                    f"Błąd SMTP: {e}",
                    NotificationTypes.ERROR
                )
                
                # Zapisz log błędu
                cursor = self.conn.cursor()
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO email_logs (deposit_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                    (deposit_id.replace('D', ''), email, subject, current_date, f"Błąd: {e}")
                )
                self.conn.commit()
                
            except Exception as e:
                logger.error(f"Nieoczekiwany błąd podczas wysyłania emaila: {e}")
                NotificationManager.get_instance().show_notification(
                    f"Błąd podczas wysyłania emaila: {e}",
                    NotificationTypes.ERROR
                )
                
                # Zapisz log błędu
                cursor = self.conn.cursor()
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO email_logs (deposit_id, email, subject, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                    (deposit_id.replace('D', ''), email, subject, current_date, f"Błąd: {e}")
                )
                self.conn.commit()
            
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania emaila: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas przygotowania emaila: {e}",
                NotificationTypes.ERROR
            )

    def print_html_preview(self, html_content, title="Podgląd wydruku"):
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

    def get_email_template(self, template_key="general", template_data=None):
        """
        Pobiera szablon email z pliku konfiguracyjnego i opcjonalnie wypełnia go danymi.
        
        Args:
            template_key (str): Klucz szablonu email
            template_data (dict, optional): Dane do wypełnienia szablonu
        
        Returns:
            dict: Szablon email z opcjonalnie podstawionymi danymi
        """
        try:
            # Import potrzebnych modułów i zmiennych
            from utils.paths import CONFIG_DIR
            from ui.dialogs.settings_dialog import DEFAULT_EMAIL_TEMPLATES
            
            # Pobierz dane firmy
            settings = QSettings("TireDepositManager", "Settings")
            company_data = {
                "company_name": settings.value("company_name", "Serwis Opon"),
                "company_address": settings.value("company_address", ""),
                "company_phone": settings.value("company_phone", ""),
                "company_email": settings.value("company_email", ""),
                "company_website": settings.value("company_website", "")
            }
            
            # Ścieżka do pliku szablonów
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            # Wczytaj szablony
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                # Jeśli plik nie istnieje, użyj domyślnych szablonów
                templates = {"email": DEFAULT_EMAIL_TEMPLATES}
            
            # Wybierz szablon
            template = templates.get("email", {}).get(template_key, DEFAULT_EMAIL_TEMPLATES["general"])
            
            # Jeśli podano dane, podstaw je do szablonu
            if template_data:
                # Scal dane firmy z przekazanymi danymi
                full_data = {**company_data, **template_data}
                
                # Podstaw dane do szablonu
                subject = template.get("subject", "")
                body = template.get("body", "")
                
                # Podstaw zmienne w temacie
                for key, value in full_data.items():
                    subject = subject.replace("{" + key + "}", str(value))
                    body = body.replace("{" + key + "}", str(value))
                
                return {
                    "subject": subject,
                    "body": body
                }
            
            return template
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu email: {e}")
            return {
                "subject": "Informacja o depozycie opon",
                "body": "<html><body><p>Informacja o depozycie opon.</p></body></html>"
            }

    def get_label_template(self, template_name="default", template_data=None):
        """
        Pobiera szablon etykiety z pliku konfiguracyjnego i opcjonalnie wypełnia go danymi.
        
        Args:
            template_name (str): Nazwa szablonu etykiety
            template_data (dict, optional): Dane do wypełnienia szablonu
        
        Returns:
            str: Szablon etykiety z opcjonalnie podstawionymi danymi
        """
        try:
            # Import potrzebnych modułów i zmiennych
            from utils.paths import CONFIG_DIR
            from ui.dialogs.settings_dialog import DEFAULT_LABEL_TEMPLATE
            
            # Pobierz dane firmy
            settings = QSettings("TireDepositManager", "Settings")
            company_data = {
                "company_name": settings.value("company_name", "Serwis Opon"),
                "company_address": settings.value("company_address", ""),
                "company_phone": settings.value("company_phone", ""),
                "company_email": settings.value("company_email", ""),
                "company_website": settings.value("company_website", "")
            }
            
            # Ścieżka do pliku szablonów
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            # Wczytaj szablony
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                # Jeśli plik nie istnieje, użyj domyślnego szablonu
                templates = {"label": {"default": DEFAULT_LABEL_TEMPLATE}}
            
            # Wybierz szablon
            template = templates.get("label", {}).get(template_name, DEFAULT_LABEL_TEMPLATE)
            
            # Jeśli podano dane, podstaw je do szablonu
            if template_data:
                # Scal dane firmy z przekazanymi danymi
                full_data = {**company_data, **template_data}
                
                # Podstaw zmienne w szablonie
                for key, value in full_data.items():
                    template = template.replace("{" + key + "}", str(value))
            
            return template
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu etykiety: {e}")
            return """<!DOCTYPE html>
    <html>
    <head>
        <title>Etykieta depozytu</title>
        <style>
            body { font-family: Arial; }
        </style>
    </head>
    <body>
        <div>{deposit_id} - {client_name}</div>
    </body>
    </html>"""

    def get_receipt_template(self, template_name="default", template_data=None):
        """
        Pobiera szablon potwierdzenia z pliku konfiguracyjnego i opcjonalnie wypełnia go danymi.
        
        Args:
            template_name (str): Nazwa szablonu potwierdzenia
            template_data (dict, optional): Dane do wypełnienia szablonu
        
        Returns:
            str: Szablon potwierdzenia z opcjonalnie podstawionymi danymi
        """
        try:
            # Import potrzebnych modułów i zmiennych
            from utils.paths import CONFIG_DIR
            from ui.dialogs.settings_dialog import DEFAULT_RECEIPT_TEMPLATE
            
            # Pobierz dane firmy
            settings = QSettings("TireDepositManager", "Settings")
            company_data = {
                "company_name": settings.value("company_name", "Serwis Opon"),
                "company_address": settings.value("company_address", ""),
                "company_phone": settings.value("company_phone", ""),
                "company_email": settings.value("company_email", ""),
                "company_website": settings.value("company_website", "")
            }
            
            # Ścieżka do pliku szablonów
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            # Wczytaj szablony
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                # Jeśli plik nie istnieje, użyj domyślnego szablonu
                templates = {"receipt": {"default": DEFAULT_RECEIPT_TEMPLATE}}
            
            # Wybierz szablon
            template = templates.get("receipt", {}).get(template_name, DEFAULT_RECEIPT_TEMPLATE)
            
            # Jeśli podano dane, podstaw je do szablonu
            if template_data:
                # Scal dane firmy z przekazanymi danymi
                full_data = {**company_data, **template_data}
                
                # Podstaw zmienne w szablonie
                for key, value in full_data.items():
                    template = template.replace("{" + key + "}", str(value))
            
            return template
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu potwierdzenia: {e}")
            return """<!DOCTYPE html>
    <html>
    <head>
        <title>Potwierdzenie przyjęcia depozytu</title>
        <style>
            body { font-family: Arial; }
        </style>
    </head>
    <body>
        <h1>Potwierdzenie przyjęcia depozytu</h1>
        <p>ID: {deposit_id}</p>
        <p>Klient: {client_name}</p>
    </body>
    </html>"""

    def send_deposit_sms_notification(self, deposit_id):
        """Wysyła powiadomienie SMS dla depozytu."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane depozytu
            query = """
            SELECT 
                d.id,
                c.name AS client_name,
                c.phone_number,
                d.tire_size,
                d.tire_type,
                d.quantity,
                d.status,
                d.location,
                d.deposit_date,
                d.pickup_date,
                d.notes
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                d.id = ?
            """
            
            cursor.execute(query, (deposit_id,))
            deposit = cursor.fetchone()
            
            if not deposit:
                NotificationManager.get_instance().show_notification(
                    f"Nie znaleziono depozytu o ID {deposit_id}",
                    NotificationTypes.ERROR
                )
                return
            
            # Formatowanie ID depozytu
            deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
            
            # Sprawdź, czy klient ma numer telefonu
            if not deposit['phone_number']:
                NotificationManager.get_instance().show_notification(
                    f"Klient {deposit['client_name']} nie ma podanego numeru telefonu",
                    NotificationTypes.WARNING
                )
                return
            
            # Formatowanie dat
            deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            current_date = datetime.now().strftime("%d-%m-%Y")
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            
            # Przygotowanie danych do szablonu
            template_data = {
                "deposit_id": deposit_id_str,
                "client_name": deposit['client_name'],
                "phone_number": deposit['phone_number'],
                "tire_size": deposit['tire_size'],
                "tire_type": deposit['tire_type'],
                "quantity": str(deposit['quantity']),
                "location": deposit['location'],
                "deposit_date": deposit_date,
                "pickup_date": pickup_date,
                "status": deposit['status'],
                "notes": deposit['notes'] or "",
                "current_date": current_date,
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone,
            }
            
            # Wybierz odpowiedni szablon SMS w zależności od statusu
            template_key = "Przyjęcie depozytu"  # domyślny szablon
            status = deposit['status']
            
            if status == "Aktywny":
                template_key = "Przyjęcie depozytu"
            elif status == "Do odbioru":
                template_key = "Przypomnienie o odbiorze"
            elif status == "Zaległy":
                template_key = "Zaległy depozyt"
            
            # Pobierz szablon SMS
            sms_template = self.get_sms_template(template_key, "deposit")
            
            # Wypełnij szablon danymi
            sms_content = sms_template
            for key, value in template_data.items():
                sms_content = sms_content.replace("{" + key + "}", str(value))
            
            # Pokaż okno podglądu przed wysłaniem
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
            
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Podgląd wiadomości SMS")
            preview_dialog.setMinimumSize(500, 300)
            
            preview_layout = QVBoxLayout(preview_dialog)
            
            # Adresat
            to_layout = QHBoxLayout()
            to_layout.addWidget(QLabel("Do:"))
            to_field = QLineEdit(deposit['phone_number'])
            to_field.setReadOnly(False)  # Możliwość edycji numeru
            to_layout.addWidget(to_field)
            preview_layout.addLayout(to_layout)
            
            # Treść SMS
            content_label = QLabel("Treść (max 160 znaków):")
            preview_layout.addWidget(content_label)
            
            sms_edit = QTextEdit(sms_content)
            sms_edit.setMaximumHeight(150)
            preview_layout.addWidget(sms_edit)
            
            # Licznik znaków
            char_counter = QLabel(f"{len(sms_content)}/160 znaków")
            char_counter.setAlignment(Qt.AlignRight)
            preview_layout.addWidget(char_counter)
            
            # Aktualizacja licznika znaków
            def update_counter():
                text = sms_edit.toPlainText()
                count = len(text)
                sms_count = (count + 159) // 160  # Zaokrąglenie w górę
                
                if count > 160:
                    char_counter.setStyleSheet("color: orange;")
                elif count > 300:
                    char_counter.setStyleSheet("color: red;")
                else:
                    char_counter.setStyleSheet("")
                    
                char_counter.setText(f"{count}/160 znaków ({sms_count} SMS)")
            
            sms_edit.textChanged.connect(update_counter)
            update_counter()  # Aktualizacja początkowa
            
            # Przyciski
            buttons_layout = QHBoxLayout()
            cancel_btn = QPushButton("Anuluj")
            cancel_btn.clicked.connect(preview_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            buttons_layout.addStretch(1)
            
            send_btn = QPushButton("Wyślij SMS")
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
            send_btn.clicked.connect(lambda: self.confirm_send_sms(deposit_id_str, to_field.text(), sms_edit.toPlainText(), preview_dialog))
            buttons_layout.addWidget(send_btn)
            
            preview_layout.addLayout(buttons_layout)
            
            preview_dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania powiadomienia SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas przygotowania powiadomienia SMS: {e}",
                NotificationTypes.ERROR
            )

    def confirm_send_sms(self, deposit_id, phone_number, content, dialog):
        """Potwierdza wysłanie SMS-a."""
        try:
            # Pobierz ustawienia SMS
            settings = QSettings("TireDepositManager", "Settings")
            sms_api_key = settings.value("sms_api_key", "")
            sms_sender = settings.value("sms_sender", "")
            enable_sms = settings.value("enable_sms", False, type=bool)
            
            # Sprawdź czy mamy wszystkie potrzebne dane
            if not sms_api_key or not sms_sender or not enable_sms:
                QMessageBox.warning(
                    self,
                    "Brak konfiguracji SMS",
                    "Brakuje danych konfiguracyjnych serwisu SMS. Przejdź do Ustawienia > Komunikacja, aby skonfigurować wysyłanie SMS-ów."
                )
                return
            
            # Zamknij dialog podglądu
            dialog.accept()
            
            # Pokazujemy komunikat, że wysyłamy SMS
            NotificationManager.get_instance().show_notification(
                f"Wysyłanie SMS-a do {phone_number}...",
                NotificationTypes.INFO
            )
            
            # FAKTYCZNE WYSYŁANIE SMS-a
            try:
                from utils.sms_sender import SMSSender, format_phone_number
                
                # Formatuj numer telefonu (dodaj prefiks 48 jeśli potrzeba)
                formatted_phone = format_phone_number(phone_number)
                
                # Utwórz obiekt SMSSender
                sms_sender_obj = SMSSender(sms_api_key, sms_sender)
                
                # Wyślij SMS
                success, result_message = sms_sender_obj.send_sms(formatted_phone, content)
                
                if success:
                    # Powiadomienie o sukcesie
                    NotificationManager.get_instance().show_notification(
                        f"SMS został pomyślnie wysłany do {formatted_phone}",
                        NotificationTypes.SUCCESS
                    )
                    
                    # Zapisz informację o wysłanym SMS-ie w bazie danych
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS sms_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            deposit_id INTEGER,
                            phone_number TEXT,
                            content TEXT,
                            sent_date TEXT,
                            status TEXT,
                            FOREIGN KEY (deposit_id) REFERENCES deposits (id)
                        )
                    """)
                    
                    # Zapisz log wysłanego SMS-a
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "INSERT INTO sms_logs (deposit_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                        (deposit_id.replace('D', ''), formatted_phone, content, current_date, "Wysłany")
                    )
                    self.conn.commit()
                    
                    logger.info(f"Wysłano SMS dla depozytu {deposit_id} do {formatted_phone}")
                else:
                    raise Exception(result_message)
                    
            except Exception as e:
                logger.error(f"Błąd podczas wysyłania SMS-a: {e}")
                NotificationManager.get_instance().show_notification(
                    f"Błąd podczas wysyłania SMS-a: {e}",
                    NotificationTypes.ERROR
                )
                
                # Zapisz log błędu
                cursor = self.conn.cursor()
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO sms_logs (deposit_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                    (deposit_id.replace('D', ''), phone_number, content, current_date, f"Błąd: {e}")
                )
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania SMS-a: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas przygotowania SMS-a: {e}",
                NotificationTypes.ERROR
            )

    def get_sms_template(self, template_name="Przyjęcie depozytu", template_type="deposit", template_data=None):
        """
        Pobiera szablon SMS z pliku konfiguracyjnego.
        
        Args:
            template_name (str): Nazwa szablonu SMS
            template_type (str): Typ szablonu (deposit, order, service)
            template_data (dict, optional): Dane do wypełnienia szablonu
            
        Returns:
            str: Szablon SMS z opcjonalnie podstawionymi danymi
        """
        try:
            # Import potrzebnych modułów i zmiennych
            from utils.paths import CONFIG_DIR
            
            # Pobierz dane firmy
            settings = QSettings("TireDepositManager", "Settings")
            company_data = {
                "company_name": settings.value("company_name", "Serwis Opon"),
                "company_address": settings.value("company_address", ""),
                "company_phone": settings.value("company_phone", ""),
                "company_email": settings.value("company_email", ""),
                "company_website": settings.value("company_website", "")
            }
            
            # Ścieżka do pliku szablonów
            templates_file = os.path.join(CONFIG_DIR, "templates.json")
            
            # Domyślne szablony dla różnych typów
            default_templates = {
                "deposit": {
                    "Przyjęcie depozytu": "Dziekujemy za skorzystanie z naszych uslug. Przyjeto depozyt {deposit_id}. Ilosc opon: {quantity}. Odbior: {pickup_date}. {company_name}",
                    "Przypomnienie o odbiorze": "Przypominamy o odbiorze depozytu {deposit_id}. Opony czekaja na odbior. W razie pytan prosimy o kontakt: {company_phone}. {company_name}",
                    "Zaległy depozyt": "Depozyt {deposit_id} zalega w naszym magazynie. Prosimy o pilny kontakt: {company_phone}. {company_name}"
                }
            }
            
            # Wczytaj szablony
            template_dict_key = f"sms_{template_type}"
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    
                    # Sprawdź, czy szablon istnieje
                    if template_dict_key in templates and template_name in templates[template_dict_key]:
                        template = templates[template_dict_key][template_name]
                    else:
                        # Jeśli nie istnieje, użyj domyślnego
                        template = default_templates.get(template_type, {}).get(template_name, "")
            else:
                # Jeśli plik nie istnieje, użyj domyślnego szablonu
                template = default_templates.get(template_type, {}).get(template_name, "")
            
            # Jeśli podano dane, podstaw je do szablonu
            if template_data:
                # Scal dane firmy z przekazanymi danymi
                full_data = {**company_data, **template_data}
                
                # Podstaw zmienne w szablonie
                for key, value in full_data.items():
                    template = template.replace("{" + key + "}", str(value))
                    
            return template
        
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu SMS: {e}")
            return f"Depozyt {{{template_type}_id}}. {company_name}"  # Prosty domyślny szablon w przypadku błędu

    def send_sms_notifications(self):
        """Wysyła powiadomienia SMS do klientów."""
        try:
            # Sprawdź czy funkcja SMS jest skonfigurowana
            settings = QSettings("TireDepositManager", "Settings")
            sms_api_key = settings.value("sms_api_key", "")
            sms_sender = settings.value("sms_sender", "")
            enable_sms = settings.value("enable_sms", False, type=bool)
            
            if not sms_api_key or not sms_sender or not enable_sms:
                QMessageBox.warning(
                    self,
                    "Brak konfiguracji SMS",
                    "Brakuje danych konfiguracyjnych serwisu SMS. Przejdź do Ustawienia > Komunikacja, aby skonfigurować wysyłanie SMS-ów."
                )
                return
                
            # W zależności od aktywnej zakładki, użyj odpowiedniej tabeli
            if self.current_tab_index == 0:
                table = self.active_deposits_table
                filter_status = self.current_status_filter
            elif self.current_tab_index == 1:
                table = self.history_deposits_table
                filter_status = "Wydany"
            elif self.current_tab_index == 2:
                table = self.pending_deposits_table
                filter_status = "Do odbioru"
            else:
                return
                
            # Wybierz domyślny szablon w zależności od zakładki
            default_template = "Przypomnienie o odbiorze"
            if self.current_tab_index == 0 and filter_status == "Aktywny":
                default_template = "Przyjęcie depozytu"
            elif self.current_tab_index == 0 and filter_status == "Zaległy":
                default_template = "Zaległy depozyt"
            
            # Pobierz listę aktywnych depozytów
            cursor = self.conn.cursor()
            
            # Buduj zapytanie w zależności od aktualnej zakładki i filtrów
            query = """
            SELECT 
                d.id,
                c.name AS client_name,
                c.phone_number,
                d.tire_size,
                d.tire_type,
                d.quantity,
                d.status,
                d.location,
                d.deposit_date,
                d.pickup_date,
                d.notes
            FROM 
                deposits d
            JOIN 
                clients c ON d.client_id = c.id
            WHERE 
                c.phone_number IS NOT NULL AND c.phone_number != ''
            """
            
            params = []
            
            # Dodaj filtr statusu jeśli potrzeba
            if filter_status != "Wszystkie" and self.current_tab_index == 0:
                query += " AND d.status = ?"
                params.append(filter_status)
            elif self.current_tab_index == 1:
                query += " AND d.status = 'Wydany'"
            elif self.current_tab_index == 2:
                query += " AND d.status = 'Do odbioru'"
                
            # Wykonaj zapytanie
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            deposits = cursor.fetchall()
            
            # Jeśli nie ma depozytów z numerami telefonów
            if not deposits:
                QMessageBox.information(
                    self,
                    "Brak depozytów",
                    "Nie znaleziono depozytów z przypisanymi numerami telefonów."
                )
                return
                
            # Dialog konfiguracji masowej wysyłki SMS
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QCheckBox, QListWidget, QListWidgetItem, QApplication
            
            config_dialog = QDialog(self)
            config_dialog.setWindowTitle("Wysyłanie powiadomień SMS")
            config_dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout(config_dialog)
            
            # Wybór szablonu
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel("Wybierz szablon SMS:"))
            
            template_combo = QComboBox()
            template_combo.addItems(["Przyjęcie depozytu", "Przypomnienie o odbiorze", "Zaległy depozyt"])
            # Ustaw domyślny szablon w zależności od statusu
            index = template_combo.findText(default_template)
            if index >= 0:
                template_combo.setCurrentIndex(index)
            template_layout.addWidget(template_combo, 1)
            
            layout.addLayout(template_layout)
            
            # Treść wiadomości
            content_label = QLabel("Treść wiadomości:")
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
            
            # Aktualizacja szablonu przy zmianie wyboru
            def update_template():
                template_name = template_combo.currentText()
                template_content = self.get_sms_template(template_name, "deposit")
                message_edit.setPlainText(template_content)
                update_counter()
                
            template_combo.currentIndexChanged.connect(update_template)
            message_edit.textChanged.connect(update_counter)
            
            # Załaduj początkowy szablon
            update_template()
            
            # Lista depozytów do wysłania
            deposits_label = QLabel(f"Znaleziono {len(deposits)} depozytów z numerami telefonów:")
            layout.addWidget(deposits_label)
            
            deposits_list = QListWidget()
            deposits_list.setSelectionMode(QListWidget.ExtendedSelection)
            layout.addWidget(deposits_list)
            
            # Wypełnij listę depozytów
            for deposit in deposits:
                deposit_id = f"D{str(deposit['id']).zfill(3)}"
                status = deposit['status']
                pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                
                item = QListWidgetItem(f"{deposit_id} - {deposit['client_name']} - {deposit['phone_number']} - {status} - Odbiór: {pickup_date}")
                item.setData(Qt.UserRole, deposit['id'])
                deposits_list.addItem(item)
                item.setCheckState(Qt.Checked)  # Domyślnie zaznaczone
                
            # Opcje
            options_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("Zaznacz wszystkie")
            select_all_btn.clicked.connect(lambda: self.select_all_items(deposits_list, True))
            options_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton("Odznacz wszystkie")
            deselect_all_btn.clicked.connect(lambda: self.select_all_items(deposits_list, False))
            options_layout.addWidget(deselect_all_btn)
            
            options_layout.addStretch()
            
            layout.addLayout(options_layout)
            
            # Przyciski
            buttons_layout = QHBoxLayout()
            
            cancel_btn = QPushButton("Anuluj")
            cancel_btn.clicked.connect(config_dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            buttons_layout.addStretch()
            
            preview_btn = QPushButton("Podgląd")
            preview_btn.clicked.connect(lambda: self.preview_mass_sms(message_edit.toPlainText(), deposits))
            buttons_layout.addWidget(preview_btn)
            
            send_btn = QPushButton("Wyślij powiadomienia")
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
                
                # Zbierz zaznaczone depozyty
                for i in range(deposits_list.count()):
                    item = deposits_list.item(i)
                    if item.checkState() == Qt.Checked:
                        deposit_id = item.data(Qt.UserRole)
                        for deposit in deposits:
                            if deposit['id'] == deposit_id:
                                selected_items.append(deposit)
                                break
                
                if not selected_items:
                    QMessageBox.warning(
                        self,
                        "Brak zaznaczonych depozytów",
                        "Zaznacz przynajmniej jeden depozyt do wysłania powiadomienia."
                    )
                    return
                    
                # Potwierdź wysyłkę
                reply = QMessageBox.question(
                    self,
                    "Potwierdź wysyłkę",
                    f"Czy na pewno chcesz wysłać {len(selected_items)} powiadomień SMS?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
                    
                # Zamknij dialog konfiguracji
                config_dialog.accept()
                
                # Inicjalizuj SMSSender
                from utils.sms_sender import SMSSender, format_phone_number
                sms_sender_obj = SMSSender(sms_api_key, sms_sender)
                
                # Pobierz dane firmy
                company_name = settings.value("company_name", "Serwis Opon")
                company_address = settings.value("company_address", "")
                company_phone = settings.value("company_phone", "")
                
                # Liczniki
                success_count = 0
                fail_count = 0
                
                # Pokaż dialog postępu
                progress_dialog = QDialog(self)
                progress_dialog.setWindowTitle("Wysyłanie SMS-ów")
                progress_dialog.setMinimumWidth(400)
                
                progress_layout = QVBoxLayout(progress_dialog)
                progress_layout.addWidget(QLabel(f"Wysyłanie {len(selected_items)} powiadomień SMS..."))
                
                progress_label = QLabel("Przygotowywanie...")
                progress_layout.addWidget(progress_label)
                
                progress_btn = QPushButton("Anuluj")
                progress_btn.clicked.connect(progress_dialog.reject)
                progress_layout.addWidget(progress_btn)
                
                progress_dialog.show()
                
                # Pętla wysyłania
                for i, deposit in enumerate(selected_items):
                    try:
                        # Aktualizacja etykiety postępu
                        progress_label.setText(f"Wysyłanie ({i+1}/{len(selected_items)}): {deposit['client_name']}")
                        QApplication.processEvents()  # Odśwież UI
                        
                        if progress_dialog.result() == QDialog.Rejected:
                            break  # Anulowano
                        
                        # Formatowanie ID depozytu
                        deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
                        
                        # Formatowanie dat
                        deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                        pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
                        
                        # Dane do szablonu
                        template_data = {
                            "deposit_id": deposit_id_str,
                            "client_name": deposit['client_name'],
                            "phone_number": deposit['phone_number'],
                            "tire_size": deposit['tire_size'],
                            "tire_type": deposit['tire_type'],
                            "quantity": str(deposit['quantity']),
                            "location": deposit['location'],
                            "deposit_date": deposit_date,
                            "pickup_date": pickup_date,
                            "status": deposit['status'],
                            "company_name": company_name,
                            "company_address": company_address,
                            "company_phone": company_phone
                        }
                        
                        # Wypełnij szablon danymi
                        message_content = message_edit.toPlainText()
                        for key, value in template_data.items():
                            message_content = message_content.replace("{" + key + "}", str(value))
                        
                        # Wyślij SMS
                        formatted_phone = format_phone_number(deposit['phone_number'])
                        success, result_message = sms_sender_obj.send_sms(formatted_phone, message_content)
                        
                        # Zapisz log
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS sms_logs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                deposit_id INTEGER,
                                phone_number TEXT,
                                content TEXT,
                                sent_date TEXT,
                                status TEXT,
                                FOREIGN KEY (deposit_id) REFERENCES deposits (id)
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
                            "INSERT INTO sms_logs (deposit_id, phone_number, content, sent_date, status) VALUES (?, ?, ?, ?, ?)",
                            (deposit['id'], formatted_phone, message_content, current_date, status)
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
                    "Podsumowanie wysyłki SMS",
                    f"Wysłano: {success_count} powiadomień\n"
                    f"Nieudane: {fail_count} powiadomień\n\n"
                    f"Szczegóły można znaleźć w logach systemu."
                )
                
                # Odśwież statystyki
                self.load_statistics()
                
            send_btn.clicked.connect(send_mass_sms)
            buttons_layout.addWidget(send_btn)
            
            layout.addLayout(buttons_layout)
            
            # Wyświetl dialog
            config_dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas przygotowania masowej wysyłki SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas przygotowania masowej wysyłki SMS: {e}",
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

    def preview_mass_sms(self, template, deposits):
        """Wyświetla podgląd SMS-a z podstawieniem danych przykładowego depozytu."""
        try:
            if not deposits:
                return
                
            # Pobierz pierwszy depozyt jako przykład
            deposit = deposits[0]
            
            # Formatowanie ID depozytu
            deposit_id_str = f"D{str(deposit['id']).zfill(3)}"
            
            # Formatowanie dat
            deposit_date = datetime.strptime(deposit['deposit_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            pickup_date = datetime.strptime(deposit['pickup_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
            
            # Pobierz dane firmy z ustawień
            settings = QSettings("TireDepositManager", "Settings")
            company_name = settings.value("company_name", "Serwis Opon")
            company_address = settings.value("company_address", "")
            company_phone = settings.value("company_phone", "")
            
            # Dane do szablonu
            template_data = {
                "deposit_id": deposit_id_str,
                "client_name": deposit['client_name'],
                "phone_number": deposit['phone_number'],
                "tire_size": deposit['tire_size'],
                "tire_type": deposit['tire_type'],
                "quantity": str(deposit['quantity']),
                "location": deposit['location'],
                "deposit_date": deposit_date,
                "pickup_date": pickup_date,
                "status": deposit['status'],
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone
            }
            
            # Wypełnij szablon danymi
            message_content = template
            for key, value in template_data.items():
                message_content = message_content.replace("{" + key + "}", str(value))
            
            # Wyświetl podgląd
            QMessageBox.information(
                self,
                "Podgląd SMS-a (przykład)",
                f"Dla depozytu: {deposit_id_str} - {deposit['client_name']}\n\n"
                f"Treść: {message_content}\n\n"
                f"Długość: {len(message_content)} znaków\n"
                f"SMS-ów: {(len(message_content) + 159) // 160}"
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania podglądu SMS: {e}")
            NotificationManager.get_instance().show_notification(
                f"Błąd podczas generowania podglądu SMS: {e}",
                NotificationTypes.ERROR
            )