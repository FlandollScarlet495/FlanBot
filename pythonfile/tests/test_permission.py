"""
services/permission.py のテスト
"""
import pytest


class TestPermission:
    """権限管理関数のテスト"""
    
    def test_is_admin_or_dev_with_dev(self, mock_interaction):
        """開発者IDの場合は True"""
        from services.permission import is_admin_or_dev
        from unittest.mock import patch
        
        # DEVELOPER_ID を mock_interaction.user.id と同じにする
        with patch('services.permission.DEVELOPER_ID', mock_interaction.user.id):
            assert is_admin_or_dev(mock_interaction)
    
    def test_is_admin_or_dev_with_admin(self, mock_interaction):
        """管理者権限がある場合は True"""
        from services.permission import is_admin_or_dev
        from unittest.mock import patch, MagicMock
        
        # 管理者権限を持つ user をモック
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = True
        
        with patch('services.permission.DEVELOPER_ID', 99999):
            assert is_admin_or_dev(mock_interaction)
    
    def test_is_admin_or_dev_without_permissions(self, mock_interaction):
        """権限がない場合は False"""
        from services.permission import is_admin_or_dev
        from unittest.mock import patch, MagicMock
        
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = False
        
        with patch('services.permission.DEVELOPER_ID', 99999):
            assert not is_admin_or_dev(mock_interaction)
    
    def test_can_use_vc_with_admin(self, mock_interaction):
        """管理者は VC コマンド を使用可能"""
        from services.permission import can_use_vc
        from unittest.mock import patch, MagicMock
        
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = True
        
        allow_data = {"users": [], "roles": []}
        
        with patch('services.permission.DEVELOPER_ID', 99999):
            assert can_use_vc(mock_interaction, allow_data)
    
    def test_can_use_vc_with_permitted_user(self, mock_interaction):
        """許可ユーザーは VC コマンド を使用可能"""
        from services.permission import can_use_vc
        from unittest.mock import patch, MagicMock
        
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = False
        
        user_id = mock_interaction.user.id
        allow_data = {"users": [user_id], "roles": []}
        
        with patch('services.permission.DEVELOPER_ID', 99999):
            assert can_use_vc(mock_interaction, allow_data)
    
    def test_can_use_vc_with_permitted_role(self, mock_interaction):
        """許可ロールを持つユーザーは VC コマンド を使用可能"""
        from services.permission import can_use_vc
        from unittest.mock import patch, MagicMock
        
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = False
        
        # ロールを持つユーザー
        role_id = 99999
        mock_role = MagicMock()
        mock_role.id = role_id
        mock_interaction.user.roles = [mock_role]
        
        allow_data = {"users": [], "roles": [role_id]}
        
        with patch('services.permission.DEVELOPER_ID', 77777):
            assert can_use_vc(mock_interaction, allow_data)
    
    def test_can_use_vc_without_permissions(self, mock_interaction):
        """許可がないユーザーは VC コマンド を使用不可"""
        from services.permission import can_use_vc
        from unittest.mock import patch, MagicMock
        
        mock_interaction.user.guild_permissions = MagicMock()
        mock_interaction.user.guild_permissions.administrator = False
        mock_interaction.user.roles = []
        
        allow_data = {"users": [], "roles": []}
        
        with patch('services.permission.DEVELOPER_ID', 99999):
            assert not can_use_vc(mock_interaction, allow_data)
