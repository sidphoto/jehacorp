import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app
from lib.core import get_job_state, get_user_id_from_request, request_job_control, enqueue_job

def handler(request):
    """
    GET /api/job?id=<job_id>
    前端用 Polling（每 1.5s）呼叫此 endpoint 獲取任務進度
    回傳：{job_id, status, events: [...], finished: bool}
    """
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    if request.method not in {"GET", "POST"}:
        return {"statusCode": 405, "body": "Method Not Allowed"}

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

    if state.get("user_id") and state.get("user_id") != uid:
        return {"statusCode": 404, "body": json.dumps({"error": "找不到此任務"}, ensure_ascii=False)}

    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
            action = body.get("action", "")
        except Exception:
            action = ""
        if action not in {"pause", "resume", "cancel"}:
            return {"statusCode": 400, "body": json.dumps({"error": "無效控制動作"}, ensure_ascii=False)}
        state = request_job_control(job_id, uid, action)
        if action == "resume" and state and state.get("status") == "queued":
            enqueue_job(job_id, state["encrypted_payload"], state["dispatch_token"], suffix=f"resume-{int(__import__('time').time())}")

    public_state = dict(state)
    public_state.pop("dispatch_token", None)
    public_state.pop("encrypted_payload", None)
    public_state.pop("user_id", None)
    return {
        "statusCode": 200,
        "body": json.dumps(public_state, ensure_ascii=False),
        "headers": {"Content-Type": "application/json; charset=utf-8"}
    }

app = make_flask_app(handler)
