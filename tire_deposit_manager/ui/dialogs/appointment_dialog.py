#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog do dodawania i edycji wizyt w serwisie.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QTextEdit, QSpinBox,
    QDialogButtonBox, QMessageBox, QCompleter
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QIcon, QFont

from ui.dialogs.client_selector_dialog import ClientSelectorDialog
from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class AppointmentDialog(QDialog):
    """
    Dialog do dodawania i edycji wizyt w serwisie.
    Umożliwia wprowadzenie informacji o kliencie, dacie, godzinie i usłudze.
    """
    
    def __init__(self, db_connection, appointment_id=None, selected_date=None, parent=None):
        """
        Inicjalizacja dialogu wizyty.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            appointment_id (int, optional): ID wizyty do edycji. Domyślnie None (nowa wizyta).
            selected_date (QDate, optional): Domyślna data dla nowej wizyty.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.appointment_id = appointment_id
        self.client_id = None
        
        title = "Dodaj nową wizytę" if appointment_id is None else "Edytuj wizytę"
        self.setWindowTitle(title)
        self.resize(600, 500)
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Jeśli edycja, załaduj dane wizyty
        if appointment_id is not None:
            self.load_appointment_data()
        else:
            # Dla nowej wizyty, ustaw domyślne wartości
            self.set_default_values(selected_date)
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Formularz danych wizyty
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Sekcja klienta
        client_section = QLabel("Dane klienta")
        client_section.setFont(QFont("Segoe UI", 10, QFont.Bold))
        form_layout.addRow(client_section)
        
        # Klient
        self.client_name_input = QLineEdit()
        self.client_name_input.setReadOnly(True)
        form_layout.addRow("Klient:", self.client_name_input)
        
        # Przyciski wyboru klienta
        client_button_layout = QHBoxLayout()
        
        select_client_button = QPushButton("Wybierz klienta")
        select_client_button.setIcon(QIcon(os.path.join(ICONS_DIR, "client.png")))
        select_client_button.clicked.connect(self.select_client)
        client_button_layout.addWidget(select_client_button)
        
        add_client_button = QPushButton("Dodaj nowego klienta")
        add_client_button.setIcon(QIcon(os.path.join(ICONS_DIR, "add-client.png")))
        add_client_button.clicked.connect(self.add_new_client)
        client_button_layout.addWidget(add_client_button)
        
        form_layout.addRow("", client_button_layout)
        
        # Sekcja terminu
        date_section = QLabel("Termin wizyty")
        date_section.setFont(QFont("Segoe UI", 10, QFont.Bold))
        form_layout.addRow(date_section)
        
        # Data wizyty
        self.appointment_date = QDateEdit()
        self.appointment_date.setCalendarPopup(True)
        self.appointment_date.setDate(QDate.currentDate())
        self.appointment_date.dateChanged.connect(self.check_appointment_conflicts)
        form_layout.addRow("Data:", self.appointment_date)
        
        # Godzina wizyty
        self.appointment_time = QTimeEdit()
        self.appointment_time.setTime(QTime(9, 0))  # Domyślnie 9:00
        self.appointment_time.setDisplayFormat("HH:mm")
        self.appointment_time.timeChanged.connect(self.check_appointment_conflicts)
        form_layout.addRow("Godzina:", self.appointment_time)
        
        # Czas trwania
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(15, 480)  # Od 15 minut do 8 godzin
        self.duration_spin.setSingleStep(15)
        self.duration_spin.setValue(60)  # Domyślnie 1 godzina
        self.duration_spin.setSuffix(" min")
        self.duration_spin.valueChanged.connect(self.check_appointment_conflicts)
        form_layout.addRow("Czas trwania:", self.duration_spin)
        
        # Sekcja usługi
        service_section = QLabel("Informacje o usłudze")
        service_section.setFont(QFont("Segoe UI", 10, QFont.Bold))
        form_layout.addRow(service_section)
        
        # Typ usługi
        self.service_type_combo = QComboBox()
        self.service_type_combo.setEditable(True)
        self.service_type_combo.addItems([
            "Wymiana opon",
            "Przechowywanie opon",
            "Naprawa opony",
            "Wyważanie kół",
            "Kontrola ciśnienia",
            "Wymiana oleju",
            "Przegląd sezonowy",
            "Konsultacja techniczna",
            "Inne"
        ])
        form_layout.addRow("Typ usługi:", self.service_type_combo)
        
        # Status wizyty
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Zaplanowana",
            "W trakcie",
            "Zakończona",
            "Anulowana"
        ])
        form_layout.addRow("Status:", self.status_combo)
        
        # Uwagi
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Wprowadź dodatkowe uwagi dotyczące wizyty...")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Uwagi:", self.notes_edit)
        
        # Dodaj formularz do głównego układu
        main_layout.addLayout(form_layout)
        
        # Ostrzeżenie o konfliktach
        self.conflict_warning = QLabel("")
        self.conflict_warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.conflict_warning.setVisible(False)
        main_layout.addWidget(self.conflict_warning)
        
        # Przyciski OK/Anuluj
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_appointment)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def set_default_values(self, selected_date):
        """
        Ustawia domyślne wartości dla nowej wizyty.
        
        Args:
            selected_date (QDate, optional): Domyślna data wizyty.
        """
        # Ustaw domyślną datę, jeśli podano
        if selected_date:
            self.appointment_date.setDate(selected_date)
        else:
            self.appointment_date.setDate(QDate.currentDate())
        
        # Ustaw domyślną godzinę (np. 9:00)
        self.appointment_time.setTime(QTime(9, 0))
        
        # Ustaw domyślny czas trwania (1 godzina)
        self.duration_spin.setValue(60)
        
        # Ustaw domyślny status
        self.status_combo.setCurrentText("Zaplanowana")
    
    def load_appointment_data(self):
        """Ładuje dane wizyty do formularza."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane wizyty
            cursor.execute("""
                SELECT 
                    a.client_id, c.name, a.appointment_date, a.appointment_time, 
                    a.service_type, a.status, a.notes, a.duration
                FROM 
                    appointments a
                JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.id = ?
            """, (self.appointment_id,))
            
            data = cursor.fetchone()
            if not data:
                logger.error(f"Nie znaleziono wizyty o ID: {self.appointment_id}")
                QMessageBox.critical(self, "Błąd", f"Nie znaleziono wizyty o ID: {self.appointment_id}")
                self.reject()
                return
            
            # Rozpakowanie danych
            self.client_id, client_name, appointment_date, appointment_time, service_type, status, notes, duration = data
            
            # Ustawienie danych w formularzu
            self.client_name_input.setText(client_name)
            
            # Ustawienie daty
            if appointment_date:
                self.appointment_date.setDate(QDate.fromString(appointment_date, "yyyy-MM-dd"))
            
            # Ustawienie godziny
            if appointment_time:
                try:
                    time_parts = appointment_time.split(":")
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        self.appointment_time.setTime(QTime(hour, minute))
                except (ValueError, IndexError):
                    # Jeśli format nie jest poprawny, użyj domyślnej godziny
                    self.appointment_time.setTime(QTime(9, 0))
            
            # Ustawienie typu usługi
            if service_type:
                # Sprawdź, czy typ usługi istnieje na liście
                index = self.service_type_combo.findText(service_type)
                if index >= 0:
                    self.service_type_combo.setCurrentIndex(index)
                else:
                    # Jeśli nie, dodaj go i ustaw jako aktualny
                    self.service_type_combo.addItem(service_type)
                    self.service_type_combo.setCurrentText(service_type)
            
            # Ustawienie statusu
            if status:
                index = self.status_combo.findText(status)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
            
            # Ustawienie uwag
            if notes:
                self.notes_edit.setText(notes)
            
            # Ustawienie czasu trwania
            if duration:
                self.duration_spin.setValue(duration)
            
            logger.debug(f"Załadowano dane wizyty o ID: {self.appointment_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych wizyty: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych wizyty:\n{str(e)}")
    
    def select_client(self):
        """Otwiera okno wyboru klienta."""
        dialog = ClientSelectorDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.client_id = dialog.selected_client_id
            self.client_name_input.setText(dialog.selected_client_name)
    
    def add_new_client(self):
        """Otwiera okno dodawania nowego klienta."""
        from ui.dialogs.client_dialog import ClientDialog
        dialog = ClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.client_id = dialog.client_id
            self.client_name_input.setText(dialog.client_name)
    
    def check_appointment_conflicts(self):
        """Sprawdza, czy wybrana data i godzina nie kolidują z innymi wizytami."""
        try:
            if not self.client_id:
                return
            
            cursor = self.conn.cursor()
            
            # Pobierz wybraną datę i godzinę
            selected_date = self.appointment_date.date().toString("yyyy-MM-dd")
            selected_time = self.appointment_time.time().toString("HH:mm")
            duration = self.duration_spin.value()
            
            # Oblicz czas zakończenia wizyty
            start_time = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
            end_time = start_time + timedelta(minutes=duration)
            
            # Pobierz inne wizyty na ten dzień
            query = """
                SELECT 
                    id, appointment_time, duration
                FROM 
                    appointments
                WHERE 
                    appointment_date = ? AND
                    id != ? AND
                    status IN ('Zaplanowana', 'W trakcie')
            """
            cursor.execute(query, (selected_date, self.appointment_id or -1))
            
            other_appointments = cursor.fetchall()
            conflicts = []
            
            for app_id, app_time, app_duration in other_appointments:
                try:
                    # Oblicz czas rozpoczęcia i zakończenia innej wizyty
                    other_start_time = datetime.strptime(f"{selected_date} {app_time}", "%Y-%m-%d %H:%M")
                    other_end_time = other_start_time + timedelta(minutes=app_duration or 60)
                    
                    # Sprawdź, czy występuje konflikt
                    if (start_time < other_end_time and end_time > other_start_time):
                        # Pobierz nazwę klienta
                        cursor.execute("""
                            SELECT c.name
                            FROM appointments a
                            JOIN clients c ON a.client_id = c.id
                            WHERE a.id = ?
                        """, (app_id,))
                        
                        client_name = cursor.fetchone()[0]
                        conflicts.append(f"{client_name} ({app_time})")
                except Exception as e:
                    logger.error(f"Błąd podczas sprawdzania konfliktu wizyt: {e}")
            
            # Wyświetl ostrzeżenie, jeśli są konflikty
            if conflicts:
                self.conflict_warning.setText(f"Uwaga: Konflikt z wizytami: {', '.join(conflicts)}")
                self.conflict_warning.setVisible(True)
            else:
                self.conflict_warning.setVisible(False)
            
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania konfliktów wizyt: {e}")
    
    def validate_form(self):
        """
        Sprawdza poprawność danych w formularzu.
        
        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym razie
        """
        # Sprawdzenie klienta
        if not self.client_id:
            QMessageBox.critical(self, "Błąd", "Musisz wybrać klienta.")
            return False
        
        # Sprawdzenie typu usługi
        if not self.service_type_combo.currentText().strip():
            QMessageBox.critical(self, "Błąd", "Typ usługi jest wymagany.")
            return False
        
        # Sprawdzenie, czy data nie jest z przeszłości (opcjonalne)
        current_date = QDate.currentDate()
        selected_date = self.appointment_date.date()
        
        if selected_date < current_date:
            response = QMessageBox.question(
                self,
                "Uwaga",
                "Wybrana data jest z przeszłości. Czy na pewno chcesz kontynuować?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if response == QMessageBox.No:
                return False
        
        return True
    
    def save_appointment(self):
        """Zapisuje wizytę do bazy danych."""
        if not self.validate_form():
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Przygotowanie danych
            client_id = self.client_id
            appointment_date = self.appointment_date.date().toString("yyyy-MM-dd")
            appointment_time = self.appointment_time.time().toString("HH:mm")
            service_type = self.service_type_combo.currentText()
            status = self.status_combo.currentText()
            notes = self.notes_edit.toPlainText()
            duration = self.duration_spin.value()
            
            # Zapis do bazy danych
            if self.appointment_id:  # Edycja istniejącej wizyty
                cursor.execute("""
                    UPDATE appointments
                    SET client_id = ?, appointment_date = ?, appointment_time = ?,
                        service_type = ?, status = ?, notes = ?, duration = ?
                    WHERE id = ?
                """, (
                    client_id, appointment_date, appointment_time,
                    service_type, status, notes, duration,
                    self.appointment_id
                ))
                
                logger.info(f"Zaktualizowano wizytę o ID: {self.appointment_id}")
                
            else:  # Nowa wizyta
                cursor.execute("""
                    INSERT INTO appointments (
                        client_id, appointment_date, appointment_time,
                        service_type, status, notes, duration
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    client_id, appointment_date, appointment_time,
                    service_type, status, notes, duration
                ))
                
                # Pobranie ID nowej wizyty
                self.appointment_id = cursor.lastrowid
                
                logger.info(f"Utworzono nową wizytę o ID: {self.appointment_id}")
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Zamknij dialog z sukcesem
            self.accept()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania wizyty: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania wizyty:\n{str(e)}")
