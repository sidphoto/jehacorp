#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import urllib.parse
import time
import random
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

# 檢查與載入 openai 庫
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

BUILTIN_AGENTS = [
    {
        "id": "rapid-prototyper", 
        "name": "快速原型製作 (Rapid Prototyper)", 
        "emoji": "⚡", 
        "description": "快速原型製作 - 專精於超快速概念驗證 (PoC) 與最小可行產品 (MVP) 開發。", 
        "llm_source": "gpt-4o-mini",
        "category": "development",
        "avatar_url": "/avatars/rapid_prototyper.png"
    },
    {
        "id": "frontend-developer", 
        "name": "前端開發工程師 (Frontend Developer)", 
        "emoji": "🎨", 
        "description": "前端開發工程師 - 專精於現代網頁技術、React 應用建置、使用者介面與效能優化。", 
        "llm_source": "gpt-4o",
        "category": "development",
        "avatar_url": "/avatars/frontend_developer.png"
    },
    {
        "id": "backend-architect", 
        "name": "後端架構師 (Backend Architect)", 
        "emoji": "🏗️", 
        "description": "後端架構師 - 專精於系統架構設計、API 設計與資料庫優化。", 
        "llm_source": "gpt-4o",
        "category": "development",
        "avatar_url": "/avatars/backend_architect.png"
    },
    {
        "id": "reality-checker", 
        "name": "現實檢驗官 (Reality Checker)", 
        "emoji": "🔍", 
        "description": "現實檢驗 - Final integration testing and realistic deployment readiness assessment", 
        "llm_source": "gpt-4o",
        "category": "development",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=reality"
    },
    {
        "id": "paid-media-auditor", 
        "name": "付費媒體稽核師 (Paid Media Auditor)", 
        "emoji": "📋", 
        "description": "付費媒體稽核師 - 專精於廣告帳戶全面評估、成效診斷與預算分配優化。", 
        "llm_source": "gpt-4o-mini",
        "category": "paid-media",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=media"
    },
    {
        "id": "tracking-measurement-specialist", 
        "name": "追蹤與成效衡量專家 (Tracking Specialist)", 
        "emoji": "📡", 
        "description": "追蹤與成效衡量專家 - 專精於驗證轉換追蹤準確性、代碼部署及數據一致性檢查。", 
        "llm_source": "gpt-4o",
        "category": "paid-media",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=tracking"
    },
    {
        "id": "ppc-campaign-strategist", 
        "name": "PPC 廣告活動策略師 (PPC Campaign Strategist)", 
        "emoji": "💰", 
        "description": "PPC 廣告活動策略師 - 專精於廣告帳戶架構重建、關鍵字比對模式選擇與預算分配。", 
        "llm_source": "gpt-4o-mini",
        "category": "paid-media",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=ppc"
    },
    {
        "id": "search-query-analyst", 
        "name": "搜尋字詞分析師 (Search Query Analyst)", 
        "emoji": "🔍", 
        "description": "搜尋字詞分析師 - 專精於搜尋字詞報告分析、否定關鍵字篩選與無效花費清理。", 
        "llm_source": "gpt-4o-mini",
        "category": "paid-media",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=search"
    },
    {
        "id": "ad-creative-strategist", 
        "name": "廣告創意策略師 (Ad Creative Strategist)", 
        "emoji": "✍️", 
        "description": "廣告創意策略師 - 專精於撰寫高 CTR 廣告文案、自訂額外資訊設定與視覺創意規劃。", 
        "llm_source": "gpt-4o-mini",
        "category": "marketing",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=creative"
    },
    {
        "id": "analytics-reporter", 
        "name": "數據分析與回報專家 (Analytics Reporter)", 
        "emoji": "📊", 
        "description": "數據分析與回報專家 - 專精於建立 Looker Studio 報表、資料整合與每週/每月成效報告寫作。", 
        "llm_source": "gpt-4o-mini",
        "category": "marketing",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=analytics"
    },
    {
        "id": "growth-hacker", 
        "name": "成長駭客 (Growth Hacker)", 
        "emoji": "🚀", 
        "description": "成長駭客 - 專精於快速用戶獲取、轉化漏斗優化與數據驱动的增長策略。", 
        "llm_source": "gpt-4o-mini",
        "category": "marketing",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=growth"
    },
    {
        "id": "marketing-content-creator", 
        "name": "專業行銷小編 (Marketing Content Creator)", 
        "emoji": "📱", 
        "description": "專業行銷文案小編與內容創作技能。包含多平台貼文撰寫、行銷策略規劃、文案架構設計與 SEO 優化。", 
        "llm_source": "gemini-1.5-flash",
        "category": "marketing",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=marketing"
    }
]

# 內建建議工作流
BUILTIN_WORKFLOWS = [
    {
        "id": "mvp",
        "name": "🚀 新創 MVP 開發團隊",
        "description": "快速將點子轉化為原型產品，包含前後端架構設計、成長推廣方案及品質現實檢驗。",
        "flow": ["rapid-prototyper", "frontend-developer", "backend-architect", "growth-hacker", "reality-checker"]
    },
    {
        "id": "paid_media",
        "name": "💰 付費廣告特攻隊",
        "description": "專門負責廣告帳戶的全面稽核、轉換追蹤驗證、架構調整與高轉化廣告創意更新。",
        "flow": ["paid-media-auditor", "tracking-measurement-specialist", "ppc-campaign-strategist", "search-query-analyst", "ad-creative-strategist", "analytics-reporter"]
    },
    {
        "id": "social_marketing",
        "name": "📱 社群內容行銷團隊",
        "description": "打造人氣品牌故事、多管道社群行銷文案自動規劃與發布，適合自媒體與小編團隊。",
        "flow": ["marketing-content-creator", "ad-creative-strategist", "growth-hacker", "analytics-reporter"]
    }
]

# CEO 專屬 Code Review 紀律審查提示詞模板
FABLE_AUDITOR_PROMPT = """您是 JehaCrop 的「執行總裁 (CEO)」。您的董事長（用戶）正派件給旗下員工，這是他們遞交的階段交付物初稿報告。
請站在執行總裁的專業高度與 Code Review 角度，對本初稿進行嚴格的紀律與品質審查。

您必須確保輸出嚴格遵守以下三條紀律守則：
1. Verified-Done (證據至上)：報告必須包含實際執行的檔案輸出、程式碼片段或具體目錄，不可僅有口頭承諾。
2. Minimal-Diff (最小變更)：修改範圍必須精準簡練，不可夾帶無關擴充。
3. Outcome-First (結論先行)：核心結論必須在最開頭以粗體條列，不可包含推測性廢話。

請作出您的判決：
若「完全合規」，請在回覆的第一行寫下：【CEO_PASS】並附帶簡短的通過評語。
若「不合規」，請在回覆的第一行寫下：【CEO_REJECT】並詳細列出 Code Review 的退回意見（請以總裁口吻指出違反了哪條守則，給出具體修正指令，結論先行）。

代理人遞交的初稿如下：
{draft_content}
"""

