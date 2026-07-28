"""
🏥 MEDGECO AI AGENT - DEMO WEB SERVER & API BRIDGE (VỚI CONTEXT WINDOW MEMORY)
Chạy web app UI/UX tương tác trực tiếp với ReAct Agent & Chatbot Baseline logic.

Tính năng mới:
    - Context Window Memory: Nạp lịch sử hội thoại nhiều lượt để AI hiểu ngữ cảnh liên tục.
    - Reset Context Window API: Xóa bộ nhớ ngữ cảnh khi người dùng yêu cầu.
"""

import http.server
import socketserver
import json
import os
import sys
import re

# Đảm bảo import từ thư mục src/
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

try:
    from app import generate_with_retry, parse_action, run_tool_safely, CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
    from providers import get_llm_provider
    provider = get_llm_provider()
except Exception as e:
    provider = None
    print(f"⚠️ Cảnh báo khi nạp backend agent: {e}")

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

def run_agent_interactive(user_query: str, history_context: list = None):
    if not provider:
        return {"mode": "agent", "finalAnswer": "Chưa nạp được Provider backend.", "trace": []}

    # Formatting Context Window (Lịch sử hội thoại trước đó)
    context_str = ""
    if history_context and len(history_context) > 0:
        context_str = "\n--- 🧠 CONTEXT WINDOW (LỊCH SỬ CHAT TRƯỚC ĐÓ) ---\n"
        for item in history_context:
            role = "Bệnh nhân" if item.get("role") == "user" else "MedGeco AI"
            content = item.get("content", "")
            context_str += f"{role}: {content}\n"
        context_str += "--- KẾT THÚC CONTEXT WINDOW ---\n\n"

    history = []
    trace_steps = []
    step = 0
    final_answer = ""

    while step < MAX_ITERATIONS:
        step += 1
        full_prompt = context_str + f"User Query Hiện Tại: {user_query}\n"
        if history:
            full_prompt += "\n".join(history) + "\n"

        response = generate_with_retry(provider, "", system_prompt=REACT_SYSTEM_PROMPT + "\n" + full_prompt)
        
        thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)(?=\n|$)", response)
        final_answer_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)

        thought_text = thought_match.group(1).strip() if thought_match else ""
        action_text = action_match.group(1).strip() if action_match else ""
        final_answer_text = final_answer_match.group(1).strip() if final_answer_match else ""

        if thought_text:
            trace_steps.append({"type": "thought", "text": thought_text})
            history.append(f"Thought: {thought_text}")

        if final_answer_text:
            final_answer = final_answer_text
            break
        elif "final answer:" in action_text.lower():
            fa_match = re.search(r"(?i)final answer:\s*(.*)", action_text, re.DOTALL)
            if fa_match:
                final_answer = fa_match.group(1).strip()
                break

        if action_text:
            trace_steps.append({"type": "action", "text": action_text})
            history.append(f"Action: {action_text}")

            tool_name, args, kwargs = parse_action(action_text)
            if tool_name:
                obs = run_tool_safely(tool_name, args, kwargs)
            else:
                obs = f"LỖI: Không thể phân tích cú pháp Action '{action_text}'."

            trace_steps.append({"type": "observation", "text": obs})
            history.append(f"Observation: {obs}")
        else:
            cleaned_resp = response.strip()
            if cleaned_resp:
                if "final answer:" in cleaned_resp.lower():
                    fa_match = re.search(r"(?i)final answer:\s*(.*)", cleaned_resp, re.DOTALL)
                    if fa_match:
                        final_answer = fa_match.group(1).strip()
                        break
                final_answer = cleaned_resp
                break
            else:
                break

    if not final_answer and step >= MAX_ITERATIONS:
        final_answer = "Tôi xin lỗi, hệ thống chưa thể hoàn thành yêu cầu do vượt quá số bước giới hạn cho phép."

    return {
        "mode": "agent",
        "finalAnswer": final_answer,
        "trace": trace_steps,
        "contextTurns": len(history_context) if history_context else 0
    }

def run_baseline_interactive(user_query: str, history_context: list = None):
    if not provider:
        return {"mode": "baseline", "response": "Chưa nạp được Provider backend.", "finalAnswer": "Chưa nạp được Provider backend."}

    context_str = ""
    if history_context and len(history_context) > 0:
        context_str = "\n--- CONTEXT WINDOW (LỊCH SỬ CHAT TRƯỚC ĐÓ) ---\n"
        for item in history_context:
            role = "Bệnh nhân" if item.get("role") == "user" else "Chatbot"
            content = item.get("content", "")
            context_str += f"{role}: {content}\n"
        context_str += "--- KẾT THÚC CONTEXT WINDOW ---\n\n"

    full_query = context_str + f"Bệnh nhân hỏi: {user_query}"
    response = generate_with_retry(provider, full_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    return {
        "mode": "baseline",
        "response": response,
        "finalAnswer": response,
        "contextTurns": len(history_context) if history_context else 0
    }

class MedGecoHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                query = data.get("query", "")
                mode = data.get("mode", "agent")
                history_context = data.get("history", [])

                if mode == "baseline":
                    response_data = run_baseline_interactive(query, history_context)
                else:
                    response_data = run_agent_interactive(query, history_context)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception as ex:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}, ensure_ascii=False).encode('utf-8'))

        elif self.path == "/api/reset_context":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Context window reset successfully"}, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_error(404, "Endpoint not found")

if __name__ == "__main__":
    print("==================================================")
    print("🏥 MEDGECO AI AGENT — DEMO WEB SERVER (VỚI CONTEXT WINDOW)")
    print("==================================================")
    print(f"🚀 Server đang khởi chạy tại: http://localhost:{PORT}")
    print(f"📂 Thư mục web static: {WEB_DIR}")
    print("==================================================")
    
    with socketserver.TCPServer(("", PORT), MedGecoHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Đã dừng MedGeco Server.")
