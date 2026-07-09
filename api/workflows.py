import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from lib.flask_compat import make_flask_app, time
from lib.core import (BUILTIN_WORKFLOWS, get_user_workflows, save_user_workflows,
                      get_user_id_from_request)

def handler(request):
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    if request.method == "GET":
        custom = get_user_workflows(uid)
        return {"statusCode": 200, "body": json.dumps(BUILTIN_WORKFLOWS + custom, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}
        wf_name = body.get("name", "").strip()
        flow = body.get("flow", [])
        if not wf_name or not flow:
            return {"statusCode": 400, "body": json.dumps({"error": "請填寫團隊名稱並挑選至少一位成員！"}, ensure_ascii=False)}
        wf_id = "wf-" + str(int(time.time()))
        new_wf = {"id": wf_id, "name": wf_name, "description": body.get("description", "").strip(), "flow": flow, "is_custom": True}
        workflows = get_user_workflows(uid)
        workflows.append(new_wf)
        save_user_workflows(uid, workflows)
        return {"statusCode": 200, "body": json.dumps({"message": "團隊工作流儲存成功！", "workflow": new_wf}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    return {"statusCode": 405, "body": "Method Not Allowed"}

app = make_flask_app(handler)
