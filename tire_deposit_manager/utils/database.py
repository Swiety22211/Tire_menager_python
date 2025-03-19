#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł do obsługi bazy danych SQLite.
Zawiera funkcje tworzenia połączenia, inicjalizacji bazy danych, tworzenia kopii zapasowych i przywracania z backupu.
"""

import os
import sqlite3
import logging
import shutil
from datetime import datetime, timedelta

from utils.paths import DATABASE_PATH, BACKUP_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

def create_connection():
    """
    Nawiązuje połączenie z bazą danych SQLite.
    
    Returns:
        Connection: Obiekt połączenia z bazą danych lub None w przypadku błędu
    """
    try:
        # Upewnij się, że katalog na bazę danych istnieje
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        # Połączenie z bazą danych
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Ustawienie zwracania wierszy jako słowniki
        conn.row_factory = sqlite3.Row
        
        # Ustawienie obsługi kluczy obcych
        conn.execute("PRAGMA foreign_keys = ON")
        
        logger.info(f"Połączono z bazą danych: {DATABASE_PATH}")
        return conn
    except Exception as e:
        logger.error(f"Błąd podczas łączenia z bazą danych: {e}")
        return None

def initialize_database(conn):
    """
    Inicjalizuje strukturę bazy danych, tworząc tabele jeśli nie istnieją.
    
    Args:
        conn: Połączenie z bazą danych SQLite
    """
    try:
        cursor = conn.cursor()
        
        # Tabela klientów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_number TEXT,
                email TEXT,
                additional_info TEXT,
                discount REAL DEFAULT 0,
                barcode TEXT
            )
        ''')
        
        # Tabela depozytów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                car_model TEXT,
                registration_number TEXT,
                tire_brand TEXT,
                tire_size TEXT,
                quantity INTEGER DEFAULT 1,
                location TEXT,
                deposit_date TEXT,
                expected_return_date TEXT,
                status TEXT DEFAULT 'Aktywny',
                season TEXT,
                price REAL,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        
        # Tabela inwentarza opon
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_model TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                price REAL,
                dot TEXT,
                season_type TEXT,
                notes TEXT
            )
        ''')
        
        # Tabela części i akcesoriów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                catalog_number TEXT,
                category TEXT,
                manufacturer TEXT,
                quantity INTEGER DEFAULT 0,
                minimum_quantity INTEGER DEFAULT 1,
                price REAL,
                location TEXT,
                description TEXT,
                barcode TEXT,
                supplier TEXT,
                vat_rate TEXT DEFAULT '23%',
                unit TEXT DEFAULT 'szt.',
                warranty TEXT
            )
        ''')
        
        # Tabela korekt stanów magazynowych
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER,
                adjustment_date TEXT,
                operation TEXT,
                quantity INTEGER,
                old_quantity INTEGER,
                new_quantity INTEGER,
                reason TEXT,
                document TEXT,
                notes TEXT,
                user TEXT,
                FOREIGN KEY(part_id) REFERENCES parts(id)
            )
        ''')
        
        # Tabela wizyt
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                appointment_date TEXT,
                appointment_time TEXT,
                service_type TEXT,
                status TEXT DEFAULT 'Zaplanowana',
                notes TEXT,
                duration INTEGER DEFAULT 60,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        
        # Tabela zamówień
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                order_date TEXT,
                status TEXT DEFAULT 'Nowe',
                total_amount REAL,
                notes TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        
        # Tabela elementów zamówienia
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_type TEXT,
                item_id INTEGER,
                name TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        ''')
        
        # Tabela lokalizacji
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                capacity INTEGER,
                used INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela ustawień
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        ''')
        
        # Tabela szablonów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT,
                last_modified TEXT
            )
        ''')
        
        # Zatwierdzenie zmian
        conn.commit()
        
        # Sprawdzenie, czy istnieją podstawowe ustawienia
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            # Dodanie podstawowych ustawień
            settings_data = [
                ('company_name', 'Serwis Opon MATEO', 'Nazwa firmy'),
                ('company_address', 'ul. Przykładowa 123, 00-000 Miasto', 'Adres firmy'),
                ('company_phone', '+48 123 456 789', 'Telefon firmowy'),
                ('company_email', 'kontakt@serwisopony.pl', 'Adres e-mail firmy'),
                ('company_tax_id', '123-456-78-90', 'NIP firmy'),
                ('default_vat_rate', '23%', 'Domyślna stawka VAT'),
                ('app_theme', 'Light', 'Motyw aplikacji (Light/Dark)'),
                ('backup_interval', '7', 'Interwał automatycznych kopii zapasowych (dni)'),
            ]
            
            cursor.executemany(
                "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                settings_data
            )
            
            conn.commit()
        
        logger.info("Struktura bazy danych została zainicjalizowana")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Błąd podczas inicjalizacji bazy danych: {e}")

def backup_database(conn, backup_path=None):
    """
    Tworzy kopię zapasową bazy danych.
    
    Args:
        conn: Połączenie z bazą danych SQLite
        backup_path (str, optional): Ścieżka do pliku kopii zapasowej. 
                                     Jeśli nie podano, nazwa zostanie wygenerowana automatycznie.
    
    Returns:
        bool: True jeśli backup zakończył się sukcesem, False w przeciwnym razie
    """
    try:
        # Zamknięcie wszystkich aktywnych transakcji
        conn.commit()
        
        # Generowanie ścieżki do pliku kopii zapasowej, jeśli nie została podana
        if not backup_path:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
        
        # Tworzenie kopii zapasowej przez kopiowanie pliku bazy danych
        shutil.copy2(DATABASE_PATH, backup_path)
        
        logger.info(f"Utworzono kopię zapasową bazy danych: {backup_path}")
        return True
    
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia kopii zapasowej: {e}")
        return False

def restore_database(backup_path):
    """
    Przywraca bazę danych z kopii zapasowej.
    
    Args:
        backup_path (str): Ścieżka do pliku kopii zapasowej
    
    Returns:
        bool: True jeśli przywracanie zakończyło się sukcesem, False w przeciwnym razie
    """
    try:
        # Sprawdzenie czy plik kopii zapasowej istnieje
        if not os.path.exists(backup_path):
            logger.error(f"Plik kopii zapasowej nie istnieje: {backup_path}")
            return False
        
        # Utworzenie kopii zapasowej aktualnej bazy danych przed przywróceniem
        current_backup_path = os.path.join(
            BACKUP_DIR, 
            f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        # Upewnij się, że katalog kopii zapasowych istnieje
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Skopiowanie aktualnej bazy danych do backup
        if os.path.exists(DATABASE_PATH):
            shutil.copy2(DATABASE_PATH, current_backup_path)
            logger.info(f"Utworzono kopię zapasową aktualnej bazy danych przed przywróceniem: {current_backup_path}")
        
        # Przywrócenie bazy danych z kopii zapasowej
        shutil.copy2(backup_path, DATABASE_PATH)
        
        logger.info(f"Przywrócono bazę danych z kopii zapasowej: {backup_path}")
        return True
    
    except Exception as e:
        logger.error(f"Błąd podczas przywracania bazy danych: {e}")
        return False

def initialize_test_data(conn):
    """
    Inicjalizuje przykładowe dane w bazie danych dla celów testowych.
    
    Args:
        conn: Połączenie z bazą danych SQLite
    """
    try:
        cursor = conn.cursor()
        
        # Sprawdzenie, czy baza danych jest pusta
        cursor.execute("SELECT COUNT(*) FROM clients")
        if cursor.fetchone()[0] > 0:
            logger.info("Baza danych już zawiera dane, pomijanie inicjalizacji przykładowych danych")
            return
        
        # Dodanie przykładowych klientów
        clients_data = [
            ('Jan Kowalski', '123456789', 'jan.kowalski@example.com', 'Stały klient', 5, 'C-00001'),
            ('Anna Nowak', '987654321', 'anna.nowak@example.com', 'VIP', 10, 'C-00002'),
            ('Piotr Wiśniewski', '555666777', 'piotr.wisniewski@example.com', '', 0, 'C-00003'),
            ('Katarzyna Lewandowska', '111222333', 'katarzyna.lewandowska@example.com', 'Klientka biznesowa', 8, 'C-00004'),
            ('Marek Wójcik', '444555666', 'marek.wojcik@example.com', '', 0, 'C-00005')
        ]
        
        cursor.executemany(
            "INSERT INTO clients (name, phone_number, email, additional_info, discount, barcode) VALUES (?, ?, ?, ?, ?, ?)",
            clients_data
        )
        
        # Dodanie przykładowych depozytów
        today = datetime.now().strftime("%Y-%m-%d")
        next_season = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        
        deposits_data = [
            (1, 'Volkswagen Golf', 'WA12345', 'Continental', '205/55 R16', 4, 'A-01-02', today, next_season, 'Aktywny', 'Zimowe', 120.00),
            (2, 'BMW X5', 'WB54321', 'Michelin', '255/50 R19', 4, 'A-02-03', today, next_season, 'Aktywny', 'Letnie', 180.00),
            (3, 'Toyota Corolla', 'WC98765', 'Bridgestone', '195/65 R15', 4, 'B-01-01', today, next_season, 'Aktywny', 'Zimowe', 100.00),
            (4, 'Audi A4', 'WD45678', 'Pirelli', '225/45 R17', 4, 'B-02-02', today, next_season, 'Aktywny', 'Letnie', 150.00),
            (5, 'Ford Focus', 'WE87654', 'Goodyear', '205/60 R16', 4, 'C-01-03', today, next_season, 'Aktywny', 'Zimowe', 110.00)
        ]
        
        cursor.executemany(
            """
            INSERT INTO deposits (
                client_id, car_model, registration_number, tire_brand, tire_size,
                quantity, location, deposit_date, expected_return_date, status, season, price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            deposits_data
        )
        
        # Dodanie przykładowych opon na stanie
        inventory_data = [
            ('Continental ContiWinterContact', '205/55 R16', 8, 450.00, '2023', 'Zimowe', ''),
            ('Michelin Pilot Sport', '255/50 R19', 4, 980.00, '2023', 'Letnie', ''),
            ('Bridgestone Blizzak', '195/65 R15', 12, 320.00, '2023', 'Zimowe', ''),
            ('Pirelli P Zero', '225/45 R17', 6, 720.00, '2023', 'Letnie', ''),
            ('Goodyear UltraGrip', '205/60 R16', 10, 390.00, '2023', 'Zimowe', '')
        ]
        
        cursor.executemany(
            """
            INSERT INTO inventory (
                brand_model, size, quantity, price, dot, season_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            inventory_data
        )
        
        # Dodanie przykładowych części i akcesoriów
        parts_data = [
            ('Olej silnikowy Mobil 1', 'MOB-1234', 'Oleje', 'Mobil', 20, 5, 150.00, 'Regał A-1', 'Syntetyczny olej silnikowy 5W-30', 'P-00001', 'AutoParts', '23%', 'L', ''),
            ('Filtr oleju Bosch', 'BOS-5678', 'Filtry', 'Bosch', 15, 3, 35.00, 'Regał A-2', 'Filtr oleju do samochodów osobowych', 'P-00002', 'AutoParts', '23%', 'szt.', '24 miesiące'),
            ('Filtr powietrza Mann', 'MAN-9101', 'Filtry', 'Mann', 12, 3, 45.00, 'Regał A-2', 'Filtr powietrza do samochodów osobowych', 'P-00003', 'AutoParts', '23%', 'szt.', '24 miesiące'),
            ('Klocki hamulcowe Zimmermann', 'ZIM-1122', 'Hamulce', 'Zimmermann', 8, 2, 220.00, 'Regał B-1', 'Klocki hamulcowe przednie', 'P-00004', 'BrakeParts', '23%', 'kpl.', '24 miesiące'),
            ('Płyn do spryskiwaczy zimowy', 'SPR-3344', 'Płyny', 'WinterClean', 30, 5, 25.00, 'Regał C-1', 'Płyn do spryskiwaczy -22°C', 'P-00005', 'CarChem', '23%', 'L', '')
        ]
        
        cursor.executemany(
            """
            INSERT INTO parts (
                name, catalog_number, category, manufacturer, quantity, minimum_quantity,
                price, location, description, barcode, supplier, vat_rate, unit, warranty
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            parts_data
        )
        
        # Dodanie przykładowych wizyt
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        day_after_tomorrow = today + timedelta(days=2)
        
        appointments_data = [
            (1, today.strftime("%Y-%m-%d"), '09:00', 'Wymiana opon', 'Zaplanowana', 'Wymiana z zimowych na letnie', 60),
            (2, tomorrow.strftime("%Y-%m-%d"), '10:30', 'Przechowywanie opon', 'Zaplanowana', 'Odbiór opon z depozytu', 30),
            (3, today.strftime("%Y-%m-%d"), '14:00', 'Naprawa opony', 'Zakończona', 'Naprawa przebitej opony', 45),
            (4, day_after_tomorrow.strftime("%Y-%m-%d"), '11:15', 'Wyważanie kół', 'Zaplanowana', '', 60),
            (5, tomorrow.strftime("%Y-%m-%d"), '16:00', 'Wymiana oleju', 'Zaplanowana', 'Wymiana oleju i filtrów', 90)
        ]
        
        cursor.executemany(
            """
            INSERT INTO appointments (
                client_id, appointment_date, appointment_time, service_type, 
                status, notes, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            appointments_data
        )
        
        # Dodanie przykładowych lokalizacji
        locations_data = [
            ('A-01', 'Regał A, półka 1', 20, 8),
            ('A-02', 'Regał A, półka 2', 20, 12),
            ('B-01', 'Regał B, półka 1', 15, 4),
            ('B-02', 'Regał B, półka 2', 15, 8),
            ('C-01', 'Regał C, półka 1', 30, 12)
        ]
        
        cursor.executemany(
            """
            INSERT INTO locations (
                name, description, capacity, used
            ) VALUES (?, ?, ?, ?)
            """,
            locations_data
        )
        
        # Dodanie przykładowych zamówień
        today_str = today.strftime("%Y-%m-%d")
        
        cursor.execute(
            """
            INSERT INTO orders (
                client_id, order_date, status, total_amount, notes
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (1, today_str, 'Nowe', 980.00, 'Pilne zamówienie')
        )
        
        order_id = cursor.lastrowid
        
        order_items_data = [
            (order_id, 'część', 2, 'Filtr oleju Bosch', 1, 35.00),
            (order_id, 'opona', 1, 'Continental ContiWinterContact 205/55 R16', 4, 450.00)
        ]
        
        cursor.executemany(
            """
            INSERT INTO order_items (
                order_id, item_type, item_id, name, quantity, price
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            order_items_data
        )
        
        # Dodanie przykładowych szablonów
        templates_data = [
            ('Faktura standardowa', 'invoice', '<!-- Szablon faktury -->', today_str),
            ('Raport dzienny', 'report', '# Raport dzienny\n\n{{date}}\n\n...', today_str),
            ('Etykieta depozytu', 'label', '**Depozyt** {{deposit_id}}\nKlient: {{client_name}}', today_str)
        ]
        
        cursor.executemany(
            """
            INSERT INTO templates (
                name, type, content, last_modified
            ) VALUES (?, ?, ?, ?)
            """,
            templates_data
        )
        
        # Zatwierdzenie zmian
        conn.commit()
        
        logger.info("Zainicjalizowano przykładowe dane w bazie danych")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Błąd podczas inicjalizacji przykładowych danych: {e}")