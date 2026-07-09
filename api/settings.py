import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from lib.core import (get_user_settings, save_user_settings, get_user_id_from_request)

def handler(request):
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    if request.method == "GET":
        s = get_user_settings(uid)
        masked = {
            "subscription": s["subscription"],
            "openai_api_key": s["openai_api_key"][:6] + "********" if s.get("openai_api_key") else "",
            "gemini_api_key": s["gemini_api_key"][:6] + "********" if s.get("gemini_api_key") else "",
            "cron_enabled": s.get("cron_enabled", False),
            "cron_schedule": s.get("cron_schedule", "every_60s"),
            "cron_idea": s.get("cron_idea", ""),
            "cron_workflow": s.get("cron_workflow", "mvp"),
        }
        return {"statusCode": 200, "body": json.dumps(masked, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}

        current = get_user_settings(uid)
        openai_key = body.get("openai_api_key", "").strip()
        gemini_key = body.get("gemini_api_key", "").strip()
        if openai_key.endswith("********"):
            openai_key = current["openai_api_key"]
        if gemini_key.endswith("********"):
            gemini_key = current["gemini_api_key"]

        updated = {
            "subscription": body.get("subscription", "free").strip(),
            "openai_api_key": openai_key,
            "gemini_api_key": gemini_key,
            "cron_enabled": body.get("cron_enabled", False),
            "cron_schedule": body.get("cron_schedule", "every_60s").strip(),
            "cron_idea": body.get("cron_idea", "").strip(),
            "cron_workflow": body.get("cron_workflow", "mvp").strip(),
        }
        save_user_settings(uid, updated)
        return {"statusCode": 200, "body": json.dumps({"message": "總裁 API 與訂閱設定保存成功！"}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    return {"statusCode": 405, "body": "Method Not Allowed"}
