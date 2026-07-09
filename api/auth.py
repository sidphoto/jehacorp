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
    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}
        email = body.get("email", "").strip()
        if not email or "@" not in email:
            return {"statusCode": 400, "body": json.dumps({"error": "請提供正確的電子郵件進行 SSO 會員註冊！"}, ensure_ascii=False)}
        # 確保 user.md 初始化
        get_user_md(email)
        username = email.split("@")[0]
        return {
            "statusCode": 200,
            "body": json.dumps({"token": email, "name": username, "avatar": "🎓", "email": email}, ensure_ascii=False),
            "headers": {"Content-Type": "application/json; charset=utf-8"}
        }
    return {"statusCode": 405, "body": "Method Not Allowed"}

app = make_flask_app(handler)
