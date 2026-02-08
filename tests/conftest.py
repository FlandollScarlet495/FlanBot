"""
pytest の設定と共通フィクスチャ
"""
import pytest
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db(tmp_path):
    """テスト用の一時的なデータベース"""
    return str(tmp_path / "test.db")


@pytest.fixture
def db_storage(temp_db):
    """テスト用の SQLiteStorage インスタンス"""
    from services.storage import SQLiteStorage
    storage = SQLiteStorage(temp_db)
    yield storage
    # クリーンアップ
    if os.path.exists(temp_db):
        os.remove(temp_db)


@pytest.fixture
def mock_interaction():
    """モック Discord Interaction"""
    class MockUser:
        id = 12345
        name = "TestUser"
        
        def __str__(self):
            return f"{self.name} ({self.id})"
    
    class MockGuild:
        id = 67890
    
    class MockInteraction:
        user = MockUser()
        guild = MockGuild()
    
    return MockInteraction()
