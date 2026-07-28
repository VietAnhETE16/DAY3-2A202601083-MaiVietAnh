"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool Engineer)
Bộ tool cho chủ đề 6: Đặt lịch khám bệnh & tư vấn chuyên khoa.

Ghi chú:
- Các tool y tế bên dưới là bộ tool chính cho đề tài.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta


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


def _match_specialty(specialty: str) -> str | None:
    specialty_key = _normalize_text(specialty)
    for canonical in SPECIALTY_DATABASE:
        if _normalize_text(canonical) == specialty_key:
            return canonical
    return None


def _valid_booking_code(value: str) -> bool:
    return bool(re.fullmatch(r"BK-[A-F0-9]{10}", value.strip().upper()))


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

DOCTOR_DATABASE = {
    "nội khoa": [
        {"name": "BS. Nguyễn Minh An", "level": "Thạc sĩ", "years": 12, "rating": 4.8},
        {"name": "BS. Trần Thu Hà", "level": "Chuyên khoa I", "years": 9, "rating": 4.7},
    ],
    "tim mạch": [
        {"name": "BS. Lê Quốc Bảo", "level": "Chuyên khoa II", "years": 15, "rating": 4.9},
        {"name": "BS. Phạm Hoài Nam", "level": "Thạc sĩ", "years": 11, "rating": 4.8},
    ],
    "da liễu": [
        {"name": "BS. Võ Ngọc Linh", "level": "Chuyên khoa I", "years": 8, "rating": 4.7},
        {"name": "BS. Đặng Minh Châu", "level": "Thạc sĩ", "years": 10, "rating": 4.8},
    ],
    "tai mũi họng": [
        {"name": "BS. Huỳnh Gia Khang", "level": "Chuyên khoa I", "years": 7, "rating": 4.6},
        {"name": "BS. Bùi Thanh Tâm", "level": "Thạc sĩ", "years": 13, "rating": 4.8},
    ],
    "nhi khoa": [
        {"name": "BS. Mai Phương Anh", "level": "Chuyên khoa II", "years": 14, "rating": 4.9},
        {"name": "BS. Đỗ Hoàng Phúc", "level": "Chuyên khoa I", "years": 8, "rating": 4.7},
    ],
    "cơ xương khớp": [
        {"name": "BS. Vũ Thành Đạt", "level": "Thạc sĩ", "years": 12, "rating": 4.8},
        {"name": "BS. Cao Minh Đức", "level": "Chuyên khoa I", "years": 10, "rating": 4.7},
    ],
    "tiêu hóa": [
        {"name": "BS. Phan Nhật Minh", "level": "Chuyên khoa II", "years": 16, "rating": 4.9},
        {"name": "BS. Lâm Bảo Ngọc", "level": "Thạc sĩ", "years": 9, "rating": 4.7},
    ],
    "sản phụ khoa": [
        {"name": "BS. Nguyễn Hoàng Yến", "level": "Chuyên khoa II", "years": 15, "rating": 4.9},
        {"name": "BS. Trịnh Mỹ Duyên", "level": "Thạc sĩ", "years": 11, "rating": 4.8},
    ],
}

SPECIALTY_PRICE_RANGE = {
    "nội khoa": (150000, 350000),
    "tim mạch": (250000, 600000),
    "da liễu": (180000, 450000),
    "tai mũi họng": (180000, 400000),
    "nhi khoa": (200000, 450000),
    "cơ xương khớp": (220000, 550000),
    "tiêu hóa": (250000, 650000),
    "sản phụ khoa": (250000, 700000),
}

