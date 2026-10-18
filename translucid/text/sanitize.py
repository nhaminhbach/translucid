import hashlib
import json
import re
import unicodedata
from typing import Any

# Terminology Purge Mappings (Constitution Alignment)
BANNED_TERM_MAPPINGS = {
    r"\bphốt\b": "đánh giá",
    r"\bbài\s+phốt\b": "bài đánh giá",
    r"\bcựu\s+người\s+thuê\b": "người thuê cũ",
}

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe00-\ufe0f]",
    flags=re.UNICODE
)

def strip_emojis(text: str) -> str:
    """Strips Unicode emojis and graphical icons to maintain clean typography."""
    if not text:
        return ""
    return EMOJI_PATTERN.sub('', text)

def normalize_unicode_text(text: str) -> str:
    """Normalizes Mathematical Alphanumeric Symbols (bold/italic) and fullwidth forms to standard text."""
    if not text:
        return ""
    return unicodedata.normalize('NFKC', text)

# Lexicon for Profanity / Ad-Hominem Insults -> [[profanity:***]]
PROFANITY_PATTERNS = [
    # Slang / abbreviations (guard 'đ' so it does not match 'đ/c', 'đ.c', or 'địa chỉ' abbreviations)
    r"\b(?:đhs|đbh|dhs|dbh)\b",
    r"\bđ\b(?!\s*[/.:])",
    r"\b(?:dm|đm|đcm|dcm|đmm|đume|dume|đmẹ|đụ\s+mẹ|địt\s+mẹ|kệ\s+mẹ|kệ\s+mọe|đèo\s+mọe|bố\s+m|bố\s+mày)\b",
    r"\b(?:qq|quần\s+què|cmn|loz|sặc\s+cục|sục\s+cặc)\b",
    r"\b(?:vãi|vcl|vkl|vailon|vai\s+lon|vl|vch|qtf)\b",
    r"\b(?:hãm|hãm\s+l|hãm\s+lol|hãm\s+lồn|hãm\s+vcl|haml|lỗ\s+hãm\s+cành\s+cạch|lo\s+ham\s+canh\s+cach)\b",
    r"(?<!nuôi\s)(?<!chăm\s)(?<!nuôi\s\d\s)(?<!nuôi\smột\s)\b(?:chó\s+má|đồ\s+chó|lũ\s+chó|thằng\s+chó|chó\s+đẻ|chó\s+chết|súc\s+vật)\b",
    r"\b(?:mất\s+dạy|khốn\s+nạn|vô\s+học|thất\s+đức|đốn\s+mạt|đểu\s+cáng|vô\s+liêm\s+sỉ)\b",
    r"\b(?:bẩn\s+tính|tiểu\s+nhân|bố\s+láo|biến\s+thái|thiểu\s+năng|ác\s+hơn\s+khơ\s+me\s+đỏ)\b",
    r"\b(?:đĩ|lồn|cặc|buồi|đéo|đéoo|cutws|dâm)\b",
]