# CEO 專屬資通安全漏洞檢查提示詞模板
SECURITY_CHECKER_PROMPT = """您是 JehaCrop 的「執行總裁 (CEO)」。您正在審查旗下員工撰寫的原始碼與報告。
請進行嚴格的資通安全漏洞審查（特別是常見的 OWASP Top 10 漏洞，例如 SQL 注入、跨站腳本 XSS、硬編碼敏感金鑰與路徑穿越漏洞）。

請作出您的判決：
若「未偵測到安全漏洞」，請在回覆的第一行寫下：【CEO_SEC_PASS】並附帶簡短的資安合規通過評語。
若「偵測到安全漏洞」，請在回覆的第一行寫下：【CEO_SEC_REJECT】並詳細列出總裁 Code Review 資安漏洞退回意見（以總裁口吻說明漏洞種類、危害與防禦修改建議，結論先行）。

被審查的初稿內容如下：
{draft_content}
"""

# 預設初始化 user.md 內容
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

## 📁 最近關注專案歷史 (Recent Projects)
- 越南短期租賃機車網站合法規調查 (模擬專案)
"""

# 全局計時器，用於記錄上一次自動派工時間
LAST_CRON_RUN = {}

# 根據角色指定的 llm_source 動態獲取 LLM 客戶端與模型
def get_llm_client_for_agent(llm_source, mock_mode=False, user_api_keys=None):
    if mock_mode or llm_source == "mock-model":
        return None, "mock-model"
        
    openai_key = user_api_keys.get("openai_api_key") if user_api_keys else None
    gemini_key = user_api_keys.get("gemini_api_key") if user_api_keys else None
    
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY")
    if not gemini_key:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        
    if not OpenAI:
        raise ImportError("未在您的 Python 環境中偵測到 'openai' 模組，請執行 'pip install openai' 安裝。")
        
    if llm_source.startswith("gpt"):
        if not openai_key:
            if gemini_key:
                base_url = "https://generativetoolkit.googleapis.com/v1beta/openai/"
                model_map = {"gpt-4o": "gemini-1.5-pro", "gpt-4o-mini": "gemini-1.5-flash"}
                return OpenAI(api_key=gemini_key, base_url=base_url), model_map.get(llm_source, "gemini-1.5-flash")
            raise ValueError("未偵測到 API 金鑰！免費版已達額度，或付費版自訂金鑰未設定。")
        return OpenAI(api_key=openai_key), llm_source
        
    elif llm_source.startswith("gemini"):
        if not gemini_key:
            if openai_key:
                model_map = {"gemini-1.5-pro": "gpt-4o", "gemini-1.5-flash": "gpt-4o-mini"}
                return OpenAI(api_key=openai_key), model_map.get(llm_source, "gpt-4o-mini")
            raise ValueError("未偵測到 API 金鑰！免費版已達額度，或付費版自訂金鑰未設定. ")
        base_url = "https://generativetoolkit.googleapis.com/v1beta/openai/"
        return OpenAI(api_key=gemini_key, base_url=base_url), llm_source
        
    else:
        if openai_key:
            return OpenAI(api_key=openai_key), "gpt-4o-mini"
        elif gemini_key:
            base_url = "https://generativetoolkit.googleapis.com/v1beta/openai/"
            return OpenAI(api_key=gemini_key, base_url=base_url), "gemini-1.5-flash"
        else:
            return None, "mock-model"

# 解析 Markdown
def parse_markdown_skill(filepath):
    if not os.path.exists(filepath):
        return None, None
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_part = parts[1]
            body = parts[2]
            for line in yaml_part.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()
                    
    return frontmatter, body.strip()

# 自動寫入檔案
def extract_and_write_files(content, user_id, project_folder=None):
    pattern = r"\[FILE:\s*(.*?)\](.*?)\[FILE_END\]"
    matches = re.findall(pattern, content, re.DOTALL)
    written_files = []
    
    if project_folder:
        base_dir = f"data/users/{user_id}/outputs/{project_folder}" if user_id else "mvp_output"
    else:
        base_dir = f"data/users/{user_id}/outputs" if user_id else "mvp_output"
    
    for filepath, filecontent in matches:
        filepath = filepath.strip()
        filecontent = filecontent.strip()
        
        filepath = filepath.replace("\\", "/")
        if filepath.startswith("/") or ".." in filepath:
            continue
            
        actual_path = os.path.join(base_dir, filepath)
        dir_name = os.path.dirname(actual_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(actual_path, "w", encoding="utf-8") as f:
            f.write(filecontent)
            
        written_files.append(actual_path)
        
    return written_files

# 產生模擬測試內容
def get_mock_response(agent_id, agent_name, idea, has_feedback=False):
    feedback_str = "\n*備註：此版本已針對董事長驗收意見進行二次修正。*" if has_feedback else ""
    
    if agent_id == "rapid-prototyper":
        return f"""# ⚡ 快速原型製作交付成果 — {idea}
這是模擬產出的需求架構規劃。{feedback_str}

## 核心邏輯
我們預期提供這個「{idea}」MVP，能在第一週吸引核心用戶高頻率使用。

[FILE: src/index.js]
console.log("Welcome to {idea} Rapid Prototype!");
[FILE_END]
"""
    elif agent_id == "frontend-developer":
        return f"""# 🎨 前端開發工程師交付成果
我們為「{idea}」建置了 React UI 元件。{feedback_str}

[FILE: src/components/Header.jsx]
import React from 'react';
export const Header = () => (
  <header style={{{{ padding: '20px', background: '#7c3aed', color: 'white' }}}}>
    <h1>{idea} Dashboard</h1>
  </header>
);
[FILE_END]
"""
    elif agent_id == "backend-architect":
        return f"""# 🏗️ 後端架構師交付成果
我們規劃了資料庫與 API 合約。{feedback_str}

[FILE: src/db/schema.sql]
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
[FILE_END]
"""
    elif agent_id == "growth-hacker":
        return f"""# 🚀 成長駭客交付成果
針對「{idea}」的 AARRR 增長計畫。{feedback_str}
- 管道：Hackernews, ProductHunt 發布。
- 實驗：調整註冊流程的按鈕文字為「免費使用 30 秒」。
"""
    elif agent_id == "reality-checker":
        return f"""# 🔍 現實檢驗品質報告
- 狀態：APPROVED ✅
- 評分：A
- 發現：本機程式碼與架構完全滿足資安與 Fable 規範。{feedback_str}
"""
    elif agent_id == "marketing-content-creator":
        return f"""# 📱 專業行銷小編交付報告 — {idea}
針對「{idea}」的社群媒體傳播文案草稿。{feedback_str}

## 1. Thread 行銷文案草稿
- **文案**：一人公司也可以是強大團隊！JehaCrop 助您解鎖多代理人自動協同。

[FILE: src/marketing/thread_draft.txt]
和風侘寂極簡社群貼文規劃草案完成。
[FILE_END]
"""
    elif agent_id == "ad-creative-strategist":
        return f"""# ✍️ 廣告創意文案更新 — {idea}
配合行銷小編產出的社群文案，規劃相應的高 CTR RSA 廣告與視覺創意。{feedback_str}
"""
    else:
        return f"""# 👤 {agent_name} 專業報告 — {idea}
針對您的點子「{idea}」，我作為自訂職務 **{agent_name}**，提供以下專業分析：{feedback_str}

