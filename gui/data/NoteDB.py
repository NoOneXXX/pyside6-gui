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
        # 新增 recent_notebooks 表
        self.conn.execute('''
                CREATE TABLE IF NOT EXISTS recent_notebooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    last_opened_time INTEGER NOT NULL
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

    '''保存这个笔记本'''
    def save_recent_notebook(self, path, timestamp):
        self.conn.execute('''
            INSERT INTO recent_notebooks (path, last_opened_time)
            VALUES (?, ?)
            ON CONFLICT(path) DO UPDATE SET last_opened_time = excluded.last_opened_time
        ''', (path, timestamp))
        self.conn.commit()

    '''获取这个笔记本'''
    def get_recent_notebooks(self, limit=5):
        cursor = self.conn.execute('''
            SELECT path FROM recent_notebooks
            ORDER BY last_opened_time DESC
            LIMIT ?
        ''', (limit,))
        return [row[0] for row in cursor.fetchall()]




