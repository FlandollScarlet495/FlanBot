"""
ストレージサービス

JSONファイルの読み書きを担当する
"""
import json
import os
from typing import Dict, Any


class JSONStorage:
    """JSONファイルの読み書きを管理するクラス"""
    
    def __init__(self, filepath: str, default_data: Dict[str, Any]):
        """
        初期化
        
        Args:
            filepath: JSONファイルのパス
            default_data: ファイルが存在しない場合のデフォルトデータ
        """
        self.filepath = filepath
        self.default_data = default_data
    
    def load(self) -> Dict[str, Any]:
        """
        データを読み込む
        
        Returns:
            dict: 読み込んだデータ
        """
        if not os.path.exists(self.filepath):
            return self.default_data.copy()
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"ファイル読み込みエラー ({self.filepath}): {e}")
            return self.default_data.copy()
    
    def save(self, data: Dict[str, Any]) -> bool:
        """
        データを保存する
        
        Args:
            data: 保存するデータ
            
        Returns:
            bool: 保存成功ならTrue
        """
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"ファイル保存エラー ({self.filepath}): {e}")
            return False


# よく使うストレージのインスタンスを作成
vc_state_storage = JSONStorage("vc_state.json", {})
vc_allow_storage = JSONStorage("vc_allow.json", {"users": [], "roles": []})
