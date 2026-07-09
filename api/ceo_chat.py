import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app
from lib.core import (get_user_md, get_user_settings, get_llm_client, get_user_id_from_request)

def handler(request):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}

    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    try:
        body = json.loads(request.body) if request.body else {}
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}

    idea = body.get("idea", "").strip()
    message = body.get("message", "").strip()
    chat_history = body.get("history", [])

    if not idea or not message:
        return {"statusCode": 400, "body": json.dumps({"error": "缺少 idea 或 message"}, ensure_ascii=False)}

    user_md = get_user_md(uid)
    user_settings = get_user_settings(uid)
    is_pro = user_settings.get("subscription") == "pro"

    system_instruction = f"""您是 JehaCrop 公司的「執行總裁 (CEO)」。
目前董事長正在與您討論全新專案：「{idea}」。
請站在執行總裁的專業高度，與董事長深入對答討論。
遵守：1. 結論先行 2. 貼合 user.md 習慣 3. 引導董事長點選派遣執行按鈕。

董事長偏好記憶 (user.md)：
{user_md}
"""
    messages = [{"role": "system", "content": system_instruction}]
    for h in chat_history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        api_keys = user_settings if is_pro else None
        client, model_name = get_llm_client("gpt-4o-mini", user_api_keys=api_keys)
        if client:
            resp = client.chat.completions.create(model=model_name, messages=messages, temperature=0.7)
            reply = resp.choices[0].message.content
        else:
            reply = f"【CEO 總裁回報】董事長好！針對您的點子「{idea}」以及「{message}」，我建議調度「新創 MVP 開發團隊」工作流。董事長若覺得可行，請點選下方派遣執行按鈕！"
    except Exception as e:
        reply = f"【CEO 總裁回報】董事長好！針對您的點子「{idea}」，我已有初步構想。請點選派遣執行按鈕！"

    return {"statusCode": 200, "body": json.dumps({"reply": reply}, ensure_ascii=False),
            "headers": {"Content-Type": "application/json; charset=utf-8"}}

app = make_flask_app(handler)
