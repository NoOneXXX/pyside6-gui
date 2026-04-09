# note_db.py
import sqlite3
import time


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

        # 3. 新增：索引异步任务队列
        self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS indexing_queue (
                        rel_path TEXT PRIMARY KEY,
                        timestamp INTEGER NOT NULL,
                        action TEXT DEFAULT 'update'
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
    def get_recent_notebooks(self, limit=15):
        cursor = self.conn.execute('''
            SELECT path FROM recent_notebooks
            ORDER BY last_opened_time DESC
            LIMIT ?
        ''', (limit,))
        return [row[0] for row in cursor.fetchall()]

    '''更新笔记本打开时间'''
    def update_notebook_last_opened(self, path: str):
        self.conn.execute('''
            UPDATE recent_notebooks
            SET last_opened_time = CURRENT_TIMESTAMP
            WHERE path = ?
        ''', (path,))
        self.conn.commit()

    '''删除这个最近的笔记本 如果找不到就删除'''
    def delete_recent_notebook(self, path):
        self.conn.execute('''
                    DELETE  FROM recent_notebooks WHERE path = ?
                ''', (path,))
        self.conn.commit()

    # 添加到索引队列
    def add_to_index_queue(self, rel_path):
        self.conn.execute('''
            INSERT INTO indexing_queue (rel_path, timestamp) 
            VALUES (?, ?) ON CONFLICT(rel_path) DO UPDATE SET timestamp=excluded.timestamp
        ''', (rel_path, int(time.time())))
        self.conn.commit()

    # 获取队列大小
    def get_queue_size(self):
        return self.conn.execute('SELECT COUNT(*) FROM indexing_queue').fetchone()[0]




