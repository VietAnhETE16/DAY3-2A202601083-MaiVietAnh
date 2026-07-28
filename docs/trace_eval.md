# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Role 5 – Observability | Đề tài 6: Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa*

---

## 🎯 MỐC 1 — BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

> **Câu hỏi trọng tâm**: Bài toán "Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa" có CẦN dùng ReAct Agent không, hay Chatbot thuần là đủ?

### Bảng đánh giá độ phù hợp (Agentic Fit)

| # | Tiêu chí | Điểm (1–5) | Lý do đánh giá |
| :-: | :--- | :---: | :--- |
| 1 | 🧠 **Multi-step Reasoning** | `5/5` | Người dùng mô tả triệu chứng → Agent cần suy luận chuyên khoa phù hợp → tra lịch bác sĩ → xác nhận đặt lịch. Ít nhất 3 bước liên tiếp phụ thuộc nhau. |
| 2 | 🛠️ **Tool Interaction** | `5/5` | Cần gọi tool thực tế: tra chuyên khoa theo triệu chứng, kiểm tra lịch bác sĩ còn trống, đặt lịch khám. Không có tool thì mọi thông tin đều là bịa đặt. |
| 3 | 🔀 **Dynamic Decision** | `5/5` | Kết quả bước trước hoàn toàn quyết định bước sau: nếu bác sĩ A không còn slot → chuyển sang bác sĩ B; nếu chuyên khoa X không phù hợp → gợi ý chuyên khoa Y. |
| 4 | ⏳ **Long Horizon** | `4/5` | Quy trình có thể kéo dài 3–5 bước (hỏi triệu chứng → gợi ý chuyên khoa → kiểm tra lịch → xác nhận đặt → thông báo xác nhận). |
| | **TỔNG ĐIỂM FIT** | **19/20** | ✅ **KẾT LUẬN: BÀI TOÁN BẮT BUỘC PHẢI DÙNG REACT AGENT!** |

### Phân tích chi tiết: Tại sao Chatbot thuần KHÔNG đủ?

| Tình huống người dùng | Chatbot thuần làm được? | ReAct Agent làm được? |
| :--- | :---: | :---: |
| "Tôi bị đau đầu chóng mặt, nên khám chuyên khoa gì?" | ⚠️ Chỉ trả lời chung chung, không tra cứu dữ liệu thực | ✅ Gọi `get_specialty_by_symptom()` → trả kết quả có bằng chứng |
| "Bác sĩ Nguyễn còn lịch ngày mai không?" | ❌ Bịa số liệu / từ chối trả lời | ✅ Gọi `check_doctor_schedule()` → trả lịch thực tế |
| "Đặt cho tôi lịch khám lúc 9h sáng thứ 3" | ❌ Không thể thực thi hành động đặt lịch | ✅ Gọi `book_appointment()` → xác nhận đặt thật |
| "Bác sĩ A hết slot, đổi sang bác sĩ B được không?" | ❌ Không biết slot trống, không thể quyết định linh hoạt | ✅ Vòng lặp Thought → Action → Observation tự điều chỉnh |

### Danh sách Tool dự kiến (Role 2 sẽ implement)

| Tên Tool | Input | Output | Mục đích |
| :--- | :--- | :--- | :--- |
| `get_specialty_by_symptom(symptom)` | Triệu chứng (str) | Tên chuyên khoa phù hợp | Tư vấn khám đúng nơi |
| `check_doctor_schedule(specialty, date)` | Chuyên khoa + ngày | Danh sách slot trống của bác sĩ | Tra lịch bác sĩ còn trống |
| `book_appointment(doctor_id, patient_name, date, time)` | ID bác sĩ + tên BN + ngày + giờ | Mã xác nhận đặt lịch | Đặt lịch khám chính thức |
| `get_doctor_info(doctor_id)` | ID bác sĩ | Hồ sơ bác sĩ (tên, chuyên khoa, kinh nghiệm) | Cung cấp thông tin để người dùng lựa chọn |

---

## 📝 MỐC 2 — PHẢN HỒI CHATBOT BASELINE

*(Sẽ cập nhật sau khi Role 3 & Role 4 hoàn thành Chatbot Baseline)*

---

## 🔍 MỐC 3 — TRACE LOG REACT AGENT

*(Sẽ cập nhật sau khi Role 4 hoàn thành ReAct Agent Loop)*

### Template Trace (sẽ điền sau)

```
[Test Case #X] — <tên câu hỏi>
Question: ...

Thought 1: ...
Action 1: tool_name["param"]
Observation 1: ...

Final Answer: ...
```

---

## 📊 MỐC 3 — BẢNG SCORING MATRIX (0–2 điểm mỗi tiêu chí)

*(Sẽ cập nhật sau khi chạy đủ 5 Test Cases)*

| Test Case | Factual Correctness | Grounding | Tool Selection | Termination | **Tổng** |
| :---: | :---: | :---: | :---: | :---: | :---: |
| TC-1 🟢 Đơn giản | — | — | — | — | —/8 |
| TC-2 🟢 Đơn giản | — | — | — | — | —/8 |
| TC-3 🟡 Multi-step | — | — | — | — | —/8 |
| TC-4 🟡 Multi-step 2 tool | — | — | — | — | —/8 |
| TC-5 🔴 Edge Case / Bẫy | — | — | — | — | —/8 |
| **TỔNG** | — | — | — | — | **—/40** |

---

## ⚔️ MỐC 4 — HYBRID FLOWCHART

*(Xem file `docs/hybrid_flowchart.mermaid`)*
