"""
Plik zawierający definicje stylów dla aplikacji Menadżer Serwisu Opon.
Zawiera ciemny (domyślny) i jasny motyw oraz dodatkowe style dla różnych komponentów.
Zoptymalizowany dla lepszego wyglądu i spójności interfejsu.
"""

# Ciemny motyw (domyślny) - zoptymalizowany
STYLE_SHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e272e;
    color: #ecf0f1;
    font-family: "Segoe UI";
    font-size: 13px;  /* Zwiększony rozmiar czcionki */
}

/* Sidebar z menu - poszerzony i poprawiony */
QFrame#sidebarFrame {
    background-color: #0c1419;
    color: white;
    min-width: 240px;  /* Poszerzony panel boczny */
    max-width: 240px;
}

/* Logo */
QLabel#logoLabel {
    background-color: transparent;
    border-radius: 30px;
    min-width: 70px;  /* Większe logo */
    max-width: 70px;
    min-height: 70px;
    max-height: 70px;
    margin: 15px auto;  /* Większy margines */
}

QLabel#appTitleLabel {
    color: white;
    font-size: 18px;  /* Większa czcionka */
    font-weight: bold;
    margin-top: 10px;
    text-align: center;
}

/* Przyciski menu bocznego - większe, lepiej widoczne */
QPushButton#menuButton {
    border: none;
    text-align: left;
    padding-left: 30px;
    padding-top: 15px;  /* Większy padding */
    padding-bottom: 15px;
    color: white;
    font-size: 15px;  /* Większa czcionka */
    background-color: transparent;
    border-radius: 0px;
}

QPushButton#menuButton:hover {
    background-color: #263238;
}

QPushButton#menuButton[active=true] {
    background-color: #3498db;
    font-weight: bold;  /* Pogrubiona czcionka dla aktywnej zakładki */
}

/* Header z tytułem i wyszukiwarką */
QFrame#headerFrame {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #263238, stop:1 #1e272e);
    border-bottom: 1px solid #0c1419;
    min-height: 70px;  /* Wyższy nagłówek */
    max-height: 70px;
}

QLabel#titleLabel {
    font-size: 22px;  /* Większy tytuł */
    font-weight: bold;
    color: #ecf0f1;
}

/* Wyszukiwarka - większa, lepiej widoczna */
QLineEdit#searchField {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 1px solid #455a64;
    border-radius: 5px;  /* Większy promień zaokrąglenia */
    padding: 8px;  /* Większy padding */
    font-size: 14px;  /* Większa czcionka */
    selection-background-color: #3498db;
    min-height: 30px;  /* Minimalna wysokość */
}

QLineEdit#searchField:focus {
    border: 2px solid #3498db;  /* Grubsza obwódka przy fokusie */
}

/* Combobox - większy, lepiej widoczny */
QComboBox {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 1px solid #455a64;
    border-radius: 5px;
    padding: 8px;
    min-height: 30px;
    font-size: 14px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;  /* Szerszy przycisk rozwijania */
    border-left-width: 1px;
    border-left-color: #455a64;
    border-left-style: solid;
}

QComboBox::down-arrow {
    image: url(icons/dropdown_arrow.png);
}

QComboBox QAbstractItemView {
    background-color: #2c3e50;
    color: #ecf0f1;
    selection-background-color: #3498db;
    selection-color: #ecf0f1;
    border: 1px solid #455a64;
}

/* Przyciski akcji - większe, lepiej widoczne */
QPushButton {
    background-color: #2c3e50;
    color: white;
    border: none;
    border-radius: 5px;  /* Większy promień */
    padding: 8px 15px;  /* Większy padding */
    min-height: 30px;
    font-size: 14px;  /* Większa czcionka */
}

QPushButton:hover {
    background-color: #3498db;
}

QPushButton:pressed {
    background-color: #2980b9;
}

QPushButton:disabled {
    background-color: #455a64;
    color: #78909c;
}

QPushButton#addButton {
    background-color: #27ae60;
    color: white;
    font-weight: bold;
    min-width: 100px;  /* Minimalna szerokość */
}

QPushButton#addButton:hover {
    background-color: #2ecc71;
}

QPushButton#addButton:pressed {
    background-color: #219653;
}

QPushButton#refreshButton {
    background-color: #3498db;
    color: white;
    min-width: 40px;  /* Minimalna szerokość */
}

QPushButton#refreshButton:hover {
    background-color: #2980b9;
}

/* Tabele - lepiej widoczne */
QTableView, QTableWidget {
    background-color: #263238;
    alternate-background-color: #1e272e;
    color: #ecf0f1;
    gridline-color: #455a64;
    border: 1px solid #455a64;
    selection-background-color: #3498db;
    selection-color: #ecf0f1;
    font-size: 14px;  /* Większa czcionka */
}