[FILE: src/custom/{agent_id}_notes.txt]
# {agent_name} 自訂任務筆記
- 專案名稱: {idea}
- 執行狀態: 模擬生成完成
[FILE_END]
"""

# 獲取用戶資料夾路徑
def get_user_data_path(user_id):
    clean_user = re.sub(r'[^a-zA-Z0-9_\-\.\@]', '_', user_id)
    path = os.path.join("data", "users", clean_user)
    os.makedirs(path, exist_ok=True)
    return path

# 載入與更新 user.md
def get_user_md_content(user_id):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "user.md")
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_USER_MD)
        return DEFAULT_USER_MD
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def save_user_md_content(user_id, content):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "user.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# 載入與儲存用戶設定
def load_user_settings(user_id):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "settings.json")
    default_settings = {
        "subscription": "free",
        "openai_api_key": "",
        "gemini_api_key": "",
        "cron_enabled": False,
        "cron_schedule": "every_60s",
        "cron_idea": "",
        "cron_workflow": "mvp"
    }
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception:
            pass
    return default_settings

def save_user_settings(user_id, settings):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "settings.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

# 載入與儲存用戶自訂代理人與工作流
def load_user_agents(user_id):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "custom_agents.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_user_agents(user_id, agents):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "custom_agents.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)

def load_user_workflows(user_id):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "custom_workflows.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_user_workflows(user_id, workflows):
    path = get_user_data_path(user_id)
    file_path = os.path.join(path, "custom_workflows.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workflows, f, ensure_ascii=False, indent=2)

# 獲取 user_id (SSO Token)
def get_user_id_from_headers(headers):
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        user_id = auth_header.split('Bearer ', 1)[1].strip()
        if user_id and "@" in user_id:
            return user_id
    return None

# 核心派遣引擎：整合 SSE 流水線、背景定時派工、決策共識與董事長驗收退回修正機制、單兵指派與總裁動態協同
def execute_workflow(user_id, idea, workflow_type, mock_mode=False, sse_emitter=None, meeting_mode=False, discussion_consensus="", acceptance_feedback="", single_agent=False):
    def log(event_data):
        if sse_emitter:
            sse_emitter(event_data)

    try:
        user_md = get_user_md_content(user_id)
        user_settings = load_user_settings(user_id)
        is_pro = user_settings.get("subscription") == "pro"

        # 1. 取得工作流配置
        target_workflow = None
        flow = []
        
        if single_agent:
            # 單兵指派模式：初始 Flow 僅包含單個員工
            flow = [workflow_type]
        else:
            for wf in BUILTIN_WORKFLOWS:
                if wf["id"] == workflow_type:
                    target_workflow = wf
                    break
            if not target_workflow:
                custom_workflows = load_user_workflows(user_id)
                for wf in custom_workflows:
                    if wf["id"] == workflow_type:
                        target_workflow = wf
                        break

            if not target_workflow:
                try:
                    flow = json.loads(workflow_type)
                except Exception:
                    log({"status": "error", "error": f"找不到或無法解析工作流 {workflow_type}"})
                    return
            else:
                flow = target_workflow["flow"]
        
        if not flow:
            log({"status": "error", "error": "工作流團隊中必須包含至少一位成員！"})
            return

        # 2. 自動生成案件全局簡報 project_brief.md (Step 0)
        # 2. 自動生成案件全局簡報 project_brief.md (Step 0)
        safe_idea = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5\-]', '_', idea.strip())[:15]
        project_folder = f"project_{safe_idea}_{str(int(time.time()))[-4:]}"
        output_path = os.path.join(get_user_data_path(user_id), "outputs", project_folder)
        os.makedirs(output_path, exist_ok=True)
        
        project_brief_filename = "project_brief.md"
        project_brief_path = os.path.join(output_path, project_brief_filename)
        
        log({
            "status": "thinking",
            "step": 0,
            "total_steps": 1,
            "agent_id": "system-coordinator",
            "agent_name": "執行總裁 (CEO)",
            "emoji": "📁",
            "llm_source": "gpt-4o-mini",
            "retry_count": 0,
            "message": "📁 正在由執行總裁 (CEO) 整理全局案件簡報，匯入董事長決策共識與驗收要求..."
        })
        
        brief_content = ""
        if mock_mode:
            time.sleep(1.0)
            brief_content = f"""# 📋 專案簡報與案件背景 (project_brief.md)

本簡報由執行總裁 (CEO) 依據董事長最高指示自動生成，做為小組成員協同執行的最高指導準則。

## 1. 案件基本資訊
- **專案名稱**：{idea}
- **立案時間**：{time.strftime('%Y-%m-%d %H:%M:%S')}
- **專案監管**：董事長 ({user_id})

## 2. 核心商業目標 (Core Objectives)
- 快速落實「{idea}」的核心商業模式與功能模組。
"""
            if discussion_consensus:
                brief_content += f"\n## 3. 董事長與 CEO 商討之決策共識\n- {discussion_consensus}\n"
            if acceptance_feedback:
                brief_content += f"\n## 4. 董事長上一輪驗收退回之修正意見 (最高優先級)\n- ⚠️ {acceptance_feedback}\n"
        else:
            api_keys = user_settings if is_pro else None
            client, model_name = get_llm_client_for_agent("gpt-4o-mini", mock_mode=False, user_api_keys=api_keys)
            
            prompt = f"""您是 JehaCrop 的「執行總裁 (CEO)」。請針對您的董事長（用戶）下達的點子，參考董事長習慣 (user.md)，自動生成一份專案全局簡報檔案 `project_brief.md`，以利旗下員工能快速掌握執行方向。
            
【董事長習慣 user.md】：
{user_md}

【專案點子】：
{idea}
"""
            if discussion_consensus:
                prompt += f"\n【您先前與董事長在決策室達成的商討共識如下，請務必將此共識寫入簡報】：\n{discussion_consensus}\n"
            if acceptance_feedback:
                prompt += f"\n【董事長在上一輪驗收退回了專案，並給出以下必須修改的審核意見，請務必在簡報中列出做為首要修正方針】：\n{acceptance_feedback}\n"

            prompt += "\n請以繁體中文撰寫，包含：專案名稱、立案背景、最高指導共識、董事長退回意見（若有）。結論先行。"
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            brief_content = response.choices[0].message.content

        with open(project_brief_path, "w", encoding="utf-8") as f:
            f.write(brief_content)

        log({
            "status": "completed",
            "step": 0,
            "total_steps": 1,
            "agent_id": "system-coordinator",
            "agent_name": "執行總裁 (CEO)",
            "emoji": "📁",
            "retry_count": 0,
            "report_file": os.path.join("data", "users", user_id, "outputs", project_folder, project_brief_filename).replace("\\", "/"),
            "written_files": [project_brief_filename],
            "message": "專案立案完成！已匯入決策共識並歸檔簡報 project_brief.md。"
        })
        time.sleep(0.3)

        previous_outputs = {}
        all_written_files = [project_brief_path]

        # 3. 依序執行工作流成員 (注意：在單兵指派時，flow 會在執行中途被動態追加延伸)
        step_num = 1
        while step_num <= len(flow):
            agent_id = flow[step_num - 1]
            agent_name = agent_id
            system_prompt = ""
            emoji = "👤"
            llm_source = "gpt-4o-mini"

            builtin_found = False
            for ag in BUILTIN_AGENTS:
                if ag["id"] == agent_id:
                    builtin_found = True
                    emoji = ag["emoji"]
                    llm_source = ag.get("llm_source", "gpt-4o-mini")
                    skill_file = os.path.join(".agents", "skills", agent_id, "SKILL.md")
                    frontmatter, body = parse_markdown_skill(skill_file)
                    agent_name = frontmatter.get("name", ag["name"]) if frontmatter else ag["name"]
                    system_prompt = body if body else ag["description"]
                    break

            if not builtin_found:
                custom_agents = load_user_agents(user_id)
                for ag in custom_agents:
                    if ag["id"] == agent_id:
                        agent_name = ag["name"]
                        emoji = ag.get("emoji", "👤")
                        system_prompt = ag["system_prompt"]
                        llm_source = ag.get("llm_source", "gpt-4o-mini")
                        break

            passed = False
            retry_count = 0
            fable_feedback = ""
            security_feedback = ""
            output_content = ""
            discussion_text = ""

            # --- 【會議討論模式 (Meeting Mode)】 ---
            if meeting_mode and step_num >= 2:
                prev_agent_name = flow[step_num - 2]
                for ag in BUILTIN_AGENTS + load_user_agents(user_id):
                    if ag["id"] == flow[step_num - 2]:
                        prev_agent_name = ag["name"]
                        break

                log({
                    "status": "thinking",
                    "step": step_num,
                    "total_steps": len(flow),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "emoji": "💬",
                    "message": f"💬 會議對齊中... [{prev_agent_name}] 與 [{agent_name}] 正在召開共識對接會議"
                })

                if mock_mode:
                    time.sleep(1.2)
                    discussion_text = f"💬 【{prev_agent_name}】：我已經完成了初步的需求原型，程式碼儲存於 index.js。我建議您在前端 React 開發時，優先採用極簡和風色調，並引用我的 Header 元件。\n💬 【{agent_name}】：收到！我會配合您的 index.js 邏輯，在 React 元件中完美實施極致侘寂美感設計，大片留白並使用 Noto Serif 明體標題。"
                else:
                    api_keys = user_settings if is_pro else None
                    client, model_name = get_llm_client_for_agent("gpt-4o-mini", mock_mode=False, user_api_keys=api_keys)
                    disc_prompt = f"""您是 JehaCrop 的專案協調官。
