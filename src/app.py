"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
import re
import inspect
import time
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_action(action_line: str):
    """
    Phân tích dòng Action để lấy tên công cụ và các tham số.
    Hỗ trợ các định dạng:
    - tên_công_cụ[tham_số_1, tham_số_2, ...]
    - tên_công_cụ(tham_số_1, tham_số_2, ...)
    - tên_công_cụ[key1=val1, key2=val2, ...]
    """
    action_line = action_line.strip()
    if action_line.startswith("Action:"):
        action_line = action_line[len("Action:"):].strip()
        
    # Khớp tên công cụ và nội dung trong ngoặc
    match = re.match(r"^(\w+)[\[\(](.*)[\]\)]$", action_line)
    if not match:
        return None, None, None
        
    tool_name = match.group(1).strip()
    args_content = match.group(2).strip()
    
    if not args_content:
        return tool_name, [], {}
        
    # Phân tích danh sách đối số, hỗ trợ có/không có dấu nháy và cặp key=val
    pattern = r'(?:\s*(\w+)\s*=)?\s*(?:"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'|([^,]+))'
    matches = re.findall(pattern, args_content)
    
    args = []
    kwargs = {}
    for key, val_dq, val_sq, val_raw in matches:
        val = val_dq or val_sq or val_raw
        if val is None:
            continue
        val = val.strip()
        
        # Nếu có key, lưu dạng keyword argument
        if key:
            kwargs[key] = val
        else:
            args.append(val)
            
    return tool_name, args, kwargs


def run_tool_safely(tool_name: str, args: list, kwargs: dict) -> str:
    """
    Thực thi công cụ một cách an toàn, ánh xạ đối số tự động dựa trên Signature.
    Trả về kết quả chuỗi (Observation) hoặc chuỗi báo lỗi an toàn (không crash).
    """
    if tool_name not in AVAILABLE_TOOLS:
        valid_tools = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Công cụ '{tool_name}' không tồn tại. Các công cụ hợp lệ gồm: {valid_tools}"
        
    func = AVAILABLE_TOOLS[tool_name]
    try:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # Khởi tạo đối số gửi đi
        bound_args = {}
        
        # Gán các đối số vị trí
        for i, val in enumerate(args):
            if i < len(param_names):
                bound_args[param_names[i]] = val
                
        # Ghi đè/bổ sung bằng đối số keyword
        for k, v in kwargs.items():
            bound_args[k] = v
            
        # Kiểm tra và điền giá trị mặc định cho tham số thiếu
        final_args = {}
        for name, param in sig.parameters.items():
            if name in bound_args:
                final_args[name] = bound_args[name]
            elif param.default == inspect.Parameter.empty:
                # Nếu thiếu tham số bắt buộc, truyền chuỗi rỗng để tool xử lý lỗi nghiệp vụ
                final_args[name] = ""
            else:
                # Tham số có giá trị mặc định, bỏ qua để Python tự điền
                pass
                
        # Gọi hàm
        result = func(**final_args)
        return str(result)
    except Exception as e:
        return f"LỖI khi thực thi công cụ '{tool_name}': {str(e)}"


