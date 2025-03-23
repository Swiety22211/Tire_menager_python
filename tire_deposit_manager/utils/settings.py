from PySide6.QtCore import QSettings

class Settings:
    """
    Klasa do zarządzania ustawieniami aplikacji.
    Implementuje wzorzec Singleton.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Zwraca instancję klasy Settings (wzorzec Singleton).
        
        Returns:
            Settings: Instancja ustawień
        """
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance
    
    def __init__(self):
        """
        Inicjalizuje obiekt ustawień.
        """
        self.settings = QSettings("TireDepositManager", "Settings")
    
    def get_setting(self, key, default=None):
        """
        Pobiera wartość ustawienia.
        
        Args:
            key (str): Klucz ustawienia
            default: Domyślna wartość, jeśli ustawienie nie istnieje
            
        Returns:
            Wartość ustawienia lub wartość domyślna
        """
        return self.settings.value(key, default)
    
    def set_setting(self, key, value):
        """
        Ustawia wartość ustawienia.
        
        Args:
            key (str): Klucz ustawienia
            value: Wartość ustawienia
        """
        self.settings.setValue(key, value)
        self.settings.sync()