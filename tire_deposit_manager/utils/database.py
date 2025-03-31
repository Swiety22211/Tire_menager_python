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

# Funkcja poprawiona do bezpiecznej inicjalizacji bazy danych
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
                barcode TEXT,
                client_type TEXT DEFAULT 'Indywidualny',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # Sprawdź, czy kolumna client_type istnieje w tabeli clients
        cursor.execute("PRAGMA table_info(clients)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Dodaj kolumnę client_type, jeśli nie istnieje
        if "client_type" not in columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN client_type TEXT DEFAULT 'Indywidualny'")
            logger.info("Dodano kolumnę client_type do tabeli clients")
            
        # Dodaj kolumnę created_at, jeśli nie istnieje
        if "created_at" not in columns:
            # Użyj stałej wartości czasu, bo SQLite nie pozwala na dodanie kolumny z funkcją jako domyślną wartość
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(f"ALTER TABLE clients ADD COLUMN created_at TEXT DEFAULT '{current_time}'")
            logger.info("Dodano kolumnę created_at do tabeli clients")
        
        # Tabela pojazdów klientów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                registration_number TEXT UNIQUE,
                vin TEXT,
                tire_size TEXT,
                vehicle_type TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        ''')
        
        # Dodanie indeksu na kolumnie client_id w tabeli vehicles
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vehicles_client_id ON vehicles(client_id)
        ''')
        
        # Dodanie indeksu na kolumnie registration_number w tabeli vehicles
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration_number)
        ''')
        
        # Sprawdź, czy tabela deposits istnieje
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deposits'")
        if not cursor.fetchone():
            # Jeśli tabela nie istnieje, utwórz ją z nową strukturą
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    deposit_date TEXT NOT NULL,
                    pickup_date TEXT NOT NULL,
                    tire_size TEXT NOT NULL,
                    tire_type TEXT NOT NULL,
                    quantity INTEGER DEFAULT 4,
                    location TEXT,
                    status TEXT DEFAULT 'Aktywny',
                    notes TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')
            logger.info("Utworzono tabelę deposits z nową strukturą")
        else:
            # Tabela już istnieje, sprawdźmy jej strukturę
            cursor.execute("PRAGMA table_info(deposits)")
            deposits_columns = [column[1] for column in cursor.fetchall()]
            
            # Sprawdzamy czy tabela ma już nową strukturę, jeśli nie, dodajemy brakujące kolumny
            if "deposit_date" not in deposits_columns:
                cursor.execute("ALTER TABLE deposits ADD COLUMN deposit_date TEXT DEFAULT (datetime('now', 'localtime'))")
                logger.info("Dodano kolumnę deposit_date do tabeli deposits")
            
            if "pickup_date" not in deposits_columns:
                cursor.execute("ALTER TABLE deposits ADD COLUMN pickup_date TEXT DEFAULT (datetime('now', '+6 months', 'localtime'))")
                logger.info("Dodano kolumnę pickup_date do tabeli deposits")
            
            if "tire_type" not in deposits_columns:
                cursor.execute("ALTER TABLE deposits ADD COLUMN tire_type TEXT DEFAULT 'Nieznany'")
                logger.info("Dodano kolumnę tire_type do tabeli deposits")
        
        # Tabela inwentarza opon
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_model TEXT NOT NULL,
                size TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                quantity INTEGER DEFAULT 0,
                price REAL,
                dot TEXT,
                season_type TEXT,
                condition TEXT DEFAULT 'Nowy',
                status TEXT DEFAULT 'Dostępny',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
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
                warranty TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
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
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
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
                vehicle_id INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
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
                vehicle_id INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
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
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
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
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # Tabela ustawień
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # Tabela szablonów
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT,
                last_modified TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')

        # Tabela logów SMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id INTEGER,
                phone_number TEXT,
                content TEXT,
                sent_date TEXT,
                status TEXT,
                FOREIGN KEY (deposit_id) REFERENCES deposits(id)
            )
        ''')

        # Tabela logów Email
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id INTEGER,
                email TEXT,
                subject TEXT,
                sent_date TEXT,
                status TEXT,
                FOREIGN KEY (deposit_id) REFERENCES deposits(id)
            )
        ''')
        
        # Tabela logów emaili zamówień
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                email TEXT,
                subject TEXT,
                sent_date TEXT,
                status TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')

        # Tabela logów SMS zamówień
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_sms_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                phone_number TEXT,
                content TEXT,
                sent_date TEXT,
                status TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
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
                ('app_theme', 'Dark', 'Motyw aplikacji (Light/Dark)'),
                ('backup_interval', '7', 'Interwał automatycznych kopii zapasowych (dni)'),
            ]
            
            cursor.executemany(
                "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                settings_data
            )
            
            conn.commit()
        
        # Aktualizacja schematu - sprawdzenie, czy tabela clients ma kolumnę client_type
        cursor.execute("PRAGMA table_info(clients)")
        columns = [column[1] for column in cursor.fetchall()]
        column_updates = []
        
        # Dodanie kolumny client_type, jeśli nie istnieje
        if "client_type" not in columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN client_type TEXT DEFAULT 'Indywidualny'")
            column_updates.append("client_type")
            logger.info("Dodano kolumnę client_type do tabeli clients")
        
        # Aktualizacja istniejących klientów - ustawienie typu klienta na podstawie nazwy
        if "client_type" in column_updates:
            cursor.execute("""
            UPDATE clients
            SET client_type = 
                CASE 
                    WHEN name LIKE '% Sp. z o.o.%' OR name LIKE '% S.A.%' OR 
                         name LIKE '% Sp.J.%' OR name LIKE '% Sp.K.%' OR 
                         name LIKE '% z o.o.%' THEN 'Firma'
                    ELSE 'Indywidualny'
                END
            WHERE client_type IS NULL
            """)
            logger.info("Zaktualizowano typy istniejących klientów")
        
        logger.info("Struktura bazy danych została zainicjalizowana")

        # Sprawdź, czy kolumna condition istnieje w tabeli inventory
        cursor.execute("PRAGMA table_info(inventory)")
        inventory_columns = [column[1] for column in cursor.fetchall()]
        
        # Dodaj kolumnę condition, jeśli nie istnieje
        if "condition" not in inventory_columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN condition TEXT DEFAULT 'Nowy'")
            logger.info("Dodano kolumnę condition do tabeli inventory")
        
        # Dodaj kolumnę manufacturer, jeśli nie istnieje
        if "manufacturer" not in inventory_columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN manufacturer TEXT")
            logger.info("Dodano kolumnę manufacturer do tabeli inventory")
            
            # Opcjonalnie, zaktualizuj istniejące rekordy, ustawiając manufacturer na podstawie brand_model
            cursor.execute("UPDATE inventory SET manufacturer = substr(brand_model, 1, instr(brand_model, ' ') - 1) WHERE brand_model LIKE '% %'")
            logger.info("Zaktualizowano dane w kolumnie manufacturer")
            conn.commit()      

        if "purchase_price" not in inventory_columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN purchase_price REAL DEFAULT 0.0")
            logger.info("Dodano kolumnę purchase_price do tabeli inventory")

        # Sprawdź, czy kolumna bieznik istnieje w tabeli inventory
        if "bieznik" not in inventory_columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN bieznik REAL DEFAULT NULL")
            logger.info("Dodano kolumnę bieznik do tabeli inventory")


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
            ('Jan Kowalski', '123456789', 'jan.kowalski@example.com', 'Stały klient', 5, 'C-00001', 'Indywidualny'),
            ('Anna Nowak', '987654321', 'anna.nowak@example.com', 'VIP', 10, 'C-00002', 'Indywidualny'),
            ('Piotr Wiśniewski', '555666777', 'piotr.wisniewski@example.com', '', 0, 'C-00003', 'Indywidualny'),
            ('Auto Max Sp. z o.o.', '111222333', 'biuro@automax.pl', 'Klient biznesowy', 15, 'C-00004', 'Firma'),
            ('Marek Wójcik', '444555666', 'marek.wojcik@example.com', '', 0, 'C-00005', 'Indywidualny')
        ]
        
        cursor.executemany(
            "INSERT INTO clients (name, phone_number, email, additional_info, discount, barcode, client_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            clients_data
        )
        
        # Dodanie przykładowych pojazdów
        vehicles_data = [
            (1, 'Volkswagen', 'Golf', 2018, 'WA12345', 'WVWZZZ1KZCM123456', '205/55 R16', 'Osobowy', 'Silnik 1.6 TDI'),
            (1, 'Toyota', 'Corolla', 2020, 'WA54321', 'SB1KC09J70E123456', '195/65 R15', 'Osobowy', 'Hybrid 1.8'),
            (2, 'BMW', 'X5', 2019, 'WB54321', 'WBACV2104L9D23456', '255/50 R19', 'SUV', 'Silnik 3.0d'),
            (3, 'Fiat', '500', 2021, 'WC98765', 'ZFA3120000J123456', '175/65 R14', 'Osobowy', 'Silnik 1.2'),
            (4, 'Mercedes', 'Sprinter', 2017, 'WD45678', 'WDB9066351S123456', '235/65 R16C', 'Dostawczy', 'Firmowy'),
            (5, 'Ford', 'Focus', 2016, 'WE87654', '1FAHP3K27CL123456', '205/60 R16', 'Osobowy', '')
        ]
        
        cursor.executemany(
            """
            INSERT INTO vehicles (
                client_id, make, model, year, registration_number, 
                vin, tire_size, vehicle_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            vehicles_data
        )
        
        # Sprawdź strukturę tabeli deposits
        cursor.execute("PRAGMA table_info(deposits)")
        deposit_columns = [column[1] for column in cursor.fetchall()]
        
        today = datetime.now().strftime("%Y-%m-%d")
        next_season = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        
        # Dodanie przykładowych depozytów odpowiednio do struktury tabeli
        if 'deposit_date' in deposit_columns and 'pickup_date' in deposit_columns and 'tire_type' in deposit_columns:
            # Nowa struktura
            deposits_data = [
                (1, today, next_season, '205/55 R16', 'Zimowe', 4, 'A-01-02', 'Aktywny', 'Opony zimowe dla Volkswagena'),
                (2, today, next_season, '255/50 R19', 'Letnie', 4, 'A-02-03', 'Aktywny', 'Opony letnie dla BMW'),
                (3, today, next_season, '175/65 R14', 'Zimowe', 4, 'B-01-01', 'Aktywny', 'Opony zimowe dla Fiata'),
                (4, today, next_season, '235/65 R16C', 'Letnie', 4, 'B-02-02', 'Aktywny', 'Opony letnie dla Sprintera'),
                (5, today, next_season, '205/60 R16', 'Zimowe', 4, 'C-01-03', 'Aktywny', 'Opony zimowe dla Forda')
            ]
            
            cursor.executemany(
                """
                INSERT INTO deposits (
                    client_id, deposit_date, pickup_date, tire_size, tire_type,
                    quantity, location, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                deposits_data
            )
        elif 'car_model' in deposit_columns and 'registration_number' in deposit_columns and 'tire_brand' in deposit_columns:
            # Stara struktura
            deposits_data = [
                (1, 'Volkswagen Golf', 'WA12345', 'Continental', '205/55 R16', 4, 'A-01-02', today, next_season, 'Aktywny', 'Zimowe', 120.00, 1),
                (2, 'BMW X5', 'WB54321', 'Michelin', '255/50 R19', 4, 'A-02-03', today, next_season, 'Aktywny', 'Letnie', 180.00, 3),
                (3, 'Fiat 500', 'WC98765', 'Bridgestone', '175/65 R14', 4, 'B-01-01', today, next_season, 'Aktywny', 'Zimowe', 100.00, 4),
                (4, 'Mercedes Sprinter', 'WD45678', 'Pirelli', '235/65 R16C', 4, 'B-02-02', today, next_season, 'Aktywny', 'Letnie', 150.00, 5),
                (5, 'Ford Focus', 'WE87654', 'Goodyear', '205/60 R16', 4, 'C-01-03', today, next_season, 'Aktywny', 'Zimowe', 110.00, 6)
            ]
            
            cursor.executemany(
                """
                INSERT INTO deposits (
                    client_id, car_model, registration_number, tire_brand, tire_size,
                    quantity, location, deposit_date, expected_return_date, status, season, price, vehicle_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            (1, today.strftime("%Y-%m-%d"), '09:00', 'Wymiana opon', 'Zaplanowana', 'Wymiana z zimowych na letnie', 60, 1),
            (2, tomorrow.strftime("%Y-%m-%d"), '10:30', 'Przechowywanie opon', 'Zaplanowana', 'Odbiór opon z depozytu', 30, 3),
            (3, today.strftime("%Y-%m-%d"), '14:00', 'Naprawa opony', 'Zakończona', 'Naprawa przebitej opony', 45, 4),
            (4, day_after_tomorrow.strftime("%Y-%m-%d"), '11:15', 'Wyważanie kół', 'Zaplanowana', '', 60, 5),
            (5, tomorrow.strftime("%Y-%m-%d"), '16:00', 'Wymiana oleju', 'Zaplanowana', 'Wymiana oleju i filtrów', 90, 6)
        ]
        
        cursor.executemany(
            """
            INSERT INTO appointments (
                client_id, appointment_date, appointment_time, service_type, 
                status, notes, duration, vehicle_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                client_id, order_date, status, total_amount, notes, vehicle_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, today_str, 'Nowe', 980.00, 'Pilne zamówienie', 1)
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

def check_and_upgrade_database(conn):
    """
    Sprawdza i aktualizuje strukturę bazy danych do najnowszej wersji.
    
    Args:
        conn: Połączenie z bazą danych SQLite
        
    Returns:
        bool: True jeśli operacja zakończyła się sukcesem, False w przeciwnym razie
    """
    try:
        cursor = conn.cursor()
        
        # Sprawdzenie aktualności struktury bazy danych
        
        # 1. Sprawdzenie tabeli vehicles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if not cursor.fetchone():
            logger.info("Tabela vehicles nie istnieje - aktualizacja schematu bazy danych")
            
            # Utwórz tabelę vehicles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER,
                    registration_number TEXT UNIQUE,
                    vin TEXT,
                    tire_size TEXT,
                    vehicle_type TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            ''')
            
            # Dodanie indeksów
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_client_id ON vehicles(client_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration_number)")
            
            logger.info("Utworzono tabelę vehicles i jej indeksy")
        
        # 2. Sprawdzenie tabeli deposits i jej struktury
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deposits'")
        if not cursor.fetchone():
            # Tabela deposits nie istnieje - utwórz zgodnie z nową strukturą
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    deposit_date TEXT NOT NULL,
                    pickup_date TEXT NOT NULL,
                    tire_size TEXT NOT NULL,
                    tire_type TEXT NOT NULL,
                    quantity INTEGER DEFAULT 4,
                    location TEXT,
                    status TEXT DEFAULT 'Aktywny',
                    notes TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            ''')
            logger.info("Utworzono tabelę deposits (nowa struktura)")
        else:
            # Sprawdzenie struktury istniejącej tabeli deposits
            cursor.execute("PRAGMA table_info(deposits)")
            columns = {column[1] for column in cursor.fetchall()}
            
            # Sprawdź, czy tabela ma nową strukturę
            required_columns = {'deposit_date', 'pickup_date', 'tire_type'}
            if not all(col in columns for col in required_columns):
                logger.info("Dodawanie brakujących kolumn do tabeli deposits")
                
                # Dodaj brakujące kolumny z nowej struktury
                if 'deposit_date' not in columns and 'expected_return_date' not in columns:
                    cursor.execute("ALTER TABLE deposits ADD COLUMN deposit_date TEXT DEFAULT (datetime('now', 'localtime'))")
                    logger.info("Dodano kolumnę deposit_date do tabeli deposits")
                
                if 'pickup_date' not in columns:
                    cursor.execute("ALTER TABLE deposits ADD COLUMN pickup_date TEXT DEFAULT (datetime('now', '+6 months', 'localtime'))")
                    logger.info("Dodano kolumnę pickup_date do tabeli deposits")
                
                if 'tire_type' not in columns and 'season' in columns:
                    # Migracja danych z kolumny season do tire_type
                    cursor.execute("ALTER TABLE deposits ADD COLUMN tire_type TEXT")
                    cursor.execute("UPDATE deposits SET tire_type = season WHERE tire_type IS NULL")
                    logger.info("Dodano kolumnę tire_type do tabeli deposits i skopiowano dane z kolumny season")
                elif 'tire_type' not in columns:
                    cursor.execute("ALTER TABLE deposits ADD COLUMN tire_type TEXT DEFAULT 'Nieznany'")
                    logger.info("Dodano kolumnę tire_type do tabeli deposits")
        
        # 3. Sprawdzenie dodatkowych kolumn w tabeli clients
        cursor.execute("PRAGMA table_info(clients)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Dodanie kolumny client_type, jeśli nie istnieje
        if "client_type" not in columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN client_type TEXT DEFAULT 'Indywidualny'")
            logger.info("Dodano kolumnę client_type do tabeli clients")
            
            # Aktualizacja istniejących klientów - ustawienie typu klienta
            cursor.execute("""
            UPDATE clients
            SET client_type = 
                CASE 
                    WHEN name LIKE '% Sp. z o.o.%' OR name LIKE '% S.A.%' OR 
                         name LIKE '% Sp.J.%' OR name LIKE '% Sp.K.%' OR 
                         name LIKE '% z o.o.%' THEN 'Firma'
                    ELSE 'Indywidualny'
                END
            WHERE client_type IS NULL
            """)
            logger.info("Zaktualizowano typy istniejących klientów")
        
        # Dodanie kolumny created_at, jeśli nie istnieje
        if "created_at" not in columns:
            # Użyj stałej wartości czasu, bo SQLite nie pozwala na dodanie kolumny z funkcją jako domyślną wartość
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(f"ALTER TABLE clients ADD COLUMN created_at TEXT DEFAULT '{current_time}'")
            logger.info("Dodano kolumnę created_at do tabeli clients")
            
            # Dodanie indeksu na created_at
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at)")
        
        # Zatwierdzenie zmian
        conn.commit()
        
        logger.info("Sprawdzenie i aktualizacja struktury bazy danych zakończona sukcesem")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Błąd podczas aktualizacji struktury bazy danych: {e}")
        return False

# Funkcja pomocnicza do konwersji starych depozytów na nowy format z przypisaniem pojazdów
def migrate_deposits_to_vehicles(conn):
    """
    Migruje dane depozytów do nowej struktury z powiązaniem z pojazdami.
    Dla każdego depozytu bez przypisanego pojazdu, tworzy nowy pojazd lub przypisuje istniejący.
    
    Args:
        conn: Połączenie z bazą danych SQLite
        
    Returns:
        bool: True jeśli operacja zakończyła się sukcesem, False w przeciwnym razie
    """
    try:
        cursor = conn.cursor()
        
        # Pobierz depozyty bez przypisanego pojazdu
        cursor.execute("""
            SELECT id, client_id, car_model, registration_number, tire_size
            FROM deposits
            WHERE vehicle_id IS NULL
        """)
        
        deposits = cursor.fetchall()
        
        if not deposits:
            logger.info("Brak depozytów do migracji")
            return True
        
        logger.info(f"Znaleziono {len(deposits)} depozytów do migracji")
        
        for deposit in deposits:
            deposit_id, client_id, car_model, reg_number, tire_size = deposit
            
            if not reg_number:
                logger.warning(f"Depozyt ID {deposit_id} nie ma numeru rejestracyjnego - pomijanie")
                continue
            
            # Sprawdź, czy pojazd już istnieje
            cursor.execute("""
                SELECT id FROM vehicles
                WHERE registration_number = ? AND client_id = ?
            """, (reg_number, client_id))
            
            existing_vehicle = cursor.fetchone()
            
            if existing_vehicle:
                # Przypisz istniejący pojazd do depozytu
                vehicle_id = existing_vehicle[0]
                logger.info(f"Przypisano istniejący pojazd ID {vehicle_id} do depozytu ID {deposit_id}")
            else:
                # Parsuj model samochodu, jeśli jest w formacie "Marka Model"
                car_parts = car_model.split(' ', 1) if car_model else ['Nieznana', 'Nieznany']
                make = car_parts[0] if len(car_parts) > 0 else 'Nieznana'
                model = car_parts[1] if len(car_parts) > 1 else 'Nieznany'
                
                # Dodaj nowy pojazd
                cursor.execute("""
                    INSERT INTO vehicles
                    (client_id, make, model, registration_number, tire_size, vehicle_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (client_id, make, model, reg_number, tire_size, 'Osobowy', 'Dodano automatycznie z depozytu'))
                
                vehicle_id = cursor.lastrowid
                logger.info(f"Utworzono nowy pojazd ID {vehicle_id} dla depozytu ID {deposit_id}")
            
            # Przypisz pojazd do depozytu
            cursor.execute("""
                UPDATE deposits
                SET vehicle_id = ?
                WHERE id = ?
            """, (vehicle_id, deposit_id))
        
        # Zatwierdzenie zmian
        conn.commit()
        
        logger.info(f"Migracja depozytów zakończona sukcesem - zaktualizowano {len(deposits)} rekordów")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Błąd podczas migracji depozytów: {e}")
        return False
    
# Funkcja do sprawdzenia i dodania brakujących kolumn
def check_and_add_missing_columns(conn):
    """
    Sprawdza i dodaje brakujące kolumny do tabel w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych SQLite
        
    Returns:
        bool: True jeśli operacja zakończyła się sukcesem, False w przeciwnym razie
    """
    try:
        cursor = conn.cursor()
        
        # Sprawdź i dodaj brakujące kolumny do tabeli inventory
        cursor.execute("PRAGMA table_info(inventory)")
        columns = {column[1] for column in cursor.fetchall()}
        
        # Lista kolumn do dodania
        columns_to_add = {
            "condition": "TEXT DEFAULT 'Nowy'",
            "manufacturer": "TEXT",
            "model": "TEXT",
            "status": "TEXT DEFAULT 'Dostępny'",
            "type": "TEXT DEFAULT 'Opona'"  # Dodana kolumna type
        }
        
        for column, definition in columns_to_add.items():
            if column not in columns:
                cursor.execute(f"ALTER TABLE inventory ADD COLUMN {column} {definition}")
                logger.info(f"Dodano kolumnę {column} do tabeli inventory")
        
        # Aktualizuj dane w kolumnach
        if "model" in columns_to_add or "manufacturer" in columns_to_add:
            cursor.execute("""
            UPDATE inventory 
            SET model = CASE
                WHEN instr(brand_model, ' ') > 0 THEN substr(brand_model, instr(brand_model, ' ') + 1)
                ELSE ''
            END,
            manufacturer = CASE
                WHEN instr(brand_model, ' ') > 0 THEN substr(brand_model, 1, instr(brand_model, ' ') - 1)
                ELSE brand_model
            END
            WHERE (model IS NULL OR model = '') AND brand_model LIKE '% %'
            """)
        
        # Zatwierdź zmiany
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Błąd podczas dodawania brakujących kolumn: {e}")
        return False