QTableView::item, QTableWidget::item {
    padding: 8px;  /* Większy padding */
    min-height: 25px;  /* Minimalna wysokość */
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #3498db;
    color: #ecf0f1;
}

QHeaderView::section {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 8px;
    border: 1px solid #455a64;
    font-weight: bold;
    font-size: 14px;  /* Większa czcionka */
}

/* Zakładki - lepiej widoczne */
QTabWidget::pane {
    border: 1px solid #455a64;
    background-color: #1e272e;
}

QTabBar::tab {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 10px 15px;  /* Większy padding */
    border: 1px solid #455a64;
    border-bottom: none;
    border-top-left-radius: 6px;  /* Większy promień */
    border-top-right-radius: 6px;
    font-size: 14px;  /* Większa czcionka */
    min-width: 120px;  /* Minimalna szerokość */
}

QTabBar::tab:selected {
    background-color: #3498db;
    border-bottom: none;
    font-weight: bold;  /* Pogrubiona czcionka dla aktywnej zakładki */
}

QTabBar::tab:!selected {
    margin-top: 3px;  /* Większy margines */
}

QTabBar::tab:hover:!selected {
    background-color: #34495e;
}

/* Status etykiety w tabelach */
QLabel[status="Aktywny"] {
    color: #2ecc71;
    font-weight: bold;
}

QLabel[status="Zakończone"] {
    color: #2ecc71;
    font-weight: bold;
}

QLabel[status="W realizacji"] {
    color: #3498db;
    font-weight: bold;
}

QLabel[status="Oczekujące"] {
    color: #f39c12;
    font-weight: bold;
}

QLabel[status="Anulowane"] {
    color: #e74c3c;
    font-weight: bold;
}

/* Stopka - lepiej widoczna */
QFrame#footer {
    background-color: #1a252f;
    color: #95a5a6;
    min-height: 35px;  /* Wyższa stopka */
    max-height: 35px;
    border-top: 1px solid #0c1419;
    font-size: 13px;  /* Większa czcionka */
}

QStatusBar {
    background-color: #1a252f;
    color: #95a5a6;
    min-height: 35px;  /* Wyższy pasek statusu */
    font-size: 13px;  /* Większa czcionka */
}

/* Dialogi - lepiej widoczne */
QDialog {
    background-color: #1e272e;
    color: #ecf0f1;
}

QDialog QLabel {
    color: #ecf0f1;
    font-size: 14px;  /* Większa czcionka */
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2c3e50;
    color: #ecf0f1;
    border: 1px solid #455a64;
    border-radius: 5px;
    padding: 8px;
    selection-background-color: #3498db;
    font-size: 14px;  /* Większa czcionka */
    min-height: 30px;  /* Minimalna wysokość */
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #3498db;  /* Grubsza obwódka przy fokusie */
}

/* Informacje, ostrzeżenia i błędy */
QLabel[type="info"] {
    color: #3498db;
    font-weight: bold;
}

QLabel[type="warning"] {
    color: #f39c12;
    font-weight: bold;
}

QLabel[type="error"] {
    color: #e74c3c;
    font-weight: bold;
}

QLabel[type="success"] {
    color: #2ecc71;
    font-weight: bold;
}

/* Powiadomienia - lepiej widoczne */
QFrame#notificationFrame {
    background-color: #2c3e50;
    border-radius: 6px;  /* Większy promień */
    border: 1px solid #455a64;
    padding: 5px;  /* Dodany padding */
}

QLabel#notificationTitle {
    color: #ecf0f1;
    font-weight: bold;
    font-size: 15px;  /* Większa czcionka */
}

QLabel#notificationMessage {
    color: #ecf0f1;
    font-size: 14px;  /* Większa czcionka */
}

/* Przyciski akcji w powiadomieniach */
QPushButton#notificationButton {
    background-color: transparent;
    color: #ecf0f1;
    border: none;
}

QPushButton#notificationButton:hover {
    color: #3498db;
}

/* Karty na pulpicie - lepiej widoczne kafelki */
QFrame[dashboard="true"] {
    border-radius: 8px;  /* Większy promień */
    padding: 10px;  /* Dodany padding */
    margin: 5px;  /* Dodany margines */
}

QLabel[dashboard="title"] {
    font-size: 16px;  /* Większa czcionka */
    font-weight: bold;
    color: white;
    margin-bottom: 5px;  /* Dodany margines */
}

QLabel[dashboard="value"] {
    font-size: 24px;  /* Większa czcionka */
    font-weight: bold;
    color: white;
}

