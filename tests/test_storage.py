"""
services/storage.py のテスト
"""
import pytest


class TestSQLiteStorage:
    """SQLiteStorage クラスのテスト"""
    
    def test_init_creates_database(self, temp_db):
        """データベース初期化が成功"""
        from services.storage import SQLiteStorage
        storage = SQLiteStorage(temp_db)
        assert storage.db_path == temp_db
    
    def test_add_user(self, db_storage):
        """ユーザー許可を追加"""
        user_id = 12345
        assert db_storage.add_user(user_id)
        
        # 追加したユーザーが含まれているか確認
        data = db_storage.load()
        assert user_id in data["users"]
    
    def test_add_user_duplicate(self, db_storage):
        """重複したユーザーは追加不可"""
        user_id = 12345
        db_storage.add_user(user_id)
        
        # 2回目は失敗
        assert not db_storage.add_user(user_id)
    
    def test_remove_user(self, db_storage):
        """ユーザー許可を削除"""
        user_id = 12345
        db_storage.add_user(user_id)
        assert db_storage.remove_user(user_id)
        
        # 削除後は存在しない
        data = db_storage.load()
        assert user_id not in data["users"]
    
    def test_remove_user_not_exists(self, db_storage):
        """存在しないユーザーの削除は失敗"""
        assert not db_storage.remove_user(99999)
    
    def test_add_role(self, db_storage):
        """ロール許可を追加"""
        role_id = 54321
        assert db_storage.add_role(role_id)
        
        # 追加したロールが含まれているか確認
        data = db_storage.load()
        assert role_id in data["roles"]
    
    def test_add_role_duplicate(self, db_storage):
        """重複したロールは追加不可"""
        role_id = 54321
        db_storage.add_role(role_id)
        
        # 2回目は失敗
        assert not db_storage.add_role(role_id)
    
    def test_remove_role(self, db_storage):
        """ロール許可を削除"""
        role_id = 54321
        db_storage.add_role(role_id)
        assert db_storage.remove_role(role_id)
        
        # 削除後は存在しない
        data = db_storage.load()
        assert role_id not in data["roles"]
    
    def test_remove_role_not_exists(self, db_storage):
        """存在しないロールの削除は失敗"""
        assert not db_storage.remove_role(99999)
    
    def test_load_empty(self, db_storage):
        """空のデータを読み込む"""
        data = db_storage.load()
        assert data == {"users": [], "roles": []}
    
    def test_save_and_load(self, db_storage):
        """データの保存と読み込み"""
        test_data = {
            "users": [11111, 22222, 33333],
            "roles": [44444, 55555]
        }
        db_storage.save(test_data)
        
        loaded_data = db_storage.load()
        assert sorted(loaded_data["users"]) == sorted(test_data["users"])
        assert sorted(loaded_data["roles"]) == sorted(test_data["roles"])
    
    def test_multiple_users_and_roles(self, db_storage):
        """複数のユーザーとロールを管理"""
        # ユーザーを複数追加
        users = [111, 222, 333]
        for uid in users:
            assert db_storage.add_user(uid)
        
        # ロールを複数追加
        roles = [444, 555, 666]
        for rid in roles:
            assert db_storage.add_role(rid)
        
        # 全て含まれているか確認
        data = db_storage.load()
        assert sorted(data["users"]) == sorted(users)
        assert sorted(data["roles"]) == sorted(roles)
