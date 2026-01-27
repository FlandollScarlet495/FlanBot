# -*- coding: utf-8 -*-
from typing import Dict
import json, os

DICT_FILE = "romaji_kana_dict.json"

def load_dict() -> Dict[str,str]:
    if not os.path.exists(DICT_FILE):
        return {}
    try:
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}

def save_dict(d: Dict[str,str]):
    try:
        with open(DICT_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

def romaji_to_kana(text: str, kana_type: str = "hiragana") -> str:
    """
    text: ローマ字
    kana_type: "hiragana" または "katakana"
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()
    d = load_dict()
    if not d:
        return text

    MAX_KEY_LEN = max((len(k) for k in d.keys()), default=0)
    VOWELS = set("aiueo")
    i = 0
    out = []

    while i < len(text):
        # 促音（同じ子音2連続）
        if (
            i + 1 < len(text)
            and text[i] == text[i + 1]
            and text[i] not in ("n",)
        ):
            out.append("っ" if kana_type == "hiragana" else "ッ")
            i += 1
            continue

        # 「ん」処理
        if text[i] == "n":
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt == "n":
                out.append("ん" if kana_type == "hiragana" else "ン")
                i += 2
                continue
            if nxt and nxt not in VOWELS and nxt != "y":
                out.append("ん" if kana_type == "hiragana" else "ン")
                i += 1
                continue

        # 長音
        if text[i] == "-":
            out.append("ー")
            i += 1
            continue

        matched = False
        max_try = min(MAX_KEY_LEN, len(text) - i)
        for L in range(max_try, 0, -1):
            seg = text[i:i + L]
            if seg in d:
                kana_char = d[seg]
                if kana_type == "katakana":
                    kana_char = ''.join(
                        chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c
                        for c in kana_char
                    )
                out.append(kana_char)
                i += L
                matched = True
                break

        if matched:
            continue

        out.append(text[i])
        i += 1

    return "".join(out)

def register_word(romaji_word: str):
    if not isinstance(romaji_word, str) or not romaji_word:
        return
    d = load_dict()
    kana_word = romaji_to_kana(romaji_word)
    if romaji_word not in d:
        d[romaji_word] = kana_word
        save_dict(d)

def register_all_patterns():
    vowels = ["a", "i", "u", "e", "o"]
    consonants = [
        "k","s","t","n","h","m","y","r","w",
        "g","z","d","b","p",
        "ky","sy","ty","ny","my","ry","gy","zy","dy","by","py",
        "q","c","j","sh","th","f","ch","x","l","dh","qy","jy","wh","v","vy"
    ]

    small_map = {
        "a":"ぁ","i":"ぃ","u":"ぅ","e":"ぇ","o":"ぉ",
        "ya":"ゃ","yu":"ゅ","yo":"ょ","tu":"っ"
    }

    d = load_dict()

    for v in vowels:
        d.setdefault(v, v)

    for c in consonants:
        for v in vowels:
            w = c + v
            if w in d:
                continue
            if c in ("l", "x"):
                d[w] = small_map.get(v, v)
            else:
                d[w] = w

    save_dict(d)

if __name__ == "__main__":
    register_all_patterns()
    tests = ["arigatou", "konnichiwa", "ohayou-", "kanpai-"]
    for t in tests:
        print(t, romaji_to_kana(t, "hiragana"), romaji_to_kana(t, "katakana"))
