"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool Engineer)
Bộ tool cho chủ đề 6: Đặt lịch khám bệnh & tư vấn chuyên khoa.

Ghi chú:
- Các tool y tế bên dưới là bộ tool chính cho đề tài.
- `get_weather` và `search_flights` được giữ lại như tool mẫu tương thích
  để file `src/app.py` hiện tại không bị vỡ import trước khi Role 4 đồng bộ.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime


def _normalize_text(value: str) -> str:
    """Chuẩn hóa text về lowercase, bỏ dấu và rút gọn khoảng trắng."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _ensure_non_empty(value: str, field_name: str) -> tuple[bool, str]:
    if not isinstance(value, str) or not value.strip():
        return False, f"LỖI: Trường '{field_name}' không được để trống."
    return True, value.strip()


def _valid_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def _valid_time(value: str) -> bool:
    return bool(re.fullmatch(r"\d{2}:\d{2}", value))


def _contains_keyword(text: str, keyword: str) -> bool:
    """Khớp từ khóa theo cụm từ hoặc theo ranh giới từ để tránh bắt nhầm."""
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return bool(re.search(pattern, text))


SPECIALTY_DATABASE = {
    "nội khoa": {
        "keywords": ["noi khoa", "internal medicine", "sot", "met moi", "da day"],
        "description": "Theo dõi bệnh mạn tính, sốt, mệt mỏi, triệu chứng tổng quát.",
        "clinics": ["Phòng khám Nội tổng quát VinHealth", "Bệnh viện Đa khoa An Tâm"],
    },
    "tim mạch": {
        "keywords": ["tim mach", "dau nguc", "tang huyet ap", "hoi hop", "tim dap nhanh"],
        "description": "Khám các vấn đề tim, huyết áp, hồi hộp, đau ngực.",
        "clinics": ["Trung tâm Tim mạch Hòa Bình", "Phòng khám Tim mạch Sức Sống"],
    },
    "da liễu": {
        "keywords": ["da lieu", "ngua", "mun", "phat ban", "viem da", "eczema"],
        "description": "Tư vấn các bệnh về da, tóc, móng và dị ứng ngoài da.",
        "clinics": ["Phòng khám Da liễu Sáng Da", "Trung tâm Da liễu Minh An"],
    },
    "tai mũi họng": {
        "keywords": ["tai mui hong", "viem hong", "viem mui", "dau tai", "nghet mui"],
        "description": "Điều trị viêm tai, mũi, họng, amidan, xoang.",
        "clinics": ["Phòng khám Tai Mũi Họng Tâm An", "Bệnh viện Tai Mũi Họng Thành Phố"],
    },
    "nhi khoa": {
        "keywords": ["tre em", "nhi", "soi sot", "ho", "non", "tieu chay"],
        "description": "Khám và theo dõi sức khỏe trẻ em.",
        "clinics": ["Khoa Nhi Gia Đình", "Phòng khám Nhi Đồng Xanh"],
    },
    "cơ xương khớp": {
        "keywords": ["co xuong khop", "khop", "lung", "cot song", "te tay", "dau goi"],
        "description": "Khám đau khớp, thoái hóa, đau cơ, chấn thương nhẹ.",
        "clinics": ["Phòng khám Cơ Xương Khớp An Bình", "Trung tâm Chấn thương Chỉnh hình"],
    },
    "tiêu hóa": {
        "keywords": ["tieu hoa", "da day", "tieu chay", "buon non", "dau bung", "chua day"],
        "description": "Khám các vấn đề dạ dày, ruột, gan mật cơ bản.",
        "clinics": ["Phòng khám Tiêu hóa Hạnh Phúc", "Trung tâm Gan Mật Tiêu hóa"],
    },
    "sản phụ khoa": {
        "keywords": ["san phu khoa", "phu khoa", "thai ky", "kinh nguyet", "mang thai"],
        "description": "Tư vấn sức khỏe phụ nữ, thai kỳ và sản phụ khoa.",
        "clinics": ["Phòng khám Sản Phụ khoa An Khang", "Trung tâm Chăm sóc Mẹ và Bé"],
    },
}

CARE_LEVEL_GUIDANCE = [
    ("kho thở", "Khuyến nghị: cần đi cấp cứu hoặc gọi hỗ trợ y tế ngay."),
    ("dau nguc", "Khuyến nghị: cần khám khẩn cấp trong ngày."),
    ("ngat", "Khuyến nghị: nên đi cấp cứu hoặc cơ sở y tế gần nhất."),
    ("chay mau", "Khuyến nghị: cần được đánh giá sớm trong ngày."),
    ("sot cao", "Khuyến nghị: nên khám sớm, đặc biệt nếu kéo dài."),
]


def suggest_specialty(symptom_summary: str) -> str:
    """
    Gợi ý chuyên khoa phù hợp dựa trên mô tả triệu chứng.

    Args:
        symptom_summary (str): Mô tả ngắn các triệu chứng hoặc nhu cầu khám.

    Returns:
        str: Chuyên khoa phù hợp nhất, mức độ ưu tiên và lý do gợi ý.
    """
    ok, cleaned = _ensure_non_empty(symptom_summary, "symptom_summary")
    if not ok:
        return cleaned

    normalized = _normalize_text(cleaned)

    for keyword, guidance in CARE_LEVEL_GUIDANCE:
        if _contains_keyword(normalized, keyword):
            return (
                f"TƯ VẤN KHẨN: {guidance} "
                f"Nên ưu tiên đánh giá lâm sàng ngay thay vì tự đặt lịch thường quy."
            )

    best_specialty = None
    best_score = 0
    best_reason = ""

    for specialty, meta in SPECIALTY_DATABASE.items():
        score = 0
        matched = []
        for keyword in meta["keywords"]:
            if _contains_keyword(normalized, keyword):
                score += 1
                matched.append(keyword)
        if score > best_score:
            best_specialty = specialty
            best_score = score
            best_reason = ", ".join(matched)

    if best_specialty:
        meta = SPECIALTY_DATABASE[best_specialty]
        return (
            f"Chuyên khoa gợi ý: {best_specialty}. "
            f"Lý do: {best_reason or meta['description']}. "
            f"Gợi ý bước tiếp theo: đặt lịch khám {best_specialty} để được bác sĩ đánh giá trực tiếp."
        )

    return (
        "Chưa xác định được chuyên khoa chính xác từ mô tả hiện tại. "
        "Nên chọn Nội khoa để sàng lọc ban đầu hoặc cung cấp thêm triệu chứng cụ thể."
    )


def find_specialists(specialty: str, city: str) -> str:
    """
    Tìm danh sách cơ sở/chuyên khoa phù hợp theo nhu cầu khám.

    Args:
        specialty (str): Tên chuyên khoa cần tìm.
        city (str): Thành phố/khu vực muốn khám.

    Returns:
        str: Danh sách gợi ý cơ sở và mô tả ngắn.
    """
    ok_specialty, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok_specialty:
        return specialty_value

    ok_city, city_value = _ensure_non_empty(city, "city")
    if not ok_city:
        return city_value

    specialty_key = _normalize_text(specialty_value)
    matched_specialty = None

    for canonical in SPECIALTY_DATABASE:
        if _normalize_text(canonical) == specialty_key:
            matched_specialty = canonical
            break

    if not matched_specialty:
        return (
            f"LỖI: Chưa có dữ liệu cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    meta = SPECIALTY_DATABASE[matched_specialty]
    clinics = "; ".join(meta["clinics"])
    return (
        f"Chuyên khoa: {matched_specialty} tại {city_value}.\n"
        f"Mô tả: {meta['description']}\n"
        f"Gợi ý cơ sở: {clinics}"
    )


def check_appointment_slots(specialty: str, city: str, date: str) -> str:
    """
    Kiểm tra khung giờ khám còn trống theo chuyên khoa, khu vực và ngày.

    Args:
        specialty (str): Chuyên khoa cần đặt lịch.
        city (str): Khu vực khám.
        date (str): Ngày khám theo định dạng YYYY-MM-DD.

    Returns:
        str: Danh sách slot trống hoặc thông báo lỗi.
    """
    ok_specialty, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok_specialty:
        return specialty_value

    ok_city, city_value = _ensure_non_empty(city, "city")
    if not ok_city:
        return city_value

    ok_date, date_value = _ensure_non_empty(date, "date")
    if not ok_date:
        return date_value
    if not _valid_date(date_value):
        return f"LỖI: Ngày khám '{date_value}' phải theo định dạng YYYY-MM-DD."

    specialty_key = _normalize_text(specialty_value)
    if specialty_key not in {_normalize_text(name) for name in SPECIALTY_DATABASE}:
        return (
            f"LỖI: Chưa có lịch trống cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    slots = ["08:00", "09:30", "13:30", "15:00"]
    slot_text = ", ".join(slots)
    return (
        f"Lịch trống {specialty_value} tại {city_value} ngày {date_value}: {slot_text}. "
        f"Khung giờ 08:00 và 13:30 thường hết nhanh."
    )


def book_medical_appointment(
    patient_name: str,
    specialty: str,
    city: str,
    date: str,
    time: str,
    phone: str = "",
    symptom_summary: str = "",
) -> str:
    """
    Đặt lịch khám bệnh giả lập theo chuyên khoa.

    Args:
        patient_name (str): Tên bệnh nhân.
        specialty (str): Chuyên khoa cần đặt.
        city (str): Thành phố khám.
        date (str): Ngày khám theo YYYY-MM-DD.
        time (str): Giờ khám theo HH:MM.
        phone (str): Số điện thoại liên hệ, không bắt buộc.
        symptom_summary (str): Mô tả triệu chứng ngắn để lưu hồ sơ.

    Returns:
        str: Mã đặt lịch và thông tin xác nhận, hoặc thông báo lỗi.
    """
    fields = [
        ("patient_name", patient_name),
        ("specialty", specialty),
        ("city", city),
        ("date", date),
        ("time", time),
    ]
    normalized_values = {}
    for field_name, raw_value in fields:
        ok, value = _ensure_non_empty(raw_value, field_name)
        if not ok:
            return value
        normalized_values[field_name] = value

    if not _valid_date(normalized_values["date"]):
        return f"LỖI: Ngày khám '{normalized_values['date']}' phải theo định dạng YYYY-MM-DD."
    if not _valid_time(normalized_values["time"]):
        return f"LỖI: Giờ khám '{normalized_values['time']}' phải theo định dạng HH:MM."

    specialty_key = _normalize_text(normalized_values["specialty"])
    if specialty_key not in {_normalize_text(name) for name in SPECIALTY_DATABASE}:
        return (
            f"LỖI: Không hỗ trợ đặt lịch cho chuyên khoa '{normalized_values['specialty']}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    if phone and not re.fullmatch(r"[0-9+\-\s]{8,20}", phone.strip()):
        return "LỖI: Số điện thoại không hợp lệ. Chỉ cho phép chữ số, dấu +, -, và khoảng trắng."

    booking_source = "|".join(
        [
            normalized_values["patient_name"],
            normalized_values["specialty"],
            normalized_values["city"],
            normalized_values["date"],
            normalized_values["time"],
            phone.strip(),
            symptom_summary.strip(),
        ]
    )
    booking_code = hashlib.sha1(booking_source.encode("utf-8")).hexdigest()[:10].upper()
    note = f" Triệu chứng ghi nhận: {symptom_summary.strip()}." if symptom_summary.strip() else ""
    phone_note = f" SĐT: {phone.strip()}." if phone.strip() else ""

    return (
        f"Đặt lịch thành công.\n"
        f"Mã đặt lịch: BK-{booking_code}\n"
        f"Bệnh nhân: {normalized_values['patient_name']}\n"
        f"Chuyên khoa: {normalized_values['specialty']}\n"
        f"Địa điểm: {normalized_values['city']}\n"
        f"Thời gian: {normalized_values['date']} {normalized_values['time']}\n"
        f"Trạng thái: Chờ xác nhận từ cơ sở y tế.{phone_note}{note}"
    )


# -------- Legacy demo tools: giữ tương thích với app hiện tại --------
def get_weather(location: str) -> str:
    """
    Tra cứu thời tiết hiện tại của một thành phố.

    Args:
        location (str): Tên thành phố.

    Returns:
        str: Thông tin thời tiết mô phỏng hoặc thông báo lỗi.
    """
    loc_lower = _normalize_text(location)
    if "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%."
    if "ho chi minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return "Thời tiết TP.HCM: 33°C, Nắng nóng, Có mây."
    if "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, Gió nhẹ, Mát mẻ."
    return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


def search_flights(origin: str, destination: str) -> str:
    """
    Tra cứu chuyến bay giữa hai địa điểm.

    Args:
        origin (str): Nơi đi.
        destination (str): Nơi đến.

    Returns:
        str: Danh sách chuyến bay mô phỏng.
    """
    ok_origin, origin_value = _ensure_non_empty(origin, "origin")
    if not ok_origin:
        return origin_value
    ok_destination, destination_value = _ensure_non_empty(destination, "destination")
    if not ok_destination:
        return destination_value

    return (
        f"Chuyến bay từ {origin_value} -> {destination_value} ngày mai:\n"
        f"1. VN123 (08:00) - Giá: 1,500,000 VNĐ (Còn vé)\n"
        f"2. VJ456 (14:30) - Giá: 1,200,000 VNĐ (Còn vé)"
    )


AVAILABLE_TOOLS = {
    "suggest_specialty": suggest_specialty,
    "find_specialists": find_specialists,
    "check_appointment_slots": check_appointment_slots,
    "book_medical_appointment": book_medical_appointment,
    "get_weather": get_weather,
    "search_flights": search_flights,
}
