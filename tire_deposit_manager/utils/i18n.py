#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł obsługi tłumaczeń i lokalizacji.
Część aplikacji Menadżer Serwisu Opon.
"""

import os
import json
import locale
import logging
from PySide6.QtCore import QSettings

from utils.paths import CONFIG_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

# Globalne ustawienia lokalizacji
_current_locale = None
_translations = {}

def initialize_locale():
    """Inicjalizuje ustawienia lokalizacji."""
    # Pobranie wybranego języka z ustawień
    settings = QSettings("TireDepositManager", "Settings")
    selected_language = settings.value("language", "pl_PL")
    
    # Ustawienie globalnej lokalizacji
    try:
        # Próba ustawienia lokalizacji
        try:
            locale.setlocale(locale.LC_ALL, selected_language)
            logger.info(f"Ustawiono lokalizację: {selected_language}")
        except locale.Error:
            # Jeśli dokładna lokalizacja nie działa, spróbuj samego języka
            try:
                if '_' in selected_language:
                    simple_language = selected_language.split('_')[0]
                    locale.setlocale(locale.LC_ALL, simple_language)
                    logger.info(f"Ustawiono uproszczoną lokalizację: {simple_language}")
                else:
                    # Ostatnia deska ratunku - lokalizacja domyślna
                    locale.setlocale(locale.LC_ALL, '')
                    logger.info("Ustawiono domyślną lokalizację")
            except Exception as e:
                logger.warning(f"Nie można ustawić żadnej lokalizacji: {e}")
    except Exception as e:
        logger.warning(f"Problem z ustawieniem lokalizacji: {e}")
    
    # Załadowanie tłumaczeń
    load_translations(selected_language)

def load_translations(language_code):
    """
    Ładuje tłumaczenia dla wybranego języka.
    
    Args:
        language_code (str): Kod języka (np. 'pl_PL')
    """
    global _current_locale, _translations
    
    # Zapamiętaj bieżący język
    _current_locale = language_code
    
    # Ścieżka do pliku tłumaczeń
    locales_dir = os.path.join(CONFIG_DIR, 'locales')
    os.makedirs(locales_dir, exist_ok=True)
    
    # Najpierw próbujemy pełny kod lokalizacji
    translations_file = os.path.join(locales_dir, f"{language_code}.json")
    
    # Jeśli plik nie istnieje, próbujemy wersję uproszczoną (sam język)
    if not os.path.exists(translations_file) and '_' in language_code:
        simple_language = language_code.split('_')[0]
        translations_file = os.path.join(locales_dir, f"{simple_language}.json")
    
    # Jeśli dalej nie ma, używamy wersji angielskiej albo pustego słownika
    if not os.path.exists(translations_file):
        english_file = os.path.join(locales_dir, "en.json")
        translations_file = english_file if os.path.exists(english_file) else None
    
    # Załaduj tłumaczenia, jeśli plik istnieje
    if translations_file and os.path.exists(translations_file):
        try:
            with open(translations_file, 'r', encoding='utf-8') as f:
                _translations = json.load(f)
            logger.info(f"Załadowano tłumaczenia z pliku: {translations_file}")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania tłumaczeń: {e}")
            _translations = {}
    else:
        # Jeśli nie ma pliku tłumaczeń, użyj pustego słownika
        _translations = {}
        logger.warning(f"Brak pliku tłumaczeń dla języka {language_code}")
        
        # Stwórz przykładowy plik tłumaczeń dla polskiego
        if language_code.startswith("pl"):
            create_default_polish_translations(locales_dir)

def create_default_polish_translations(locales_dir):
    """Tworzy podstawowy plik tłumaczeń dla języka polskiego."""
    try:
        polish_translations = {
            "__language_name__": "Polski",
            "Opony nowe": "Opony nowe",
            "Opony używane": "Opony używane",
            "Wartość magazynu": "Wartość magazynu",
            "Niski stan": "Niski stan",
            "Wszystkie": "Wszystkie",
            "ID": "ID",
            "Producent": "Producent",
            "Model": "Model",
            "Rozmiar": "Rozmiar",
            "Typ": "Typ",
            "Ilość": "Ilość",
            "Cena": "Cena",
            "DOT": "DOT",
            "Status": "Status",
            "Akcje": "Akcje",
            "Dostępna": "Dostępna",
            "Rezerwacja": "Rezerwacja",
            "Sprzedana": "Sprzedana",
            "Zamówiona": "Zamówiona",
            "Wycofana": "Wycofana",
            "Zimowe": "Zimowe",
            "Letnie": "Letnie",
            "Całoroczne": "Całoroczne",
            "Nowa": "Nowa",
            "Używana": "Używana",
            "Strona": "Strona",
            "z": "z",
            "Poprzednia": "Poprzednia",
            "Następna": "Następna",
            "Filtruj": "Filtruj",
            "Szukaj po producencie, modelu, rozmiarze...": "Szukaj po producencie, modelu, rozmiarze...",
            "Dodaj nową oponę": "Dodaj nową oponę",
            "Import": "Import",
            "Eksport": "Eksport",
            "Raport": "Raport",
            "Zarządzanie Magazynem Opon": "Zarządzanie Magazynem Opon",
            "Generuj etykiety dla wybranych opon": "Generuj etykiety dla wybranych opon",
            "Raport Magazynowy": "Raport Magazynowy",
            "Eksportuj listę opon": "Eksportuj listę opon",
            "Brak zaznaczenia": "Brak zaznaczenia",
            "Zaznacz opony, dla których chcesz wygenerować etykiety.": "Zaznacz opony, dla których chcesz wygenerować etykiety.",
            "Opcje drukowania": "Opcje drukowania",
            "Wybierz opcję drukowania etykiet:": "Wybierz opcję drukowania etykiet:",
            "Podgląd": "Podgląd",
            "Drukuj bezpośrednio": "Drukuj bezpośrednio",
            "Anuluj": "Anuluj",
            "Wybierz typ raportu": "Wybierz typ raportu",
            "Wybierz typ raportu, który chcesz wygenerować:": "Wybierz typ raportu, który chcesz wygenerować:",
            "Raport stanu magazynowego": "Raport stanu magazynowego",
            "Raport niskiego stanu": "Raport niskiego stanu",
            "Raport wartości magazynu": "Raport wartości magazynu",
            "Raport sprzedanych opon": "Raport sprzedanych opon",
            "Wybierz okres": "Wybierz okres",
            "Za jaki okres chcesz wygenerować raport:": "Za jaki okres chcesz wygenerować raport:",
            "Ostatni tydzień": "Ostatni tydzień",
            "Ostatni miesiąc": "Ostatni miesiąc",
            "Ostatni kwartał": "Ostatni kwartał",
            "Bieżący rok": "Bieżący rok",
            "Wszystkie": "Wszystkie",
            "Wybierz format eksportu": "Wybierz format eksportu",
            "Wybierz format pliku:": "Wybierz format pliku:",
            "Plik Excel (*.xlsx)": "Plik Excel (*.xlsx)",
            "Plik PDF (*.pdf)": "Plik PDF (*.pdf)",
            "Wybierz zakres danych": "Wybierz zakres danych",
            "Wybierz zakres danych do eksportu:": "Wybierz zakres danych do eksportu:",
            "Wszystkie opony": "Wszystkie opony",
            "Tylko opony nowe": "Tylko opony nowe",
            "Tylko opony używane": "Tylko opony używane",
            "Tylko wyświetlane (z filtrami)": "Tylko wyświetlane (z filtrami)",
            "Zapisz jako": "Zapisz jako",
            "Dane zostały odświeżone": "Dane zostały odświeżone"
        }
        
        # Zapisz tłumaczenia do pliku
        pl_file = os.path.join(locales_dir, "pl.json")
        with open(pl_file, 'w', encoding='utf-8') as f:
            json.dump(polish_translations, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Utworzono domyślny plik tłumaczeń dla języka polskiego: {pl_file}")
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia domyślnego pliku tłumaczeń: {e}")

def _(text):
    """
    Funkcja tłumacząca tekst na aktualnie wybrany język.
    
    Args:
        text (str): Tekst do przetłumaczenia
    
    Returns:
        str: Przetłumaczony tekst
    """
    global _translations
    
    # Jeśli tłumaczenia nie zostały załadowane, zainicjalizuj
    if not _translations:
        initialize_locale()
    
    # Zwróć tłumaczenie lub oryginalny tekst, jeśli tłumaczenie nie istnieje
    return _translations.get(text, text)

def get_available_languages():
    """
    Zwraca listę dostępnych języków.
    
    Returns:
        list: Lista dostępnych języków w formacie [(kod, nazwa), ...]
    """
    # Ścieżka do katalogu z tłumaczeniami
    locales_dir = os.path.join(CONFIG_DIR, 'locales')
    
    # Sprawdź, czy katalog istnieje
    if not os.path.exists(locales_dir):
        os.makedirs(locales_dir, exist_ok=True)
        logger.warning(f"Utworzono katalog tłumaczeń: {locales_dir}")
        # Utwórz domyślne tłumaczenia polskie
        create_default_polish_translations(locales_dir)
        return [('pl', 'Polski')]
    
    # Lista dostępnych języków
    languages = []
    
    # Przeszukaj katalog
    for filename in os.listdir(locales_dir):
        if filename.endswith('.json'):
            code = filename[:-5]  # Usuń rozszerzenie .json
            
            # Pobierz nazwę języka z pliku (jeśli dostępna)
            try:
                with open(os.path.join(locales_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('__language_name__', code)
            except Exception:
                name = code
            
            languages.append((code, name))
    
    # Jeśli lista jest pusta, dodaj domyślny język
    if not languages:
        languages.append(('pl', 'Polski'))
        # Utwórz domyślne tłumaczenia
        create_default_polish_translations(locales_dir)
    
    return languages

def current_locale():
    """
    Zwraca aktualnie wybrany język.
    
    Returns:
        str: Kod języka
    """
    global _current_locale
    
    # Jeśli lokalizacja nie została zainicjalizowana, zainicjalizuj
    if _current_locale is None:
        initialize_locale()
    
    return _current_locale