import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PySide6.QtGui import QIcon

class SystemTrayManager:
    def __init__(self, app, main_window):
        self.app = app
        self.main_window = main_window

        # Tworzenie ikony zasobnika
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), parent=app)
        self.tray_icon.setToolTip("Tire Deposit Manager")

        # Tworzenie menu kontekstowego
        self.tray_menu = QMenu()

        # Akcja otwierania aplikacji
        open_action = QAction("Otwórz", self.tray_menu)
        open_action.triggered.connect(self.show_main_window)
        self.tray_menu.addAction(open_action)

        # Separator
        self.tray_menu.addSeparator()

        # Akcja wyjścia z aplikacji
        exit_action = QAction("Wyjdź", self.tray_menu)
        exit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(exit_action)

        # Przypisanie menu do ikony
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def show_main_window(self):
        if self.main_window.isMinimized():
            self.main_window.showNormal()
        self.main_window.activateWindow()

    def quit_application(self):
        reply = QMessageBox.question(
            None, "Potwierdzenie wyjścia", "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.app.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    from ui.main_window import MainWindow
    main_window = MainWindow()
    SystemTrayManager(app, main_window)
    main_window.show()
    sys.exit(app.exec())
