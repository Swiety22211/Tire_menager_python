#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka zarządzania finansami w aplikacji.
Umożliwia przeglądanie i wprowadzanie danych finansowych, generowanie raportów oraz zarządzanie wydatkami.
Zawiera funkcje wprowadzania stanu kasy, rejestrowania wydatków oraz analizy finansowej.
"""

import os
import logging
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
import calendar
import locale

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, 
    QPushButton, QLineEdit, QLabel, QComboBox, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox, QMenu,
    QTabWidget, QSplitter, QTextEdit, QSpinBox, QDoubleSpinBox, QSpacerItem, 
    QSizePolicy, QDialog, QFileDialog, QGroupBox, QScrollArea, QToolButton,
    QCalendarWidget
)
from PySide6.QtCore import Qt, QDate, QDateTime, Signal, Slot, QObject, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QPen, QBrush, QPalette, QFont
try:
    from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis, QBarSeries, QBarSet, QBarCategoryAxis
except ImportError:
    logger.warning("QtCharts not available. Chart functionality will be disabled.")

from utils.paths import ICONS_DIR
from utils.settings import Settings
from ui.notifications import NotificationManager, NotificationTypes
from utils.i18n import _  # Funkcja do obsługi lokalizacji

# Logger
logger = logging.getLogger("TireDepositManager")

# Wspólne style CSS - zaczerpnięte z clients_tab.py i dostosowane
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
    "STAT_CARD_RED": """
        QFrame#statCard {
            background-color: #e03131;
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
    "FORM_GROUP": """
        QGroupBox {
            border: 1px solid #444444;
            border-radius: 5px;
            margin-top: 15px;
            font-weight: bold;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            color: white;
            padding: 0 5px;
        }
    """,
    "DATE_EDIT": """
        QDateEdit {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        QDateEdit::drop-down {
            border: none;
            padding-right: 10px;
        }
        QDateEdit QAbstractItemView {
            background-color: #343a40;
            color: white;
            border: 1px solid #1a1d21;
            selection-background-color: #4dabf7;
        }
    """,
    "DOUBLE_SPIN_BOX": """
        QDoubleSpinBox {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 25px;
        }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
            width: 16px;
            border: none;
            background-color: #4dabf7;
            border-radius: 3px;
        }
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #339af0;
        }
    """,
    "LINE_EDIT": """
        QLineEdit {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            min-height: 25px;
        }
        QLineEdit:focus {
            border: 1px solid #4dabf7;
        }
    """,
    "TEXT_EDIT": """
        QTextEdit {
            background-color: #343a40;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        QTextEdit:focus {
            border: 1px solid #4dabf7;
        }
    """,
    "POSITIVE_VALUE": """
        QLabel {
            color: #40c057;
            font-weight: bold;
        }
    """,
    "NEGATIVE_VALUE": """
        QLabel {
            color: #fa5252;
            font-weight: bold;
        }
    """
}

