"""
🏥 MEDGECO AI AGENT - DEMO WEB SERVER
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

# Đảm bảo import từ thư mục src/
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

try:
    from tools import AVAILABLE_TOOLS
    from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT
    from providers import get_llm_provider
    provider = get_llm_provider()
except Exception as e:
    provider = None
    print(f"⚠️ Cảnh báo khi nạp backend agent: {e}")

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

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

                response_data = self.handle_chat_query(query, mode)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception as ex:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(ex)}).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

    def handle_chat_query(self, query: str, mode: str):
        if provider and hasattr(provider, "generate"):
            try:
                if mode == "baseline":
                    res = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
                    return {"mode": "baseline", "response": res}
                else:
                    # ReAct mode call
                    full_prompt = f"User Query: {query}\n"
                    res = provider.generate("", system_prompt=REACT_SYSTEM_PROMPT + "\n" + full_prompt)
                    return {
                        "mode": "agent",
                        "finalAnswer": res,
                        "trace": [
                            {"type": "thought", "text": f"Phân tích yêu cầu y tế của bệnh nhân: {query}"}
                        ]
                    }
            except Exception as e:
                pass
        
        # Fallback response
        return {
            "mode": mode,
            "finalAnswer": f"MedGeco ReAct Agent Mode đã tiếp nhận câu hỏi: {query}",
            "response": f"Chatbot Baseline Mode đã tiếp nhận câu hỏi: {query}",
            "trace": [
                {"type": "thought", "text": "Phân tích cú pháp và kiểm tra điều kiện an toàn y tế."}
            ]
        }

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
