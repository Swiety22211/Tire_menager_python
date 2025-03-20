"""
Plik zawierający definicje stylów dla aplikacji Menadżer Serwisu Opon.
Zawiera ciemny motyw dostosowany do zrzutu ekranu.
"""

# Ciemny motyw - zgodny ze zrzutem ekranu
STYLE_SHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e272e;
    color: #ecf0f1;
    font-family: "Segoe UI";
    font-size: 13px;
}

/* Sidebar z menu - jednolite ciemne tło */
QFrame#sidebarFrame {
    background-color: #1a1d21;
    color: white;
    min-width: 240px;
    max-width: 240px;
}

/* Logo - bez niebieskiego tła */
QLabel#logoLabel {
    background-color: transparent;
    border-radius: 0px;

}

QLabel#appTitleLabel {
    color: white;
    font-size: 18px;
    font-weight: bold;
    margin-top: 10px;
    text-align: center;
}

/* Elementy menuWidget i footerWidget aby zapewnić jednolite tło */
QWidget#logoWidget, QWidget#menuContainer, QWidget#sidebarFooter {
    background-color: #1a1d21;
}

/* Przyciski menu bocznego */
QPushButton#menuButton {
    border: none;
    text-align: left;
    padding-left: 30px;
    padding-top: 15px;
    padding-bottom: 15px;
    color: white;
    font-size: 15px;
    background-color: transparent;
    border-radius: 0px;
}

QPushButton#menuButton:hover {
    background-color: #2c3034;
}

QPushButton#menuButton[active=true] {
    background-color: #4dabf7;
    font-weight: bold;
}

/* Header z tytułem i wyszukiwarką - transparentny */
QFrame#headerFrame {
    background: transparent;
    border-bottom: 1px solid #2c3034;
    min-height: 70px;
    max-height: 70px;
}

QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #ecf0f1;
    background-color: transparent;
}

/* Wyszukiwarka */
QFrame#searchBox {
    background-color: #2c3034;
    border-radius: 5px;
    min-height: 30px;
}

QLineEdit#searchField {
    border: none;
    background: transparent;
    color: white;
    font-size: 14px;
    min-height: 30px;
}

/* Combobox */
QComboBox {
    background-color: #2c3034;
    color: white;
    border-radius: 5px;
    padding: 5px 10px;
    min-height: 35px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: url(icons/dropdown_arrow.png);
}

QComboBox QAbstractItemView {
    background-color: #2c3034;
    color: white;
    selection-background-color: #4dabf7;
    selection-color: white;
    border: 1px solid #2c3034;
}

/* Przyciski akcji */
QPushButton {
    background-color: #2c3034;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    min-height: 35px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #4dabf7;
}

QPushButton#addButton {
    background-color: #51cf66;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    min-height: 35px;
}

QPushButton#addButton:hover {
    background-color: #40c057;
}

QPushButton#refreshButton {
    background-color: #4dabf7;
    color: white;
    border-radius: 5px;
    font-size: 18px;
    min-height: 35px;
}

QPushButton#refreshButton:hover {
    background-color: #339af0;
}

/* Tabele */
QTableView, QTableWidget {
    background-color: #1e272e;
    alternate-background-color: #2c3034;
    color: white;
    gridline-color: #2c3034;
    border: 1px solid #2c3034;
    selection-background-color: #4dabf7;
    selection-color: white;
    font-size: 14px;
}

QTableView::item, QTableWidget::item {
    padding: 8px;
    min-height: 25px;
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #4dabf7;
    color: white;
}

QHeaderView::section {
    background-color: #2c3034;
    color: white;
    padding: 8px;
    border: 1px solid #2c3034;
    font-weight: bold;
    font-size: 14px;
}

/* Statusy w tabelach */
QTableWidgetItem[status="Zakończone"] {
    color: #51cf66;
}

QTableWidgetItem[status="W realizacji"] {
    color: #4dabf7;
}

QTableWidgetItem[status="Oczekujące"] {
    color: #ffa94d;
}

/* Stopka */
QFrame#footer {
    background-color: transparent;
    color: #bdc3c7;
    min-height: 35px;
    max-height: 35px;
    border-top: 1px solid #2c3034;
    font-size: 13px;
}

QStatusBar {
    background-color: transparent;
    color: #bdc3c7;
    min-height: 35px;
    font-size: 13px;
}

/* Karty na pulpicie */
QFrame[dashboard="true"] {
    border-radius: 8px;
    padding: 15px;
    margin: 5px;
}

QLabel[dashboard="title"] {
    font-size: 16px;
    font-weight: bold;
    color: white;
    margin-bottom: 5px;
}

QLabel[dashboard="value"] {
    font-size: 28px;
    font-weight: bold;
    color: white;
}

QLabel[dashboard="change"] {
    font-size: 14px;
    color: white;
}

/* Dialogi z powiadomieniami */
QDialog {
    background-color: #1e272e;
    color: white;
}

QMessageBox {
    background-color: #1e272e;
    color: white;
}

QMessageBox QLabel {
    color: white;
    font-size: 14px;
}

QMessageBox QPushButton {
    background-color: #4dabf7;
    color: white;
    min-width: 100px;
    min-height: 35px;
    border-radius: 5px;
    font-size: 14px;
    font-weight: bold;
}

QMessageBox QPushButton:hover {
    background-color: #339af0;
}
"""

# Funkcja do wyboru stylu w zależności od motywu
def get_style_sheet(theme="Dark"):
    """
    Zwraca arkusz stylu w zależności od wybranego motywu.
    Uwaga: Zawsze zwracamy ciemny motyw zgodnie z wymaganiami.
    
    Args:
        theme (str): Nazwa motywu (ignorowana - zawsze zwracamy "Dark")
        
    Returns:
        str: Arkusz stylu CSS
    """
    # Niezależnie od parametru, zwracamy ciemny motyw (zgodnie z wymaganiem)
    return STYLE_SHEET