#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog wyświetlający szczegóły części/akcesorium.
"""

import os
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QFrame, QSpacerItem, QSizePolicy, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class PartDetailsDialog(QDialog):
    """
    Dialog wyświetlający szczegóły części/akcesorium.
    Umożliwia również korektę stanu, drukowanie etykiet i inne akcje.
    """
    
    def __init__(self, db_connection, part_id, parent=None):
        """
        Inicjalizacja dialogu szczegółów części/akcesorium.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            part_id (int): ID części/akcesorium
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.part_id = part_id
        
        self.setWindowTitle("Szczegóły części/akcesorium")
        self.resize(700, 500)
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Ładowanie danych części/akcesorium
        self.load_part_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        
        # Ikona części/akcesorium
        icon_label = QLabel()
        icon_pixmap = QPixmap(os.path.join(ICONS_DIR, "parts.png"))
        icon_label.setPixmap(icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        # Tytuł części/akcesorium
        self.title_label = QLabel("Szczegóły części/akcesorium")
        self.title_label.setObjectName("headerLabel")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        # Status dostępności
        self.availability_label = QLabel("Status")
        self.availability_label.setObjectName("statusLabel")
        self.availability_label.setStyleSheet("""
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        """)
        header_layout.addWidget(self.availability_label)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Główna sekcja z danymi
        content_layout = QGridLayout()
        
        # Sekcja informacji podstawowych
        basic_frame = QFrame()
        basic_frame.setObjectName("detailsFrame")
        basic_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        basic_layout = QVBoxLayout(basic_frame)
        
        basic_title = QLabel("Informacje podstawowe")
        basic_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        basic_layout.addWidget(basic_title)
        
        basic_form = QFormLayout()
        
        self.name_label = QLabel()
        basic_form.addRow("Nazwa:", self.name_label)
        
        self.catalog_number_label = QLabel()
        basic_form.addRow("Nr katalogowy:", self.catalog_number_label)
        
        self.category_label = QLabel()
        basic_form.addRow("Kategoria:", self.category_label)
        
        self.manufacturer_label = QLabel()
        basic_form.addRow("Producent:", self.manufacturer_label)
        
        basic_layout.addLayout(basic_form)
        content_layout.addWidget(basic_frame, 0, 0)
        
        # Sekcja informacji o stanie i cenie
        stock_frame = QFrame()
        stock_frame.setObjectName("detailsFrame")
        stock_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        stock_layout = QVBoxLayout(stock_frame)
        
        stock_title = QLabel("Stan i cena")
        stock_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        stock_layout.addWidget(stock_title)
        
        stock_form = QFormLayout()
        
        self.quantity_label = QLabel()
        stock_form.addRow("Ilość:", self.quantity_label)
        
        self.minimum_quantity_label = QLabel()
        stock_form.addRow("Minimalna ilość:", self.minimum_quantity_label)
        
        self.price_label = QLabel()
        stock_form.addRow("Cena:", self.price_label)
        
        self.location_label = QLabel()
        stock_form.addRow("Lokalizacja:", self.location_label)
        
        stock_layout.addLayout(stock_form)
        content_layout.addWidget(stock_frame, 0, 1)
        
        # Sekcja informacji dodatkowych
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        details_layout = QVBoxLayout(details_frame)
        
        details_title = QLabel("Informacje dodatkowe")
        details_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        details_layout.addWidget(details_title)
        
        details_form = QFormLayout()
        
        self.barcode_label = QLabel()
        details_form.addRow("Kod kreskowy:", self.barcode_label)
        
        self.vat_rate_label = QLabel()
        details_form.addRow("Stawka VAT:", self.vat_rate_label)
        
        self.unit_label = QLabel()
        details_form.addRow("Jednostka miary:", self.unit_label)
        
        self.supplier_label = QLabel()
        details_form.addRow("Dostawca:", self.supplier_label)
        
        self.warranty_label = QLabel()
        details_form.addRow("Gwarancja:", self.warranty_label)
        
        details_layout.addLayout(details_form)
        content_layout.addWidget(details_frame, 1, 0)
        
        # Sekcja opisu
        description_frame = QFrame()
        description_frame.setObjectName("detailsFrame")
        description_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        description_layout = QVBoxLayout(description_frame)
        
        description_title = QLabel("Opis")
        description_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        description_layout.addWidget(description_title)
        
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.description_label.setMinimumHeight(80)
        description_layout.addWidget(self.description_label)
        
        content_layout.addWidget(description_frame, 1, 1)
        
        main_layout.addLayout(content_layout)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edytuj")
        edit_button.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
        edit_button.clicked.connect(self.edit_part)
        action_layout.addWidget(edit_button)
        
        adjust_stock_button = QPushButton("Korekta stanu")
        adjust_stock_button.setIcon(QIcon(os.path.join(ICONS_DIR, "adjust.png")))
        adjust_stock_button.clicked.connect(self.adjust_stock)
        action_layout.addWidget(adjust_stock_button)
        
        print_label_button = QPushButton("Drukuj etykietę")
        print_label_button.setIcon(QIcon(os.path.join(ICONS_DIR, "print.png")))
        print_label_button.clicked.connect(self.print_label)
        action_layout.addWidget(print_label_button)
        
        order_button = QPushButton("Zamów")
        order_button.setIcon(QIcon(os.path.join(ICONS_DIR, "order.png")))
        order_button.clicked.connect(self.create_order)
        action_layout.addWidget(order_button)
        
        # Elastyczna przestrzeń
        action_layout.addStretch(1)
        
        # Przycisk usuwania
        delete_button = QPushButton("Usuń")
        delete_button.setObjectName("deleteButton")
        delete_button.setIcon(QIcon(os.path.join(ICONS_DIR, "delete.png")))
        delete_button.clicked.connect(self.delete_part)
        action_layout.addWidget(delete_button)
        
        # Przycisk zamknięcia
        close_button = QPushButton("Zamknij")
        close_button.setIcon(QIcon(os.path.join(ICONS_DIR, "close.png")))
        close_button.clicked.connect(self.accept)
        action_layout.addWidget(close_button)
        
        main_layout.addLayout(action_layout)
    
    def load_part_data(self):
        """Ładuje dane części/akcesorium z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane części/akcesorium
            query = """
                SELECT name, catalog_number, category, manufacturer, 
                    quantity, price, location, description, barcode, 
                    minimum_quantity, supplier, vat_rate, unit, warranty
                FROM parts
                WHERE id = ?
            """
            cursor.execute(query, (self.part_id,))
            
            data = cursor.fetchone()
            if not data:
                logger.error(f"Nie znaleziono części/akcesorium o ID: {self.part_id}")
                QMessageBox.critical(self, "Błąd", f"Nie znaleziono części/akcesorium o ID: {self.part_id}")
                self.reject()
                return
            
            # Rozpakowanie danych
            (name, catalog_number, category, manufacturer, 
             quantity, price, location, description, barcode, 
             minimum_quantity, supplier, vat_rate, unit, warranty) = data
            
            # Aktualizacja danych w interfejsie
            self.title_label.setText(f"{name}")
            
            # Ustawienie statusu dostępności z odpowiednim kolorem
            if quantity > 0:
                if quantity <= minimum_quantity:
                    self.availability_label.setText("Niski stan")
                    self.availability_label.setStyleSheet("background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
                else:
                    self.availability_label.setText("Dostępny")
                    self.availability_label.setStyleSheet("background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            else:
                self.availability_label.setText("Niedostępny")
                self.availability_label.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            
            # Dane podstawowe
            self.name_label.setText(name or "-")
            self.catalog_number_label.setText(catalog_number or "-")
            self.category_label.setText(category or "-")
            self.manufacturer_label.setText(manufacturer or "-")
            
            # Dane stanu i ceny
            self.quantity_label.setText(f"{quantity}" if quantity is not None else "-")
            self.minimum_quantity_label.setText(f"{minimum_quantity}" if minimum_quantity is not None else "-")
            
            # Formatowanie ceny
            if price is not None:
                self.price_label.setText(f"{price:.2f} PLN")
            else:
                self.price_label.setText("-")
            
            self.location_label.setText(location or "-")
            
            # Dane dodatkowe
            self.barcode_label.setText(barcode or "-")
            self.vat_rate_label.setText(vat_rate or "-")
            self.unit_label.setText(unit or "-")
            self.supplier_label.setText(supplier or "-")
            self.warranty_label.setText(warranty or "-")
            
            # Opis
            self.description_label.setText(description or "-")
            
            logger.debug(f"Załadowano dane części/akcesorium o ID: {self.part_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych części/akcesorium: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych części/akcesorium:\n{str(e)}")
    
    def edit_part(self):
        """Otwiera okno edycji części/akcesorium."""
        from ui.dialogs.part_dialog import PartDialog
        dialog = PartDialog(self.conn, part_id=self.part_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_part_data()
    
    def adjust_stock(self):
        """Otwiera okno korekty stanu magazynowego."""
        from ui.dialogs.stock_adjustment_dialog import StockAdjustmentDialog
        dialog = StockAdjustmentDialog(
            self.conn, 
            self.part_id, 
            self.name_label.text(), 
            int(self.quantity_label.text() if self.quantity_label.text() != "-" else "0"), 
            parent=self
        )
        
        if dialog.exec() == QDialog.Accepted:
            self.load_part_data()
            NotificationManager.get_instance().show_notification(
                "Stan magazynowy został zaktualizowany pomyślnie.",
                NotificationTypes.SUCCESS
            )
    
    def print_label(self):
        """Drukuje etykietę dla części/akcesorium."""
        try:
            from ui.dialogs.print_label_dialog import PrintLabelDialog
            dialog = PrintLabelDialog(
                self.conn,
                part_id=self.part_id,
                entity_type="part",
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas drukowania etykiety: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania etykiety:\n{str(e)}")
    
    def create_order(self):
        """Tworzy zamówienie dla części/akcesorium."""
        try:
            # Sprawdź, czy część ma wszystkie wymagane dane
            name = self.name_label.text()
            catalog_number = self.catalog_number_label.text()
            manufacturer = self.manufacturer_label.text()
            
            # Otwarcie okna nowego zamówienia z predefiniowanymi danymi
            from ui.dialogs.order_dialog import OrderDialog
            dialog = OrderDialog(self.conn, parent=self)
            
            # Ustawienie danych zamówienia
            dialog.set_order_item(name, catalog_number, manufacturer)
            
            if dialog.exec() == QDialog.Accepted:
                NotificationManager.get_instance().show_notification(
                    "Zamówienie zostało utworzone pomyślnie.",
                    NotificationTypes.SUCCESS
                )
            
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia zamówienia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas tworzenia zamówienia:\n{str(e)}")
    
    def delete_part(self):
        """Usuwa część/akcesorium."""
        confirmation = QMessageBox.question(
            self,
            "Potwierdź usunięcie",
            "Czy na pewno chcesz usunąć tę część/akcesorium? Ta operacja jest nieodwracalna.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmation == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                
                # Usunięcie części/akcesorium
                cursor.execute("DELETE FROM parts WHERE id = ?", (self.part_id,))
                
                # Zatwierdzenie zmian
                self.conn.commit()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    "Część/akcesorium została usunięta pomyślnie.",
                    NotificationTypes.SUCCESS
                )
                
                # Zamknij okno
                self.accept()
                
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Błąd podczas usuwania części/akcesorium: {e}")
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania części/akcesorium:\n{str(e)}")
