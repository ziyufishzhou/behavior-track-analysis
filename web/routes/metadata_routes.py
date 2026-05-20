"""元数据编辑 API"""
from flask import Blueprint, request, jsonify
from config.paths import METADATA_FILE
import pandas as pd

bp = Blueprint('metadata', __name__, url_prefix='/api/metadata')


@bp.route('')
def get_metadata():
    """读取 metadata.xlsx"""
    if not METADATA_FILE.exists():
        return jsonify({'columns': [], 'rows': []})
    df = pd.read_excel(str(METADATA_FILE))
    return jsonify({
        'columns': list(df.columns),
        'rows': df.values.tolist()
    })


@bp.route('', methods=['POST'])
def save_metadata():
    """保存 metadata.xlsx（更新模式：保留手动添加的列）"""
    data = request.get_json()
    rows = data.get('rows', [])
    cols = data.get('columns', [])
    if not rows or not cols:
        return jsonify({'error': '空数据'}), 400

    new_df = pd.DataFrame(rows, columns=cols)

    # 更新模式：保留旧文件中不在新列中的额外列
    update = data.get('update', True)
    if update and METADATA_FILE.exists():
        old_df = pd.read_excel(str(METADATA_FILE))
        extra_cols = [c for c in old_df.columns if c not in cols]
        if extra_cols:
            # 用 FileName 作为 key 合并
            key_col = 'FileName' if 'FileName' in cols else None
            if key_col and key_col in old_df.columns:
                new_df = new_df.merge(old_df[extra_cols + [key_col]], on=key_col, how='left')
            else:
                # 没有 key 列，直接拼接额外列
                for c in extra_cols:
                    new_df[c] = old_df[c].values[:len(new_df)]

    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_df.to_excel(str(METADATA_FILE), index=False)
    return jsonify({'ok': True})


@bp.route('/rescan', methods=['POST'])
def rescan():
    """重新扫描 — 从 grouped/ 目录结构推断标签，合并到现有 metadata（不覆盖已有值）"""
    from preprocessing.build_metadata import build_metadata
    update = request.json.get('update', True) if request.json else True

    # 如果 metadata.xlsx 已存在且 update=True，则只填充空值
    build_metadata(update=update)
    return get_metadata()


@bp.route('/columns', methods=['POST'])
def add_column():
    """添加新列"""
    data = request.get_json()
    col_name = data.get('name', '').strip()
    if not col_name:
        return jsonify({'error': '列名不能为空'}), 400

    if METADATA_FILE.exists():
        df = pd.read_excel(str(METADATA_FILE))
        if col_name in df.columns:
            return jsonify({'error': '列已存在'}), 400
        df[col_name] = ''
        df.to_excel(str(METADATA_FILE), index=False)
    else:
        df = pd.DataFrame(columns=[col_name])
        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(str(METADATA_FILE), index=False)

    return jsonify({'ok': True})