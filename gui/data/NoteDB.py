# note_db.py
import sqlite3

class NoteDB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                title TEXT NOT NULL,
                parent_id TEXT,
                created_time INTEGER NOT NULL,
                updated_time INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def insert_note(self, id_, path, title, parent_id, created_time, updated_time):
        self.conn.execute(
            '''
            INSERT INTO notes (id, path, title, parent_id, created_time, updated_time)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (id_, path, title, parent_id, created_time, updated_time)
        )
        self.conn.commit()