INSURANCE_PARTNERS = {
    "bảo việt": "Hỗ trợ bảo lãnh viện phí tại quầy tiếp nhận.",
    "pvi": "Hỗ trợ xác minh quyền lợi trước khi khám.",
    "bảo minh": "Có thể áp dụng thanh toán một phần theo gói bảo hiểm.",
    "vbi": "Hỗ trợ hồ sơ bồi thường sau khám.",
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


def list_specialties() -> str:
    """Liệt kê các chuyên khoa đang hỗ trợ."""
    lines = []
    for specialty, meta in SPECIALTY_DATABASE.items():
        lines.append(f"- {specialty}: {meta['description']}")
    return "Danh sách chuyên khoa hỗ trợ:\n" + "\n".join(lines)


def get_specialty_details(specialty: str) -> str:
    """Trả về mô tả, cơ sở gợi ý và từ khóa nhận diện cho một chuyên khoa."""
    ok, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có dữ liệu cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    meta = SPECIALTY_DATABASE[matched]
    keywords = ", ".join(meta["keywords"])
    clinics = "; ".join(meta["clinics"])
    return (
        f"Chuyên khoa: {matched}\n"
        f"Mô tả: {meta['description']}\n"
        f"Từ khóa: {keywords}\n"
        f"Gợi ý cơ sở: {clinics}"
    )


def estimate_consultation_fee(specialty: str, city: str = "") -> str:
    """Ước tính khoảng phí khám ban đầu theo chuyên khoa."""
    ok, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có bảng phí cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    min_fee, max_fee = SPECIALTY_PRICE_RANGE.get(matched, (150000, 500000))
    city_note = f" tại {city.strip()}" if city.strip() else ""
    return (
        f"Ước tính phí khám {matched}{city_note}: "
        f"{min_fee:,} - {max_fee:,} VNĐ."
    )


def list_doctors_by_specialty(specialty: str) -> str:
    """Liệt kê bác sĩ mẫu theo chuyên khoa."""
    ok, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có dữ liệu bác sĩ cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    doctors = DOCTOR_DATABASE.get(matched, [])
    if not doctors:
        return f"Chưa có danh sách bác sĩ mẫu cho chuyên khoa {matched}."

    lines = []
    for idx, doctor in enumerate(doctors, start=1):
        lines.append(
            f"{idx}. {doctor['name']} - {doctor['level']} - {doctor['years']} năm kinh nghiệm - "
            f"đánh giá {doctor['rating']}/5"
        )
    return f"Danh sách bác sĩ gợi ý cho {matched}:\n" + "\n".join(lines)


def prepare_before_visit(specialty: str, symptoms: str = "") -> str:
    """Gợi ý việc cần chuẩn bị trước khi đi khám."""
    ok, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có hướng dẫn chuẩn bị cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    base_items = [
        "CCCD hoặc giấy tờ tùy thân",
        "Bảo hiểm y tế/bảo hiểm tư nhân nếu có",
        "Danh sách thuốc đang dùng",
        "Kết quả xét nghiệm hoặc chẩn đoán cũ",
    ]
    if symptoms.strip():
        base_items.append(f"Ghi chú triệu chứng: {symptoms.strip()}")
    if matched in {"nội khoa", "tiêu hóa"}:
        base_items.append("Nên nhịn ăn nếu được cơ sở y tế yêu cầu trước khi làm xét nghiệm")
    elif matched in {"sản phụ khoa", "nhi khoa"}:
        base_items.append("Mang theo sổ khám thai hoặc sổ tiêm chủng nếu có")

    return "Chuẩn bị trước khi khám:\n" + "\n".join(f"- {item}" for item in base_items)


def teleconsultation_available(specialty: str) -> str:
    """Thông báo khả năng tư vấn từ xa cho chuyên khoa."""
    ok, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có dữ liệu tư vấn online cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    supported = {
        "nội khoa",
        "da liễu",
        "tai mũi họng",
        "tiêu hóa",
        "sản phụ khoa",
    }
    if matched in supported:
        return (
            f"Chuyên khoa {matched} hỗ trợ tư vấn từ xa cho các tình huống theo dõi ban đầu "
            f"hoặc tái khám đơn giản."
        )
    return f"Chuyên khoa {matched} nên ưu tiên khám trực tiếp trước khi tư vấn từ xa."


def reschedule_appointment(booking_code: str, new_date: str, new_time: str) -> str:
    """Đổi lịch hẹn theo mã đặt lịch giả lập."""
    ok_code, code_value = _ensure_non_empty(booking_code, "booking_code")
    if not ok_code:
        return code_value
    if not _valid_booking_code(code_value):
        return "LỖI: Mã đặt lịch không hợp lệ. Định dạng phải là BK-XXXXXXXXXX."

    ok_date, date_value = _ensure_non_empty(new_date, "new_date")
    if not ok_date:
        return date_value
    if not _valid_date(date_value):
        return f"LỖI: Ngày mới '{date_value}' phải theo định dạng YYYY-MM-DD."

    ok_time, time_value = _ensure_non_empty(new_time, "new_time")
    if not ok_time:
        return time_value
    if not _valid_time(time_value):
        return f"LỖI: Giờ mới '{time_value}' phải theo định dạng HH:MM."

    return (
        f"Đổi lịch thành công.\n"
        f"Mã đặt lịch: {code_value.upper()}\n"
        f"Thời gian mới: {date_value} {time_value}\n"
        f"Trạng thái: Đã ghi nhận yêu cầu đổi lịch, chờ cơ sở y tế xác nhận."
    )


def cancel_appointment(booking_code: str, reason: str = "") -> str:
    """Hủy lịch hẹn giả lập."""
    ok_code, code_value = _ensure_non_empty(booking_code, "booking_code")
    if not ok_code:
        return code_value
    if not _valid_booking_code(code_value):
        return "LỖI: Mã đặt lịch không hợp lệ. Định dạng phải là BK-XXXXXXXXXX."

    note = f" Lý do: {reason.strip()}." if reason.strip() else ""
    return (
        f"Hủy lịch thành công.\n"
        f"Mã đặt lịch: {code_value.upper()}\n"
        f"Trạng thái: Lịch hẹn đã bị hủy.{note}"
    )


def appointment_reminder(patient_name: str, date: str, time: str, specialty: str = "") -> str:
    """Tạo nhắc lịch khám."""
    ok_name, name_value = _ensure_non_empty(patient_name, "patient_name")
    if not ok_name:
        return name_value
    ok_date, date_value = _ensure_non_empty(date, "date")
    if not ok_date:
        return date_value
    if not _valid_date(date_value):
        return f"LỖI: Ngày nhắc lịch '{date_value}' phải theo định dạng YYYY-MM-DD."
    ok_time, time_value = _ensure_non_empty(time, "time")
    if not ok_time:
        return time_value
    if not _valid_time(time_value):
        return f"LỖI: Giờ nhắc lịch '{time_value}' phải theo định dạng HH:MM."

    specialty_note = f" chuyên khoa {specialty.strip()}" if specialty.strip() else ""
    return (
        f"Nhắc lịch cho {name_value}{specialty_note}: {date_value} lúc {time_value}. "
        f"Vui lòng đến sớm 15 phút và mang theo giấy tờ cần thiết."
    )


def clinic_directions(city: str, specialty: str) -> str:
    """Gợi ý địa điểm khám theo khu vực và chuyên khoa."""
    ok_city, city_value = _ensure_non_empty(city, "city")
    if not ok_city:
        return city_value
    ok_spec, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok_spec:
        return specialty_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có dữ liệu cơ sở cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    clinics = "; ".join(SPECIALTY_DATABASE[matched]["clinics"])
    return f"Gợi ý cơ sở khám {matched} tại {city_value}: {clinics}."


def insurance_support(provider: str) -> str:
    """Tra cứu hỗ trợ bảo hiểm mẫu."""
    ok, provider_value = _ensure_non_empty(provider, "provider")
    if not ok:
        return provider_value

    normalized = _normalize_text(provider_value)
    for key, policy in INSURANCE_PARTNERS.items():
        if key in normalized:
            return f"Nhà bảo hiểm {provider_value}: {policy}"
    return (
        f"Chưa có cấu hình hỗ trợ cho '{provider_value}'. "
        f"Đơn vị hiện có: {', '.join(INSURANCE_PARTNERS.keys())}."
    )


def validate_symptom_urgency(symptom_summary: str) -> str:
    """Đánh giá sơ bộ mức độ khẩn cấp từ mô tả triệu chứng."""
    ok, cleaned = _ensure_non_empty(symptom_summary, "symptom_summary")
    if not ok:
        return cleaned

    normalized = _normalize_text(cleaned)
    for keyword, guidance in CARE_LEVEL_GUIDANCE:
        if _contains_keyword(normalized, keyword):
            return f"Mức độ ưu tiên: cao. {guidance}"
    return "Mức độ ưu tiên: thường quy. Có thể đặt lịch khám chuyên khoa phù hợp."


def next_available_dates(specialty: str, city: str) -> str:
    """Trả về ngày khám giả lập sắp tới cho chuyên khoa."""
    ok_spec, specialty_value = _ensure_non_empty(specialty, "specialty")
    if not ok_spec:
        return specialty_value
    ok_city, city_value = _ensure_non_empty(city, "city")
    if not ok_city:
        return city_value

    matched = _match_specialty(specialty_value)
    if not matched:
        return (
            f"LỖI: Chưa có lịch cho chuyên khoa '{specialty_value}'. "
            f"Các chuyên khoa hợp lệ gồm: {', '.join(SPECIALTY_DATABASE.keys())}."
        )

    today = datetime.now().date()
    results = []
    for offset in (1, 3, 5):
        candidate = today + timedelta(days=offset)
        results.append(candidate.strftime("%Y-%m-%d"))

    return (
        f"Ngày gợi ý còn trống cho {matched} tại {city_value}: "
        f"{', '.join(results)}."
    )


AVAILABLE_TOOLS = {
    "suggest_specialty": suggest_specialty,
    "find_specialists": find_specialists,
    "check_appointment_slots": check_appointment_slots,
    "book_medical_appointment": book_medical_appointment,
    "list_specialties": list_specialties,
    "get_specialty_details": get_specialty_details,
    "estimate_consultation_fee": estimate_consultation_fee,
    "list_doctors_by_specialty": list_doctors_by_specialty,
    "prepare_before_visit": prepare_before_visit,
    "teleconsultation_available": teleconsultation_available,
    "reschedule_appointment": reschedule_appointment,
    "cancel_appointment": cancel_appointment,
    "appointment_reminder": appointment_reminder,
    "clinic_directions": clinic_directions,
    "insurance_support": insurance_support,
    "validate_symptom_urgency": validate_symptom_urgency,
    "next_available_dates": next_available_dates,
}
