"""
権限管理サービス

ユーザーの権限チェックを担当する
"""
import discord
from typing import Dict, Any, List
from ..config import DEVELOPER_ID


def is_admin_or_dev(interaction: discord.Interaction) -> bool:
    """
    管理者または開発者かチェック
    
    Args:
        interaction: Discordのインタラクション
        
    Returns:
        bool: 管理者または開発者ならTrue
    """
    return (
        interaction.user.id == DEVELOPER_ID
        or interaction.user.guild_permissions.administrator
    )


def can_use_vc(interaction: discord.Interaction, allow_data: dict) -> bool:
    """
    VCコマンドを使用できるかチェック
    
    Args:
        interaction: Discordのインタラクション
        allow_data: VC許可リストのデータ
        
    Returns:
        bool: 使用可能ならTrue
    """
    # 管理者または開発者は常にOK
    if is_admin_or_dev(interaction):
        return True
    
    member = interaction.user
    
    # ユーザー許可チェック
    if member.id in allow_data.get("users", []):
        return True
    
    # ロール許可チェック
    member_role_ids = {r.id for r in member.roles}
    if any(rid in member_role_ids for rid in allow_data.get("roles", [])):
        return True
    
    return False
