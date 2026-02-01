"""
顔・名前登録のストレージ抽象層
-----------------------------
パーソナルモードの「名前と顔が一致した場合に有効」用。
現状はローカル JSON ファイル。将来 S3 等に差し替え可能にするため、
API は list / get / save / delete に統一する。
"""

import os
import json
import uuid
import threading

# データファイル（将来は S3 等に差し替え）
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_REGISTRY_FILE = os.path.join(_DATA_DIR, 'face_registry.json')
_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load():
    _ensure_dir()
    if not os.path.exists(_REGISTRY_FILE):
        return {'persons': []}
    with open(_REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(data):
    _ensure_dir()
    with open(_REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_persons():
    """登録者一覧（id, name のみ。顔データは返さない）"""
    with _lock:
        data = _load()
    return [{'id': p['id'], 'name': p['name']} for p in data.get('persons', [])]


def get_person(person_id, include_face=True):
    """1件取得。include_face=False のときは faceData を含めない"""
    with _lock:
        data = _load()
    for p in data.get('persons', []):
        if p['id'] == person_id:
            out = {'id': p['id'], 'name': p['name']}
            if include_face and p.get('faceData'):
                out['faceData'] = p['faceData']
            return out
    return None


def create_person(name):
    """名前のみで新規登録。id を発行して返す"""
    with _lock:
        data = _load()
        person_id = str(uuid.uuid4())
        data.setdefault('persons', []).append({
            'id': person_id,
            'name': name.strip(),
            'faceData': None
        })
        _save(data)
    return {'id': person_id, 'name': name.strip()}


def update_face(person_id, face_data):
    """指定 id の顔データを更新。存在しなければ False"""
    with _lock:
        data = _load()
        for p in data.get('persons', []):
            if p['id'] == person_id:
                p['faceData'] = face_data
                _save(data)
                return True
    return False


def delete_person(person_id):
    """指定 id を削除。存在しなければ False"""
    with _lock:
        data = _load()
        persons = data.get('persons', [])
        new_list = [p for p in persons if p['id'] != person_id]
        if len(new_list) == len(persons):
            return False
        data['persons'] = new_list
        _save(data)
        return True