# Lexicon for Criminal Accusations -> [[claim:concise civil terminology]]
CIVIL_CLAIM_MAPPINGS = [
    # Penal Code criminal offenses & aggravated allegations (must be checked first)
    (r"\b(?:lừa\s+đảo\s+)?chiếm\s+đoạt\s+(?:tiền\s+|tài\s+sản\s+)?chuyên\s+nghiệp\b", "[[claim:giữ tài sản trái thỏa thuận]]"),
    (r"\b(?:lừa\s+đảo\s+)?chiếm\s+đoạt\s+(?:tiền|tài\s+sản)?\b", "[[claim:giữ tài sản trái thỏa thuận]]"),
    (r"\bchiếm\s+đoạt(?:\s+chuyên\s+nghiệp)?\b", "[[claim:giữ tài sản trái thỏa thuận]]"),
    (r"\bcưỡng\s+đoạt\s+(?:tiền|tài\s+sản)?\b", "[[claim:yêu cầu tài chính trái cam kết]]"),
    (r"\btống\s+tiền\b", "[[claim:yêu cầu tài chính trái cam kết]]"),
    (r"\b(?:trốn|né)\s+thuế\b", "[[claim:nghĩa vụ tài chính]]"),
    (r"\b(?:câu|ăn\s+gian)\s+(?:số\s+)?điện\b", "[[claim:chỉ số điện bất thường]]"),
    (r"\b(?:đấm|đánh)\s+(?:cả\s+)?khách\b", "[[claim:hành vi xô xát]]"),
    (r"\b(?:lấy|giữ)\s+(?:giấy\s+tờ\s+)?(?:cccd|cmnd|căn\s+cước)\b", "[[claim:giữ giấy tờ tùy thân]]"),
    (r"\bgiấy\s+tờ(?:\s+tạm\s+trú)?\s+giả\b", "[[claim:tính xác thực giấy tờ]]"),
    (r"\bkhoá\s+(?:cửa\s+)?(?:nhốt|ngoài)\b", "[[claim:hạn chế di chuyển]]"),
    (r"\b(?:nhốt|giam)\s+(?:lại|người)?\b", "[[claim:hạn chế di chuyển]]"),
    (r"\blừa\s+(?:sv|sinh\s+viên)\b", "[[claim:sai cam kết hợp đồng]]"),
    (r"\bđe\s+(?:dọa|doạ)(?:\s+giết\s+người)?\b", "[[claim:gây áp lực tinh thần]]"),
    (r"\bdọa\s+nạt\b", "[[claim:gây áp lực tinh thần]]"),
    (r"\bgian\s+lận\b", "[[claim:không minh bạch]]"),

    # Deposit withholding
    (r"\b(?:quỵt|quịt)\s+(?:tiền\s+)?cọc\b", "[[claim:không hoàn cọc]]"),
    (r"\bbùng\s+cọc\b", "[[claim:không hoàn cọc]]"),
    (r"\bnuốt\s+cọc\b", "[[claim:không hoàn cọc]]"),
    (r"\bcướp\s+cọc\b", "[[claim:không hoàn cọc]]"),
    (r"\b(?:quỵt|quịt)\s+tiền\b", "[[claim:không trả tiền cọc]]"),
    (r"\b(?:quỵt|quịt)\b", "[[claim:không hoàn tiền]]"),
    
    # Financial gouging & unagreed fees
    (r"\băn\s+chặn\s+(?:tiền\s+)?(?:cọc|phí)?\b", "[[claim:thu phí không rõ ràng]]"),
    (r"\băn\s+cướp\b", "[[claim:tính phí bất hợp lý]]"),
    (r"\blừa\s+đảo(?:\s+chuyên\s+nghiệp)?\b", "[[claim:sai cam kết ban đầu]]"),
    (r"\blừa\s+đảo\b", "[[claim:sai cam kết ban đầu]]"),
    (r"\bchặt\s+chém\b", "[[claim:thu phí quá cao]]"),
    (r"\bđiện\s+ảo\b", "[[claim:chỉ số điện bất thường]]"),
    (r"\bnước\s+ảo\b", "[[claim:chỉ số nước bất thường]]"),
    
    # Personal privacy / physical violations
    (r"\bvuốt\s+đùi\b", "[[claim:hành vi khiếm nhã]]"),
    (r"\bquấy\s+rối\b", "[[claim:hành vi khiếm nhã]]"),
    (r"\bquay\s+lén\b", "[[claim:xâm phạm riêng tư]]"),
    (r"\bnhìn\s+trộm\b", "[[claim:xâm phạm riêng tư]]"),
    (r"\bcạy\s+cửa\s+(?:vào\s+phòng)?\b", "[[claim:vào phòng khi chưa đồng ý]]"),
    (r"\bxông\s+vào\s+phòng\b", "[[claim:vào phòng khi chưa đồng ý]]"),
    (r"\bvào\s+phòng\s+tự\s+ý\b", "[[claim:vào phòng khi chưa đồng ý]]"),
    (r"\btự\s+ý\s+vào\s+phòng\b", "[[claim:vào phòng khi chưa đồng ý]]"),
    (r"\bđánh\s+người\b", "[[claim:hành vi xô xát]]"),
]