class ExpenseDialog(QDialog):
    """Dialog do dodawania lub edycji wydatku."""
    
    def __init__(self, conn, parent=None, expense_id=None):
        super().__init__(parent)
        self.conn = conn
        self.expense_id = expense_id
        
        self.setWindowTitle(_("Dodaj wydatek") if expense_id is None else _("Edytuj wydatek"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        self.setup_ui()
        
        if expense_id:
            self.load_expense(expense_id)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formularz
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Data
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setStyleSheet(STYLES["DATE_EDIT"])
        form_layout.addRow(_("Data:"), self.date_edit)
        
        # Kategoria
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            _("Czynsz"), _("Media"), _("Materiały"), _("Usługi"), 
            _("Wynagrodzenia"), _("Podatki"), _("Marketing"), 
            _("Naprawy"), _("Księgowość"), _("Inne")
        ])
        self.category_combo.setStyleSheet(STYLES["COMBO_BOX"])
        form_layout.addRow(_("Kategoria:"), self.category_combo)
        
        # Opis
        self.description_edit = QLineEdit()
        self.description_edit.setStyleSheet(STYLES["LINE_EDIT"])
        self.description_edit.setPlaceholderText(_("Podaj opis wydatku"))
        form_layout.addRow(_("Opis:"), self.description_edit)
        
        # Kwota
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setSuffix(" zł")
        self.amount_spin.setStyleSheet(STYLES["DOUBLE_SPIN_BOX"])
        form_layout.addRow(_("Kwota [PLN]:"), self.amount_spin)
        
        # Metoda płatności
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            _("Gotówka"), _("Przelew"), _("Karta"), _("BLIK"), _("Inne")
        ])
        self.payment_method_combo.setStyleSheet(STYLES["COMBO_BOX"])
        form_layout.addRow(_("Metoda płatności:"), self.payment_method_combo)
        
        # Uwagi
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(STYLES["TEXT_EDIT"])
        self.notes_edit.setPlaceholderText(_("Dodatkowe uwagi"))
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow(_("Uwagi:"), self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Przyciski
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton(_("Anuluj"))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(STYLES["UTILITY_BUTTON"])
        
        self.save_button = QPushButton(_("Zapisz wydatek"))
        self.save_button.clicked.connect(self.save_expense)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def load_expense(self, expense_id):
        """Ładuje dane wydatku do edycji."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT date, category, description, amount, payment_method, notes
                FROM expenses
                WHERE id = ?
            """, (expense_id,))
            
            expense = cursor.fetchone()
            if expense:
                date, category, description, amount, payment_method, notes = expense
                
                # Ustawienie wartości w formularzu
                self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
                
                # Ustawienie kategorii
                index = self.category_combo.findText(category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
                    
                self.description_edit.setText(description)
                self.amount_spin.setValue(amount)
                
                # Ustawienie metody płatności
                index = self.payment_method_combo.findText(payment_method)
                if index >= 0:
                    self.payment_method_combo.setCurrentIndex(index)
                    
                self.notes_edit.setText(notes or "")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych wydatku: {e}")
            QMessageBox.critical(
                self,
                _("Błąd"),
                _("Nie można załadować danych wydatku: {}").format(str(e))
            )
    
    def save_expense(self):
        """Zapisuje dane wydatku."""
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            category = self.category_combo.currentText()
            description = self.description_edit.text().strip()
            amount = self.amount_spin.value()
            payment_method = self.payment_method_combo.currentText()
            notes = self.notes_edit.toPlainText()
            
            if not description:
                QMessageBox.warning(
                    self,
                    _("Brak opisu"),
                    _("Proszę podać opis wydatku.")
                )
                return
            
            if amount <= 0:
                QMessageBox.warning(
                    self,
                    _("Nieprawidłowa kwota"),
                    _("Kwota wydatku musi być większa od zera.")
                )
                return
            
            cursor = self.conn.cursor()
            
            if self.expense_id:
                # Aktualizacja istniejącego wydatku
                cursor.execute("""
                    UPDATE expenses
                    SET date = ?, category = ?, description = ?, amount = ?, payment_method = ?, notes = ?
                    WHERE id = ?
                """, (date, category, description, amount, payment_method, notes, self.expense_id))
                
                message = _("Zaktualizowano dane wydatku")
            else:
                # Dodanie nowego wydatku
                cursor.execute("""
                    INSERT INTO expenses (date, category, description, amount, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date, category, description, amount, payment_method, notes))
                
                message = _("Dodano nowy wydatek")
            
            self.conn.commit()
            logger.info("Zainicjalizowano tabele finansowe w bazie danych")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas inicjalizacji tabel finansowych: {e}")
            
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        # Główny layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Nagłówek z tytułem
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Tytuł zakładki finansów
        title_label = QLabel(_("Zarządzanie Finansami"))
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)
        
        # Elastyczny odstęp
        header_layout.addStretch(1)
        
        # Przycisk eksportu raportu
        self.export_button = QPushButton("📊 " + _("Generuj raport"))
        self.export_button.setObjectName("exportButton")
        self.export_button.setFixedHeight(40)
        self.export_button.setMinimumWidth(150)
        self.export_button.setStyleSheet("""
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
        """)
        self.export_button.clicked.connect(self.export_report)
        header_layout.addWidget(self.export_button)
        
        main_layout.addLayout(header_layout)
        
        # Grupa filtrów
        self.create_filter_section(main_layout)
        
        # Zakładki dla różnych sekcji finansowych
        self.finances_tabs = QTabWidget()
        self.finances_tabs.setStyleSheet(STYLES["TABS"])
        
        # Zakładka raporty dobowe
        self.daily_report_tab = QWidget()
        self.setup_daily_report_tab()
        self.finances_tabs.addTab(self.daily_report_tab, _("Raporty dobowe"))
        
        # Zakładka wydatki miesięczne
        self.monthly_expenses_tab = QWidget()
        self.setup_monthly_expenses_tab()
        self.finances_tabs.addTab(self.monthly_expenses_tab, _("Wydatki miesięczne"))
        
        # Zakładka analiza
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.finances_tabs.addTab(self.analysis_tab, _("Analiza finansowa"))
        
        main_layout.addWidget(self.finances_tabs)
        
    def create_filter_section(self, main_layout):
        """Tworzy panel filtrów."""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_frame.setStyleSheet("""
            QFrame#filterFrame {
                background-color: #2c3034;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        filter_frame.setMinimumHeight(90)
        filter_frame.setMaximumHeight(90)
        
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 10, 15, 10)
        
        # Etykieta filtrowania
        filter_title = QLabel(_("Filtruj okres:"))
        filter_title.setStyleSheet("color: white; font-weight: bold;")
        filter_layout.addWidget(filter_title)
        
        # Przyciski filtrów okresów
        self.period_buttons = {}
        
        for period in ["Dzisiaj", "Tydzień", "Miesiąc", "Rok", "Niestandardowy"]:
            btn = QPushButton(_(period))
            btn.setProperty("period", period)
            btn.setCheckable(True)
            btn.setMinimumWidth(100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #343a40;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #4dabf7;
                }
                QPushButton:checked {
                    background-color: #4dabf7;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(self.change_period_filter)
            filter_layout.addWidget(btn)
            self.period_buttons[period] = btn
        
        # Pole wyboru daty dla filtra niestandardowego
        date_layout = QHBoxLayout()
        
        from_label = QLabel(_("Od:"))
        from_label.setStyleSheet("color: white;")
        date_layout.addWidget(from_label)
        
        self.from_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.from_date_edit.setStyleSheet(STYLES["DATE_EDIT"])
        self.from_date_edit.dateChanged.connect(self.custom_date_changed)
        date_layout.addWidget(self.from_date_edit)
        
        to_label = QLabel(_("Do:"))
        to_label.setStyleSheet("color: white;")
        date_layout.addWidget(to_label)
        
        self.to_date_edit = QDateEdit(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.to_date_edit.setStyleSheet(STYLES["DATE_EDIT"])
        self.to_date_edit.dateChanged.connect(self.custom_date_changed)
        date_layout.addWidget(self.to_date_edit)
        
        filter_layout.addLayout(date_layout)
        
        # Przycisk filtrowania
        self.filter_button = QPushButton(_("Filtruj"))
        self.filter_button.setObjectName("filterButton")
        self.filter_button.setStyleSheet(STYLES["FILTER_BUTTON"])
        self.filter_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_button)
        
        main_layout.addWidget(filter_frame)
        
        # Domyślnie wybierz miesiąc
        self.period_buttons["Miesiąc"].setChecked(True)
        
    def setup_daily_report_tab(self):
        """Konfiguruje zakładkę raportów dobowych."""
        layout = QVBoxLayout(self.daily_report_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)
        
        # Sekcja wprowadzania stanu kasy
        cash_input_section = QGroupBox(_("Wprowadź stan kasy na koniec dnia"))
        cash_input_section.setStyleSheet(STYLES["FORM_GROUP"])
        cash_input_layout = QVBoxLayout(cash_input_section)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)
        
        # Data
        date_layout = QHBoxLayout()
        date_label = QLabel(_("Data:"))
        date_layout.addWidget(date_label)
        
        self.cash_date_edit = QDateEdit(QDate.currentDate())
        self.cash_date_edit.setCalendarPopup(True)
        self.cash_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.cash_date_edit.setStyleSheet(STYLES["DATE_EDIT"])
        date_layout.addWidget(self.cash_date_edit)
        
        form_layout.addLayout(date_layout)
        
        # Stan kasy
        amount_layout = QHBoxLayout()
        amount_label = QLabel(_("Stan kasy [PLN]:"))
        amount_layout.addWidget(amount_label)
        
        self.cash_amount_spin = QDoubleSpinBox()
        self.cash_amount_spin.setRange(0, 999999.99)
        self.cash_amount_spin.setDecimals(2)
        self.cash_amount_spin.setValue(0.00)
        self.cash_amount_spin.setSuffix(" zł")
        self.cash_amount_spin.setStyleSheet(STYLES["DOUBLE_SPIN_BOX"])
        amount_layout.addWidget(self.cash_amount_spin)
        
        form_layout.addLayout(amount_layout)
        
        # Komentarz
        comment_layout = QHBoxLayout()
        comment_label = QLabel(_("Komentarz:"))
        comment_layout.addWidget(comment_label)
        
        self.cash_comment_edit = QLineEdit()
        self.cash_comment_edit.setStyleSheet(STYLES["LINE_EDIT"])
        self.cash_comment_edit.setPlaceholderText(_("Np. dzień zwykły - sezon wymiany opon"))
        comment_layout.addWidget(self.cash_comment_edit)
        
        form_layout.addLayout(comment_layout)
        
        # Przycisk zapisu
        self.save_cash_button = QPushButton(_("Zapisz stan kasy"))
        self.save_cash_button.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        self.save_cash_button.clicked.connect(self.add_cash_register_entry)
        form_layout.addWidget(self.save_cash_button)
        
        cash_input_layout.addLayout(form_layout)
        layout.addWidget(cash_input_section)
        
        # Sekcja porównania
        comparison_section = QGroupBox(_("Porównanie"))
        comparison_section.setStyleSheet(STYLES["FORM_GROUP"])
        comparison_layout = QHBoxLayout(comparison_section)
        
        # Obecny stan kasy
        current_layout = QVBoxLayout()
        current_title = QLabel(_("Stan kasy (aktualny):"))
        current_title.setStyleSheet("color: white; font-weight: bold;")
        current_layout.addWidget(current_title)
        
        self.current_cash_label = QLabel("0.00 zł")
        self.current_cash_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        current_layout.addWidget(self.current_cash_label, alignment=Qt.AlignCenter)
        comparison_layout.addLayout(current_layout)
        
        # Stan kasy z poprzedniego dnia
        previous_layout = QVBoxLayout()
        previous_title = QLabel(_("Stan kasy (poprzedni):"))
        previous_title.setStyleSheet("color: white; font-weight: bold;")
        previous_layout.addWidget(previous_title)
        
        self.previous_cash_label = QLabel("0.00 zł")
        self.previous_cash_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        previous_layout.addWidget(self.previous_cash_label, alignment=Qt.AlignCenter)
        comparison_layout.addLayout(previous_layout)
        
        # Różnica
        difference_layout = QVBoxLayout()
        difference_title = QLabel(_("Różnica:"))
        difference_title.setStyleSheet("color: white; font-weight: bold;")
        difference_layout.addWidget(difference_title)
        
        self.difference_cash_label = QLabel("+0.00 zł (0%)")
        self.difference_cash_label.setStyleSheet("color: #40c057; font-size: 24px; font-weight: bold;")
        difference_layout.addWidget(self.difference_cash_label, alignment=Qt.AlignCenter)
        comparison_layout.addLayout(difference_layout)
        
        layout.addWidget(comparison_section)
        
        # Tabela stanów kasy
        history_label = QLabel(_("Historia stanów kasy:"))
        history_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(history_label)
        
        self.cash_history_table = QTableWidget()
        self.cash_history_table.setColumnCount(4)
        self.cash_history_table.setHorizontalHeaderLabels([
            _("Data"), _("Stan kasy [PLN]"), _("Różnica"), _("Komentarz")
        ])
        self.cash_history_table.setStyleSheet(STYLES["TABLE_WIDGET"])
        self.cash_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cash_history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.cash_history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cash_history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cash_history_table.setAlternatingRowColors(True)
        self.cash_history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.cash_history_table)
        
    def setup_monthly_expenses_tab(self):
        """Konfiguruje zakładkę wydatków miesięcznych."""
        layout = QVBoxLayout(self.monthly_expenses_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)
        
        # Nagłówek z wyborem miesiąca
        header_layout = QHBoxLayout()
        
        month_label = QLabel(_("Miesiąc:"))
        month_label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(month_label)
        
        self.month_combo = QComboBox()
        # Dodaj nazwy miesięcy
        months = [
            _("Styczeń"), _("Luty"), _("Marzec"), _("Kwiecień"), _("Maj"), _("Czerwiec"),
            _("Lipiec"), _("Sierpień"), _("Wrzesień"), _("Październik"), _("Listopad"), _("Grudzień")
        ]
        self.month_combo.addItems(months)
        current_month =
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                message,
                NotificationTypes.SUCCESS,
                duration=3000
            )
            
            # Zamknięcie dialogu
            self.accept()
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wydatku: {e}")
            self.conn.rollback()
            
            QMessageBox.critical(
                self,
                _("Błąd"),
                _("Wystąpił błąd podczas zapisywania wydatku: {}").format(str(e))
            )


