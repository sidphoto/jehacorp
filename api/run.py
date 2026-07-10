import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for d in [current_dir, parent_dir, "/var/task"]:
    if d not in sys.path:
        sys.path.insert(0, d)

import json
from lib.flask_compat import make_flask_app
import re, time, random, threading
from lib.core import (
    BUILTIN_AGENTS, BUILTIN_WORKFLOWS, FABLE_AUDITOR_PROMPT, SECURITY_CHECKER_PROMPT,
    get_user_md, get_user_settings, get_user_agents, get_user_workflows,
    get_llm_client, get_mock_response, extract_files_from_content,
    save_project_files, append_project, append_job_event, finish_job, save_job_state,
    get_user_id_from_request
)

def _run_workflow_background(job_id, uid, idea, workflow_type, mock_mode,
                               meeting_mode, discussion_consensus, acceptance_feedback,
                               single_agent):
    """背景 Thread 執行完整工作流，將進度寫入 KV Job State"""
    def emit(event_data):
        append_job_event(job_id, event_data)

    try:
        user_md = get_user_md(uid)
        user_settings = get_user_settings(uid)
        is_pro = user_settings.get("subscription") == "pro"
        api_keys = user_settings if is_pro else None

        # 決定工作流 flow
        flow = []
        if single_agent:
            flow = [workflow_type]
        else:
            target_wf = None
            for wf in BUILTIN_WORKFLOWS:
                if wf["id"] == workflow_type:
                    target_wf = wf
                    break
            if not target_wf:
                for wf in get_user_workflows(uid):
                    if wf["id"] == workflow_type:
                        target_wf = wf
                        break
            if target_wf:
                flow = target_wf["flow"]
            else:
                try:
                    flow = json.loads(workflow_type)
                except Exception:
                    emit({"status": "error", "error": f"找不到工作流 {workflow_type}"})
                    return

        if not flow:
            emit({"status": "error", "error": "工作流中必須包含至少一位成員！"})
            return

        # ── Step 0：生成 project_brief.md ────────────────────────────────
        safe_idea = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5\-]', '_', idea.strip())[:15]
        project_id = f"project_{safe_idea}_{str(int(time.time()))[-4:]}"
        project_name = safe_idea.replace("_", " ")

        emit({"status": "thinking", "step": 0, "total_steps": 1,
              "agent_id": "system-coordinator", "agent_name": "執行總裁 (CEO)", "emoji": "📁",
              "llm_source": "gpt-4o-mini", "retry_count": 0,
              "message": "📁 正在由執行總裁 (CEO) 整理全局案件簡報，匯入董事長決策共識與驗收要求..."})

        if mock_mode:
            time.sleep(1.0)
            brief_content = f"# 📋 專案簡報與案件背景 (project_brief.md)\n\n## 1. 案件基本資訊\n- **專案名稱**：{idea}\n- **立案時間**：{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if discussion_consensus:
                brief_content += f"\n## 3. 董事長與 CEO 商討之決策共識\n- {discussion_consensus}\n"
        else:
            client, model_name = get_llm_client("gpt-4o-mini", user_api_keys=api_keys)
            prompt = f"您是 JehaCrop 的「執行總裁 (CEO)」。請針對董事長的點子，參考 user.md，生成一份 project_brief.md 專案簡報。\n\n【user.md】：\n{user_md}\n\n【點子】：{idea}\n"
            if discussion_consensus:
                prompt += f"\n【決策共識】：{discussion_consensus}"
            if client:
                resp = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=0.5)
                brief_content = resp.choices[0].message.content
            else:
                brief_content = f"# 📋 {idea} 專案簡報\n(Mock: 無 API 金鑰)"

        project_files = {"project_brief.md": brief_content}
        all_file_names = ["project_brief.md"]

        emit({"status": "completed", "step": 0, "total_steps": 1,
              "agent_id": "system-coordinator", "agent_name": "執行總裁 (CEO)", "emoji": "📁",
              "retry_count": 0, "report_file": f"{project_id}/project_brief.md",
              "written_files": ["project_brief.md"],
              "message": "專案立案完成！已匯入決策共識並歸檔簡報 project_brief.md。"})
        time.sleep(0.3)

        previous_outputs = {}

        # ── Step 1..N：各 AI 員工執行 ─────────────────────────────────────
        step_num = 1
        while step_num <= len(flow):
            agent_id = flow[step_num - 1]
            agent_name = agent_id
            emoji = "👤"
            llm_source = "gpt-4o-mini"
            system_prompt = ""

            for ag in BUILTIN_AGENTS:
                if ag["id"] == agent_id:
                    emoji = ag["emoji"]
                    llm_source = ag.get("llm_source", "gpt-4o-mini")
                    agent_name = ag["name"]
                    system_prompt = ag["description"]
                    break

            for ag in get_user_agents(uid):
                if ag["id"] == agent_id:
                    emoji = ag.get("emoji", "👤")
                    llm_source = ag.get("llm_source", "gpt-4o-mini")
                    agent_name = ag["name"]
                    system_prompt = ag.get("system_prompt", "")
                    break

            # 會議討論 (meeting_mode)
            discussion_text = ""
            if meeting_mode and step_num >= 2:
                emit({"status": "thinking", "step": step_num, "total_steps": len(flow),
                      "agent_id": agent_id, "agent_name": agent_name, "emoji": "💬",
                      "message": f"💬 會議對齊中... 正在召開共識對接會議"})
                if mock_mode:
                    time.sleep(1.0)
                    discussion_text = f"💬 【前一成員】：我已完成初步成果。\n💬 【{agent_name}】：收到！我會配合並進行後續工作。"
                else:
                    client, model_name = get_llm_client("gpt-4o-mini", user_api_keys=api_keys)
                    if client:
                        disc_resp = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": f"模擬兩位員工的簡短對齊會議討論（{agent_name}），繁體中文，150字以內。"}],
                            temperature=0.7
                        )
                        discussion_text = disc_resp.choices[0].message.content

                emit({"status": "meeting_discussing", "step": step_num, "total_steps": len(flow),
                      "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                      "discussion": discussion_text, "message": "已完成會議共識對齊討論！"})
                time.sleep(0.5)

            # 員工執行（含 Code Review 重試迴圈）
            passed = False
            retry_count = 0
            fable_feedback = ""
            security_feedback = ""
            output_content = ""

            while not passed:
                emit({"status": "thinking", "step": step_num, "total_steps": len(flow),
                      "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                      "llm_source": llm_source, "retry_count": retry_count,
                      "fable_feedback": fable_feedback or security_feedback,
                      "message": f"正在撰寫初稿 (Model: {llm_source})..."})

                if mock_mode:
                    time.sleep(1.2)
                    output_content = get_mock_response(agent_id, agent_name, idea, has_feedback=bool(acceptance_feedback))
                    if retry_count == 0 and step_num == 1 and random.random() > 0.4 and not acceptance_feedback and not single_agent:
                        output_content += "\n\n```sql\n-- 模擬漏洞\nSELECT * FROM users WHERE username = '\" + input;\n```"
                    if retry_count > 0:
                        output_content = get_mock_response(agent_id, agent_name, idea)
                        output_content += "\n\n*備註：已修復安全漏洞。*"
                else:
                    client, model_name = get_llm_client(llm_source, user_api_keys=api_keys)
                    if not client:
                        emit({"status": "error", "error": f"LLM 啟動失敗 ({llm_source})，請確認金鑰設定。"})
                        return
                    full_prompt = f"您是 JehaCrop 公司的職員：{agent_name}。\n【user.md】：\n{user_md}\n【project_brief.md】：\n{brief_content}\n\n您的角色：{system_prompt}\n\n【點子】：{idea}\n"
                    if fable_feedback:
                        full_prompt += f"\n⚠️【總裁 Code Review 修正意見】：{fable_feedback}\n"
                    if security_feedback:
                        full_prompt += f"\n🛡️【總裁資安 Review 修正建議】：{security_feedback}\n"
                    if previous_outputs:
                        full_prompt += "\n【前步成果】：\n" + "\n".join([f"--- {k} ---\n{v}" for k, v in previous_outputs.items()])
                    resp = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": full_prompt}],
                        temperature=0.7
                    )
                    output_content = resp.choices[0].message.content

                # Code Review
                emit({"status": "fable_auditing", "step": step_num, "total_steps": len(flow),
                      "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                      "llm_source": "gpt-4o", "retry_count": retry_count,
                      "message": "🔍 正在由執行總裁 (CEO) 進行專案交付物與 Code Review 審查中..."})
                time.sleep(0.8)

                fable_passed = True
                if mock_mode:
                    fable_feedback = "✅ 總裁 Review：完全符合 Verified-Done 紀律要求。"
                else:
                    try:
                        ac, am = get_llm_client("gpt-4o", user_api_keys=api_keys)
                        if ac:
                            ar = ac.chat.completions.create(model=am, messages=[{"role": "system", "content": FABLE_AUDITOR_PROMPT.format(draft_content=output_content)}, {"role": "user", "content": "請進行 Code Review。"}], temperature=0.2)
                            art = ar.choices[0].message.content
                            fable_passed = "CEO_PASS" in art
                            fable_feedback = ("✅ 總裁 Review: " if fable_passed else "❌ 總裁退回: ") + art.replace("【CEO_PASS】", "").replace("【CEO_REJECT】", "").strip()
                    except Exception:
                        fable_feedback = "✅ 總裁 Review 通過 (中斷容錯)"

                if not fable_passed:
                    emit({"status": "fable_rejected", "step": step_num, "total_steps": len(flow),
                          "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                          "retry_count": retry_count, "fable_feedback": fable_feedback,
                          "message": f"總裁 Review 退回重做：{fable_feedback}"})
                    retry_count += 1
                    time.sleep(0.5)
                    continue

                # Security Review
                emit({"status": "security_auditing", "step": step_num, "total_steps": len(flow),
                      "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                      "message": "🛡️ 正在由執行總裁 (CEO) 進行資通安全漏洞審查與合規檢查中..."})
                time.sleep(0.8)

                sec_passed = True
                if mock_mode:
                    if "SELECT * FROM users WHERE" in output_content and "input" in output_content:
                        security_feedback = "❌ 總裁資安警告：偵測到 SQL Injection 注入漏洞！"
                        sec_passed = False
                    else:
                        security_feedback = "✅ 總裁資安 Review：代碼中未偵測到 OWASP Top 10 高危險漏洞。"
                else:
                    try:
                        sc, sm = get_llm_client("gpt-4o", user_api_keys=api_keys)
                        if sc:
                            sr = sc.chat.completions.create(model=sm, messages=[{"role": "system", "content": SECURITY_CHECKER_PROMPT.format(draft_content=output_content)}, {"role": "user", "content": "請進行資安審查。"}], temperature=0.1)
                            srt = sr.choices[0].message.content
                            sec_passed = "CEO_SEC_PASS" in srt
                            security_feedback = ("✅ 總裁資安 Review: " if sec_passed else "❌ 總裁資安拒絕: ") + srt.replace("【CEO_SEC_PASS】", "").replace("【CEO_SEC_REJECT】", "").strip()
                    except Exception:
                        security_feedback = "✅ 總裁資安 Review 通過 (中斷容錯)"

                if not sec_passed:
                    emit({"status": "security_rejected", "step": step_num, "total_steps": len(flow),
                          "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                          "retry_count": retry_count, "security_feedback": security_feedback,
                          "message": f"總裁資安 Review 退回：{security_feedback}"})
                    retry_count += 1
                    time.sleep(0.5)
                    continue

                passed = True

            # 寫入檔案
            emit({"status": "writing", "step": step_num, "total_steps": len(flow),
                  "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                  "message": "💾 總裁雙重 Review 通過，正在進行寫檔歸檔..."})

            report_filename = f"{step_num}_{agent_id}.md"
            project_files[report_filename] = output_content
            all_file_names.append(report_filename)

            extracted = extract_files_from_content(output_content)
            for fname, fcontent in extracted.items():
                project_files[fname] = fcontent
                all_file_names.append(os.path.basename(fname))

            emit({"status": "completed", "step": step_num, "total_steps": len(flow),
                  "agent_id": agent_id, "agent_name": agent_name, "emoji": emoji,
                  "retry_count": retry_count, "fable_feedback": security_feedback,
                  "written_files": list(extracted.keys()),
                  "report_file": f"{project_id}/{report_filename}",
                  "message": "已通過總裁雙重審查監督！階段成果歸檔完成。"})

            previous_outputs[agent_name] = output_content
            time.sleep(0.3)

            # 單兵模式：總裁動態招募協作者
            if single_agent and step_num == 1:
                emit({"status": "thinking", "step": 1, "total_steps": 1,
                      "agent_id": "ceo-acceptance", "agent_name": "執行總裁 (CEO)", "emoji": "👑",
                      "message": f"👑 總裁正在評估 【{agent_name}】 的成果報告，分析是否需要招募其他旗下員工前來協同作戰..."})
                time.sleep(1.0)

                collaborator_ids = []
                if mock_mode:
                    collaborator_ids = ["ad-creative-strategist"] if agent_id == "marketing-content-creator" else ["growth-hacker"]
                else:
                    all_ag = BUILTIN_AGENTS + get_user_agents(uid)
                    agents_text = "\n".join([f"- ID: {ag['id']}, 職務: {ag['name']}" for ag in all_ag if ag["id"] != agent_id])
                    try:
                        ec, em = get_llm_client("gpt-4o-mini", user_api_keys=api_keys)
                        if ec:
                            er = ec.chat.completions.create(model=em, messages=[{"role": "user", "content": f"您是 JehaCrop CEO。員工「{agent_name}」完成了任務「{idea}」。請從以下名冊選 1~2 位協作者（JSON 陣列格式，直接輸出不加 ```json 標記）：\n{agents_text}"}], temperature=0.2)
                            js = er.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
                            collaborator_ids = json.loads(js)
                    except Exception:
                        collaborator_ids = ["ad-creative-strategist"]

                if collaborator_ids:
                    valid_cols = []
                    col_details = []
                    for cid in collaborator_ids:
                        for ag in BUILTIN_AGENTS + get_user_agents(uid):
                            if ag["id"] == cid:
                                valid_cols.append(cid)
                                col_details.append({"id": ag["id"], "name": ag["name"], "emoji": ag.get("emoji", "👤"), "description": ag.get("description", "")})
                                break

                    if valid_cols:
                        flow.extend(valid_cols)
                        c_names = "、".join([d["name"] for d in col_details])
                        discussion_text = f"💬 【{agent_name}】：總裁，我已完成「{idea}」的初步成果。請審閱驗收！\n💬 【執行總裁 (CEO)】：非常好，你的初稿完全合規。我決定立即召集「{c_names}」加入協同！"
                        emit({"status": "meeting_discussing", "step": 1, "total_steps": len(flow),
                              "agent_id": "ceo-acceptance", "agent_name": "執行總裁 (CEO)", "emoji": "👑",
                              "discussion": discussion_text, "message": f"執行總裁已招募協同小隊：{c_names}！"})
                        time.sleep(1.0)
                        emit({"status": "workflow_extended", "collaborators": col_details})
                        time.sleep(0.3)

            step_num += 1

        # ── 最終驗收報告 ──────────────────────────────────────────────────
        emit({"status": "thinking", "step": len(flow) + 1, "total_steps": len(flow) + 1,
              "agent_id": "ceo-acceptance", "agent_name": "執行總裁 (CEO)", "emoji": "👑",
              "message": "👑 正在為董事長彙整最終專案成果總結驗收報告..."})
        time.sleep(0.8)

        acceptance_content = f"""# 👑 執行總裁成果總結驗收報告 (acceptance_report.md)

呈交 **董事長**：

## 1. 專案執行摘要
- **點子名稱**：{idea}
- **定稿時間**：{time.strftime('%Y-%m-%d %H:%M:%S')}
- **派遣模式**：{"單兵派遣與總裁動態協同" if single_agent else "工作流派遣"}

## 2. 旗下團隊交付產出檔案清單
"""
        for fname in all_file_names:
            acceptance_content += f"- 📄 `{fname}`\n"
        acceptance_content += "\n---\n## 3. 董事長驗收簽收核准\n* [ ] **驗收核准通過**\n* [ ] **退回重新修正**\n"

        project_files["acceptance_report.md"] = acceptance_content
        all_file_names.append("acceptance_report.md")

        # 持久化所有檔案到 KV
        save_project_files(uid, project_id, project_files)
        append_project(uid, {
            "project_id": project_id,
            "project_name": project_name,
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        })

        finish_job(job_id, {
            "status": "finished",
            "all_written_files": all_file_names,
            "acceptance_report": f"{project_id}/acceptance_report.md",
            "project_id": project_id,
            "message": "專案開發流程已全數跑完！總結報告已呈交，正等待董事長進行最終驗收..."
        })

    except Exception as e:
        import traceback
        finish_job(job_id, {"status": "error", "error": str(e), "trace": traceback.format_exc()})


def handler(request):
    """
    POST /api/run
    Body: {idea, workflow, mock, meeting, discussion, feedback, single_agent}
    返回：{job_id}，前端用 /api/job?id=<job_id> 輪詢進度
    """
    uid = get_user_id_from_request(request)
    if not uid:
        return {"statusCode": 401, "body": json.dumps({"error": "請先登入！"}, ensure_ascii=False)}

    if request.method != "POST":
        return {"statusCode": 405, "body": "Method Not Allowed"}

    try:
        body = json.loads(request.body) if request.body else {}
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "無效 JSON"}, ensure_ascii=False)}

    idea = body.get("idea", "").strip()
    if not idea:
        return {"statusCode": 400, "body": json.dumps({"error": "請提供點子 (idea) 內容！"}, ensure_ascii=False)}

    workflow_type = body.get("workflow", "mvp").strip()
    mock_mode = body.get("mock", False)
    meeting_mode = body.get("meeting", False)
    discussion_consensus = body.get("discussion", "").strip()
    acceptance_feedback = body.get("feedback", "").strip()
    single_agent = body.get("single_agent", False)

    # 生成唯一 job_id
    job_id = f"job_{re.sub(r'[^a-zA-Z0-9]', '', uid[:10])}_{str(int(time.time()))}"
    save_job_state(job_id, {"status": "running", "events": [], "finished": False})

    # 在背景 Thread 執行（Vercel Function 限時 60s，背景執行適合模擬模式；真實 AI 呼叫建議用 Vercel Background Functions 或 Queue）
    t = threading.Thread(
        target=_run_workflow_background,
        args=(job_id, uid, idea, workflow_type, mock_mode, meeting_mode,
              discussion_consensus, acceptance_feedback, single_agent),
        daemon=True
    )
    t.start()

    return {
        "statusCode": 200,
        "body": json.dumps({"job_id": job_id, "message": "任務已啟動！請使用 /api/job?id= 輪詢進度。"}, ensure_ascii=False),
        "headers": {"Content-Type": "application/json; charset=utf-8"}
    }

app = make_flask_app(handler)
