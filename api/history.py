import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app
from lib.core import (list_user_projects, get_project_files, get_user_id_from_request)

def handler(request):
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "未授權"}, ensure_ascii=False)}

    projects = list_user_projects(uid)
    result = []
    for p in reversed(projects):  # 最新的排前面
        project_id = p.get("project_id", "")
        files_dict = get_project_files(uid, project_id)
        files = []
        for fname, fcontent in files_dict.items():
            files.append({
                "filename": fname,
                "relative_path": f"api/file?project={project_id}&file={fname}",
                "size": len(fcontent.encode("utf-8")),
                "updated_at": p.get("created_at", "")
            })
        result.append({
            "project_id": project_id,
            "project_name": p.get("project_name", project_id),
            "created_at": p.get("created_at", ""),
            "files": files
        })
    return {"statusCode": 200, "body": json.dumps(result, ensure_ascii=False),
            "headers": {"Content-Type": "application/json; charset=utf-8"}}

app = make_flask_app(handler)
