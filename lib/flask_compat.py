"""
lib/flask_compat.py — Vercel Python Serverless 相容層
將原本 handler(request) → dict 的格式，包裝成 Flask WSGI app
讓每個 api/*.py 只需最後一行：app = make_flask_app(handler)
"""
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from flask import Flask, request as flask_request, Response


class _FakeRequest:
    """將 Flask request 適配成 handler 期待的介面"""
    def __init__(self):
        self.method = flask_request.method
        self.headers = flask_request.headers
        self.body = flask_request.get_data(as_text=True)
        # 保留完整 query string，方便 /api/job?id=xxx 等解析
        self.path = flask_request.full_path.rstrip('?')


def make_flask_app(handler_fn):
    """
    接受任一 handler(request) -> dict 函數，
    返回一個可被 Vercel 識別的 Flask WSGI app。
    """
    app = Flask(__name__)

    # CORS 預檢
    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return resp

    # 捕捉所有路徑（Vercel 已做路由，這裡只是讓 Flask 不報 404）
    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
    @app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
    def _dispatch(path):
        if flask_request.method == 'OPTIONS':
            return Response('', 204)

        try:
            fake_req = _FakeRequest()
            result = handler_fn(fake_req)

            status_code = result.get('statusCode', 200)
            body = result.get('body', '')
            headers = result.get('headers', {'Content-Type': 'application/json; charset=utf-8'})

            resp = Response(body, status=status_code)
            for k, v in headers.items():
                resp.headers[k] = v
            return resp
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            err_body = json.dumps({"error": f"後端崩潰錯誤日誌：\n{err_msg}"}, ensure_ascii=False)
            resp = Response(err_body, status=500, mimetype="application/json")
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

    return app