class FinancesTab(QWidget):
    """
    Zakładka zarządzania finansami w aplikacji.
    Umożliwia przeglądanie i wprowadzanie danych finansowych oraz zarządzanie wydatkami.
    """
    
    # Sygnały
    expense_added = Signal(int)  # Emitowany po dodaniu wydatku (parametr: expense_id)
    expense_updated = Signal(int)  # Emitowany po aktualizacji wydatku (parametr: expense_id)
    expense_deleted = Signal(int)  # Emitowany po usunięciu wydatku (parametr: expense_id)
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki finansów.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        self.initialize_database()
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Załadowanie danych finansowych
        self.load_data()
        
    def initialize_database(self):
        """Inicjalizuje tabele bazy danych potrzebne do pracy z finansami."""
        try:
            cursor = self.conn.cursor()
            
            # Tabela stanów kasy
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_register (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    amount REAL NOT NULL,
                    comment TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Tabela wydatków
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Tabela przychodów
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            self.conn.commit()
            
    """Dialog do wprowadzania stanu kasy na koniec dnia."""
    
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle(_("Wprowadź stan kasy"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formularz
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Data
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setStyleSheet(STYLES["DATE_EDIT"])
        form_layout.addRow(_("Data:"), self.date_edit)
        
        # Stan kasy
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setSuffix(" zł")
        self.amount_spin.setStyleSheet(STYLES["DOUBLE_SPIN_BOX"])
        form_layout.addRow(_("Stan kasy [PLN]:"), self.amount_spin)
        
        # Komentarz
        self.comment_edit = QTextEdit()
        self.comment_edit.setStyleSheet(STYLES["TEXT_EDIT"])
        self.comment_edit.setPlaceholderText(_("Dodatkowe uwagi - np. sezon wymiany opon"))
        form_layout.addRow(_("Komentarz:"), self.comment_edit)
        
        layout.addLayout(form_layout)
        
        # Przyciski
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton(_("Anuluj"))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(STYLES["UTILITY_BUTTON"])
        
        self.save_button = QPushButton(_("Zapisz stan kasy"))
        self.save_button.clicked.connect(self.save_cash_register)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def save_cash_register(self):
        """Zapisuje wprowadzony stan kasy do bazy danych."""
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            amount = self.amount_spin.value()
            comment = self.comment_edit.toPlainText()
            
            cursor = self.conn.cursor()
            
            # Sprawdź, czy już istnieje wpis na ten dzień
            cursor.execute("""
                SELECT id FROM cash_register
                WHERE date = ?
            """, (date,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Aktualizacja istniejącego wpisu
                cursor.execute("""
                    UPDATE cash_register
                    SET amount = ?, comment = ?
                    WHERE date = ?
                """, (amount, comment, date))
                
                message = _("Zaktualizowano stan kasy na dzień {}").format(
                    self.date_edit.date().toString("dd-MM-yyyy")
                )
            else:
                # Dodanie nowego wpisu
                cursor.execute("""
                    INSERT INTO cash_register (date, amount, comment)
                    VALUES (?, ?, ?)
                """, (date, amount, comment))
                
                message = _("Zapisano stan kasy na dzień {}").format(
                    self.date_edit.date().toString("dd-MM-yyyy")
                )
            
            self.conn.commit()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                message,
                NotificationTypes.SUCCESS,
                duration=3000
            )
            
            # Zamknięcie dialogu
            self.accept()
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania stanu kasy: {e}")
            self.conn.rollback()
            
            QMessageBox.critical(
                self,
                _("Błąd"),
                _("Wystąpił błąd podczas zapisywania stanu kasy: {}").format(str(e))
            )

            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
            
            # Akcje menu
            edit_action = menu.addAction(f"✏️ {_('Edytuj wydatek')}")
            menu.addSeparator()
            delete_action = menu.addAction(f"🗑️ {_('Usuń wydatek')}")
            
            # Wyświetlenie menu i przetwarzanie wybranej akcji
            action = menu.exec(self.expenses_table.mapToGlobal(position))
            
            if action == edit_action:
                self.edit_expense(expense_id)
            elif action == delete_action:
                self.delete_expense(expense_id)
        
        def export_report(self):
            """Eksportuje raport finansowy do pliku."""
            try:
                # Menu wyboru formatu eksportu
                menu = QMenu(self)
                menu.setStyleSheet(STYLES["MENU"])
                
                # Akcje menu
                csv_action = menu.addAction(f"📊 {_('Eksportuj do CSV')}")
                excel_action = menu.addAction(f"📝 {_('Eksportuj do Excel')}")
                pdf_action = menu.addAction(f"📄 {_('Eksportuj do PDF')}")
                
                # Wyświetlenie menu
                action = menu.exec(self.export_button.mapToGlobal(self.export_button.rect().bottomRight()))
                
                if action == csv_action:
                    self.export_to_csv()
                elif action == excel_action:
                    self.export_to_excel()
                elif action == pdf_action:
                    self.export_to_pdf()
                    
            except Exception as e:
                logger.error(f"Błąd podczas eksportu raportu: {e}")
                
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas eksportu raportu: {}").format(str(e))
                )
        
        def export_to_csv(self):
            """Eksportuje dane finansowe do pliku CSV."""
            try:
                # Wybór pliku do zapisu
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    _("Zapisz raport jako CSV"),
                    f"raport_finansowy_{datetime.now().strftime('%Y%m%d')}.csv",
                    "CSV (*.csv)"
                )
                
                if not file_path:
                    return
                
                # Pobierz dane z bazy
                cursor = self.conn.cursor()
                
                # Ustal zakres dat
                from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
                to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
                
                # Pobierz stany kasy
                cursor.execute("""
                    SELECT date, amount, comment
                    FROM cash_register
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                """, (from_date, to_date))
                
                cash_records = cursor.fetchall()
                
                # Pobierz wydatki
                cursor.execute("""
                    SELECT date, category, description, amount, payment_method, notes
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                """, (from_date, to_date))
                
                expenses = cursor.fetchall()
                
                # Zapisz do pliku CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    import csv
                    writer = csv.writer(csv_file)
                    
                    # Nagłówek raportu
                    writer.writerow([
                        _("Raport finansowy"),
                        _("Od:"), from_date,
                        _("Do:"), to_date,
                        _("Wygenerowano:"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
                    
                    writer.writerow([])  # Pusta linia
                    
                    # Sekcja stanów kasy
                    writer.writerow([_("Stany kasy")])
                    writer.writerow([_("Data"), _("Stan kasy [PLN]"), _("Komentarz")])
                    
                    for record in cash_records:
                        date, amount, comment = record
                        writer.writerow([date, f"{amount:.2f}", comment or ""])
                    
                    writer.writerow([])  # Pusta linia
                    
                    # Sekcja wydatków
                    writer.writerow([_("Wydatki")])
                    writer.writerow([
                        _("Data"), _("Kategoria"), _("Opis"), 
                        _("Kwota [PLN]"), _("Metoda płatności"), _("Uwagi")
                    ])
                    
                    for expense in expenses:
                        date, category, description, amount, payment_method, notes = expense
                        writer.writerow([
                            date, category, description, 
                            f"{amount:.2f}", payment_method or "", notes or ""
                        ])
                    
                    writer.writerow([])  # Pusta linia
                    
                    # Sekcja podsumowania
                    writer.writerow([_("Podsumowanie")])
                    
                    # Suma wydatków
                    total_expenses = sum(expense[3] for expense in expenses)
                    writer.writerow([_("Suma wydatków:"), f"{total_expenses:.2f} zł"])
                    
                    # Podsumowanie wydatków według kategorii
                    writer.writerow([])
                    writer.writerow([_("Wydatki według kategorii")])
                    writer.writerow([_("Kategoria"), _("Kwota [PLN]"), _("Udział [%]")])
                    
                    # Pobierz sumę wydatków według kategorii
                    categories = {}
                    for expense in expenses:
                        category = expense[1]
                        amount = expense[3]
                        categories[category] = categories.get(category, 0) + amount
                    
                    # Sortuj kategorie według kwoty (malejąco)
                    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                    
                    for category, amount in sorted_categories:
                        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                        writer.writerow([category, f"{amount:.2f}", f"{percentage:.1f}%"])
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Raport został wyeksportowany do CSV"),
                    NotificationTypes.SUCCESS,
                    duration=3000
                )
                
            except Exception as e:
                logger.error(f"Błąd podczas eksportu do CSV: {e}")
                raise e
        
        def export_to_excel(self):
            """Eksportuje dane finansowe do pliku Excel."""
            try:
                # Wybór pliku do zapisu
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    _("Zapisz raport jako Excel"),
                    f"raport_finansowy_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "Excel (*.xlsx)"
                )
                
                if not file_path:
                    return
                
                # Informacja o braku implementacji
                QMessageBox.information(
                    self,
                    _("Informacja"),
                    _("Eksport do formatu Excel zostanie zaimplementowany w przyszłej wersji aplikacji.")
                )
                
            except Exception as e:
                logger.error(f"Błąd podczas eksportu do Excel: {e}")
                raise e
        
        def export_to_pdf(self):
            """Eksportuje dane finansowe do pliku PDF."""
            try:
                # Wybór pliku do zapisu
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    _("Zapisz raport jako PDF"),
                    f"raport_finansowy_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "PDF (*.pdf)"
                )
                
                if not file_path:
                    return
                
                # Informacja o braku implementacji
                QMessageBox.information(
                    self,
                    _("Informacja"),
                    _("Eksport do formatu PDF zostanie zaimplementowany w przyszłej wersji aplikacji.")
                )
                
            except Exception as e:
                logger.error(f"Błąd podczas eksportu do PDF: {e}")
                raise e
        
        def refresh_data(self):
            """Odświeża dane w zakładce finansów."""
            self.load_data()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                _("Dane finansowe zostały odświeżone"),
                NotificationTypes.INFO,
                duration=3000
            )
        
        def search(self, text):
            """
            Wyszukuje podany tekst w danych finansowych.
            
            Args:
                text (str): Tekst do wyszukania
            """
            if len(text) < 3:
                return
            
            # Aktualizacja zakładki wydatków
            self.finances_tabs.setCurrentIndex(1)  # Przełączenie na zakładkę wydatków
            
            try:
                cursor = self.conn.cursor()
                
                # Wyszukaj wydatki zawierające podany tekst
                cursor.execute("""
                    SELECT id, date, category, description, amount, payment_method
                    FROM expenses
                    WHERE 
                        description LIKE ? OR
                        category LIKE ? OR
                        notes LIKE ?
                    ORDER BY date DESC
                """, (f"%{text}%", f"%{text}%", f"%{text}%"))
                
                expenses = cursor.fetchall()
                
                # Aktualizacja tabeli wydatków
                self.expenses_table.setRowCount(0)
                total_amount = 0
                
                for expense in expenses:
                    expense_id, date, category, description, amount, payment_method = expense
                    total_amount += amount
                    
                    # Dodaj wiersz do tabeli
                    row = self.expenses_table.rowCount()
                    self.expenses_table.insertRow(row)
                    
                    # Zapisz ID wydatku jako dane wiersza
                    self.expenses_table.setRowHeight(row, 40)
                    
                    # Data
                    date_obj = QDate.fromString(date, "yyyy-MM-dd")
                    date_item = QTableWidgetItem(date_obj.toString("dd-MM-yyyy"))
                    date_item.setData(Qt.UserRole, expense_id)
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.expenses_table.setItem(row, 0, date_item)
                    
                    # Kategoria
                    category_item = QTableWidgetItem(category)
                    self.expenses_table.setItem(row, 1, category_item)
                    
                    # Opis
                    self.expenses_table.setItem(row, 2, QTableWidgetItem(description))
                    
                    # Kwota
                    amount_item = QTableWidgetItem(f"{amount:.2f} zł")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    amount_item.setForeground(QColor("#fa5252"))  # Czerwony dla wydatków
                    self.expenses_table.setItem(row, 3, amount_item)
                    
                    # Metoda płatności
                    payment_item = QTableWidgetItem(payment_method)
                    payment_item.setTextAlignment(Qt.AlignCenter)
                    self.expenses_table.setItem(row, 4, payment_item)
                    
                    # Przyciski akcji (ta sama implementacja co wcześniej)
                    actions_cell = QWidget()
                    actions_layout = QHBoxLayout(actions_cell)
                    actions_layout.setContentsMargins(5, 2, 5, 2)
                    actions_layout.setSpacing(5)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4dabf7;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover {
                            background-color: #339af0;
                        }
                    """)
                    edit_btn.clicked.connect(lambda checked, eid=expense_id: self.edit_expense(eid))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("🗑️")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #fa5252;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover {
                            background-color: #e03131;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, eid=expense_id: self.delete_expense(eid))
                    actions_layout.addWidget(delete_btn)
                    
                    actions_layout.addStretch(1)
                    
                    self.expenses_table.setCellWidget(row, 5, actions_cell)
                
                # Aktualizacja sumy wydatków
                self.total_expenses_label.setText(f"{total_amount:.2f} zł")
                
                # Powiadomienie
                if expenses:
                    NotificationManager.get_instance().show_notification(
                        _("Znaleziono {} pasujących wydatków").format(len(expenses)),
                        NotificationTypes.INFO,
                        duration=3000
                    )
                else:
                    NotificationManager.get_instance().show_notification(
                        _("Nie znaleziono pasujących wydatków"),
                        NotificationTypes.WARNING,
                        duration=3000
                    )
                
            except Exception as e:
                logger.error(f"Błąd podczas wyszukiwania wydatków: {e}")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #fa5252;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover {
                            background-color: #e03131;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, eid=expense_id: self.delete_expense(eid))
                    actions_layout.addWidget(delete_btn)
                    
                    actions_layout.addStretch(1)
                    
                    self.expenses_table.setCellWidget(row, 5, actions_cell)
                
                # Aktualizacja sumy wydatków
                self.total_expenses_label.setText(f"{total_amount:.2f} zł")
                
            except Exception as e:
                logger.error(f"Błąd podczas ładowania wydatków miesięcznych: {e}")
                raise e
        
        def update_financial_analysis(self):
            """Aktualizuje kartę analizy finansowej."""
            try:
                cursor = self.conn.cursor()
                
                # Ustal zakres dat dla wybranego miesiąca i roku
                year = int(self.year_combo.currentText())
                month = self.month_combo.currentIndex() + 1
                
                # Tworzenie zakresu dat dla wybranego miesiąca
                first_day = QDate(year, month, 1)
                last_day = first_day.addMonths(1).addDays(-1)
                
                from_date = first_day.toString("yyyy-MM-dd")
                to_date = last_day.toString("yyyy-MM-dd")
                
                # Pobranie sumy wydatków
                cursor.execute("""
                    SELECT SUM(amount)
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                """, (from_date, to_date))
                
                result = cursor.fetchone()
                total_expenses = result[0] if result[0] is not None else 0
                
                # Pobranie sumy przychodów
                cursor.execute("""
                    SELECT SUM(amount)
                    FROM income
                    WHERE date BETWEEN ? AND ?
                """, (from_date, to_date))
                
                result = cursor.fetchone()
                total_income = result[0] if result[0] is not None else 0
                
                # Obliczenie salda i marży
                balance = total_income - total_expenses
                margin = (balance / total_income * 100) if total_income > 0 else 0
                
                # Aktualizacja kart statystycznych
                self.income_card.value_label.setText(f"{total_income:.2f} zł")
                self.expenses_card.value_label.setText(f"{total_expenses:.2f} zł")
                self.balance_card.value_label.setText(f"{balance:.2f} zł")
                self.margin_card.value_label.setText(f"{margin:.1f}%")
                
                # Aktualizacja wykresu trendu
                self.update_trend_chart(year, month)
                
                # Aktualizacja wykresu kategorii i tabeli
                self.update_categories_chart(from_date, to_date)
                
            except Exception as e:
                logger.error(f"Błąd podczas aktualizacji analizy finansowej: {e}")
        
        def update_trend_chart(self, year, month):
            """
            Aktualizuje dane na wykresie trendu stanu kasy.
            
            Args:
                year (int): Rok
                month (int): Miesiąc
            """
            try:
                if hasattr(self.cash_trend_chart, 'series'):
                    cursor = self.conn.cursor()
                    
                    # Liczba dni w miesiącu
                    first_day = QDate(year, month, 1)
                    days_in_month = first_day.daysInMonth()
                    
                    # Przygotuj listę wszystkich dni w miesiącu
                    dates = []
                    for day in range(1, days_in_month + 1):
                        date = QDate(year, month, day)
                        dates.append(date.toString("yyyy-MM-dd"))
                    
                    # Pobierz stany kasy dla każdego dnia
                    cash_data = {}
                    
                    # Pobierz tylko dostępne daty z bazy
                    cursor.execute("""
                        SELECT date, amount
                        FROM cash_register
                        WHERE strftime('%Y-%m', date) = ?
                        ORDER BY date
                    """, (f"{year}-{month:02d}",))
                    
                    for date, amount in cursor.fetchall():
                        cash_data[date] = amount
                    
                    # Przygotuj dane do wykresu
                    chart_data = []
                    
                    for i, date in enumerate(dates):
                        day = i + 1
                        amount = cash_data.get(date, None)
                        if amount is not None:
                            chart_data.append((day, amount))
                    
                    # Aktualizacja serii danych
                    self.cash_trend_chart.series.clear()
                    
                    if chart_data:
                        for day, amount in chart_data:
                            self.cash_trend_chart.series.append(day, amount)
                        
                        # Aktualizacja zakresu osi
                        min_day = 1
                        max_day = days_in_month
                        
                        amounts = [amount for _, amount in chart_data]
                        min_amount = min(amounts) * 0.9 if amounts else 0
                        max_amount = max(amounts) * 1.1 if amounts else 100
                        
                        self.cash_trend_chart.axis_x.setRange(min_day, max_day)
                        self.cash_trend_chart.axis_y.setRange(min_amount, max_amount)
                        
                        # Aktualizacja tytułu wykresu
                        month_name = self.month_combo.currentText()
                        self.cash_trend_chart.chart.setTitle(f"{_('Trend stanu kasy')} - {month_name} {year}")
                    else:
                        # Brak danych
                        self.cash_trend_chart.axis_x.setRange(1, days_in_month)
                        self.cash_trend_chart.axis_y.setRange(0, 100)
                        
                        month_name = self.month_combo.currentText()
                        self.cash_trend_chart.chart.setTitle(f"{_('Trend stanu kasy')} - {month_name} {year} ({_('brak danych')})")
            
            except Exception as e:
                logger.error(f"Błąd podczas aktualizacji wykresu trendu: {e}")
        
        def update_categories_chart(self, from_date, to_date):
            """
            Aktualizuje wykres i tabelę kategorii wydatków.
            
            Args:
                from_date (str): Data początkowa
                to_date (str): Data końcowa
            """
            try:
                cursor = self.conn.cursor()
                
                # Pobierz sumę wydatków według kategorii
                cursor.execute("""
                    SELECT category, SUM(amount) as total
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    GROUP BY category
                    ORDER BY total DESC
                """, (from_date, to_date))
                
                categories_data = cursor.fetchall()
                
                # Aktualizacja tabeli kategorii
                self.categories_table.setRowCount(0)
                
                total_amount = 0
                categories = []
                values = []
                
                for category, amount in categories_data:
                    total_amount += amount
                    categories.append(category)
                    values.append(amount)
                    
                    # Dodaj wiersz do tabeli
                    row = self.categories_table.rowCount()
                    self.categories_table.insertRow(row)
                    
                    # Kategoria
                    self.categories_table.setItem(row, 0, QTableWidgetItem(category))
                    
                    # Kwota
                    amount_item = QTableWidgetItem(f"{amount:.2f} zł")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.categories_table.setItem(row, 1, amount_item)
                    
                    # Procent
                    percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                    percent_item = QTableWidgetItem(f"{percentage:.1f}%")
                    percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.categories_table.setItem(row, 2, percent_item)
                
                # Aktualizacja wykresu kategorii
                if hasattr(self.categories_chart, 'bar_set'):
                    # Ogranicz liczbę kategorii na wykresie do 5-8 najważniejszych
                    top_categories_count = min(len(categories), 8)
                    top_categories = categories[:top_categories_count]
                    top_values = values[:top_categories_count]
                    
                    # Ustaw nowe dane dla wykresu
                    self.categories_chart.bar_set.remove(0, self.categories_chart.bar_set.count())
                    self.categories_chart.bar_set.append(top_values)
                    
                    # Aktualizacja kategorii na osi X
                    self.categories_chart.axis_x.clear()
                    self.categories_chart.axis_x.append(top_categories)
                    
                    # Aktualizacja zakresu osi Y
                    max_value = max(top_values) * 1.1 if top_values else 100
                    self.categories_chart.axis_y.setRange(0, max_value)
                    
                    # Aktualizacja tytułu wykresu
                    month_name = self.month_combo.currentText()
                    year = self.year_combo.currentText()
                    self.categories_chart.chart.setTitle(f"{_('Wydatki według kategorii')} - {month_name} {year}")
            
            except Exception as e:
                logger.error(f"Błąd podczas aktualizacji wykresu kategorii: {e}")
        
        def add_cash_register_entry(self):
            """Dodaje nowy wpis stanu kasy."""
            try:
                dialog = CashRegisterDialog(self.conn, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    # Odśwież dane
                    self.load_data()
            except Exception as e:
                logger.error(f"Błąd podczas dodawania wpisu stanu kasy: {e}")
                
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas dodawania wpisu stanu kasy: {}").format(str(e))
                )
        
        def add_expense(self):
            """Dodaje nowy wydatek."""
            try:
                dialog = ExpenseDialog(self.conn, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    # Odśwież dane
                    self.load_data()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        _("Dodano nowy wydatek"),
                        NotificationTypes.SUCCESS,
                        duration=3000
                    )
            except Exception as e:
                logger.error(f"Błąd podczas dodawania wydatku: {e}")
                
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas dodawania wydatku: {}").format(str(e))
                )
        
        def edit_expense(self, expense_id):
            """
            Edytuje istniejący wydatek.
            
            Args:
                expense_id (int): ID wydatku
            """
            try:
                dialog = ExpenseDialog(self.conn, parent=self, expense_id=expense_id)
                if dialog.exec() == QDialog.Accepted:
                    # Odśwież dane
                    self.load_data()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        _("Wydatek został zaktualizowany"),
                        NotificationTypes.SUCCESS,
                        duration=3000
                    )
                    
                    # Emituj sygnał
                    self.expense_updated.emit(expense_id)
            except Exception as e:
                logger.error(f"Błąd podczas edycji wydatku: {e}")
                
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas edycji wydatku: {}").format(str(e))
                )
        
        def delete_expense(self, expense_id):
            """
            Usuwa wydatek.
            
            Args:
                expense_id (int): ID wydatku
            """
            try:
                # Pobierz informacje o wydatku
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT description FROM expenses WHERE id = ?
                """, (expense_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Nie znaleziono wydatku o ID={expense_id}")
                    return
                
                description = result[0]
                
                # Potwierdzenie usunięcia
                reply = QMessageBox.question(
                    self,
                    _("Potwierdzenie usunięcia"),
                    _("Czy na pewno chcesz usunąć wydatek: {}?").format(description),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Usuń wydatek
                    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                    self.conn.commit()
                    
                    # Odśwież dane
                    self.load_data()
                    
                    # Powiadomienie
                    NotificationManager.get_instance().show_notification(
                        _("Wydatek został usunięty"),
                        NotificationTypes.SUCCESS,
                        duration=3000
                    )
                    
                    # Emituj sygnał
                    self.expense_deleted.emit(expense_id)
            
            except Exception as e:
                logger.error(f"Błąd podczas usuwania wydatku: {e}")
                
                QMessageBox.critical(
                    self,
                    _("Błąd"),
                    _("Wystąpił błąd podczas usuwania wydatku: {}").format(str(e))
                )
        
        def show_expense_context_menu(self, position):
            """
            Wyświetla menu kontekstowe dla tabeli wydatków.
            
            Args:
                position (QPoint): Pozycja kliknięcia
            """
            item = self.expenses_table.itemAt(position)
            if not item:
                return
                
            row = item.row()
            expense_id = self.expenses_table.item(row, 0).data(Qt.UserRole)
            
            # Tworzenie menu kontekstowego
            menu = QMenu(self)
            menu.setStyleSheet(STYLES["MENU"])
                            # Przykładowe dane kategorii (zostaną zaktualizowane przy ładowaniu)
                    categories = [_("Czynsz"), _("Media"), _("Materiały"), _("Usługi"), _("Wynagrodzenia")]
                    values = [3500, 1200, 2500, 800, 5000]
                    
                    # Tworzenie zestawu danych
                    bar_set = QBarSet(_("Kwota"))
                    bar_set.append(values)
                    bar_set.setColor(QColor("#4dabf7"))
                    bar_set.setBorderColor(QColor("#339af0"))
                    
                    series.append(bar_set)
                    chart.addSeries(series)
                    
                    # Oś kategorii
                    axis_x = QBarCategoryAxis()
                    axis_x.append(categories)
                    axis_x.setTitleText(_("Kategoria"))
                    axis_x.setTitleBrush(QColor("white"))
                    axis_x.setLabelsColor(QColor("white"))
                    
                    # Oś wartości
                    axis_y = QValueAxis()
                    axis_y.setLabelFormat("%.2f zł")
                    axis_y.setTitleText(_("Kwota"))
                    axis_y.setTitleBrush(QColor("white"))
                    axis_y.setLabelsColor(QColor("white"))
                    
                    chart.addAxis(axis_x, Qt.AlignBottom)
                    chart.addAxis(axis_y, Qt.AlignLeft)
                    
                    series.attachAxis(axis_x)
                    series.attachAxis(axis_y)
                    
                    # Widok wykresu
                    chart_view = QChartView(chart)
                    chart_view.setRenderHint(QPainter.Antialiasing)
                    chart_view.setMinimumHeight(250)
                    chart_view.setMinimumWidth(450)
                    
                    chart_layout.addWidget(chart_view)
                    
                    # Zapisz referencję do komponentów wykresu
                    chart_widget.chart = chart
                    chart_widget.series = series
                    chart_widget.axis_x = axis_x
                    chart_widget.axis_y = axis_y
                    chart_widget.bar_set = bar_set
                    
                except Exception as e:
                    logger.error(f"Błąd podczas tworzenia wykresu kategorii: {e}")
                    
                    # Fallback - jeśli QtCharts nie działa
                    label = QLabel(_("Wykres kategorii niedostępny. Moduł QtCharts nie jest zainstalowany."))
                    label.setStyleSheet("color: white; background-color: #343a40; padding: 15px; border-radius: 5px;")
                    label.setAlignment(Qt.AlignCenter)
                    label.setMinimumHeight(250)
                    
                    chart_layout.addWidget(label)
                
                return chart_widget
                
            except Exception as e:
                logger.error(f"Błąd podczas tworzenia widgetu wykresu kategorii: {e}")
                
                # Fallback w przypadku błędu
                fallback = QLabel(_("Wykres kategorii niedostępny."))
                fallback.setStyleSheet("color: white; background-color: #343a40; padding: 15px; border-radius: 5px;")
                fallback.setAlignment(Qt.AlignCenter)
                fallback.setMinimumHeight(250)
                
                return fallback
        
        def change_period_filter(self):
            """Obsługuje zmianę filtra okresu."""
            sender = self.sender()
            period = sender.property("period")
            
            # Odznacz inne przyciski
            for name, btn in self.period_buttons.items():
                if name != period:
                    btn.setChecked(False)
            
            # Ustaw daty dla wybranego okresu
            today = QDate.currentDate()
            
            if period == "Dzisiaj":
                self.from_date_edit.setDate(today)
                self.to_date_edit.setDate(today)
            elif period == "Tydzień":
                self.from_date_edit.setDate(today.addDays(-7))
                self.to_date_edit.setDate(today)
            elif period == "Miesiąc":
                self.from_date_edit.setDate(today.addMonths(-1))
                self.to_date_edit.setDate(today)
            elif period == "Rok":
                self.from_date_edit.setDate(today.addYears(-1))
                self.to_date_edit.setDate(today)
            
            # Wywołaj filtrowanie
            if period != "Niestandardowy":
                self.apply_filters()
        
        def custom_date_changed(self):
            """Obsługuje zmianę niestandardowego zakresu dat."""
            # Sprawdź czy daty są poprawne
            from_date = self.from_date_edit.date()
            to_date = self.to_date_edit.date()
            
            if from_date > to_date:
                # Automatycznie koryguj datę końcową
                self.to_date_edit.setDate(from_date)
            
            # Zaznacz przycisk niestandardowego okresu
            for name, btn in self.period_buttons.items():
                btn.setChecked(name == "Niestandardowy")
        
        def apply_filters(self):
            """Stosuje wybrane filtry do danych."""
            # Załaduj dane z wybranego okresu
            self.load_data()
        
        def load_data(self):
            """Ładuje dane finansowe zgodnie z wybranymi filtrami."""
            try:
                # Aktualizuj stan kasy
                self.load_cash_register_data()
                
                # Aktualizuj wydatki
                self.load_monthly_expenses()
                
                # Aktualizuj analizę
                self.update_financial_analysis()
                
            except Exception as e:
                logger.error(f"Błąd podczas ładowania danych finansowych: {e}")
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    _("Wystąpił błąd podczas ładowania danych finansowych"),
                    NotificationTypes.ERROR,
                    duration=3000
                )
        
        def load_cash_register_data(self):
            """Ładuje dane stanu kasy."""
            try:
                cursor = self.conn.cursor()
                
                # Pobranie stanów kasy z wybranego okresu
                from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
                to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
                
                cursor.execute("""
                    SELECT date, amount, comment
                    FROM cash_register
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (from_date, to_date))
                
                records = cursor.fetchall()
                
                # Aktualizacja tabeli historii
                self.cash_history_table.setRowCount(0)
                
                previous_amount = None
                
                for i, record in enumerate(records):
                    date, amount, comment = record
                    
                    # Dodaj wiersz do tabeli
                    row = self.cash_history_table.rowCount()
                    self.cash_history_table.insertRow(row)
                    
                    # Data
                    date_obj = QDate.fromString(date, "yyyy-MM-dd")
                    date_item = QTableWidgetItem(date_obj.toString("dd-MM-yyyy"))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.cash_history_table.setItem(row, 0, date_item)
                    
                    # Stan kasy
                    amount_item = QTableWidgetItem(f"{amount:.2f} zł")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.cash_history_table.setItem(row, 1, amount_item)
                    
                    # Różnica
                    if i < len(records) - 1:
                        next_record = records[i + 1]
                        next_amount = next_record[1]
                        difference = amount - next_amount
                        percentage = (difference / next_amount) * 100 if next_amount != 0 else 0
                        
                        diff_text = f"{'+' if difference >= 0 else ''}{difference:.2f} zł ({'+' if percentage >= 0 else ''}{percentage:.1f}%)"
                        diff_item = QTableWidgetItem(diff_text)
                        diff_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        
                        # Kolorowanie różnicy
                        if difference > 0:
                            diff_item.setForeground(QColor("#40c057"))  # Zielony dla dodatnich
                        elif difference < 0:
                            diff_item.setForeground(QColor("#fa5252"))  # Czerwony dla ujemnych
                        
                        self.cash_history_table.setItem(row, 2, diff_item)
                    else:
                        self.cash_history_table.setItem(row, 2, QTableWidgetItem("-"))
                    
                    # Komentarz
                    self.cash_history_table.setItem(row, 3, QTableWidgetItem(comment or ""))
                    
                    # Zachowanie pierwszego i ostatniego rekordu dla porównania
                    if i == 0:
                        self.current_cash_label.setText(f"{amount:.2f} zł")
                    
                    if previous_amount is None and i + 1 < len(records):
                        previous_amount = records[i + 1][1]
                        self.previous_cash_label.setText(f"{previous_amount:.2f} zł")
                
                # Aktualizacja różnicy w sekcji porównania
                if records and previous_amount is not None:
                    current_amount = records[0][1]
                    difference = current_amount - previous_amount
                    percentage = (difference / previous_amount) * 100 if previous_amount != 0 else 0
                    
                    diff_text = f"{'+' if difference >= 0 else ''}{difference:.2f} zł ({'+' if percentage >= 0 else ''}{percentage:.1f}%)"
                    self.difference_cash_label.setText(diff_text)
                    
                    # Kolorowanie etykiety różnicy
                    if difference > 0:
                        self.difference_cash_label.setStyleSheet("color: #40c057; font-size: 24px; font-weight: bold;")
                    elif difference < 0:
                        self.difference_cash_label.setStyleSheet("color: #fa5252; font-size: 24px; font-weight: bold;")
                    else:
                        self.difference_cash_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
                else:
                    self.current_cash_label.setText("0.00 zł")
                    self.previous_cash_label.setText("0.00 zł")
                    self.difference_cash_label.setText("+0.00 zł (0%)")
                    self.difference_cash_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
            
            except Exception as e:
                logger.error(f"Błąd podczas ładowania danych stanu kasy: {e}")
                raise e
        
        def load_monthly_expenses(self):
            """Ładuje wydatki miesięczne."""
            try:
                cursor = self.conn.cursor()
                
                # Ustal zakres dat dla wybranego miesiąca i roku
                year = int(self.year_combo.currentText())
                month = self.month_combo.currentIndex() + 1
                
                # Tworzenie zakresu dat dla wybranego miesiąca
                first_day = QDate(year, month, 1)
                last_day = first_day.addMonths(1).addDays(-1)
                
                from_date = first_day.toString("yyyy-MM-dd")
                to_date = last_day.toString("yyyy-MM-dd")
                
                cursor.execute("""
                    SELECT id, date, category, description, amount, payment_method
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (from_date, to_date))
                
                expenses = cursor.fetchall()
                
                # Aktualizacja tabeli wydatków
                self.expenses_table.setRowCount(0)
                total_amount = 0
                
                for expense in expenses:
                    expense_id, date, category, description, amount, payment_method = expense
                    total_amount += amount
                    
                    # Dodaj wiersz do tabeli
                    row = self.expenses_table.rowCount()
                    self.expenses_table.insertRow(row)
                    
                    # Zapisz ID wydatku jako dane wiersza
                    self.expenses_table.setRowHeight(row, 40)
                    
                    # Data
                    date_obj = QDate.fromString(date, "yyyy-MM-dd")
                    date_item = QTableWidgetItem(date_obj.toString("dd-MM-yyyy"))
                    date_item.setData(Qt.UserRole, expense_id)
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.expenses_table.setItem(row, 0, date_item)
                    
                    # Kategoria
                    category_item = QTableWidgetItem(category)
                    self.expenses_table.setItem(row, 1, category_item)
                    
                    # Opis
                    self.expenses_table.setItem(row, 2, QTableWidgetItem(description))
                    
                    # Kwota
                    amount_item = QTableWidgetItem(f"{amount:.2f} zł")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    amount_item.setForeground(QColor("#fa5252"))  # Czerwony dla wydatków
                    self.expenses_table.setItem(row, 3, amount_item)
                    
                    # Metoda płatności
                    payment_item = QTableWidgetItem(payment_method)
                    payment_item.setTextAlignment(Qt.AlignCenter)
                    self.expenses_table.setItem(row, 4, payment_item)
                    
                    # Przyciski akcji
                    actions_cell = QWidget()
                    actions_layout = QHBoxLayout(actions_cell)
                    actions_layout.setContentsMargins(5, 2, 5, 2)
                    actions_layout.setSpacing(5)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4dabf7;
                            color: white;
                            border-radius: 4px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover {
                            background-color: #339af0;
                        }
                    """)
                    edit_btn.clicked.connect(lambda checked, eid=expense_id: self.edit_expense(eid))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("🗑️")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #fa5252        
                    self.month_combo.addItems(months)
            current_month = datetime.now().month - 1  # Indeksowanie od 0
            self.month_combo.setCurrentIndex(current_month)
            self.month_combo.setStyleSheet(STYLES["COMBO_BOX"])
            self.month_combo.currentIndexChanged.connect(self.load_monthly_expenses)
            header_layout.addWidget(self.month_combo)
            
            year_label = QLabel(_("Rok:"))
            year_label.setStyleSheet("color: white; font-weight: bold;")
            header_layout.addWidget(year_label)
            
            self.year_combo = QComboBox()
            # Dodaj lata od 2020 do bieżącego roku + 2
            current_year = datetime.now().year
            years = [str(year) for year in range(2020, current_year + 3)]
            self.year_combo.addItems(years)
            self.year_combo.setCurrentText(str(current_year))
            self.year_combo.setStyleSheet(STYLES["COMBO_BOX"])
            self.year_combo.currentIndexChanged.connect(self.load_monthly_expenses)
            header_layout.addWidget(self.year_combo)
            
            header_layout.addStretch(1)
            
            # Przycisk dodawania wydatku
            self.add_expense_button = QPushButton("➕ " + _("Dodaj wydatek"))
            self.add_expense_button.setObjectName("addButton")
            self.add_expense_button.setStyleSheet(STYLES["ADD_BUTTON"])
            self.add_expense_button.clicked.connect(self.add_expense)
            header_layout.addWidget(self.add_expense_button)
            
            layout.addLayout(header_layout)
            
            # Tabela wydatków miesięcznych
            self.expenses_table = QTableWidget()
            self.expenses_table.setColumnCount(6)
            self.expenses_table.setHorizontalHeaderLabels([
                _("Data"), _("Kategoria"), _("Opis"), _("Kwota [PLN]"), _("Metoda płatności"), _("Akcje")
            ])
            self.expenses_table.setStyleSheet(STYLES["TABLE_WIDGET"])
            self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.expenses_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.expenses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.expenses_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.expenses_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
            self.expenses_table.setColumnWidth(5, 150)
            self.expenses_table.setAlternatingRowColors(True)
            self.expenses_table.verticalHeader().setVisible(False)
            self.expenses_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.expenses_table.customContextMenuRequested.connect(self.show_expense_context_menu)
            
            layout.addWidget(self.expenses_table)
            
            # Podsumowanie wydatków
            summary_layout = QHBoxLayout()
            
            summary_label = QLabel(_("Suma wydatków w wybranym miesiącu:"))
            summary_label.setStyleSheet("color: white; font-weight: bold;")
            summary_layout.addWidget(summary_label)
            
            self.total_expenses_label = QLabel("0.00 zł")
            self.total_expenses_label.setStyleSheet("color: #fa5252; font-size: 18px; font-weight: bold;")
            summary_layout.addWidget(self.total_expenses_label)
            
            summary_layout.addStretch(1)
            
            layout.addLayout(summary_layout)
            
        def setup_analysis_tab(self):
            """Konfiguruje zakładkę analizy finansowej."""
            layout = QVBoxLayout(self.analysis_tab)
            layout.setContentsMargins(0, 10, 0, 0)
            layout.setSpacing(15)
            
            # Przegląd finansowy - karty
            cards_layout = QHBoxLayout()
            cards_layout.setSpacing(15)
            
            # Karta przychody miesiąca
            self.income_card = self.create_stat_card(
                "💰", _("Przychody miesiąca"), "0.00 zł", STYLES["STAT_CARD_GREEN"]
            )
            cards_layout.addWidget(self.income_card)
            
            # Karta wydatki miesiąca
            self.expenses_card = self.create_stat_card(
                "💸", _("Wydatki miesiąca"), "0.00 zł", STYLES["STAT_CARD_RED"]
            )
            cards_layout.addWidget(self.expenses_card)
            
            # Karta saldo
            self.balance_card = self.create_stat_card(
                "⚖️", _("Saldo"), "0.00 zł", STYLES["STAT_CARD_BLUE"]
            )
            cards_layout.addWidget(self.balance_card)
            
            # Karta marża
            self.margin_card = self.create_stat_card(
                "📊", _("Marża"), "0%", STYLES["STAT_CARD_LIGHT_BLUE"]
            )
            cards_layout.addWidget(self.margin_card)
            
            layout.addLayout(cards_layout)
            
            # Wykres trendu stanu kasy
            chart_label = QLabel(_("Trend stanu kasy:"))
            chart_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            layout.addWidget(chart_label)
            
            self.cash_trend_chart = self.create_trend_chart()
            layout.addWidget(self.cash_trend_chart)
            
            # Rozkład wydatków według kategorii
            categories_layout = QHBoxLayout()
            
            # Wykres kategorii
            chart_frame = QFrame()
            chart_frame.setMaximumWidth(500)
            chart_frame.setMinimumHeight(300)
            chart_layout = QVBoxLayout(chart_frame)
            
            categories_chart_label = QLabel(_("Wydatki według kategorii:"))
            categories_chart_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            chart_layout.addWidget(categories_chart_label)
            
            self.categories_chart = self.create_categories_chart()
            chart_layout.addWidget(self.categories_chart)
            
            categories_layout.addWidget(chart_frame)
            
            # Tabela kategorii
            categories_table_layout = QVBoxLayout()
            
            categories_table_label = QLabel(_("Podsumowanie wydatków wg kategorii:"))
            categories_table_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            categories_table_layout.addWidget(categories_table_label)
            
            self.categories_table = QTableWidget()
            self.categories_table.setColumnCount(3)
            self.categories_table.setHorizontalHeaderLabels([
                _("Kategoria"), _("Kwota [PLN]"), _("Udział")
            ])
            self.categories_table.setStyleSheet(STYLES["TABLE_WIDGET"])
            self.categories_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.categories_table.setAlternatingRowColors(True)
            self.categories_table.verticalHeader().setVisible(False)
            categories_table_layout.addWidget(self.categories_table)
            
            categories_layout.addLayout(categories_table_layout)
            
            layout.addLayout(categories_layout)
            
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
            background_color = ""
            for line in style.split("\n"):
                if "background-color:" in line:
                    background_color = line.split("background-color:")[1].split(";")[0].strip()
                    break
            
            # Tytuł z ikoną
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
            
            # Wartość
            value_label = QLabel(value)
            if background_color:
                value_label.setStyleSheet(f"{STYLES['STAT_LABEL']} background-color: {background_color};")
            else:
                value_label.setStyleSheet(STYLES["STAT_LABEL"])
            layout.addWidget(value_label)
            
            # Zapisanie referencji do etykiety wartości
            card.value_label = value_label
            
            return card
        
        def create_trend_chart(self):
            """
            Tworzy wykres trendu stanu kasy.
            
            Returns:
                QWidget: Widget z wykresem
            """
            try:
                # Sprawdź czy QtCharts jest dostępne
                chart_widget = QWidget()
                chart_layout = QVBoxLayout(chart_widget)
                chart_layout.setContentsMargins(0, 0, 0, 0)
                
                try:
                    # Utworzenie wykresu
                    chart = QChart()
                    chart.setTitle(_("Trend stanu kasy"))
                    chart.setTitleFont(QFont("Segoe UI", 12))
                    chart.setTitleBrush(QColor("white"))
                    chart.setBackgroundBrush(QBrush(QColor("#2c3034")))
                    chart.setAnimationOptions(QChart.SeriesAnimations)
                    
                    # Utworzenie serii danych
                    series = QLineSeries()
                    series.setName(_("Stan kasy"))
                    
                    # Próbki danych (zostaną zaktualizowane przy ładowaniu)
                    for i in range(30):
                        series.append(i, i * 100)
                    
                    chart.addSeries(series)
                    
                    # Osie
                    axis_x = QValueAxis()
                    axis_x.setLabelFormat("%d")
                    axis_x.setTitleText(_("Dzień miesiąca"))
                    axis_x.setTitleBrush(QColor("white"))
                    axis_x.setLabelsColor(QColor("white"))
                    
                    axis_y = QValueAxis()
                    axis_y.setLabelFormat("%.2f zł")
                    axis_y.setTitleText(_("Stan kasy"))
                    axis_y.setTitleBrush(QColor("white"))
                    axis_y.setLabelsColor(QColor("white"))
                    
                    chart.addAxis(axis_x, Qt.AlignBottom)
                    chart.addAxis(axis_y, Qt.AlignLeft)
                    
                    series.attachAxis(axis_x)
                    series.attachAxis(axis_y)
                    
                    # Widok wykresu
                    chart_view = QChartView(chart)
                    chart_view.setRenderHint(QPainter.Antialiasing)
                    chart_view.setMinimumHeight(300)
                    
                    chart_layout.addWidget(chart_view)
                    
                    # Zapisz referencję do komponentów wykresu
                    chart_widget.chart = chart
                    chart_widget.series = series
                    chart_widget.axis_x = axis_x
                    chart_widget.axis_y = axis_y
                    
                except Exception as e:
                    logger.error(f"Błąd podczas tworzenia wykresu trendu: {e}")
                    
                    # Fallback - jeśli QtCharts nie działa
                    label = QLabel(_("Wykres trendu niedostępny. Moduł QtCharts nie jest zainstalowany."))
                    label.setStyleSheet("color: white; background-color: #343a40; padding: 15px; border-radius: 5px;")
                    label.setAlignment(Qt.AlignCenter)
                    label.setMinimumHeight(300)
                    
                    chart_layout.addWidget(label)
                
                return chart_widget
                
            except Exception as e:
                logger.error(f"Błąd podczas tworzenia widgetu wykresu trendu: {e}")
                
                # Fallback w przypadku błędu
                fallback = QLabel(_("Wykres trendu niedostępny."))
                fallback.setStyleSheet("color: white; background-color: #343a40; padding: 15px; border-radius: 5px;")
                fallback.setAlignment(Qt.AlignCenter)
                fallback.setMinimumHeight(300)
                
                return fallback
        
        def create_categories_chart(self):
            """
            Tworzy wykres wydatków według kategorii.
            
            Returns:
                QWidget: Widget z wykresem
            """
            try:
                # Sprawdź czy QtCharts jest dostępne
                chart_widget = QWidget()
                chart_layout = QVBoxLayout(chart_widget)
                chart_layout.setContentsMargins(0, 0, 0, 0)
                
                try:
                    # Utworzenie wykresu
                    chart = QChart()
                    chart.setTitle(_("Wydatki według kategorii"))
                    chart.setTitleFont(QFont("Segoe UI", 12))
                    chart.setTitleBrush(QColor("white"))
                    chart.setBackgroundBrush(QBrush(QColor("#2c3034")))
                    chart.setAnimationOptions(QChart.SeriesAnimations)
                    
                    # Utworzenie serii danych
                    series = QBarSeries()
                    
                    # Przykładowe dane kategorii (zostaną zaktualizowane przy ładowaniu)
                    categories =