def generate_with_retry(provider, prompt: str, system_prompt: str = "", max_retries: int = 5) -> str:
    """
    Gọi LLM sinh nội dung với cơ chế tự động thử lại khi gặp lỗi 429 RESOURCE_EXHAUSTED (Rate Limit).
    Tích hợp tự động đổi model khi gặp lỗi 403/404 hoặc lỗi quyền truy cập dự án.
    """
    models_progression = ["gemini-1.5-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
    delay = 15
    for attempt in range(max_retries):
        response = provider.generate(prompt, system_prompt=system_prompt)
        
        # Nhận diện lỗi 403 hoặc 404 để tự động nâng cấp/chuyển đổi model
        if "403" in response or "404" in response or "PERMISSION_DENIED" in response or "NOT_FOUND" in response:
            if hasattr(provider, "model_name"):
                current_model = provider.model_name
                if current_model in models_progression:
                    idx = models_progression.index(current_model)
                    if idx + 1 < len(models_progression):
                        next_model = models_progression[idx + 1]
                        print(f"⚠️ Lỗi xác thực/không khả dụng của model '{current_model}'. Đang tự động đổi sang: '{next_model}'...")
                        provider.model_name = next_model
                        # Thử lại ngay lập tức với model mới
                        continue
        
        # Nhận diện lỗi Rate Limit hoặc Quota
        if "429" in response or "RESOURCE_EXHAUSTED" in response:
            print(f"⚠️ [Rate Limit] Hồi đáp bị giới hạn tần suất (429). Đang đợi {delay} giây trước khi thử lại (Lượt {attempt + 1}/{max_retries})...")
            time.sleep(delay)
            delay = min(delay * 2, 60)  # Tăng dần thời gian chờ (exponential backoff)
        else:
            return response
            
    return response


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Đợi giãn cách tối thiểu giữa các kịch bản test để tránh dồn dập
    time.sleep(2)
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = generate_with_retry(provider, user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"\n🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    # Khởi tạo lịch sử ReAct để gửi cho LLM ở mỗi bước lặp
    history = []
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Xây dựng prompt chứa toàn bộ lịch sử ReAct hiện tại
        full_prompt = user_query + "\n"
        if history:
            full_prompt += "\n".join(history) + "\n"
            
        # Đợi giãn cách tối thiểu giữa các lượt để giảm nguy cơ chạm quota
        time.sleep(2)
        
        # Gọi LLM sinh bước suy luận tiếp theo
        response = generate_with_retry(provider, "", system_prompt=REACT_SYSTEM_PROMPT + "\n" + full_prompt)
        
        # Log phản hồi thô của LLM
        print(f"🤖 LLM Response (Raw):\n{response.strip()}")
        
        # Tìm các khối Thought, Action, Final Answer bằng regex
        thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)(?=\n|$)", response)
        final_answer_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
        
        thought_text = thought_match.group(1).strip() if thought_match else ""
        action_text = action_match.group(1).strip() if action_match else ""
        final_answer_text = final_answer_match.group(1).strip() if final_answer_match else ""
        
        # In Thought ra màn hình console
        if thought_text:
            print(f"🧠 Thought: {thought_text}")
            
        # Lưu Thought vào lịch sử
        step_history = []
        if thought_text:
            step_history.append(f"Thought: {thought_text}")
            
        # Nếu LLM trả về câu trả lời cuối cùng hoặc Action có chứa Final Answer
        if final_answer_text:
            print(f"🏁 Final Answer: {final_answer_text}")
            break
        elif "final answer:" in action_text.lower():
            fa_match = re.search(r"(?i)final answer:\s*(.*)", action_text, re.DOTALL)
            if fa_match:
                print(f"🏁 Final Answer (Sửa lỗi format): {fa_match.group(1).strip()}")
                break
            
        # Nếu LLM quyết định hành động gọi Tool
        if action_text:
            print(f"🛠️ Action: {action_text}")
            step_history.append(f"Action: {action_text}")
            
            # Phân tích Action
            tool_name, args, kwargs = parse_action(action_text)
            
            if tool_name:
                # Thực thi công cụ y tế tương ứng
                obs = run_tool_safely(tool_name, args, kwargs)
            else:
                obs = f"LỖI: Không thể phân tích cú pháp Action '{action_text}'. Vui lòng sử dụng định dạng: tên_công_cụ[tham_số_1, tham_số_2, ...]"
                
            print(f"👁️ Observation: {obs}")
            step_history.append(f"Observation: {obs}")
            
            # Cập nhật lịch sử để chuẩn bị cho vòng lặp tiếp theo
            history.extend(step_history)
            
        # Fallback trong trường hợp LLM không sinh đúng format nhưng có phản hồi trực tiếp
        else:
            cleaned_resp = response.strip()
            if cleaned_resp:
                if "final answer:" in cleaned_resp.lower():
                    fa_match = re.search(r"(?i)final answer:\s*(.*)", cleaned_resp, re.DOTALL)
                    if fa_match:
                        print(f"🏁 Final Answer (Tự động sửa): {fa_match.group(1).strip()}")
                        break
                print(f"🏁 Final Answer (Tự động nhận diện): {cleaned_resp}")
                break
            else:
                print("⚠️ Cảnh báo: Phản hồi rỗng từ LLM. Ngắt lặp.")
                break
                
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        fallback_msg = (
            "Tôi xin lỗi, hệ thống chưa thể hoàn thành yêu cầu đặt lịch khám do vượt quá số bước giới hạn cho phép. "
            "Vui lòng cung cấp thêm thông tin rõ ràng hoặc liên hệ hotline y tế VinHealth để được hỗ trợ trực tiếp."
        )
        print(f"🏁 Final Answer (Fallback): {fallback_msg}")


class MedicalMockProvider:
    """Giả lập phản hồi y tế offline để tránh lỗi quota/xác thực API 403/404."""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        if "đau mắt đỏ" in text or "mắt đỏ" in text:
            return """Chào bạn, 

Dựa trên các triệu chứng bạn mô tả (đau mắt đỏ 2 ngày, ngứa, chảy nước mắt và ra nhiều gèn), bạn nên đăng ký khám tại **Khoa Mắt (Nhãn khoa)** của các bệnh viện đa khoa hoặc đến các phòng khám chuyên khoa Mắt uy tín. Bác sĩ chuyên khoa sẽ soi mắt bằng dụng cụ chuyên dùng để chẩn đoán chính xác nguyên nhân (do virus, vi khuẩn hay dị ứng) và kê đơn thuốc phù hợp.

Do tôi là Chatbot AI thông thường và không có công cụ tra cứu lịch hẹn thời gian thực, tôi không thể trực tiếp kiểm tra hay đặt lịch khám giúp bạn. Bạn có thể tự đặt lịch khám qua hotline hoặc website của cơ sở y tế. 

Về chăm sóc tạm thời tại nhà: bạn hãy rửa mắt bằng nước muối sinh lý 0.9% sạch, tránh dụi mắt và dùng riêng khăn mặt để tránh lây nhiễm. Tuyệt đối không tự ý mua thuốc nhỏ mắt chứa kháng sinh hay corticoid khi chưa được bác sĩ khám và chỉ định."""
        
        elif "ngực" in text or "khó thở" in text or "vã mồ hôi" in text:
            return """🚨 **CẢNH BÁO NGUY HIỂM KHẨN CẤP:** 

Triệu chứng đau tức ngực dữ dội, vã mồ hôi hột và khó thở ở người lớn tuổi là biểu hiện cực kỳ nguy hiểm, có nguy cơ cao liên quan đến các vấn đề tim mạch cấp tính như **nhồi máu cơ tim**. 

**Bạn cần gọi ngay cấp cứu 115 hoặc đưa bác đến ngay phòng cấp cứu của bệnh viện gần nhất lập tức!** Không nên trì hoãn hoặc tự di chuyển bằng xe máy nếu tình trạng khó thở nặng hơn.

Tôi xin phép từ chối tiếp nhận thông tin đặt lịch khám thường quy cho ngày mai trong tình huống này, vì sức khỏe và tính mạng của bác cần được can thiệp y tế khẩn cấp ngay bây giờ."""
            
        elif "tai mũi họng" in text or "nguyễn văn a" in text:
            return """Chào bạn, tôi ghi nhận bạn có nhu cầu đặt lịch khám chuyên khoa **Tai Mũi Họng** với **Bác sĩ Nguyễn Văn A** vào sáng thứ 7 tuần này lúc **9:00**.

Tuy nhiên, do tôi là Chatbot baseline không có công cụ truy cập hệ thống thời gian thực, tôi không thể tự tra cứu lịch trực trống của bác sĩ cũng như không thể xác nhận lịch hẹn trực tiếp cho bạn trên hệ thống. 

Để chúng tôi có thể chuyển thông tin này cho nhân viên hỗ trợ đặt lịch liên hệ lại hỗ trợ bạn, bạn vui lòng cung cấp thêm các thông tin sau:
1. **Họ và tên bệnh nhân**
2. **Số điện thoại liên hệ**
3. **Khu vực/Thành phố muốn khám**

Hoặc bạn có thể liên hệ trực tiếp đến hotline của phòng khám/bệnh viện để được xác nhận lịch nhanh chóng nhất."""
            
        elif "da liễu" in text:
            return """Chào bạn, tôi đã ghi nhận nhu cầu muốn đặt lịch khám chuyên khoa **Da liễu** của bạn trong tuần này.

Tuy nhiên, để có thể hỗ trợ đăng ký lịch, thông tin hiện tại vẫn còn thiếu ngày khám cụ thể và khung giờ mong muốn. Bạn vui lòng bổ sung các thông tin sau:
- **Ngày mong muốn khám** (Ví dụ: thứ 5, thứ 6...)
- **Khung giờ thuận tiện** (Buổi sáng hay chiều, giờ cụ thể nếu có)
- **Họ và tên bệnh nhân cùng Số điện thoại liên hệ**

Vì tôi là chatbot thông thường không thể tự truy cập lịch khám trực tiếp, tôi sẽ ghi nhận các thông tin trên và chuyển cho bộ phận CSKH để gọi lại hỗ trợ đặt lịch cho bạn sớm nhất có thể."""
            
        elif "nhi khoa" in text or "bk9823" in text or "đổi" in text:
            return """Chào bạn, tôi đã tiếp nhận yêu cầu đổi lịch hẹn mã số **#BK9823** chuyên khoa Nhi khoa từ 10:00 sáng mai sang **14:00 chiều thứ Sáu**.

Do tôi không được kết nối với cơ sở dữ liệu quản lý lịch hẹn y tế của hệ thống, tôi không thể tự thực hiện thao tác cập nhật hay điều chỉnh thời gian lịch hẹn này trực tiếp giúp bạn. 

Để đổi lịch hẹn thành công và tránh ảnh hưởng đến giờ khám của bé, bạn vui lòng thực hiện một trong các cách sau:
1. Gọi điện đến hotline chăm sóc khách hàng của phòng khám để nhân viên cập nhật mã hẹn.
2. Truy cập ứng dụng y tế của VinHealth nơi bạn đã đăng ký lịch để tự điều chỉnh."""
            
        return "Chào bạn, tôi là Chatbot tư vấn y tế baseline hỗ trợ thông tin tổng quát."


if __name__ == "__main__":
    print("==================================================")
    print("🏥 HỆ THỐNG Y TẾ VINHEALTH - ĐẶT LỊCH & TƯ VẤN CHUYÊN KHOA")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Lựa chọn chạy từ dòng lệnh:
    # - Không truyền tham số: Chạy tất cả Test Cases
    # - Truyền tham số số (0-9): Chạy test case tương ứng
    # - Truyền tham số ID (TC01_...): Chạy test case tương ứng
    
    run_all = True
    target_test = None
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.lower() != "all":
            if arg.isdigit():
                idx = int(arg)
                if 0 <= idx < len(tests):
                    target_test = tests[idx]
                    run_all = False
            else:
                for t in tests:
                    if t["id"].lower() == arg.lower():
                        target_test = t
                        run_all = False
                        break
                        
    if run_all:
        print("🚀 Bắt đầu kiểm thử tự động ghép nối vòng lặp ReAct Agent...")
        for idx, test in enumerate(tests, start=1):
            print(f"\n==================================================")
            print(f"📝 TEST CASE {idx}/{len(tests)}: {test['id']} - {test['description']}")
            print(f"❓ Câu hỏi: {test['user_input']}")
            print(f"==================================================")
            
            print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
            run_baseline_chatbot(test["user_input"], provider)
            
            print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
            run_react_agent(test["user_input"], provider)
            print(f"\n[KẾT THÚC TEST CASE {test['id']}]")
            print("==================================================")
    else:
        if target_test:
            print(f"\n==================================================")
            print(f"📝 CHẠY KIỂM THỬ: {target_test['id']} - {target_test['description']}")
            print(f"❓ Câu hỏi: {target_test['user_input']}")
            print(f"==================================================")
            
            print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
            run_baseline_chatbot(target_test["user_input"], provider)
            
            print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
            run_react_agent(target_test["user_input"], provider)
            print("==================================================")
        else:
            print(f"❌ Lỗi: Không tìm thấy Test Case khớp với tham số '{sys.argv[1]}'.")
