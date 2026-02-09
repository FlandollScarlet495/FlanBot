import sqlite3
from config import DB_PATH

class SQLiteBase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)
