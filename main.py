"""
main.py
"""

#vfrom database.migrations import run_migrations
from database.database import DatabaseManager
from ui.main_window import MainWindow


def main():
    # Migrations AVANT de créer DatabaseManager
    #run_migrations("database.db")
    
    # Maintenant DatabaseManager est sûr
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()