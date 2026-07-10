"""
lib/core.py — JehaCorp 共用邏輯模組
所有 Serverless Functions 共用的：Agent 設定、AI 呼叫、KV 讀寫封裝
"""
import os
import json
import re
import time
import random

# ── 嘗試載入 openai ───────────────────────────────────────────────────────────
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ── Vercel Serverless Postgres (Neon) KV 適配封裝 ──────────────────────────────
try:
    import psycopg2
    # Vercel Serverless Postgres 自動注入的環境變數 (優先使用 POSTGRES_URL)
    _PG_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL") or ""

    def _get_pg_conn():
        if not _PG_URL:
            return None
        # 建立 TCP 直連 Postgres
        conn = psycopg2.connect(_PG_URL)
        conn.autocommit = True
        return conn

    # 初始化建表
    if _PG_URL:
        try:
            with _get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS kv_store (
                            key VARCHAR(512) PRIMARY KEY,
                            value TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
        except Exception as e:
            print(f"[PG_INIT_ERROR] err={e}")

    def kv_get(key):
        if not _PG_URL:
            return None
        try:
            with _get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT value FROM kv_store WHERE key = %s;", (key,))
                    row = cur.fetchone()
                    return row[0] if row else None
        except Exception as e:
            print(f"[PG_GET_ERROR] key={key}, err={e}")
            return None

    def kv_set(key, value, ex=None):
        if not _PG_URL:
            return False
        try:
            with _get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO kv_store (key, value, updated_at) 
                        VALUES (%s, %s, CURRENT_TIMESTAMP) 
                        ON CONFLICT (key) 
                        DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
                    """, (key, str(value)))
                    return True
        except Exception as e:
            print(f"[PG_SET_ERROR] key={key}, err={e}")
            return False

    def kv_get_json(key):
        raw = kv_get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return None

    def kv_set_json(key, value, ex=None):
        return kv_set(key, json.dumps(value, ensure_ascii=False), ex)

except Exception as global_err:
    print(f"[PG_GLOBAL_INIT_ERROR] {global_err}")
    def kv_get(key): return None
    def kv_set(key, value, ex=None): return False
    def kv_get_json(key): return None
    def kv_set_json(key, value, ex=None): return False


# ── 預設資料 ─────────────────────────────────────────────────────────────────
DEFAULT_USER_MD = """# 🎓 總裁習慣與偏好記憶庫 (user.md)

本檔案記錄總裁的寫作語氣、美感偏好及開發紀律，所有 AI 員工在派遣執行任務時，均會自動讀取並對齊此偏好。

## 👥 基本偏好 (User Preferences)
- **溝通語言**：一律使用 **繁體中文（台灣，zh-TW）** 進行內容創作與程式碼註解。
- **美學風格**：偏好 **日式樸素極簡美感 (Wabi-Sabi 侘寂風格)**，強調大片留白、溫潤色調、優雅的明體標題與舒展的字距。
- **文案口吻**：專業、溫慢、誠懇且具備說服力，避免浮誇誇大的行銷詞彙。

## 🎯 開發紀律 (Fable Auditor Rules)
- 嚴格遵守 Fable 三大紀律守則：
  1. **Verified-Done (證據至上)**：報告中必須提供本機代碼路徑或真實執行細節。
  2. **Minimal-Diff (最小變更)**：每次修改都必須直擊要害，精準簡化。
  3. **Outcome-First (結論先行)**：核心結論必須在 Markdown 報告的最開頭以粗體條列。
"""

BUILTIN_AGENTS = [
    {"id": "rapid-prototyper", "name": "快速原型製作 (Rapid Prototyper)", "emoji": "⚡", "description": "快速原型製作 - 專精於超快速概念驗證 (PoC) 與最小可行產品 (MVP) 開發。", "llm_source": "gpt-4o-mini", "category": "development", "avatar_url": "/avatars/rapid_prototyper.png"},
    {"id": "frontend-developer", "name": "前端開發工程師 (Frontend Developer)", "emoji": "🎨", "description": "前端開發工程師 - 專精於現代網頁技術、React 應用建置、使用者介面與效能優化。", "llm_source": "gpt-4o", "category": "development", "avatar_url": "/avatars/frontend_developer.png"},
    {"id": "backend-architect", "name": "後端架構師 (Backend Architect)", "emoji": "🏗️", "description": "後端架構師 - 專精於系統架構設計、API 設計與資料庫優化。", "llm_source": "gpt-4o", "category": "development", "avatar_url": "/avatars/backend_architect.png"},
    {"id": "reality-checker", "name": "現實檢驗官 (Reality Checker)", "emoji": "🔍", "description": "現實檢驗 - Final integration testing and realistic deployment readiness assessment", "llm_source": "gpt-4o", "category": "development", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=reality"},
    {"id": "paid-media-auditor", "name": "付費媒體稽核師 (Paid Media Auditor)", "emoji": "📋", "description": "付費媒體稽核師 - 專精於廣告帳戶全面評估、成效診斷與預算分配優化。", "llm_source": "gpt-4o-mini", "category": "paid-media", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=media"},
    {"id": "tracking-measurement-specialist", "name": "追蹤與成效衡量專家 (Tracking Specialist)", "emoji": "📡", "description": "追蹤與成效衡量專家 - 專精於驗證轉換追蹤準確性、代碼部署及數據一致性檢查。", "llm_source": "gpt-4o", "category": "paid-media", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=tracking"},
    {"id": "ppc-campaign-strategist", "name": "PPC 廣告活動策略師 (PPC Campaign Strategist)", "emoji": "💰", "description": "PPC 廣告活動策略師 - 專精於廣告帳戶架構重建、關鍵字比對模式選擇與預算分配。", "llm_source": "gpt-4o-mini", "category": "paid-media", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=ppc"},
    {"id": "search-query-analyst", "name": "搜尋字詞分析師 (Search Query Analyst)", "emoji": "🔍", "description": "搜尋字詞分析師 - 專精於搜尋字詞報告分析、否定關鍵字篩選與無效花費清理。", "llm_source": "gpt-4o-mini", "category": "paid-media", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=search"},
    {"id": "ad-creative-strategist", "name": "廣告創意策略師 (Ad Creative Strategist)", "emoji": "✍️", "description": "廣告創意策略師 - 專精於撰寫高 CTR 廣告文案、自訂額外資訊設定與視覺創意規劃。", "llm_source": "gpt-4o-mini", "category": "marketing", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=creative"},
    {"id": "analytics-reporter", "name": "數據分析與回報專家 (Analytics Reporter)", "emoji": "📊", "description": "數據分析與回報專家 - 專精於建立 Looker Studio 報表、資料整合與每週/每月成效報告寫作。", "llm_source": "gpt-4o-mini", "category": "marketing", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=analytics"},
    {"id": "growth-hacker", "name": "成長駭客 (Growth Hacker)", "emoji": "🚀", "description": "成長駭客 - 專精於快速用戶獲取、轉化漏斗優化與數據驅動的增長策略。", "llm_source": "gpt-4o-mini", "category": "marketing", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=growth"},
    {"id": "marketing-content-creator", "name": "專業行銷小編 (Marketing Content Creator)", "emoji": "📱", "description": "專業行銷文案小編與內容創作技能。包含多平台貼文撰寫、行銷策略規劃、文案架構設計與 SEO 優化。", "llm_source": "gemini-1.5-flash", "category": "marketing", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=marketing"},
]

BUILTIN_WORKFLOWS = [
    {"id": "mvp", "name": "🚀 新創 MVP 開發團隊", "description": "快速將點子轉化為原型產品，包含前後端架構設計、成長推廣方案及品質現實檢驗。", "flow": ["rapid-prototyper", "frontend-developer", "backend-architect", "growth-hacker", "reality-checker"]},
    {"id": "paid_media", "name": "💰 付費廣告特攻隊", "description": "專門負責廣告帳戶的全面稽核、轉換追蹤驗證、架構調整與高轉化廣告創意更新。", "flow": ["paid-media-auditor", "tracking-measurement-specialist", "ppc-campaign-strategist", "search-query-analyst", "ad-creative-strategist", "analytics-reporter"]},
    {"id": "social_marketing", "name": "📱 社群內容行銷團隊", "description": "打造人氣品牌故事、多管道社群行銷文案自動規劃與發布，適合自媒體與小編團隊。", "flow": ["marketing-content-creator", "ad-creative-strategist", "growth-hacker", "analytics-reporter"]},
]

FABLE_AUDITOR_PROMPT = """您是 JehaCrop 的「執行總裁 (CEO)」。請對以下初稿進行嚴格的 Code Review 審查。
若「完全合規」，請在回覆的第一行寫下：【CEO_PASS】
若「不合規」，請在回覆的第一行寫下：【CEO_REJECT】並詳細列出退回意見。
初稿如下：\n{draft_content}"""

SECURITY_CHECKER_PROMPT = """您是 JehaCrop 的「執行總裁 (CEO)」。請進行嚴格的資通安全漏洞審查（OWASP Top 10）。
若「未偵測到安全漏洞」，請在回覆的第一行寫下：【CEO_SEC_PASS】
若「偵測到安全漏洞」，請在回覆的第一行寫下：【CEO_SEC_REJECT】並列出漏洞細節。
被審查的初稿內容如下：\n{draft_content}"""


# ── KV 用戶資料鍵名工具 ──────────────────────────────────────────────────────
def _clean_uid(user_id):
    return re.sub(r'[^a-zA-Z0-9_\-\.@]', '_', user_id)

def user_key(user_id, suffix):
    return f"user:{_clean_uid(user_id)}:{suffix}"


# ── 用戶資料存取 ──────────────────────────────────────────────────────────────
def get_user_md(user_id):
    val = kv_get_json(user_key(user_id, "user_md"))
    if val is None:
        kv_set_json(user_key(user_id, "user_md"), {"content": DEFAULT_USER_MD})
        return DEFAULT_USER_MD
    return val.get("content", DEFAULT_USER_MD) if isinstance(val, dict) else val

def save_user_md(user_id, content):
    kv_set_json(user_key(user_id, "user_md"), {"content": content})

def get_user_settings(user_id):
    defaults = {"subscription": "free", "openai_api_key": "", "gemini_api_key": "", "cron_enabled": False, "cron_schedule": "every_60s", "cron_idea": "", "cron_workflow": "mvp"}
    val = kv_get_json(user_key(user_id, "settings"))
    if val and isinstance(val, dict):
        defaults.update(val)
    return defaults

def save_user_settings(user_id, settings):
    kv_set_json(user_key(user_id, "settings"), settings)

def get_user_agents(user_id):
    val = kv_get_json(user_key(user_id, "custom_agents"))
    return val if isinstance(val, list) else []

def save_user_agents(user_id, agents):
    kv_set_json(user_key(user_id, "custom_agents"), agents)

def get_user_workflows(user_id):
    val = kv_get_json(user_key(user_id, "custom_workflows"))
    return val if isinstance(val, list) else []

def save_user_workflows(user_id, workflows):
    kv_set_json(user_key(user_id, "custom_workflows"), workflows)


# ── 專案 / 成果儲存 (KV 模式) ─────────────────────────────────────────────────
def save_project_files(user_id, project_id, files_dict):
    """files_dict = {filename: content_str, ...}"""
    existing = kv_get_json(user_key(user_id, f"project:{project_id}:files")) or {}
    existing.update(files_dict)
    kv_set_json(user_key(user_id, f"project:{project_id}:files"), existing)

def get_project_files(user_id, project_id):
    return kv_get_json(user_key(user_id, f"project:{project_id}:files")) or {}

def list_user_projects(user_id):
    val = kv_get_json(user_key(user_id, "project_list"))
    return val if isinstance(val, list) else []

def append_project(user_id, project_meta):
    projects = list_user_projects(user_id)
    projects.append(project_meta)
    kv_set_json(user_key(user_id, "project_list"), projects)


# ── 非同步 Job 狀態儲存 (Polling 機制用) ──────────────────────────────────────
def save_job_state(job_id, state):
    """state = {status, events: [], finished: bool}"""
    kv_set_json(f"job:{job_id}", state, ex=3600)  # TTL 1 小時

def get_job_state(job_id):
    return kv_get_json(f"job:{job_id}")

def append_job_event(job_id, event):
    state = get_job_state(job_id) or {"status": "running", "events": [], "finished": False}
    state.setdefault("events", []).append(event)
    save_job_state(job_id, state)

def finish_job(job_id, final_event):
    state = get_job_state(job_id) or {"status": "finished", "events": [], "finished": True}
    state["finished"] = True
    state["status"] = "finished"
    state.setdefault("events", []).append(final_event)
    save_job_state(job_id, state)


# ── Auth 輔助 ──────────────────────────────────────────────────────────────────
def get_user_id_from_request(req):
    auth = req.headers.get("Authorization", "") or req.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        uid = auth.split("Bearer ", 1)[1].strip()
        if uid and "@" in uid:
            return uid
    return None


# ── LLM 客戶端 ────────────────────────────────────────────────────────────────
def get_llm_client(llm_source, user_api_keys=None):
    if not OpenAI:
        return None, "mock-model"

    openai_key = (user_api_keys or {}).get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
    gemini_key = (user_api_keys or {}).get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")

    if llm_source.startswith("gpt"):
        if openai_key:
            return OpenAI(api_key=openai_key), llm_source
        if gemini_key:
            model_map = {"gpt-4o": "gemini-1.5-pro", "gpt-4o-mini": "gemini-1.5-flash"}
            return OpenAI(api_key=gemini_key, base_url="https://generativetoolkit.googleapis.com/v1beta/openai/"), model_map.get(llm_source, "gemini-1.5-flash")
        return None, "mock-model"
    elif llm_source.startswith("gemini"):
        if gemini_key:
            return OpenAI(api_key=gemini_key, base_url="https://generativetoolkit.googleapis.com/v1beta/openai/"), llm_source
        if openai_key:
            model_map = {"gemini-1.5-pro": "gpt-4o", "gemini-1.5-flash": "gpt-4o-mini"}
            return OpenAI(api_key=openai_key), model_map.get(llm_source, "gpt-4o-mini")
        return None, "mock-model"
    else:
        if openai_key:
            return OpenAI(api_key=openai_key), "gpt-4o-mini"
        if gemini_key:
            return OpenAI(api_key=gemini_key, base_url="https://generativetoolkit.googleapis.com/v1beta/openai/"), "gemini-1.5-flash"
        return None, "mock-model"


# ── Mock 回應生成器 ────────────────────────────────────────────────────────────
def get_mock_response(agent_id, agent_name, idea, has_feedback=False):
    suffix = "\n\n*備註：此版本已針對董事長驗收意見進行二次修正。*" if has_feedback else ""
    templates = {
        "rapid-prototyper": f"# ⚡ 快速原型製作交付成果 — {idea}\n這是模擬產出的需求架構規劃。{suffix}\n\n[FILE: src/index.js]\nconsole.log(\"Welcome to {idea} Rapid Prototype!\");\n[FILE_END]\n",
        "frontend-developer": f"# 🎨 前端開發工程師交付成果\n為「{idea}」建置了 React UI 元件。{suffix}\n\n[FILE: src/components/Header.jsx]\nimport React from 'react';\nexport const Header = () => <header><h1>{idea}</h1></header>;\n[FILE_END]\n",
        "backend-architect": f"# 🏗️ 後端架構師交付成果\n規劃了資料庫與 API 合約。{suffix}\n\n[FILE: src/db/schema.sql]\nCREATE TABLE items (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL);\n[FILE_END]\n",
        "marketing-content-creator": f"# 📱 專業行銷小編交付報告 — {idea}\n針對「{idea}」的社群文案草稿。{suffix}\n\n[FILE: thread_draft.txt]\n和風侘寂極簡社群貼文規劃草案完成。\n[FILE_END]\n",
        "ad-creative-strategist": f"# ✍️ 廣告創意文案更新 — {idea}\n配合行銷小編產出，規劃高 CTR 廣告創意。{suffix}\n",
        "growth-hacker": f"# 🚀 成長駭客交付成果\n針對「{idea}」的 AARRR 增長計畫。{suffix}\n- 管道：Hackernews, ProductHunt 發布。\n",
        "reality-checker": f"# 🔍 現實檢驗品質報告\n- 狀態：APPROVED ✅\n- 評分：A{suffix}\n",
    }
    return templates.get(agent_id, f"# 👤 {agent_name} 專業報告 — {idea}\n針對「{idea}」，提供以下專業分析：{suffix}\n\n[FILE: custom/{agent_id}_notes.txt]\n# {agent_name} 自訂任務筆記\n- 執行狀態: 模擬生成完成\n[FILE_END]\n")


# ── 檔案解析器 ────────────────────────────────────────────────────────────────
def extract_files_from_content(content):
    """從 [FILE: path]...[FILE_END] 標記中解析出檔案名稱與內容的 dict"""
    import re
    pattern = r'\[FILE:\s*(.*?)\](.*?)\[FILE_END\]'
    matches = re.findall(pattern, content, re.DOTALL)
    files = {}
    for filepath, filecontent in matches:
        filepath = filepath.strip().replace('\\', '/').lstrip('/')
        if '..' not in filepath and filepath:
            files[filepath] = filecontent.strip()
    return files