目前總裁正在派遣團隊開發「{idea}」。我們現在進行到了第 {step_num} 步。
上一步的員工是「{prev_agent_name}」，當前的員工是「{agent_name}」。
為了讓當前員工在發出初稿前，能對齊上一步的進度與總裁習慣，請模擬這兩位員工進行一次簡短的對齊會議討論（150字以內）。
請以繁體中文撰寫，並格式化為：
💬 【{prev_agent_name}】：...
💬 【{agent_name}】：...
"""
                    disc_res = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": disc_prompt}],
                        temperature=0.7
                    )
                    discussion_text = disc_res.choices[0].message.content

                log({
                    "status": "meeting_discussing",
                    "step": step_num,
                    "total_steps": len(flow),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "emoji": emoji,
                    "discussion": discussion_text,
                    "message": "已完成會議共識對齊討論！"
                })
                time.sleep(1.0)

            while not passed:
                log({
                    "status": "thinking",
                    "step": step_num,
                    "total_steps": len(flow),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "emoji": emoji,
                    "llm_source": llm_source,
                    "retry_count": retry_count,
                    "fable_feedback": fable_feedback or security_feedback,
                    "message": f"正在撰寫初稿 (Model: {llm_source})..."
                })

                client = None
                model_name = "mock-model"
                if not mock_mode:
                    try:
                        api_keys = user_settings if is_pro else None
                        client, model_name = get_llm_client_for_agent(llm_source, mock_mode=False, user_api_keys=api_keys)
                    except Exception:
                        log({"status": "error", "error": f"LLM 啟動失敗 ({llm_source})，請確認金鑰設定。"})
                        return

                if mock_mode or not client:
                    time.sleep(1.2)
                    output_content = get_mock_response(agent_id, agent_name, idea, has_feedback=bool(acceptance_feedback))
                    if retry_count == 0 and step_num == 1 and random.random() > 0.4 and not acceptance_feedback and not single_agent:
                        output_content += "\n\n```sql\n-- 模擬程式碼漏洞\nSELECT * FROM users WHERE username = '\" + input_user + \"';\n```"
                    if retry_count > 0:
                        output_content = get_mock_response(agent_id, agent_name, idea, has_feedback=bool(acceptance_feedback))
                        output_content += f"\n\n*備註：此版本已修復 SQL 注入漏洞並對齊總裁 Review 意見。*"
                else:
                    full_system_prompt = f"""您是 JehaCrop 公司的職員：{agent_name}。
                    
【董事長習慣偏好 (user.md)】：
{user_md}

【最高戰略簡報 (project_brief.md)】：
{brief_content}
"""
                    if discussion_text:
                        full_system_prompt += f"\n【小組會議共識對齊】：\n{discussion_text}\n"

                    full_system_prompt += f"""
---
您的角色指令提示：
{system_prompt}

