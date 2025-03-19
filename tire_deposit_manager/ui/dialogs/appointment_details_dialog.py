#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog wyświetlający szczegóły wizyty.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QFrame, QSpacerItem, QSizePolicy, QFormLayout, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor

from ui.notifications import NotificationManager, NotificationTypes
from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class AppointmentDetailsDialog(QDialog):
    """
    Dialog wyświetlający szczegóły wizyty.
    Umożliwia również zmianę statusu wizyty, wysłanie przypomnień i inne akcje.
    """
    
    def __init__(self, db_connection, appointment_id, parent=None):
        """
        Inicjalizacja dialogu szczegółów wizyty.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
            appointment_id (int): ID wizyty
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        self.conn = db_connection
        self.appointment_id = appointment_id
        
        self.setWindowTitle("Szczegóły wizyty")
        self.resize(700, 500)
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Ładowanie danych wizyty
        self.load_appointment_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika."""
        main_layout = QVBoxLayout(self)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        
        # Ikona wizyty
        icon_label = QLabel()
        icon_pixmap = QPixmap(os.path.join(ICONS_DIR, "calendar.png"))
        icon_label.setPixmap(icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        # Tytuł wizyty
        self.title_label = QLabel("Wizyta #")
        self.title_label.setObjectName("headerLabel")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch(1)
        
        # Status wizyty
        self.status_label = QLabel("Status")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("""
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_label)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Główna sekcja z danymi
        content_layout = QGridLayout()
        
        # Sekcja informacji o kliencie
        client_frame = QFrame()
        client_frame.setObjectName("detailsFrame")
        client_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        client_layout = QVBoxLayout(client_frame)
        
        client_title = QLabel("Dane klienta")
        client_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        client_layout.addWidget(client_title)
        
        client_form = QFormLayout()
        
        self.client_name_label = QLabel()
        client_form.addRow("Nazwa:", self.client_name_label)
        
        self.client_phone_label = QLabel()
        client_form.addRow("Telefon:", self.client_phone_label)
        
        self.client_email_label = QLabel()
        client_form.addRow("E-mail:", self.client_email_label)
        
        client_layout.addLayout(client_form)
        content_layout.addWidget(client_frame, 0, 0)
        
        # Sekcja informacji o terminie
        date_frame = QFrame()
        date_frame.setObjectName("detailsFrame")
        date_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        date_layout = QVBoxLayout(date_frame)
        
        date_title = QLabel("Termin wizyty")
        date_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        date_layout.addWidget(date_title)
        
        date_form = QFormLayout()
        
        self.appointment_date_label = QLabel()
        date_form.addRow("Data:", self.appointment_date_label)
        
        self.appointment_time_label = QLabel()
        date_form.addRow("Godzina:", self.appointment_time_label)
        
        self.duration_label = QLabel()
        date_form.addRow("Czas trwania:", self.duration_label)
        
        date_layout.addLayout(date_form)
        content_layout.addWidget(date_frame, 0, 1)
        
        # Sekcja informacji o usłudze
        service_frame = QFrame()
        service_frame.setObjectName("detailsFrame")
        service_frame.setStyleSheet("""
            QFrame#detailsFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        service_layout = QVBoxLayout(service_frame)
        
        service_title = QLabel("Informacje o usłudze")
        service_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        service_layout.addWidget(service_title)
        
        service_form = QFormLayout()
        
        self.service_type_label = QLabel()
        service_form.addRow("Typ usługi:", self.service_type_label)
        
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        service_form.addRow("Uwagi:", self.notes_label)
        
        service_layout.addLayout(service_form)
        content_layout.addWidget(service_frame, 1, 0, 1, 2)
        
        main_layout.addLayout(content_layout)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edytuj")
        edit_button.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.png")))
        edit_button.clicked.connect(self.edit_appointment)
        action_layout.addWidget(edit_button)
        
        # Przycisk zmiany statusu
        self.change_status_button = QPushButton("Zmień status")
        self.change_status_button.setIcon(QIcon(os.path.join(ICONS_DIR, "status.png")))
        self.change_status_button.clicked.connect(self.show_status_menu)
        action_layout.addWidget(self.change_status_button)
        
        # Przyciski komunikacji
        send_email_button = QPushButton("Wyślij e-mail")
        send_email_button.setIcon(QIcon(os.path.join(ICONS_DIR, "email.png")))
        send_email_button.clicked.connect(self.send_email)
        action_layout.addWidget(send_email_button)
        
        send_sms_button = QPushButton("Wyślij SMS")
        send_sms_button.setIcon(QIcon(os.path.join(ICONS_DIR, "sms.png")))
        send_sms_button.clicked.connect(self.send_sms)
        action_layout.addWidget(send_sms_button)
        
        # Elastyczna przestrzeń
        action_layout.addStretch(1)
        
        # Przycisk usuwania
        delete_button = QPushButton("Usuń")
        delete_button.setObjectName("deleteButton")
        delete_button.setIcon(QIcon(os.path.join(ICONS_DIR, "delete.png")))
        delete_button.clicked.connect(self.delete_appointment)
        action_layout.addWidget(delete_button)
        
        # Przycisk zamknięcia
        close_button = QPushButton("Zamknij")
        close_button.setIcon(QIcon(os.path.join(ICONS_DIR, "close.png")))
        close_button.clicked.connect(self.accept)
        action_layout.addWidget(close_button)
        
        main_layout.addLayout(action_layout)
    
    def load_appointment_data(self):
        """Ładuje dane wizyty z bazy danych."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane wizyty
            cursor.execute("""
                SELECT 
                    a.client_id, c.name, c.phone_number, c.email,
                    a.appointment_date, a.appointment_time, a.service_type, 
                    a.status, a.notes, a.duration
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
            client_id, client_name, client_phone, client_email, appointment_date, appointment_time, service_type, status, notes, duration = data
            
            # Aktualizacja danych w interfejsie
            self.title_label.setText(f"Wizyta #{self.appointment_id}: {client_name}")
            
            # Ustawienie statusu z odpowiednim kolorem
            self.status_label.setText(status)
            
            if status == "Zaplanowana":
                self.status_label.setStyleSheet("background-color: #3498db; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            elif status == "W trakcie":
                self.status_label.setStyleSheet("background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            elif status == "Zakończona":
                self.status_label.setStyleSheet("background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            elif status == "Anulowana":
                self.status_label.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
            
            # Dane klienta
            self.client_name_label.setText(client_name)
            self.client_phone_label.setText(client_phone or "-")
            self.client_email_label.setText(client_email or "-")
            
            # Dane terminu
            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                    
                    # Dodaj dzień tygodnia
                    weekday = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"][date_obj.weekday()]
                    formatted_date += f" ({weekday})"
                    
                    self.appointment_date_label.setText(formatted_date)
                except ValueError:
                    self.appointment_date_label.setText(appointment_date)
            else:
                self.appointment_date_label.setText("-")
            
            self.appointment_time_label.setText(appointment_time or "-")
            self.duration_label.setText(f"{duration or 60} minut")
            
            # Dane usługi
            self.service_type_label.setText(service_type or "-")
            self.notes_label.setText(notes or "-")
            
            logger.debug(f"Załadowano dane wizyty o ID: {self.appointment_id}")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych wizyty: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych wizyty:\n{str(e)}")
    
    def edit_appointment(self):
        """Otwiera okno edycji wizyty."""
        from ui.dialogs.appointment_dialog import AppointmentDialog
        dialog = AppointmentDialog(self.conn, appointment_id=self.appointment_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_appointment_data()
    
    def show_status_menu(self):
        """Wyświetla menu wyboru statusu wizyty."""
        menu = QMenu(self)
        
        # Pobierz aktualny status
        current_status = self.status_label.text()
        
        # Dodaj opcje statusów
        statuses = ["Zaplanowana", "W trakcie", "Zakończona", "Anulowana"]
        
        for status in statuses:
            if status != current_status:  # Nie pokazuj aktualnego statusu
                action = menu.addAction(status)
                action.triggered.connect(lambda checked, s=status: self.change_status(s))
        
        # Wyświetl menu pod przyciskiem
        menu.exec(self.change_status_button.mapToGlobal(self.change_status_button.rect().bottomLeft()))
    
    def change_status(self, new_status):
        """
        Zmienia status wizyty.
        
        Args:
            new_status (str): Nowy status wizyty
        """
        try:
            cursor = self.conn.cursor()
            
            # Aktualizacja statusu
            cursor.execute(
                "UPDATE appointments SET status = ? WHERE id = ?",
                (new_status, self.appointment_id)
            )
            
            # Zatwierdzenie zmian
            self.conn.commit()
            
            # Odświeżenie danych
            self.load_appointment_data()
            
            # Powiadomienie
            NotificationManager.get_instance().show_notification(
                f"Status wizyty został zmieniony na '{new_status}'.",
                NotificationTypes.SUCCESS
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas aktualizacji statusu wizyty: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas aktualizacji statusu wizyty:\n{str(e)}")
    
    def delete_appointment(self):
        """Usuwa wizytę."""
        confirmation = QMessageBox.question(
            self,
            "Potwierdź usunięcie",
            "Czy na pewno chcesz usunąć tę wizytę? Ta operacja jest nieodwracalna.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmation == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                
                # Usunięcie wizyty
                cursor.execute("DELETE FROM appointments WHERE id = ?", (self.appointment_id,))
                
                # Zatwierdzenie zmian
                self.conn.commit()
                
                # Powiadomienie
                NotificationManager.get_instance().show_notification(
                    "Wizyta została usunięta pomyślnie.",
                    NotificationTypes.SUCCESS
                )
                
                # Zamknij okno
                self.accept()
                
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Błąd podczas usuwania wizyty: {e}")
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania wizyty:\n{str(e)}")
    
    def send_email(self):
        """Wysyła e-mail z przypomnieniem o wizycie."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane klienta i wizyty
            cursor.execute("""
                SELECT 
                    c.email, c.name, a.appointment_date, a.appointment_time, a.service_type
                FROM 
                    appointments a
                JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.id = ?
            """, (self.appointment_id,))
            
            data = cursor.fetchone()
            if not data:
                QMessageBox.critical(self, "Błąd", "Nie znaleziono danych wizyty.")
                return
            
            email, client_name, appointment_date, appointment_time, service_type = data
            
            if not email:
                QMessageBox.warning(self, "Brak adresu e-mail", f"Klient {client_name} nie ma przypisanego adresu e-mail.")
                return
            
            # Formatowanie daty
            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except ValueError:
                    formatted_date = appointment_date
            else:
                formatted_date = "-"
            
            # Przygotowanie treści e-maila
            email_subject = f"Przypomnienie o wizycie w serwisie"
            email_body = f"""Szanowny/a {client_name},

Przypominamy o zaplanowanej wizycie w naszym serwisie:

Data: {formatted_date}
Godzina: {appointment_time}
Usługa: {service_type}

W razie pytań lub konieczności zmiany terminu prosimy o kontakt.

Z poważaniem,
Zespół Serwisu Opon MATEO
"""
            
            # Otwarcie okna do wysłania e-maila
            from ui.dialogs.send_email_dialog import SendEmailDialog
            dialog = SendEmailDialog(
                self.conn, 
                self.appointment_id, 
                email_to=email,
                email_subject=email_subject,
                email_body=email_body,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania e-maila: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wysyłania e-maila:\n{str(e)}")
    
    def send_sms(self):
        """Wysyła SMS z przypomnieniem o wizycie."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz dane klienta i wizyty
            cursor.execute("""
                SELECT 
                    c.phone_number, c.name, a.appointment_date, a.appointment_time, a.service_type
                FROM 
                    appointments a
                JOIN 
                    clients c ON a.client_id = c.id
                WHERE 
                    a.id = ?
            """, (self.appointment_id,))
            
            data = cursor.fetchone()
            if not data:
                QMessageBox.critical(self, "Błąd", "Nie znaleziono danych wizyty.")
                return
            
            phone_number, client_name, appointment_date, appointment_time, service_type = data
            
            if not phone_number:
                QMessageBox.warning(self, "Brak numeru telefonu", f"Klient {client_name} nie ma przypisanego numeru telefonu.")
                return
            
            # Formatowanie daty
            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except ValueError:
                    formatted_date = appointment_date
            else:
                formatted_date = "-"
            
            # Przygotowanie treści SMS
            sms_text = f"Przypomnienie: {client_name}, masz wizytę {formatted_date} o {appointment_time} - {service_type}. Pozdrawiamy, Serwis Opon MATEO"
            
            # Otwarcie okna do wysłania SMS
            from ui.dialogs.send_sms_dialog import SendSMSDialog
            dialog = SendSMSDialog(
                self.conn, 
                self.appointment_id,
                phone_number=phone_number,
                sms_text=sms_text,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania SMS: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wysyłania SMS:\n{str(e)}")