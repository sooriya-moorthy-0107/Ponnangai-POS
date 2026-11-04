def get_product_sort_key(product_name):
    name_lower = product_name.lower().strip()
    base_order = [
        "Cloth wash", "Comfort", "Dish wash", "Floor Cleaner", "Toilet cleaner",
        "Tiles Cleaner", "Glass cleaner", "Hand wash", "Phenoyl", "Phenoyl compound",
        "Peethambari", "Odonil zipper", "Checked cloth", "Odonil cake",
        "Dustbin cover small", "Dustbin cover medium", "Dustbin cover large",
        "Dustbin cover Extra large", "Silver polish", "Mini scent", "Dish wash soap",
        "Multi cake", "Sambrani Box", "Agarbatthi", "Sink cleaner drainex powder",
        "Mop stick", "Mop base", "Mat", "Toilet brush double side", "Napthelene balls pkt",
        "Green Scrubber", "Steel Scrubber", "Bleaching powder", "Ant chalk",
        "Soft broom", "Tissue pkt", "Box Room Spray", "Bathing Soap", "Sambrani pcs",
        "Eytex Zipper", "Eytex Cake", "Soapoil", "Multi purpose"
    ]
    base_idx = 999
    matched_base = ""
    for i, base in enumerate(base_order):
        if base.lower() in name_lower:
            if len(base) > len(matched_base):
                base_idx = i
                matched_base = base.lower()
                
    if base_idx == 999:
        return (999, 999, product_name)
        
    variant_idx = 1
    if "wos" in name_lower or "water bottle" in name_lower or "1/2 ltr" in name_lower:
        variant_idx = 2
    elif "5 ltr" in name_lower or "5l" in name_lower or "5 l" in name_lower:
        variant_idx = 3
        
    return (base_idx, variant_idx, product_name)

def clean_csv_val(val):
    if val is None:
        return ""
    s = str(val).strip()
    if len(s) >= 2:
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
    return s

def parse_csv_int(val, default=None):
    cleaned = clean_csv_val(val)
    if not cleaned:
        return default
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_CSV_SIZE = 10 * 1024 * 1024   # 10 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def validate_image_bytes(content: bytes) -> bool:
    """Verifies file magic bytes to guarantee file is a genuine image (not script/SVG)."""
    if len(content) < 8:
        return False
    # PNG: \x89PNG\r\n\x1a\n
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # JPEG: \xff\xd8\xff
    if content.startswith(b"\xff\xd8\xff"):
        return True
    # WebP: RIFF....WEBP
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return True
    return False

async def read_bounded_upload(file, max_bytes: int) -> bytes:
    """Reads uploaded file chunks up to max_bytes, raising ValueError if exceeded."""
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise ValueError(f"File exceeds maximum allowed size of {max_bytes // (1024 * 1024)}MB")
        chunks.append(chunk)
    return b"".join(chunks)