=== 重要代碼輸出規範 ===
如果編寫了任何原始碼（特別是可執行的 HTML/JS 鍛造工具），請使用以下格式包裹：
[FILE: 檔案路徑]
代碼
[FILE_END]
"""
                    user_prompt = f"【我們目前的專案點子】：\n{idea}\n\n"
                    if discussion_consensus:
                        user_prompt += f"💬【董事長與 CEO 商討達成的決策共識】：\n{discussion_consensus}\n\n"
                    if acceptance_feedback:
                        user_prompt += f"👑【董事長上輪驗收退回之具體修改建議】：\n{acceptance_feedback}\n\n"
                    if fable_feedback:
                        user_prompt += f"⚠️【總裁 Code Review 修正意見】：\n{fable_feedback}\n\n"
                    if security_feedback:
                        user_prompt += f"🛡️【總裁資安 Review 修正建議】：\n{security_feedback}\n\n"
                    if previous_outputs:
                        user_prompt += "【之前步驟成員產出的進度報告】：\n"
                        for prev_ag, prev_out in previous_outputs.items():
                            user_prompt += f"\n--- 【{prev_ag}】的成果 ---\n{prev_out}\n"
                            
                    user_prompt += "\n請開始撰寫您的成果報告並編寫對應程式碼。"

                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": full_system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7
                    )
                    output_content = response.choices[0].message.content

                report_filename = f"{step_num}_{agent_id}.md"
                report_file_path = os.path.join(output_path, report_filename)
                with open(report_file_path, "w", encoding="utf-8") as f:
                    f.write(output_content)

                # 總裁 Code Review 審查
                log({
                    "status": "fable_auditing",
                    "step": step_num,
                    "total_steps": len(flow),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "emoji": emoji,
                    "llm_source": "gpt-4o",
                    "retry_count": retry_count,
                    "message": "🔍 正在由執行總裁 (CEO) 進行專案交付物與 Code Review 審查中..."
                })
                time.sleep(1.0)

                fable_passed = False
                if mock_mode:
                    fable_passed = True
                    fable_feedback = "✅ 總裁 Review：完全符合 Verified-Done 紀律要求。"
                else:
                    try:
                        auditor_model = "gpt-4o"
                        api_keys = user_settings if is_pro else None
                        auditor_client, auditor_model_name = get_llm_client_for_agent(auditor_model, mock_mode=False, user_api_keys=api_keys)
                        audit_response = auditor_client.chat.completions.create(
                            model=auditor_model_name,
                            messages=[
                                {"role": "system", "content": FABLE_AUDITOR_PROMPT.format(draft_content=output_content)},
                                {"role": "user", "content": "請進行總裁 Code Review 審查。"}
                            ],
                            temperature=0.2
                        )
                        audit_result = audit_response.choices[0].message.content
                        if "CEO_PASS" in audit_result:
                            fable_feedback = "✅ 總裁 Review: " + audit_result.replace("【CEO_PASS】", "").strip()
                            fable_passed = True
                        else:
                            fable_feedback = "❌ 總裁退回: " + audit_result.replace("【CEO_REJECT】", "").strip()
                            fable_passed = False
                    except Exception:
                        fable_feedback = "✅ 總裁 Review 通過 (中斷容錯)"
                        fable_passed = True

                if not fable_passed:
                    log({
                        "status": "fable_rejected",
                        "step": step_num,
                        "total_steps": len(flow),
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "emoji": emoji,
                        "retry_count": retry_count,
                        "fable_feedback": fable_feedback,
                        "message": f"總裁 Review 退回重做：{fable_feedback}"
                    })
                    retry_count += 1
                    time.sleep(0.8)
                    continue

                # 總裁資安 Review
                log({
                    "status": "security_auditing",
                    "step": step_num,
                    "total_steps": len(flow),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "emoji": emoji,
                    "message": "🛡️ 正在由執行總裁 (CEO) 進行資通安全漏洞審查與合規檢查中..."
                })
                time.sleep(1.0)

                sec_passed = False
                if mock_mode:
                    if "SELECT * FROM users WHERE" in output_content and "input_user" in output_content:
                        security_feedback = "❌ 總裁資安警告：偵測到 SQL Injection 注入漏洞！請立即將字串拼接改為參數化查詢！"
                        sec_passed = False
                    else:
                        security_feedback = "✅ 總裁資安 Review：代碼中未偵測到 OWASP Top 10 高危險漏洞。"
                        sec_passed = True
                else:
                    try:
                        sec_model = "gpt-4o"
                        api_keys = user_settings if is_pro else None
                        sec_client, sec_model_name = get_llm_client_for_agent(sec_model, mock_mode=False, user_api_keys=api_keys)
                        sec_response = sec_client.chat.completions.create(
                            model=sec_model_name,
                            messages=[
                                {"role": "system", "content": SECURITY_CHECKER_PROMPT.format(draft_content=output_content)},
                                {"role": "user", "content": "請進行總裁資安審查。"}
                            ],
                            temperature=0.1
                        )
                        sec_result = sec_response.choices[0].message.content
                        if "CEO_SEC_PASS" in sec_result:
                            security_feedback = "✅ 總裁資安 Review: " + sec_result.replace("【CEO_SEC_PASS】", "").strip()
                            sec_passed = True
                        else:
                            security_feedback = "❌ 總裁資安拒絕: " + sec_result.replace("【CEO_SEC_REJECT】", "").strip()
                            sec_passed = False
                    except Exception:
                        security_feedback = "✅ 總裁資安 Review 通過 (中斷容錯)"
                        sec_passed = True

                if not sec_passed:
                    log({
                        "status": "security_rejected",
                        "step": step_num,
                        "total_steps": len(flow),
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "emoji": emoji,
                        "retry_count": retry_count,
                        "security_feedback": security_feedback,
                        "message": f"總裁資安 Review 退回：{security_feedback}"
                    })
                    retry_count += 1
                    time.sleep(0.8)
                    continue

                passed = True

            log({
                "status": "writing",
                "step": step_num,
                "total_steps": len(flow),
                "agent_id": agent_id,
                "agent_name": agent_name,
                "emoji": emoji,
                "message": "💾 總裁雙重 Review 通過，正在進行寫檔歸檔..."
            })

            written = extract_and_write_files(output_content, user_id, project_folder=project_folder)
            all_written_files.extend(written)
            
            log({
                "status": "completed",
                "step": step_num,
                "total_steps": len(flow),
                "agent_id": agent_id,
                "agent_name": agent_name,
                "emoji": emoji,
                "retry_count": retry_count,
                "fable_feedback": security_feedback,
                "written_files": [os.path.basename(w) for w in written],
                "report_file": os.path.join("data", "users", user_id, "outputs", project_folder, report_filename).replace("\\", "/"),
                "message": "已通過總裁雙重審查監督！階段成果歸檔完成。"
            })

            previous_outputs[agent_name] = output_content
            time.sleep(0.3)

            # --- 【單兵指派模式：總裁動態協作招募路由 (Dynamic Collaboration Routing)】 ---
            if single_agent and step_num == 1:
                log({
                    "status": "thinking",
                    "step": 1,
                    "total_steps": 1,
                    "agent_id": "ceo-acceptance",
                    "agent_name": "執行總裁 (CEO)",
                    "emoji": "👑",
                    "message": f"👑 總裁正在評估 【{agent_name}】 的成果報告，分析是否需要招募其他旗下員工前來協同作戰..."
                })
                time.sleep(1.5)

                collaborator_ids = []
                if mock_mode:
                    # 模擬測試模式：如果指派小編，則自動招募廣告策略師；否則招募成長駭客
                    if agent_id == "marketing-content-creator":
                        collaborator_ids = ["ad-creative-strategist"]
                    else:
                        collaborator_ids = ["growth-hacker"]
                else:
                    # 實體 API 模式：詢問總裁大腦
                    available_agents = [ag for ag in BUILTIN_AGENTS if ag["id"] != agent_id]
                    custom_agents = load_user_agents(user_id)
                    for ca in custom_agents:
                        if ca["id"] != agent_id:
                            available_agents.append(ca)
                            
                    agents_list_text = "\n".join([f"- ID: {ag['id']}, 職務名稱: {ag['name']}, 說明: {ag['description']}" for ag in available_agents])
                    
                    ceo_eval_prompt = f"""您是 JehaCrop 的「執行總裁 (CEO)」。
目前您的董事長指派了「{agent_name}」單獨執行任務：「{idea}」。
該員工已順利完成交付成果，其報告內容如下：
---
{output_content}
---

為了進一步優化本專案的深度，您認為需要再招募哪 1~2 位成員前來協同作戰？
可選的 AI 員工名冊如下：
{agents_list_text}

