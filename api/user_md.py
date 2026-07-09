import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app
from lib.core import get_user_md, save_user_md, get_user_id_from_request

def handler(request):
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    if request.method == "GET":
        content = get_user_md(uid)
        return {"statusCode": 200, "body": json.dumps({"content": content}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}
        content = body.get("content", "").strip()
        if not content:
            return {"statusCode": 400, "body": json.dumps({"error": "記憶庫內容不可為空！"}, ensure_ascii=False)}
        save_user_md(uid, content)
        return {"statusCode": 200, "body": json.dumps({"message": "總裁習慣記憶庫更新成功！"}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    return {"statusCode": 405, "body": "Method Not Allowed"}

app = make_flask_app(handler)