PHONE_REGEX = re.compile(r'(?:\+84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9\d)(?:[\s.\-]?\d){7,8}\b')

def mask_phone_number(text: str) -> str:
    """Masks Vietnamese mobile phone numbers to format [[pii:098***4321]]."""
    if not text:
        return ""
    
    def repl(m: re.Match) -> str:
        raw = m.group(0)
        digits = re.sub(r'[^\d+]', '', raw)
        if digits.startswith('+84'):
            digits = '0' + digits[3:]
        elif digits.startswith('84'):
            digits = '0' + digits[2:]
        if len(digits) >= 10:
            masked = digits[:3] + '***' + digits[-4:]
            return f"[[pii:{masked}]]"
        return raw

    return PHONE_REGEX.sub(repl, text)

def neutralize_profanity(text: str) -> str:
    """Replaces vulgar and ad-hominem insult patterns with [[profanity:***]]."""
    if not text:
        return ""
    clean = text
    for pattern in PROFANITY_PATTERNS:
        clean = re.sub(pattern, "[[profanity:***]]", clean, flags=re.IGNORECASE)
    return clean

def neutralize_accusations(text: str) -> str:
    """Converts criminal accusations into concise civil dispute shortcodes."""
    if not text:
        return ""
    clean = text
    for pattern, replacement in CIVIL_CLAIM_MAPPINGS:
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
    return clean

EXCLUDED_NAME_TOKENS = {
    "quản", "lý", "lí", "quản lý", "quản lí", "chủ", "chủ nhà", "chủ trọ", 
    "bảo vệ", "bảo kê", "người", "người thuê", "khách", "khách thuê", 
    "sinh viên", "sv", "xe", "phòng", "nhà", "trọ", "scoopy", "vision", 
    "lead", "sh", "wave", "bố", "mẹ", "ông", "bà", "anh", "chị", "em",
    "bạn", "nó", "chúng", "tụi", "đứa", "đội", "nhóm", "lừa", "đảo", "quỵt"
}

def redact_personal_names(text: str, names: list[str] | None = None) -> str:
    """Replaces mentions of named landlords/managers with generic functional titles or [[pii:***]]."""
    if not text:
        return ""
    clean = text
    
    # Redact common contextual name triggers first
    contextual_patterns = [
        (r'(chủ\s+trọ\s+tên\s+(?:là\s+)?)([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)?)', r'\1[[pii:***]]'),
        (r'(chủ\s+nhà\s+tên\s+(?:là\s+)?)([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)?)', r'\1[[pii:***]]'),
        (r'(quản\s+lý\s+tên\s+(?:là\s+)?)([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)?)', r'\1[[pii:***]]'),
        (r'(bác\s+chủ\s+tên\s+(?:là\s+)?)([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)?)', r'\1[[pii:***]]'),
    ]
    for pat, repl in contextual_patterns:
        clean = re.sub(pat, repl, clean, flags=re.IGNORECASE)

    # Safe replacement for 'thằng/mụ <Tên>' avoiding role nouns like 'quản lý' or vehicles like 'Scoopy'
    def replace_thang_mu(match: re.Match) -> str:
        prefix = match.group(1)
        name_candidate = match.group(2).strip()
        words = name_candidate.split()
        if any(w.lower() in EXCLUDED_NAME_TOKENS for w in words):
            return match.group(0)
        if not all(w[0].isupper() for w in words):
            return match.group(0)
        return f"{prefix} [[pii:***]]"

    clean = re.sub(r'\b(thằng|con\s+mụ|mụ|bác|chú|cô|anh|chị)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)?)\b', replace_thang_mu, clean)

    # Redact explicit named individuals passed from NER
    if names:
        for name in names:
            name_clean = name.strip()
            if len(name_clean) >= 2 and name_clean.lower() not in EXCLUDED_NAME_TOKENS and name_clean.lower() not in ("hà nội", "sài gòn", "cọc"):
                pattern = r'(?:\b|\s)' + re.escape(name_clean) + r'(?:\b|\s|[!?,.])'
                clean = re.sub(pattern, " [[pii:***]] ", clean, flags=re.IGNORECASE)

    # Clean up accidental double shortcodes or whitespace
    clean = re.sub(r'(\[\[pii:\*\*\*\]\]\s*)+', r'[[pii:***]] ', clean)
    return clean.strip()