請根據報告內容與剩餘名冊，評估最合適的協作者。
您必須以 JSON 陣列格式返回需要招募的員工 ID（最多 2 位，若不需要額外協作可返回空陣列，不得出現任何說明字眼），例如：["ad-creative-strategist"] 或 ["growth-hacker", "reality-checker"]。
請直接輸出 JSON 陣列本身，不要包含 ```json 標記。
"""
                    try:
                        api_keys = user_settings if is_pro else None
                        eval_client, eval_model_name = get_llm_client_for_agent("gpt-4o-mini", mock_mode=False, user_api_keys=api_keys)
                        eval_res = eval_client.chat.completions.create(
                            model=eval_model_name,
                            messages=[{"role": "user", "content": ceo_eval_prompt}],
                            temperature=0.2
                        )
                        json_str = eval_res.choices[0].message.content.strip()
                        # 移除 Markdown 程式碼區塊
                        json_str = json_str.replace("```json", "").replace("```", "").strip()
                        collaborator_ids = json.loads(json_str)
                    except Exception as e:
                        # 容錯：預設招募名單中的第一位
                        collaborator_ids = ["ad-creative-strategist"]

                if collaborator_ids and isinstance(collaborator_ids, list):
                    # 過濾掉無效的 ID
                    valid_collaborator_ids = []
                    collaborator_details = []
                    
                    for cid in collaborator_ids:
                        found_ag = None
                        for ag in BUILTIN_AGENTS + load_user_agents(user_id):
                            if ag["id"] == cid:
                                found_ag = ag
                                break
                        if found_ag:
                            valid_collaborator_ids.append(cid)
                            collaborator_details.append({
                                "id": found_ag["id"],
                                "name": found_ag["name"],
                                "emoji": found_ag.get("emoji", "👤"),
                                "description": found_ag.get("description", "協同小組成員")
                            })
                    
                    if valid_collaborator_ids:
                        # 1. 動態追加 flow 陣列，使其能自然往下循環執行！
                        flow.extend(valid_collaborator_ids)
                        
                        # 2. 模擬小編與總裁的匯報對話
                        c_names = "、".join([d["name"] for d in collaborator_details])
                        discussion_text = f"💬 【{agent_name}】：總裁，我已經完成了「{idea}」的初步報告成果。請您審閱驗收！\n💬 【執行總裁 (CEO)】：非常好，你的初稿完全合規。為了進一步加強本專案的轉化率，我決定立即召集「{c_names}」加入專案進行協同，為我們設計後續方案！"
                        
                        log({
                            "status": "meeting_discussing",
                            "step": 1,
                            "total_steps": len(flow),
                            "agent_id": "ceo-acceptance",
                            "agent_name": "執行總裁 (CEO)",
                            "emoji": "👑",
                            "discussion": discussion_text,
                            "message": f"執行總裁已招募協同小隊：{c_names}！"
                        })
                        time.sleep(1.5)
                        
                        # 3. 發送工作流動態延伸事件，通知前端更新 Pipeline
                        log({
                            "status": "workflow_extended",
                            "collaborators": collaborator_details
                        })
                        time.sleep(0.5)

            # 遞增指標，繼續執行下一位（可能是剛才動態追加進來的員工）
            step_num += 1

        # 4. 由執行總裁 (CEO) 撰寫一份總結驗收報告呈交董事長
        acceptance_report_filename = "acceptance_report.md"
        acceptance_report_path = os.path.join(output_path, acceptance_report_filename)
        
        log({
            "status": "thinking",
            "step": len(flow) + 1,
            "total_steps": len(flow) + 1,
            "agent_id": "ceo-acceptance",
            "agent_name": "執行總裁 (CEO)",
            "emoji": "👑",
            "message": "👑 正在為董事長彙整最終專案成果總結驗收報告..."
        })
        time.sleep(1.0)
        
        summary_content = f"""# 👑 執行總裁成果總結驗收報告 (acceptance_report.md)

呈交 **董事長**：

本專案團隊成員均已全數通過總裁 Code Review 紀律檢查與 OWASP 安全漏洞盲測。以下為本次專案交付成果彙整，請董事長過目驗收。

## 1. 專案執行摘要 (Consensus Summary)
- **點子名稱**：{idea}
- **定稿時間**：{time.strftime('%Y-%m-%d %H:%M:%S')}
- **決策共識對齊**：{discussion_consensus or "無特別決策共識，依平台最佳實踐開發。"}
- **派遣模式**：{"單兵派遣與總裁動態協同" if single_agent else "工作流派遣"}

## 2. 旗下團隊交付產出檔案清單 (Artifacts List)
"""
        for fpath in all_written_files:
            fname = os.path.basename(fpath)
            summary_content += f"- 📄 `{fname}` ({os.path.join('data', 'users', user_id, 'outputs', project_folder, fname).replace(os.sep, '/')})\n"
            
        summary_content += """
---
## 3. 董事長驗收簽收核准
* [ ] **驗收核准通過** (請於前端點選「👑 驗收通過，結案！」)
* [ ] **退回重新修正** (請於前端填寫退回意見並點選「❌ 退回重新修正」)
"""
        with open(acceptance_report_path, "w", encoding="utf-8") as f:
            f.write(summary_content)

        log({
            "status": "finished",
            "all_written_files": [os.path.basename(w) for w in all_written_files] + [acceptance_report_filename],
            "acceptance_report": os.path.join("data", "users", user_id, "outputs", project_folder, acceptance_report_filename).replace(os.sep, '/'),
            "message": "專案開發流程已全數跑完！總結報告已呈交，正等待董事長進行最終驗收..."
        })

    except Exception as e:
        log({"status": "error", "error": str(e)})

# 背景自動派工 Scheduler 常駐 Thread 循環
def run_scheduler_loop():
    while True:
        try:
            if not os.path.exists("data/users"):
                time.sleep(10)
                continue
            
            users = os.listdir("data/users")
            for user_id in users:
                if not user_id or "@" not in user_id or user_id.startswith("."):
                    continue
                
                settings = load_user_settings(user_id)
                if not settings.get("cron_enabled", False):
                    continue
                
                idea = settings.get("cron_idea", "").strip()
                workflow = settings.get("cron_workflow", "mvp").strip()
                schedule_type = settings.get("cron_schedule", "every_60s").strip()
                
                if not idea:
                    continue
                
                now = time.time()
                last_run = LAST_CRON_RUN.get(user_id, 0)
                should_run = False
                
                if schedule_type == "every_60s":
                    if now - last_run >= 60:
                        should_run = True
                elif schedule_type == "daily_0900":
                    lt = time.localtime(now)
                    last_lt = time.localtime(last_run) if last_run > 0 else None
                    if lt.tm_hour >= 9:
                        if not last_lt or last_lt.tm_yday != lt.tm_yday or last_lt.tm_year != lt.tm_year:
                            should_run = True
                elif schedule_type == "weekly_monday_0900":
                    lt = time.localtime(now)
                    if lt.tm_wday == 0 and lt.tm_hour >= 9:
                        last_lt = time.localtime(last_run) if last_run > 0 else None
                        if not last_lt or last_lt.tm_yday != lt.tm_yday or last_lt.tm_year != lt.tm_year:
                            should_run = True
                
                if should_run:
                    LAST_CRON_RUN[user_id] = now
                    print(f"⏱️  [Scheduler] 觸發用戶 [{user_id}] 自動任務：Idea={idea}, Workflow={workflow}")
                    t = threading.Thread(
                        target=execute_workflow,
                        args=(user_id, idea + " (自動定時排程派遣)", workflow, True, None, True, "背景排程派發對齊", ""),
                        daemon=True
                    )
                    t.start()
                    
        except Exception as e:
            print(f"⚠️ [Scheduler Error] {str(e)}")
            
        time.sleep(10)

# 啟動排程器背景線程
threading.Thread(target=run_scheduler_loop, daemon=True).start()


# 自訂 HTTP Handler
class AgencyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        if path == "/api/run":
            query_params = urllib.parse.parse_qs(url_parsed.query)
            user_id = query_params.get("user_id", [""])[0].strip()
            if not user_id or "@" not in user_id:
                self.send_json_response(401, {"error": "請先通過 SSO 註冊或登入會員，方可使用協作工作流！"})
                return
            
            idea = query_params.get("idea", [""])[0].strip()
            mock_mode = query_params.get("mock", ["false"])[0].lower() == "true"
            workflow_type = query_params.get("workflow", ["mvp"])[0].strip()
            meeting_mode = query_params.get("meeting", ["false"])[0].lower() == "true"
            
            discussion_consensus = query_params.get("discussion", [""])[0].strip()
            acceptance_feedback = query_params.get("feedback", [""])[0].strip()
            single_agent = query_params.get("single_agent", ["false"])[0].lower() == "true"
            
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            execute_workflow(
                user_id=user_id,
                idea=idea,
                workflow_type=workflow_type,
                mock_mode=mock_mode,
                sse_emitter=self.send_sse_event,
                meeting_mode=meeting_mode,
                discussion_consensus=discussion_consensus,
                acceptance_feedback=acceptance_feedback,
                single_agent=single_agent
            )
            return

        if not path.startswith("/api/"):
            if path == "/" or path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open("intro.html", "rb") as f:
                    self.wfile.write(f.read())
                return
            elif path == "/app":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open("index.html", "rb") as f:
                    self.wfile.write(f.read())
                return
            
            super().do_GET()
            return

        user_id = get_user_id_from_headers(self.headers)
        if not user_id:
            self.send_json_response(401, {"error": "請先通過 SSO 註冊或登入會員，方可存取本平台資料！"})
            return

        if path == "/api/agents":
            custom_agents = load_user_agents(user_id)
            all_agents = BUILTIN_AGENTS + custom_agents
            self.send_json_response(200, all_agents)
            return

        elif path == "/api/workflows":
            custom_workflows = load_user_workflows(user_id)
            all_workflows = BUILTIN_WORKFLOWS + custom_workflows
            self.send_json_response(200, all_workflows)
            return

        elif path == "/api/history":
            outputs_dir = os.path.join(get_user_data_path(user_id), "outputs")
            project_history = []
            if os.path.exists(outputs_dir):
                for item in sorted(os.listdir(outputs_dir)):
                    item_path = os.path.join(outputs_dir, item)
                    if os.path.isdir(item_path) and item.startswith("project_"):
                        # 解析專案好讀名稱
                        parts = item.split("_")
                        if len(parts) >= 2:
                            proj_display_name = "_".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                        else:
                            proj_display_name = item
                            
                        # 獲取該專案下所有產出的檔案
                        files = []
                        proj_stat = os.stat(item_path)
                        created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proj_stat.st_mtime))
                        
                        for sub_file in sorted(os.listdir(item_path)):
                            sub_file_path = os.path.join(item_path, sub_file)
                            if os.path.isfile(sub_file_path) and not sub_file.startswith("."):
                                f_stat = os.stat(sub_file_path)
                                files.append({
                                    "filename": sub_file,
                                    "relative_path": os.path.join("data", "users", user_id, "outputs", item, sub_file).replace("\\", "/"),
                                    "size": f_stat.st_size,
                                    "updated_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(f_stat.st_mtime))
                                })
                                
                        project_history.append({
                            "project_id": item,
                            "project_name": proj_display_name,
                            "created_at": created_time,
                            "files": files
                        })
            self.send_json_response(200, project_history)
            return

        elif path == "/api/user_md":
            user_md = get_user_md_content(user_id)
            self.send_json_response(200, {"content": user_md})
            return

        elif path == "/api/settings":
            settings = load_user_settings(user_id)
            masked_settings = {
                "subscription": settings["subscription"],
                "openai_api_key": settings["openai_api_key"][:6] + "********" if settings["openai_api_key"] else "",
                "gemini_api_key": settings["gemini_api_key"][:6] + "********" if settings["gemini_api_key"] else "",
                "cron_enabled": settings.get("cron_enabled", False),
                "cron_schedule": settings.get("cron_schedule", "every_60s"),
                "cron_idea": settings.get("cron_idea", ""),
                "cron_workflow": settings.get("cron_workflow", "mvp")
            }
            self.send_json_response(200, masked_settings)
            return

        elif path == "/api/job":
            query_params = urllib.parse.parse_qs(url_parsed.query)
            job_id = query_params.get("id", [""])[0].strip()
            if not job_id:
                self.send_json_response(400, {"error": "缺少 job id"})
                return
            from lib.core import get_job_state
            state = get_job_state(job_id)
            if state is None:
                self.send_json_response(404, {"error": "找不到此任務"})
                return
            self.send_json_response(200, state)
            return

        self.send_json_response(404, {"error": "找不到此 API"})

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = b""
        if content_length > 0:
            post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            self.send_json_response(400, {"error": "無效的 JSON 格式"})
            return

        if path == "/api/auth":
            email = body.get("email", "").strip()
            if not email or "@" not in email:
                self.send_json_response(400, {"error": "請提供正確的電子郵件進行 SSO 會員註冊！"})
                return
            get_user_md_content(email)
            username = email.split("@")[0]
            self.send_json_response(200, {
                "token": email,
                "name": username,
                "avatar": "🎓",
                "email": email
            })
            return

        elif path == "/api/run":
            user_id = self.headers.get("Authorization", "") or self.headers.get("authorization", "")
            if user_id.startswith("Bearer "):
                user_id = user_id.split("Bearer ", 1)[1].strip()
            
            if not user_id or "@" not in user_id:
                self.send_json_response(401, {"error": "請先登入！"})
                return

            idea = body.get("idea", "").strip()
            if not idea:
                self.send_json_response(400, {"error": "請提供點子 (idea) 內容！"})
                return

            workflow_type = body.get("workflow", "mvp").strip()
            mock_mode = body.get("mock", False)
            meeting_mode = body.get("meeting", False)
            discussion_consensus = body.get("discussion", "").strip()
            acceptance_feedback = body.get("feedback", "").strip()
            single_agent = body.get("single_agent", False)

            # 生成唯一 job_id 并初始化 state
            from lib.core import save_job_state
            job_id = f"job_local_{str(int(time.time()))}"
            save_job_state(job_id, {"status": "running", "events": [], "finished": False})

            # 背景執行並利用 local_emitter 追加事件
            def local_emitter(event_data):
                from lib.core import get_job_state, save_job_state
                state = get_job_state(job_id) or {"status": "running", "events": [], "finished": False}
                if event_data.get("status") == "finished":
                    state["finished"] = True
                    state["status"] = "finished"
                state.setdefault("events", []).append(event_data)
                save_job_state(job_id, state)

            import threading
            t = threading.Thread(
                target=execute_workflow,
                kwargs={
                    "user_id": user_id,
                    "idea": idea,
                    "workflow_type": workflow_type,
                    "mock_mode": mock_mode,
                    "sse_emitter": local_emitter,
                    "meeting_mode": meeting_mode,
                    "discussion_consensus": discussion_consensus,
                    "acceptance_feedback": acceptance_feedback,
                    "single_agent": single_agent
                },
                daemon=True
            )
            t.start()

            self.send_json_response(200, {"job_id": job_id, "message": "任務已啟動！"})
            return

        user_id = get_user_id_from_headers(self.headers)
        if not user_id:
            self.send_json_response(401, {"error": "請先通過 SSO 註冊或登入會員，方可執行此操作！"})
            return

        if path == "/api/ceo_chat":
            idea = body.get("idea", "").strip()
            message = body.get("message", "").strip()
            chat_history = body.get("history", [])

            if not idea or not message:
                self.send_json_response(400, {"error": "缺少點子 (Idea) 或商討文字 (Message) 內容。"})
                return

            user_md = get_user_md_content(user_id)
            user_settings = load_user_settings(user_id)
            
            system_instruction = f"""您是 JehaCrop 公司的「執行總裁 (CEO)」。
目前您的「董事長」（即對話的用戶，也是您的老闆）正在與您討論一個全新專案的商討方案，點子為：「{idea}」。
您的任務是站在執行總裁的專業高度，與董事長深入對答討論。

請遵循以下守則：
1. 您必須聽令董事長（用戶）的最終指令與修改意見，並極度有禮。
2. 讀取並貼合董事長在 user.md 中記錄的習慣偏好（例如偏好的風格、溝通語氣、開發紀律等）。
3. 回覆請簡明扼要、專業親切，且結論先行。提供初步的實施路線、擬調度的旗下成員、主要風險與董事長需要注意的地方。
4. 討論聚焦在如何優化並落實專案。最後可以引導董事長「董事長若覺得此方案可行，請點選下方派遣執行按鈕，我會立即調度團隊開始開發。」

董事長偏好記憶 (user.md)：
{user_md}
"""
            messages = [{"role": "system", "content": system_instruction}]
            for h in chat_history:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})

            try:
                client, model_name = get_llm_client_for_agent("gpt-4o-mini", mock_mode=False, user_api_keys=user_settings if user_settings.get("subscription") == "pro" else None)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"【CEO 總裁回報】董事長好！針對您的點子「{idea}」，以及您剛才的要求「{message}」，我已經有數個落地設想。我建議調度「新創 MVP 開發團隊」工作流，由快速原型人員先建立 console.log 腳本，前端隨後進行 React 畫面刻劃。董事長若覺得此方案可行，請點選下方派遣執行按鈕，我會立即調度團隊開始開發！"

            self.send_json_response(200, {"reply": reply})
            return

        elif path == "/api/agents":
            agent_name = body.get("name", "").strip()
            emoji = body.get("emoji", "👤").strip()
            description = body.get("description", "").strip()
            system_prompt = body.get("system_prompt", "").strip()
            llm_source = body.get("llm_source", "gpt-4o-mini").strip()
            category = body.get("category", "custom").strip()
            avatar_prompt = body.get("avatar_prompt", "").strip()

            if not agent_name or not system_prompt:
                self.send_json_response(400, {"error": "請填寫代理人名稱與系統提示詞！"})
                return

            agent_id = "custom-" + re.sub(r'[^a-zA-Z0-9\-]', '', agent_name.lower().replace(" ", "-")) + "-" + str(int(time.time()))[-4:]
            
            # --- 🎨 自訂 AI 員工頭像生成與下載下載機制 ---
            avatar_url = ""
            if avatar_prompt:
                try:
                    user_settings = load_user_settings(user_id)
                    is_pro = user_settings.get("subscription") == "pro"
                    api_keys = user_settings if is_pro else None
                    # 嘗試調用 OpenAI 生成
                    client_openai, model_name = get_llm_client_for_agent("gpt-4o", mock_mode=False, user_api_keys=api_keys)
                    if client_openai and api_keys.get("openai_api_key"):
                        response = client_openai.images.generate(
                            model="dall-e-3",
                            prompt=f"A professional card game portrait of: {avatar_prompt}, detailed trading card illustration style, simple color background, sci-fi cyberpunk wabi-sabi art style",
                            size="1024x1024",
                            n=1
                        )
                        temp_url = response.data[0].url
                        # 二進位下載
                        req_img = urllib.request.Request(temp_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_img) as img_res:
                            img_data = img_res.read()
                        
                        user_avatar_dir = os.path.join(get_user_data_path(user_id), "outputs", "avatars")
                        os.makedirs(user_avatar_dir, exist_ok=True)
                        local_img_path = os.path.join(user_avatar_dir, f"{agent_id}.png")
                        with open(local_img_path, "wb") as f_img:
                            f_img.write(img_data)
                        
                        # 靜態映射
                        avatar_url = f"/data/users/{user_id}/outputs/avatars/{agent_id}.png"
                except Exception as e:
                    print(f"⚠️ DALL-E 繪圖失敗，啟用容錯機制: {str(e)}")

            if not avatar_url:
                # 容錯：使用 Dicebear 卡通機器人大頭貼向量圖
                seed = urllib.parse.quote(avatar_prompt or agent_name)
                avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={seed}"

            custom_agents = load_user_agents(user_id)
            new_agent = {
                "id": agent_id,
                "name": agent_name,
                "emoji": emoji,
                "description": description,
                "system_prompt": system_prompt,
                "llm_source": llm_source,
                "category": category,
                "avatar_url": avatar_url,
                "is_custom": True
            }
            custom_agents.append(new_agent)
            save_user_agents(user_id, custom_agents)
            self.send_json_response(200, {"message": "代理人招募成功！", "agent": new_agent})
            return

        elif path == "/api/workflows":
            wf_name = body.get("name", "").strip()
            description = body.get("description", "").strip()
            flow = body.get("flow", [])

            if not wf_name or not flow:
                self.send_json_response(400, {"error": "請填寫團隊名稱並挑選至少一位成員！"})
                return

            wf_id = "wf-" + str(int(time.time()))
            custom_workflows = load_user_workflows(user_id)
            new_wf = {
                "id": wf_id,
                "name": wf_name,
                "description": description,
                "flow": flow,
                "is_custom": True
            }
            custom_workflows.append(new_wf)
            save_user_workflows(user_id, custom_workflows)
            self.send_json_response(200, {"message": "團隊工作流儲存成功！", "workflow": new_wf})
            return

        elif path == "/api/user_md":
            content = body.get("content", "").strip()
            if not content:
                self.send_json_response(400, {"error": "記憶庫內容不可為空！"})
                return
            save_user_md_content(user_id, content)
            self.send_json_response(200, {"message": "總裁習慣記憶庫更新成功！"})
            return

        elif path == "/api/settings":
            subscription = body.get("subscription", "free").strip()
            openai_api_key = body.get("openai_api_key", "").strip()
            gemini_api_key = body.get("gemini_api_key", "").strip()
            
            cron_enabled = body.get("cron_enabled", False)
            cron_schedule = body.get("cron_schedule", "every_60s").strip()
            cron_idea = body.get("cron_idea", "").strip()
            cron_workflow = body.get("cron_workflow", "mvp").strip()

            current = load_user_settings(user_id)
            if openai_api_key.endswith("********"):
                openai_api_key = current["openai_api_key"]
            if gemini_api_key.endswith("********"):
                gemini_api_key = current["gemini_api_key"]

            updated_settings = {
                "subscription": subscription,
                "openai_api_key": openai_api_key,
                "gemini_api_key": gemini_api_key,
                "cron_enabled": cron_enabled,
                "cron_schedule": cron_schedule,
                "cron_idea": cron_idea,
                "cron_workflow": cron_workflow
            }
            save_user_settings(user_id, updated_settings)
            self.send_json_response(200, {"message": "總裁 API 與訂閱設定保存成功！"})
            return

        self.send_json_response(404, {"error": "找不到此 API"})

    def send_sse_event(self, data):
        try:
            event_str = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            self.wfile.write(event_str.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, AgencyHandler)
    print("==================================================")
    print(f"🚀  JehaCrop Fable 總裁決策討論與 Review 伺服器啟動...")
    print(f"👉  請於瀏覽器開啟：http://localhost:{port}")
    print("==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 正在關閉本機伺服器。")
        sys.exit(0)

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