QLabel[dashboard="change"] {
    font-size: 14px;  /* Większa czcionka */
    color: white;
}
"""

# Jasny motyw (alternatywny) - zoptymalizowany
LIGHT_STYLE_SHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f5f5;  /* Jaśniejsze tło */
    color: #333333;  /* Ciemniejszy tekst dla lepszego kontrastu */
    font-family: "Segoe UI";
    font-size: 13px;  /* Zwiększony rozmiar czcionki */
}

/* Sidebar z menu - poszerzony i poprawiony */
QFrame#sidebarFrame {
    background-color: #2c3e50;  /* Ciemny sidebar nawet w jasnym motywie */
    color: white;
    min-width: 240px;  /* Poszerzony panel boczny */
    max-width: 240px;
}

/* Logo */
QLabel#logoLabel {
    background-color: #3498db;
    border-radius: 30px;
    min-width: 70px;  /* Większe logo */
    max-width: 70px;
    min-height: 70px;
    max-height: 70px;
    margin: 15px auto;  /* Większy margines */
}

QLabel#appTitleLabel {
    color: white;
    font-size: 18px;  /* Większa czcionka */
    font-weight: bold;
    margin-top: 10px;
    text-align: center;
}

/* Przyciski menu bocznego - większe, lepiej widoczne */
QPushButton#menuButton {
    border: none;
    text-align: left;
    padding-left: 30px;
    padding-top: 15px;  /* Większy padding */
    padding-bottom: 15px;
    color: white;
    font-size: 15px;  /* Większa czcionka */
    background-color: transparent;
    border-radius: 0px;
}

QPushButton#menuButton:hover {
    background-color: #34495e;
}

QPushButton#menuButton[active=true] {
    background-color: #3498db;
    font-weight: bold;  /* Pogrubiona czcionka dla aktywnej zakładki */
}

/* Header z tytułem i wyszukiwarką */
QFrame#headerFrame {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #f8f9fa, stop:1 #e9ecef);
    border-bottom: 1px solid #cccccc;
    min-height: 70px;  /* Wyższy nagłówek */
    max-height: 70px;
}

QLabel#titleLabel {
    font-size: 22px;  /* Większy tytuł */
    font-weight: bold;
    color: #2c3e50;
}

/* Wyszukiwarka - większa, lepiej widoczna */
QLineEdit#searchField {
    background-color: white;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 5px;  /* Większy promień zaokrąglenia */
    padding: 8px;  /* Większy padding */
    font-size: 14px;  /* Większa czcionka */
    selection-background-color: #3498db;
    min-height: 30px;  /* Minimalna wysokość */
}

QLineEdit#searchField:focus {
    border: 2px solid #3498db;  /* Grubsza obwódka przy fokusie */
}

/* Combobox - większy, lepiej widoczny */
QComboBox {
    background-color: white;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 5px;
    padding: 8px;
    min-height: 30px;
    font-size: 14px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;  /* Szerszy przycisk rozwijania */
    border-left-width: 1px;
    border-left-color: #cccccc;
    border-left-style: solid;
}

QComboBox::down-arrow {
    image: url(icons/dropdown_arrow.png);
}

QComboBox QAbstractItemView {
    background-color: white;
    color: #333333;
    selection-background-color: #3498db;
    selection-color: white;
    border: 1px solid #cccccc;
}

/* Przyciski akcji - większe, lepiej widoczne */
QPushButton {
    background-color: #f0f0f0;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 5px;  /* Większy promień */
    padding: 8px 15px;  /* Większy padding */
    min-height: 30px;
    font-size: 14px;  /* Większa czcionka */
}

QPushButton:hover {
    background-color: #e0e0e0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #a0a0a0;
    border: 1px solid #cccccc;
}

QPushButton#addButton {
    background-color: #27ae60;
    color: white;
    font-weight: bold;
    border: none;
    min-width: 100px;  /* Minimalna szerokość */
}

QPushButton#addButton:hover {
    background-color: #2ecc71;
}

QPushButton#addButton:pressed {
    background-color: #219653;
}

QPushButton#refreshButton {
    background-color: #3498db;
    color: white;
    border: none;
    min-width: 40px;  /* Minimalna szerokość */
}

QPushButton#refreshButton:hover {
    background-color: #2980b9;
}

/* Tabele - lepiej widoczne */
QTableView, QTableWidget {
    background-color: white;
    alternate-background-color: #f9f9f9;
    color: #333333;
    gridline-color: #e0e0e0;
    border: 1px solid #cccccc;
    selection-background-color: #3498db;
    selection-color: white;
    font-size: 14px;  /* Większa czcionka */
}

QTableView::item, QTableWidget::item {
    padding: 8px;  /* Większy padding */
    min-height: 25px;  /* Minimalna wysokość */
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #f0f0f0;
    color: #333333;
    padding: 8px;
    border: 1px solid #cccccc;
    font-weight: bold;
    font-size: 14px;  /* Większa czcionka */
}

/* Zakładki - lepiej widoczne */
QTabWidget::pane {
    border: 1px solid #cccccc;
    background-color: white;
}

QTabBar::tab {
    background-color: #f0f0f0;
    color: #333333;
    padding: 10px 15px;  /* Większy padding */
    border: 1px solid #cccccc;
    border-bottom: none;
    border-top-left-radius: 6px;  /* Większy promień */
    border-top-right-radius: 6px;
    font-size: 14px;  /* Większa czcionka */
    min-width: 120px;  /* Minimalna szerokość */
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom-color: white;
    font-weight: bold;  /* Pogrubiona czcionka dla aktywnej zakładki */
}

QTabBar::tab:!selected {
    margin-top: 3px;  /* Większy margines */
}

QTabBar::tab:hover:!selected {
    background-color: #e0e0e0;
}

/* Status etykiety w tabelach */
QLabel[status="Aktywny"] {
    color: #27ae60;
    font-weight: bold;
}

QLabel[status="Zakończone"] {
    color: #27ae60;
    font-weight: bold;
}

QLabel[status="W realizacji"] {
    color: #3498db;
    font-weight: bold;
}

QLabel[status="Oczekujące"] {
    color: #f39c12;
    font-weight: bold;
}

QLabel[status="Anulowane"] {
    color: #e74c3c;
    font-weight: bold;
}

/* Stopka - lepiej widoczna */
QFrame#footer {
    background-color: #e0e0e0;
    color: #666666;
    min-height: 35px;  /* Wyższa stopka */
    max-height: 35px;
    border-top: 1px solid #cccccc;
    font-size: 13px;  /* Większa czcionka */
}

QStatusBar {
    background-color: #e0e0e0;
    color: #666666;
    min-height: 35px;  /* Wyższy pasek statusu */
    font-size: 13px;  /* Większa czcionka */
}

/* Dialogi - lepiej widoczne */
QDialog {
    background-color: #f5f5f5;
    color: #333333;
}

QDialog QLabel {
    color: #333333;
    font-size: 14px;  /* Większa czcionka */
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: white;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 5px;
    padding: 8px;
    selection-background-color: #3498db;
    font-size: 14px;  /* Większa czcionka */
    min-height: 30px;  /* Minimalna wysokość */
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #3498db;  /* Grubsza obwódka przy fokusie */
}

/* Informacje, ostrzeżenia i błędy */
QLabel[type="info"] {
    color: #3498db;
    font-weight: bold;
}

QLabel[type="warning"] {
    color: #f39c12;
    font-weight: bold;
}

QLabel[type="error"] {
    color: #e74c3c;
    font-weight: bold;
}

QLabel[type="success"] {
    color: #2ecc71;
    font-weight: bold;
}

/* Powiadomienia - lepiej widoczne */
QFrame#notificationFrame {
    background-color: white;
    border-radius: 6px;  /* Większy promień */
    border: 1px solid #cccccc;
    padding: 5px;  /* Dodany padding */
}

QLabel#notificationTitle {
    color: #333333;
    font-weight: bold;
    font-size: 15px;  /* Większa czcionka */
}

QLabel#notificationMessage {
    color: #333333;
    font-size: 14px;  /* Większa czcionka */
}

/* Przyciski akcji w powiadomieniach */
QPushButton#notificationButton {
    background-color: transparent;
    color: #3498db;
    border: none;
}

QPushButton#notificationButton:hover {
    color: #2980b9;
}

/* Karty na pulpicie - lepiej widoczne kafelki */
QFrame[dashboard="true"] {
    border-radius: 8px;  /* Większy promień */
    padding: 10px;  /* Dodany padding */
    margin: 5px;  /* Dodany margines */
}

QLabel[dashboard="title"] {
    font-size: 16px;  /* Większa czcionka */
    font-weight: bold;
    margin-bottom: 5px;  /* Dodany margines */
}

QLabel[dashboard="value"] {
    font-size: 24px;  /* Większa czcionka */
    font-weight: bold;
}

QLabel[dashboard="change"] {
    font-size: 14px;  /* Większa czcionka */
}
"""

# Funkcja do wyboru stylu w zależności od motywu
def get_style_sheet(theme="Dark"):
    """
    Zwraca arkusz stylu w zależności od wybranego motywu.
    
    Args:
        theme (str): Nazwa motywu ("Dark" lub "Light")
        
    Returns:
        str: Arkusz stylu CSS
    """
    if theme.lower() == "light":
        return LIGHT_STYLE_SHEET
    else:
        return STYLE_SHEET