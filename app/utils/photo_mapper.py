import os
import re

KNOWN_PHOTO_MAP = {
    # 5L Cans
    "comfort 5 ltr": "5L_Comfort_blue.png",
    "comfort 5 ltr can": "5L_Comfort_blue.png",
    "comfort 5l": "5L_Comfort_blue.png",
    "comfort 5 liter": "5L_Comfort_blue.png",
    "comfort 5 litre": "5L_Comfort_blue.png",
    "dish wash 5 ltr": "5L_Dishwash.png",
    "dish wash 5 ltr can": "5L_Dishwash.png",
    "dishwash 5 liter": "5L_Dishwash.png",
    "dishwash 5l": "5L_Dishwash.png",
    "toilet cleaner 5 ltr": "5L_Toiletcleaner.png",
    "toilet cleaner 5 ltr can": "5L_Toiletcleaner.png",
    "toilet cleaner 5 liter": "5L_Toiletcleaner.png",
    "floor cleaner 5 ltr": "5L_Floorcleaner_yellow.png",
    "floor cleaner 5 ltr can": "5L_Floorcleaner_yellow.png",
    "floorwash 5 liter": "5L_Floorcleaner_yellow.png",
    "cloth wash 5 ltr": "5L_Clothwash.png",
    "cloth wash 5 ltr can": "5L_Clothwash.png",
    "clothwash 5 liter": "5L_Clothwash.png",
    "tiles cleaner 5 ltr": "5L_Tilescleaner.png",
    "tiles cleaner 5 ltr can": "5L_Tilescleaner.png",
    "tiles cleaner 5 liter": "5L_Tilescleaner.png",
    "glass cleaner 5 ltr": "5L_Glasscleaner.png",
    "glass cleaner 5 ltr can": "5L_Glasscleaner.png",
    "glass cleaner 5 liter": "5L_Glasscleaner.png",
    "phenoyl 5 ltr": "5L_Phenyol.png",
    "phenoyl 5 ltr can": "5L_Phenyol.png",
    "phenoyl compound 5 ltr": "5L_Phenyol_Compund.png",

    # Bottles & 500ml / 1 Liter Variants
    "comfort sticker": "S_Comfort_blue.png",
    "comfort 500ml": "S_Comfort_blue.png",
    "cloth wash sticker": "S_Clothwash.png",
    "clothwash 500ml": "S_Clothwash.png",
    "clothwash 1 liter": "clothwash_1_liter.JPG",
    "tiles cleaner sticker": "S_Tilescleaner.png",
    "tiles cleaner 500ml": "S_Tilescleaner.png",
    "hand wash sticker": "S_Handwash_pink.png",
    "hand wash 500ml": "S_Handwash_pink.png",
    "dish wash sticker": "S_Dishwash.png",
    "dish wash 500ml": "S_Dishwash.png",
    "dishwash 500ml": "S_Dishwash.png",
    "dishwash 1 liter": "dishwash_1_liter.png",
    "floor cleaner sticker": "S_Floorwash_pink.png",
    "floor cleaner 500ml": "S_Floorwash_pink.png",
    "floorwash 500ml": "S_Floorwash_pink.png",
    "floorwash 1 liter": "floorwash_1_liter.png",
    "toilet cleaner sticker": "S_Toiletcleaner.png",
    "toilet cleaner 500ml": "S_Toiletcleaner.png",
    "toiletcleaner 500ml": "S_Toiletcleaner.png",
    "toilet cleaner 1 liter": "toiletcleaner_500ml.JPG",
    "glass cleaner sticker": "S_Glasscleaner.png",
    "glass cleaner 500ml": "S_Glasscleaner.png",
    "black phenoyl sticker": "S_Blackphenyol.png",
    "black phenoyl 500ml": "S_Blackphenyol.png",

    # General Hardware, Cleaning & Household Items
    "odonil zipper": "o_odonil_zipper.png",
    "checked cloth": "o_checked_cloth.png",
    "odonil cake": "o_odonil_Airfreshner.png",
    "dustbin cover small": "o_Garbage_cover_Small.png",
    "dustbin cover medium": "o_Garbage_cover_Medium.png",
    "dustbin cover large": "o_Garbage_cover_Large.png",
    "dustbin cover extra large": "o_Garbage_cover_Extra_large.png",
    "silver polish": "o_Silvershine.png",
    "mini scent": "o_MiniScent.png",
    "dish wash soap": "o_Dishsoap.png",
    "multi cake": "o_multicake.png",
    "multi purpose": "o_multicake.png",
    "sambrani box": "o_Sambrani.png",
    "sambrani pcs": "o_sambrani_pcs.png",
    "sambrani pkt": "o_Sambrani.png",
    "agarbatthi": "o_oodubathi1.png",
    "sink cleaner drainex powder": "o_Drain_cleaner.png",
    "mop stick": "o_MopStick.png",
    "mop": "o_MopStick.png",
    "mat": "o_Mat.png",
    "toilet brush double side": "o_Toiletbrush.png",
    "toilet brush": "o_Toiletbrush.png",
    "naphthalene balls pkt": "o_Napthelene balls.png",
    "napthelene balls pkt": "o_Napthelene balls.png",
    "green scrubber": "o_Greenscrubber.png",
    "steel scrubber": "o_Steelscrubber.png",
    "bleaching powder": "o_Bleaching.png",
    "ant chalk": "o_Antchalk.png",
    "soft broom": "o_Softbroom.png",
    "hard broom": "o_Softbroom.png",
    "tissue pkt": "o_Tissuepacket.png",
    "box room spray": "o_RoomSpray_box.png",
    "room spray": "o_RoomSpray_box.png",
    "bathing soap": "o_Bathsoap.png",
    "soap": "o_Bathsoap.png",
    "eytex zipper": "o_eyetex_zipper.png",
    "eytex cake": "o_eyetex_zipper.png",
    "soapoil": "o_Rat_poison.png",
    "peethambari": "o_Sambrani.png",
}

def auto_map_product_photo(product_name: str, requested_image: str = None) -> str:
    """
    Automatically maps a product name to its matching photo filename in the Supabase Storage bucket.
    """
    if requested_image and str(requested_image).strip():
        img = str(requested_image).strip()
        if not (img.lower().endswith('.jpg') or img.lower().endswith('.png') or img.lower().endswith('.jpeg')):
            img += '.png'
        return img

    if not product_name:
        return "default.jpg"

    name_clean = product_name.lower().strip()

    # 1. Exact match from dictionary
    if name_clean in KNOWN_PHOTO_MAP:
        return KNOWN_PHOTO_MAP[name_clean]

    # 2. Substring match from dictionary (longest matching key wins)
    best_match = None
    best_len = 0
    for key, filename in KNOWN_PHOTO_MAP.items():
        if key in name_clean and len(key) > best_len:
            best_match = filename
            best_len = len(key)

    if best_match:
        return best_match

    # 3. Normalized slug (e.g. "Floor Cleaner 1L" -> "floor_cleaner_1l.jpg")
    slug = re.sub(r'[^a-z0-9]+', '_', name_clean).strip('_')
    return f"{slug}.jpg"
