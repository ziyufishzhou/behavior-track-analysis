"""Video import API."""
from flask import Blueprint, request, jsonify
import pandas as pd

from config.paths import METADATA_FILE, get_video_dir, resolve_project_path, set_video_dir
from gui.utils import extract_mouse_id, is_video_file


bp = Blueprint("import", __name__, url_prefix="/api/import")


@bp.route("/videos")
def list_videos():
    """Recursively list all videos under the configured video directory."""
    video_dir = get_video_dir()
    videos = []
    if video_dir.exists():
        for f in sorted(video_dir.rglob("*")):
            if f.is_file() and is_video_file(str(f)):
                videos.append(str(f.relative_to(video_dir)))
    print(f"[import] video_dir={video_dir}, found {len(videos)} video files")
    return jsonify({"videos": videos, "video_dir": str(video_dir), "exists": video_dir.exists()})


@bp.route("/video-dir", methods=["GET"])
def get_video_root():
    video_dir = get_video_dir()
    return jsonify({"video_dir": str(video_dir), "exists": video_dir.exists()})


@bp.route("/video-dir", methods=["POST"])
def save_video_root():
    data = request.get_json(silent=True) or {}
    path = str(data.get("video_dir", "")).strip()
    if not path:
        return jsonify({"error": "视频目录不能为空"}), 400

    video_dir = resolve_project_path(path)
    if not video_dir.exists() or not video_dir.is_dir():
        return jsonify({
            "error": f"视频目录不存在或不是文件夹: {video_dir}",
            "video_dir": str(video_dir),
            "exists": False,
        }), 400

    set_video_dir(video_dir)
    print(f"[import] set video_dir={video_dir}")
    return jsonify({"ok": True, "video_dir": str(video_dir), "exists": True})


@bp.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("videos")
    added = []
    video_dir = get_video_dir()
    video_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.filename and is_video_file(f.filename):
            dest = video_dir / f.filename
            if not dest.exists():
                f.save(str(dest))
                added.append(f.filename)
    return jsonify({"uploaded": len(added), "names": added, "video_dir": str(video_dir)})


@bp.route("/metadata")
def get_metadata():
    if not METADATA_FILE.exists():
        return jsonify({"columns": [], "rows": []})
    df = pd.read_excel(str(METADATA_FILE))
    return jsonify({
        "columns": list(df.columns),
        "rows": df.values.tolist(),
    })


@bp.route("/metadata", methods=["POST"])
def save_metadata():
    """Save video labels only; CSV grouping belongs to preprocessing."""
    data = request.get_json()
    rows = data.get("rows", [])
    cols = ["FileName", "Experiment", "Group", "Condition", "MouseID", "Phase"]
    new_df = pd.DataFrame(rows, columns=cols if rows and len(cols) == len(rows[0]) else cols)

    if METADATA_FILE.exists():
        old_df = pd.read_excel(str(METADATA_FILE))
        extra_cols = [c for c in old_df.columns if c not in cols]
        if extra_cols:
            new_df = new_df.merge(old_df[extra_cols + ["FileName"]], on="FileName", how="left")

    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_df.to_excel(str(METADATA_FILE), index=False)
    print(f"[import] saved metadata: {len(new_df)} rows")

    return jsonify({"ok": True, "task_id": None})


@bp.route("/extract-mouse-id")
def extract_mouse_id_api():
    filename = request.args.get("filename", "")
    mid = extract_mouse_id(filename)
    return jsonify({"mouse_id": mid})
