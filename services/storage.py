"""
ストレージサービス

SQLiteデータベースの読み書きを担当する
"""
import sqlite3
from typing import Dict, Any, List
from config import DB_PATH
from .logger import logger


class SQLiteStorage:
    """SQLiteデータベースを管理するクラス"""
    
    def __init__(self, db_path: str):
        """
        初期化
        
        Args:
            db_path: SQLiteデータベースのパス
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """データベースを初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # VC許可テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vc_allows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        target_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        UNIQUE(type, target_id)
                    )
                """)
                
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"データベース初期化エラー ({self.db_path}): {e}")
    
    def load(self) -> Dict[str, Any]:
        """
        VC許可データを読み込む（互換性のため）
        
        Returns:
            dict: {"users": [...], "roles": [...]} 形式
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT target_id FROM vc_allows WHERE type = 'user'")
                users = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT target_id FROM vc_allows WHERE type = 'role'")
                roles = [row[0] for row in cursor.fetchall()]
                
                return {"users": users, "roles": roles}
        except sqlite3.Error as e:
            logger.error(f"データ読み込みエラー ({self.db_path}): {e}")
            return {"users": [], "roles": []}
    
    def save(self, data: Dict[str, Any]) -> bool:
        """
        VC許可データを保存（互換性のため）
        
        Args:
            data: {"users": [...], "roles": [...]} 形式
            
        Returns:
            bool: 保存成功ならTrue
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 既存データをクリア
                cursor.execute("DELETE FROM vc_allows")
                
                # ユーザーを追加
                for user_id in data.get("users", []):
                    cursor.execute(
                        "INSERT INTO vc_allows (type, target_id, user_id) VALUES (?, ?, ?)",
                        ("user", user_id, user_id)
                    )
                
                # ロールを追加
                for role_id in data.get("roles", []):
                    cursor.execute(
                        "INSERT INTO vc_allows (type, target_id, user_id) VALUES (?, ?, ?)",
                        ("role", role_id, 0)
                    )
                
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"データ保存エラー ({self.db_path}): {e}")
            return False
    
    def add_user(self, user_id: int) -> bool:
        """
        ユーザー許可を追加
        
        Args:
            user_id: ユーザーID
            
        Returns:
            bool: 成功ならTrue
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO vc_allows (type, target_id, user_id) VALUES (?, ?, ?)",
                    ("user", user_id, user_id)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            logger.error(f"ユーザー追加エラー: {e}")
            return False
    
    def remove_user(self, user_id: int) -> bool:
        """
        ユーザー許可を削除
        
        Args:
            user_id: ユーザーID
            
        Returns:
            bool: 成功ならTrue
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vc_allows WHERE type = 'user' AND target_id = ?",
                    (user_id,)
                )
                conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"エラー: {e}")
            return False
    
    def add_role(self, role_id: int) -> bool:
        """
        ロール許可を追加
        
        Args:
            role_id: ロールID
            
        Returns:
            bool: 成功ならTrue
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO vc_allows (type, target_id, user_id) VALUES (?, ?, ?)",
                    ("role", role_id, 0)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            logger.error(f"エラー: {e}")
            return False
    
    def remove_role(self, role_id: int) -> bool:
        """
        ロール許可を削除
        
        Args:
            role_id: ロールID
            
        Returns:
            bool: 成功ならTrue
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vc_allows WHERE type = 'role' AND target_id = ?",
                    (role_id,)
                )
                conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"エラー: {e}")
            return False


# よく使うストレージのインスタンスを作成
vc_allow_storage = SQLiteStorage(DB_PATH)
