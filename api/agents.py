import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app, re, time
from lib.core import (BUILTIN_AGENTS, get_user_agents, save_user_agents,
                      get_user_settings, get_llm_client, get_user_id_from_request)

def handler(request):
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    if request.method == "GET":
        custom = get_user_agents(uid)
        all_agents = BUILTIN_AGENTS + custom
        return {"statusCode": 200, "body": json.dumps(all_agents, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    if request.method == "POST":
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}

        agent_name = body.get("name", "").strip()
        system_prompt = body.get("system_prompt", "").strip()
        if not agent_name or not system_prompt:
            return {"statusCode": 400, "body": json.dumps({"error": "請填寫代理人名稱與系統提示詞！"}, ensure_ascii=False)}

        emoji = body.get("emoji", "👤").strip()
        description = body.get("description", "").strip()
        llm_source = body.get("llm_source", "gpt-4o-mini").strip()
        category = body.get("category", "custom").strip()
        avatar_prompt = body.get("avatar_prompt", "").strip()
        agent_id = "custom-" + re.sub(r'[^a-zA-Z0-9\-]', '', agent_name.lower().replace(" ", "-")) + "-" + str(int(time.time()))[-4:]

        # 頭像生成 (若有 avatar_prompt 且有 OpenAI Key)
        avatar_url = ""
        if avatar_prompt:
            try:
                user_settings = get_user_settings(uid)
                if user_settings.get("subscription") == "pro" and user_settings.get("openai_api_key"):
                    import urllib.request as ureq, urllib.parse as uparse
                    client, _ = get_llm_client("gpt-4o", user_api_keys=user_settings)
                    if client:
                        resp = client.images.generate(
                            model="dall-e-3",
                            prompt=f"A professional card game portrait of: {avatar_prompt}, trading card illustration style, cyberpunk wabi-sabi art style",
                            size="1024x1024", n=1
                        )
                        avatar_url = resp.data[0].url  # 直接用臨時 URL (Vercel 無本地儲存)
            except Exception:
                pass

        if not avatar_url:
            import urllib.parse as uparse
            seed = uparse.quote(avatar_prompt or agent_name)
            avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={seed}"

        custom_agents = get_user_agents(uid)
        new_agent = {
            "id": agent_id, "name": agent_name, "emoji": emoji,
            "description": description, "system_prompt": system_prompt,
            "llm_source": llm_source, "category": category,
            "avatar_url": avatar_url, "is_custom": True
        }
        custom_agents.append(new_agent)
        save_user_agents(uid, custom_agents)
        return {"statusCode": 200, "body": json.dumps({"message": "代理人招募成功！", "agent": new_agent}, ensure_ascii=False),
                "headers": {"Content-Type": "application/json; charset=utf-8"}}

    return {"statusCode": 405, "body": "Method Not Allowed"}

app = make_flask_app(handler)
