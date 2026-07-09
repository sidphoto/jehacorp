import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from lib.flask_compat import make_flask_app
from lib.core import get_job_state, get_user_id_from_request

def handler(request):
    """
    GET /api/job?id=<job_id>
    前端用 Polling（每 1.5s）呼叫此 endpoint 獲取任務進度
    回傳：{job_id, status, events: [...], finished: bool}
    """
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    params = {}
    if "?" in (request.path or ""):
        import urllib.parse
        qs = request.path.split("?", 1)[1]
        params = dict(urllib.parse.parse_qsl(qs))

    job_id = params.get("id", "").strip()
    if not job_id:
        return {"statusCode": 400, "body": json.dumps({"error": "缺少 job id"}, ensure_ascii=False)}

    state = get_job_state(job_id)
    if state is None:
        return {"statusCode": 404, "body": json.dumps({"error": "找不到此任務，可能已過期"}, ensure_ascii=False)}

    return {
        "statusCode": 200,
        "body": json.dumps(state, ensure_ascii=False),
        "headers": {"Content-Type": "application/json; charset=utf-8"}
    }

app = make_flask_app(handler)
