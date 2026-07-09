import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from lib.flask_compat import make_flask_app
from lib.core import get_project_files, get_user_id_from_request

def handler(request):
    """
    GET /api/file?project=<project_id>&file=<filename>
    返回 KV 中儲存的檔案內容（純文字或 markdown）
    """
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    params = {}
    if "?" in (request.path or ""):
        import urllib.parse
        qs = request.path.split("?", 1)[1]
        params = dict(urllib.parse.parse_qsl(qs))

    project_id = params.get("project", "").strip()
    filename = params.get("file", "").strip()

    if not project_id or not filename:
        return {"statusCode": 400, "body": json.dumps({"error": "缺少 project 或 file 參數"}, ensure_ascii=False)}

    # 安全性：防止路徑穿越
    if ".." in filename or filename.startswith("/"):
        return {"statusCode": 400, "body": json.dumps({"error": "無效的檔案路徑"}, ensure_ascii=False)}

    files = get_project_files(uid, project_id)
    if filename not in files:
        return {"statusCode": 404, "body": json.dumps({"error": "找不到此檔案"}, ensure_ascii=False)}

    content = files[filename]
    # 根據副檔名設定 Content-Type
    content_type = "text/plain; charset=utf-8"
    if filename.endswith(".md"):
        content_type = "text/markdown; charset=utf-8"
    elif filename.endswith(".html"):
        content_type = "text/html; charset=utf-8"
    elif filename.endswith(".json"):
        content_type = "application/json; charset=utf-8"

    return {
        "statusCode": 200,
        "body": content,
        "headers": {
            "Content-Type": content_type,
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    }

app = make_flask_app(handler)
