"""
🏥 MEDGECO AI AGENT - DEMO WEB SERVER & API BRIDGE
Chạy web app UI/UX tương tác trực tiếp với ReAct Agent & Chatbot Baseline logic.

Cách chạy:
    python server.py
Mở trình duyệt:
    http://localhost:8000
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

def run_agent_interactive(user_query: str):
    if not provider:
        return {"mode": "agent", "finalAnswer": "Chưa nạp được Provider backend.", "trace": []}

    history = []
    trace_steps = []
    step = 0
    final_answer = ""

    while step < MAX_ITERATIONS:
        step += 1
        full_prompt = user_query + "\n"
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
        "trace": trace_steps
    }

def run_baseline_interactive(user_query: str):
    if not provider:
        return {"mode": "baseline", "response": "Chưa nạp được Provider backend.", "finalAnswer": "Chưa nạp được Provider backend."}

    response = generate_with_retry(provider, user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    return {
        "mode": "baseline",
        "response": response,
        "finalAnswer": response
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

                if mode == "baseline":
                    response_data = run_baseline_interactive(query)
                else:
                    response_data = run_agent_interactive(query)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception as ex:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

if __name__ == "__main__":
    print("==================================================")
    print("🏥 MEDGECO AI AGENT — UX/UI DEMO WEB SERVER")
    print("==================================================")
    print(f"🚀 Server đang khởi chạy tại: http://localhost:{PORT}")
    print(f"📂 Thư mục web static: {WEB_DIR}")
    print("Bấm Ctrl+C để dừng server.")
    print("==================================================")
    
    with socketserver.TCPServer(("", PORT), MedGecoHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Đã dừng MedGeco Server.")