def sanitize_review_text(
    content: str,
    target_phone: str | None = None,
    personal_names: list[str] | None = None,
    profane_words: list[str] | None = None,
    accusation_phrases: list[str] | None = None,
) -> str:
    """
    Master sanitizer transforming volatile, accusatory social text into neutral, 
    interactive shortcode copy with factual event descriptions and PII masking.
    """
    if not content:
        return ""
    
    clean = sanitize_content(content)
    
    # 1. Mask Phone numbers
    clean = mask_phone_number(clean)
    if target_phone:
        # Also ensure specific target_phone string is masked if still lingering in any raw format
        clean_target = re.sub(r'[^\d+]', '', target_phone)
        if len(clean_target) >= 9:
            masked = clean_target[:3] + '***' + clean_target[-4:]
            clean = clean.replace(target_phone, f"[[pii:{masked}]]")
    
    # 2. Redact personal names
    clean = redact_personal_names(clean, personal_names)
    
    # 3. Neutralize criminal accusations into concise civil terminology
    clean = neutralize_accusations(clean)
    if accusation_phrases:
        for phrase in accusation_phrases:
            p_strip = phrase.strip()
            if len(p_strip) >= 3:
                clean = re.sub(r'(?:\b|\s)' + re.escape(p_strip) + r'(?:\b|\s|[!?,.])', " [[claim:không hoàn cọc]] ", clean, flags=re.IGNORECASE)

    # 4. Neutralize profanity and insults
    clean = neutralize_profanity(clean)
    if profane_words:
        for w in profane_words:
            w_strip = w.strip()
            if len(w_strip) >= 2:
                clean = re.sub(r'(?:\b|\s)' + re.escape(w_strip) + r'(?:\b|\s|[!?,.])', " [[profanity:***]] ", clean, flags=re.IGNORECASE)

    # 5. Tag Enforcer & Malformed Tag Repair
    # Force ANY profanity tag content to be strictly *** and fix boundary defects
    clean = re.sub(r'h?\[\[profanity:[^\]]+\]\](?:m|l|loz|oz)?', '[[profanity:***]]', clean)
    # Unnest tags
    clean = re.sub(r'\[\[claim:[^\]]*\[\[claim:([^\]]+)\]\][^\]]*\]\]', r'[[claim:\1]]', clean)
    clean = re.sub(r'\[\[profanity:[^\]]*\[\[profanity:([^\]]+)\]\][^\]]*\]\]', r'[[profanity:***]]', clean)
    clean = re.sub(r'\[\[(pii|profanity|claim):\s*\[\[(?:pii|profanity|claim):([^\]]+)\]\]\s*\]\]', r'[[\1:\2]]', clean)
    clean = re.sub(r'\[\[(pii|profanity|claim):\s*\[\[([^\]]+)\]\]\s*\]\]', r'[[\1:\2]]', clean)
    # Fix phone prefix leaks: +84 [[pii:768***522]] -> [[pii:076***522]]
    clean = re.sub(r'\+84\s*\[\[pii:(\d{3})\*\*\*(\d{3,4})\]\]', r'[[pii:0\1***\2]]', clean)
    clean = re.sub(r'\+84\s*\[\[pii:\*\*\*\]\]', r'[[pii:***]]', clean)
    # Mask social handles: @quinchang___
    clean = re.sub(r'@[\w_]{3,}', '[[pii:***]]', clean)
    # Clean up trailing qualifiers and accidental duplicate/adjacent shortcodes
    clean = re.sub(r'(\[\[claim:[^\]]+\]\])\s*chuyên\s+nghiệp\b', r'\1', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\[\[claim:sai cam kết ban đầu\]\]\s*\[\[claim:giữ tài sản trái thỏa thuận\]\]', r'[[claim:giữ tài sản trái thỏa thuận]]', clean)
    # Fix unmatched closing parenthesis: [[claim:...]]) -> [[claim:...]]
    clean = re.sub(r'(\[\[(?:pii|profanity|claim):[^\]]+\]\])\s*\)', r'\1', clean)
    clean = re.sub(r'\[\[(?:pii|profanity|claim):([^\]]+)\s*\)\]\]', r'[[\1]]', clean)
    clean = strip_emojis(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def strip_safety_shortcodes(text: str) -> str:
    """Strips [[type:value]] shortcodes to yield pure plain text (e.g. for search index or OpenGraph)."""
    if not text:
        return ""
    return re.sub(r'\[\[(?:pii|profanity|claim):([^\]]+)\]\]', r'\1', text)

def sanitize_address(raw_address: str) -> str:
    """Strips noisy location prefixes and standardizes address strings."""
    if not raw_address:
        return "Hà Nội"
    clean = re.sub(r'^(?:[^\w\s]|khu\s+vực\s+)*', '', raw_address, flags=re.IGNORECASE).strip()
    clean = re.sub(r'^(?:khu\s+vực\s+phường|phường)\s*', '', clean, flags=re.IGNORECASE).strip()
    return clean if clean else "Hà Nội"

def sanitize_content(raw_content: str) -> str:
    """Sanitizes review content text, purging banned terms, emojis, font hacks, and noisy headers."""
    if not raw_content:
        return ""
    clean = normalize_unicode_text(raw_content)
    clean = strip_emojis(clean)
    # Strip leading header artifacts or location tags like 'Khu vực...', but preserve bullet points (-, *, +, •, 1.)
    clean = re.sub(r'^(?:[^\w\s\-*+•0-9]|Khu\s+vực)[^\n]*\n+', '', clean, flags=re.IGNORECASE).strip()
    for pattern, replacement in BANNED_TERM_MAPPINGS.items():
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
    return clean.strip()

def normalize_text_key(text: str) -> str:
    """Normalizes text for ascii comparison and hash key generation."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text.lower().strip())
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def compute_content_hash(content: str, addr: str = "") -> str:
    """Full text content + address SHA-256 hash (eliminates collisions and handles cross-run dedup)."""
    norm_content = normalize_text_key(content)
    if not norm_content:
        return ""
    combined = f"{normalize_text_key(addr)}||{norm_content}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def sanitize_cell_text(text: Any) -> str:
    """Sanitizes text cells for deterministic 1-line-per-record CSV output."""
    if not text:
        return ""
    t = str(text).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    return re.sub(r'\s+', ' ', t)

def moderate_reviews_with_gemini(
    items: list[dict[str, Any]],
    batch_size: int = 20
) -> list[dict[str, Any]]:
    """
    Moderates a batch of rental review posts using Gemini (gemini-3.5-flash-lite).
    Extracts structured entities (target_phone, target_brand, landlord_name, personal_names)
    and produces naturally phrased, legally shielded content with [[pii:...]], [[profanity:...]],
    and [[claim:...]] shortcodes.
    """
    import os
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    results: list[dict[str, Any]] = [{} for _ in range(len(items))]
    
    if not GEMINI_API_KEY:
        # Fallback to deterministic rule-based sanitization
        for idx, item in enumerate(items):
            raw = item.get("content") or ""
            target_phone = item.get("target_phone")
            landlord_name = item.get("landlord_name")
            sanitized = sanitize_review_text(raw, target_phone=target_phone, personal_names=[landlord_name] if landlord_name else None)
            results[idx] = {
                "target_phone": target_phone,
                "target_brand": item.get("target_brand"),
                "landlord_name": landlord_name,
                "personal_names": [landlord_name] if landlord_name else [],
                "has_pii": "[[pii:" in sanitized,
                "has_profanity": "[[profanity:" in sanitized,
                "has_claim": "[[claim:" in sanitized,
                "sanitized_content": sanitized,
            }
        return results

    try:
        from google import genai
        from google.genai import types
        from pydantic import BaseModel, Field

        class ReviewModItem(BaseModel):
            index: int
            target_phone: str | None = Field(None, description="Clean mobile phone digits of landlord/agent/subject, e.g. 0987654321")
            target_brand: str | None = Field(None, description="Commercial chain/brand if any, e.g. Hoàng Long House")
            landlord_name: str | None = Field(None, description="Landlord or manager personal name if mentioned")
            personal_names: list[str] = Field(default_factory=list, description="All individual personal names mentioned in text to redact")
            has_pii: bool = Field(False, description="True if text contains phone numbers, personal names, or private personal data")
            has_profanity: bool = Field(False, description="True if text contains insults, vulgarity, curses")
            has_claim: bool = Field(False, description="True if text alleges civil dispute, deposit withholding, unagreed charges")
            sanitized_content: str = Field(..., description="The review text naturally rewritten with [[pii:...]], [[profanity:...]], and [[claim:...]] shortcodes embedded")

        class ReviewModBatch(BaseModel):
            results: list[ReviewModItem]

        client = genai.Client(api_key=GEMINI_API_KEY)
        system_instruction = (
            "You are an expert legal moderation and PII protection engine for Vietnamese rental reviews (Nhaminhbach).\n"
            "Your objective: Shield the platform from criminal defamation (Penal Code Art 156) and false criminal accusations (Penal Code Arts 174, 175, 200) under Vietnamese law while preserving authentic tenant facts.\n\n"
            "RULES:\n"
            "1. STRICT PRESERVATION OF STRUCTURE & FACTUAL CONTENT: Do NOT summarize, drop, or truncate any sentences, pros/cons, bullet points, or factual room conditions (e.g. noise, insects, parking, cleanliness, repairs, water/electricity). Keep all lines and details intact.\n"
            "2. PII Masking: Mask all phone numbers to [[pii:098***4321]]. Replace personal names of landlords/managers with [[pii:***]]. Do NOT mask role nouns like 'quản lý', 'chủ trọ', 'bảo vệ', or vehicle models like 'Scoopy'.\n"
            "3. Profanity: Replace insults, curses, vulgar terms with strictly [[profanity:***]]. NEVER output raw words inside the tag (e.g. DO NOT output [[profanity:vl]] or [[profanity:haml]], ONLY [[profanity:***]]).\n"
            "4. Criminal Accusations to Civil Claims: You MUST neutralize ALL criminal offense terminology, criminal accusations, and aggravating qualifiers into concise civil dispute terminology embedded in [[claim:nội dung]].\n"
            "   - Criminal offense terms to eliminate: 'chiếm đoạt tài sản', 'lừa đảo', 'lừa đảo chiếm đoạt tài sản', 'ăn cướp', 'cưỡng đoạt', 'tống tiền', 'quỵt cọc', 'ăn chặn', 'trốn thuế', 'câu điện', 'ăn gian điện', 'đấm khách', 'nhốt lại', 'giữ cccd', 'lừa sinh viên'.\n"
            "   - Neutralize compound clauses cleanly: e.g. 'lừa sinh viên kí hợp đồng cọc 3' -> '[[claim:sai cam kết hợp đồng cọc]]'. NEVER leave criminal offense words unshielded.\n"
            "5. Natural Flow: Ensure the text reads naturally in Vietnamese without robotic word swaps or adjacent duplicate tags.\n"
            "6. Identity extraction: Extract target_phone (clean digits only), target_brand, landlord_name, personal_names.\n"
        )

        for start_idx in range(0, len(items), batch_size):
            chunk = items[start_idx:start_idx + batch_size]
            batch_payload = []
            for i, it in enumerate(chunk):
                raw_txt = it.get("content") or ""
                batch_payload.append({"index": start_idx + i, "text": raw_txt})

            response = None
            last_err = None
            for model_name in ("gemini-3.5-flash-lite", "gemini-3.8-flash"):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=json.dumps(batch_payload, ensure_ascii=False),
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=ReviewModBatch,
                            temperature=0.0
                        )
                    )
                    break
                except Exception as ex:  # noqa: BLE001
                    last_err = ex
                    continue
            if response is None:
                raise last_err or RuntimeError("No model succeeded")
            parsed = json.loads(response.text)
            batch_results = parsed.get("results", []) if isinstance(parsed, dict) else parsed
            for res in batch_results:
                idx = res.get("index")
                if idx is not None and 0 <= idx < len(results):
                    # Also double check with rule sanitizer to guarantee all regex PII/phones are fully masked
                    gemini_sanitized = res.get("sanitized_content", "")
                    phone_extracted = res.get("target_phone")
                    personal_names = res.get("personal_names") or []
                    
                    # Run rule pass on top to catch any leftover phone or profane patterns
                    final_sanitized = sanitize_review_text(
                        gemini_sanitized,
                        target_phone=phone_extracted,
                        personal_names=personal_names
                    )
                    
                    results[idx] = {
                        "target_phone": phone_extracted,
                        "target_brand": res.get("target_brand"),
                        "landlord_name": res.get("landlord_name"),
                        "personal_names": personal_names,
                        "has_pii": bool(res.get("has_pii")) or "[[pii:" in final_sanitized,
                        "has_profanity": bool(res.get("has_profanity")) or "[[profanity:" in final_sanitized,
                        "has_claim": bool(res.get("has_claim")) or "[[claim:" in final_sanitized,
                        "sanitized_content": final_sanitized,
                    }
    except Exception as e:  # noqa: BLE001
        print(f"[Gemini Moderation Error] {e}. Falling back to rule-based sanitizer.")
        for idx, item in enumerate(items):
            if not results[idx]:
                raw = item.get("content") or ""
                target_phone = item.get("target_phone")
                landlord_name = item.get("landlord_name")
                sanitized = sanitize_review_text(raw, target_phone=target_phone, personal_names=[landlord_name] if landlord_name else None)
                results[idx] = {
                    "target_phone": target_phone,
                    "target_brand": item.get("target_brand"),
                    "landlord_name": landlord_name,
                    "personal_names": [landlord_name] if landlord_name else [],
                    "has_pii": "[[pii:" in sanitized,
                    "has_profanity": "[[profanity:" in sanitized,
                    "has_claim": "[[claim:" in sanitized,
                    "sanitized_content": sanitized,
                }

    return results



CCCD_REGEX = re.compile(r'\b\d{12}\b')


def tokenize_pii_vault(text: str) -> tuple[str, dict[str, str]]:
    """
    Gate 1 Deterministic Pre-Inference Token Vault.
    Normalizes Unicode (NFKC) and replaces raw 10-digit Vietnamese phone numbers
    and 12-digit citizen IDs (CCCD) with session tokens (<PII_PHONE_01>, <PII_ID_01>)
    prior to external LLM transit so raw PII never enters cloud model logs.
    """
    if not text:
        return "", {}
    normalized = normalize_unicode_text(text)
    vault: dict[str, str] = {}
    phone_idx = 0
    id_idx = 0

    def repl_phone(m: re.Match) -> str:
        nonlocal phone_idx
        phone_idx += 1
        token = f"<PII_PHONE_{phone_idx:02d}>"
        vault[token] = m.group(0)
        return token

    def repl_id(m: re.Match) -> str:
        nonlocal id_idx
        id_idx += 1
        token = f"<PII_ID_{id_idx:02d}>"
        vault[token] = m.group(0)
        return token

    quarantined = PHONE_REGEX.sub(repl_phone, normalized)
    quarantined = CCCD_REGEX.sub(repl_id, quarantined)
    return quarantined, vault
