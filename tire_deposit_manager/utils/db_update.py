#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skrypt do aktualizacji schematu bazy danych.
"""

import os
import sqlite3
import logging
import sys
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki, aby zaimportować moduły
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.paths import DATABASE_PATH

# Logger
logger = logging.getLogger("TireDepositManager")
logging.basicConfig(level=logging.INFO)

def update_database_schema():
    """Aktualizuje schemat bazy danych."""
    try:
        # Połączenie z bazą danych
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Sprawdzenie, czy tabela vehicles istnieje
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if not cursor.fetchone():
            logger.info("Tworzenie tabeli vehicles")
            cursor.execute("""
                CREATE TABLE vehicles (
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
                    created_at TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # Tworzenie indeksów
            cursor.execute("CREATE INDEX idx_vehicles_client_id ON vehicles(client_id)")
            cursor.execute("CREATE INDEX idx_vehicles_registration ON vehicles(registration_number)")
        
        # Sprawdzenie, czy kolumny istnieją w tabeli clients
        cursor.execute("PRAGMA table_info(clients)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Dla SQLite 3.31.0 i nowszych można użyć "IF NOT EXISTS" w ALTER TABLE
        # ale dla kompatybilności używamy sprawdzenia
        
        # Dodanie kolumny client_type, jeśli nie istnieje
        if "client_type" not in columns:
            logger.info("Dodawanie kolumny client_type do tabeli clients")
            cursor.execute("ALTER TABLE clients ADD COLUMN client_type TEXT DEFAULT 'Indywidualny'")
            
            # Aktualizacja istniejących rekordów
            cursor.execute("""
                UPDATE clients
                SET client_type = 
                    CASE 
                        WHEN name LIKE '% Sp. z o.o.%' OR name LIKE '% S.A.%' OR 
                             name LIKE '% Sp.J.%' OR name LIKE '% Sp.K.%' OR 
                             name LIKE '% z o.o.%' THEN 'Firma'
                        ELSE 'Indywidualny'
                    END
            """)
        
        # Dodanie kolumny created_at, jeśli nie istnieje
        if "created_at" not in columns:
            logger.info("Dodawanie kolumny created_at do tabeli clients")
            # Dodajemy kolumnę bez domyślnej wartości
            cursor.execute("ALTER TABLE clients ADD COLUMN created_at TEXT")
            
            # Ustawiamy wartość dla wszystkich istniejących rekordów
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE clients SET created_at = ?", (current_timestamp,))
            
            logger.info(f"Zaktualizowano kolumnę created_at dla istniejących rekordów na: {current_timestamp}")
        
        # Zatwierdzenie zmian
        conn.commit()
        conn.close()
        logger.info("Aktualizacja schematu bazy danych zakończona pomyślnie")
        return True
        
    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji bazy danych: {e}")
        return False

if __name__ == "__main__":
    update_database_schema()