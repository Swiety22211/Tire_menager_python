import logging
import requests
import json
from typing import Dict, Any, Optional, Tuple, Union

# Logger
logger = logging.getLogger("TireDepositManager")

def format_phone_number(phone: str) -> str:
    """
    Formatuje numer telefonu do formatu wymaganego przez API SMS Planet.
    
    Args:
        phone (str): Numer telefonu w dowolnym formacie
    
    Returns:
        str: Sformatowany numer telefonu (48xxxxxxxxx)
    """
    # Usuń wszystkie znaki niebędące cyframi
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Dodaj prefiks krajowy, jeśli go nie ma
    if len(clean_phone) == 9:
        # Numer polski bez prefiksu
        return "48" + clean_phone
    elif clean_phone.startswith("48") and len(clean_phone) == 11:
        # Już ma prefiks 48
        return clean_phone
    else:
        # Inny format - zwróć bez zmian
        return clean_phone

class SMSSender:
    """Klasa do wysyłania SMS-ów przez API SMS Planet."""
    
    def __init__(self, token: str, sender: str):
        """
        Inicjalizacja obiektu SMSSender.
        
        Args:
            token (str): Token API SMS Planet
            sender (str): Nazwa nadawcy SMS
        """
        self.token = token
        self.sender = sender
        self.base_url = "https://api2.smsplanet.pl/sms"
    
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        Wysyłanie wiadomości SMS.
        
        Args:
            phone_number (str): Numer telefonu odbiorcy (dowolny format)
            message (str): Treść wiadomości SMS
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Formatuj numer telefonu
            formatted_phone = format_phone_number(phone_number)
            
            # Sprawdź czy numer ma przynajmniej 9 cyfr
            if len(formatted_phone) < 9:
                return False, "Nieprawidłowy format numeru telefonu. Numer powinien mieć co najmniej 9 cyfr."
            
            # Sprawdź długość wiadomości
            if len(message) > 480:  # Limit do 3 SMS-ów
                return False, "Wiadomość jest zbyt długa. Maksymalna długość to 480 znaków (3 SMS-y)."
            
            # Przygotuj dane do wysłania zgodnie z dokumentacją API
            payload = {
                "from": self.sender,
                "to": formatted_phone,
                "msg": message
            }
            
            # Przygotuj nagłówki z tokenem Bearer
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {self.token}'
            }
            
            # Dodaj debugowanie
            logger.debug(f"Wysyłanie żądania do API SMS Planet: {self.base_url}")
            logger.debug(f"Payload: {payload}")
            logger.debug(f"Nagłówki: {headers}")
            
            # Wyślij żądanie do API
            response = requests.post(self.base_url, data=payload, headers=headers)
            
            # Logowanie odpowiedzi
            logger.debug(f"Odpowiedź z API SMS Planet (kod: {response.status_code}): {response.text}")
            
            # Sprawdzenie odpowiedzi zgodnie z dokumentacją
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if "messageId" in response_data:
                        # Poprawna odpowiedź z API
                        sms_id = response_data.get("messageId", "")
                        return True, f"SMS wysłany pomyślnie. ID: {sms_id}"
                    elif "errorMsg" in response_data:
                        # Błąd od API
                        error_msg = response_data.get("errorMsg", "")
                        error_code = response_data.get("errorCode", "")
                        return False, f"Błąd API SMS Planet: {error_msg} (kod: {error_code})"
                    else:
                        return False, f"Nieoczekiwana odpowiedź API: {response.text}"
                except json.JSONDecodeError:
                    # Nieprawidłowa odpowiedź, niezgodna z dokumentacją
                    if "<!DOCTYPE html>" in response.text:
                        logger.error("API zwróciło HTML zamiast JSON. Nieprawidłowy endpoint lub problem z konfiguracją.")
                        return False, "Nieprawidłowa odpowiedź z serwera (HTML). Sprawdź konfigurację API."
                    else:
                        return False, f"Nieoczekiwana odpowiedź serwera: {response.text[:100]}"
            else:
                # Kod statusu HTTP inny niż 200
                return False, f"Błąd API (kod: {response.status_code}): {response.text[:100]}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Błąd połączenia z API SMS Planet: {e}")
            return False, f"Błąd połączenia z API: {str(e)}"
            
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas wysyłania SMS: {e}")
            return False, f"Nieoczekiwany błąd: {str(e)}"