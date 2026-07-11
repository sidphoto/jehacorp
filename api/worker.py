import sys, os, json

for path in [os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "/var/task"]:
    if path not in sys.path:
        sys.path.insert(0, path)

from lib.flask_compat import make_flask_app
from lib.core import claim_job, decrypt_job_payload
from api.run import _run_workflow_background


def handler(request):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}
    try:
        body = json.loads(request.body) if request.body else {}
        job_id = body["job_id"]
        dispatch_token = body["dispatch_token"]
        encrypted_payload = body["payload"]
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "invalid worker payload"})}

    state = claim_job(job_id, dispatch_token)
    if not state:
        return {"statusCode": 200, "body": json.dumps({"ack": True, "duplicate": True})}

    payload = decrypt_job_payload(encrypted_payload)
    _run_workflow_background(
        job_id, payload["uid"], payload["idea"], payload["workflow_type"], payload["mock_mode"],
        payload["meeting_mode"], payload["discussion_consensus"], payload["acceptance_feedback"],
        payload["single_agent"], payload["collaboration_mode"], payload["custom_openai_api_key"],
        payload["custom_gemini_api_key"], payload["token_budget"],
    )
    return {"statusCode": 200, "body": json.dumps({"ack": True})}


app = make_flask_app(handler)
