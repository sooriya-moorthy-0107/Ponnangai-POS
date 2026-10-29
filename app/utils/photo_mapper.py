import os
import re

KNOWN_PHOTO_MAP = {
    # 5L Cans
    "comfort 5 ltr": "5L_Comfort_blue.png",
    "comfort 5 ltr can": "5L_Comfort_blue.png",
    "comfort 5l": "5L_Comfort_blue.png",
    "dishwash 5 ltr": "5L_Dishwash.png",
    "dish wash 5 ltr": "5L_Dishwash.png",
    "dishwash 5 liter": "5L_Dishwash.png",
    "toilet cleaner 5 ltr": "5L_Toiletcleaner.png",
    "toilet cleaner 5 liter": "5L_Toiletcleaner.png",
    "floorwash 5 ltr": "5L_Floowcelaner_pink.png",
    "floor cleaner 5 ltr": "5L_Floorcleaner_yellow.png",
    "clothwash 5 ltr": "5L_Clothwash.png",
    "cloth wash 5 ltr": "5L_Clothwash.png",
    "tiles cleaner 5 ltr": "5L_Tilescleaner.png",
    "glass cleaner 5 ltr": "5L_Glasscleaner.png",
    "phenoyl 5 ltr": "5L_Phenyol.png",
    "phenoyl compound 5 ltr": "5L_Phenyol_Compund.png",
    "handwash 5 ltr": "S_Handwash_green.png",

    # 1 Ltr Can / Bottle Variants (C_...)
    "comfort 1 ltr": "C_Comfort_blue.png",
    "toilet cleaner 1 ltr": "C_Toiletcleaner.png",
    "tiles cleaner 1 ltr": "C_Tilescleaner.png",
    "glass cleaner 1 ltr": "C_glasscleaner.png",
    "phenoyl 1 ltr": "C_Phenyol.png",
    "phenoyl compound 1 ltr": "C_Phenyol_compound.png",
    "clothwash 1 ltr": "C_Clothwash.png",
    "dishwash 1 ltr": "C_Dishwash.png",
    "floorwash 1 ltr": "C_Floorwash_pink.png",
    "handwash 1 ltr": "S_Handwash_pink.png",

    # Loose Variants (WOS_...)
    "comfort loose": "WOS_Comfort_blue.png",
    "toilet cleaner loose": "WOS_Toiletcleaner.png",
    "clothwash loose": "WOS_Clothwash.png",
    "dishwash loose": "WOS_Dishwash.png",
    "floorwash loose": "WOS_Floorwash_pink.png",
    "handwash loose": "S_Handwash_yellow.png",
    "tiles cleaner loose": "C_Tilescleaner.png",
    "glass cleaner loose": "C_glasscleaner.png",
    "phenoyl loose": "C_Phenyol.png",
    "phenoyl compound loose": "C_Phenyol_compound.png",
    "soap oil loose": "professional.png",
    "multi loose": "o_multicake.png",

    # Sticker Variants (S_...)
    "comfort sticker": "S_Comfort_blue.png",
    "toilet cleaner sticker": "S_Toiletcleaner.png",
    "tiles cleaner sticker": "S_Tilescleaner.png",
    "glass cleaner sticker": "S_Glasscleaner.png",
    "phenoyl sticker": "S_Phenyol.png",
    "phenoyl compound sticker": "S_Phenyol_compound.png",
    "clothwash sticker": "S_Clothwash.png",
    "dishwash sticker": "S_Dishwash.png",
    "floorwash sticker": "S_Floorwash_pink.png",
    "handwash sticker": "S_Handwash_pink.png",

    # Cleaning Essentials & Hardware (o_...)
    "peethambari": "o_Silvershine.png",
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
    "agarbatthi": "o_oodubathi1.png",
    "sink cleaner drainex powder": "o_Drain_cleaner.png",
    "mop stick": "o_MopStick.png",
    "mop base": "o_Mop_base.png",
    "mat": "o_Mat.png",
    "toilet brush double side": "o_Toiletbrush.png",
    "green scrubber": "o_Greenscrubber.png",
    "steel scrubber": "o_Steelscrubber.png",
    "bleaching powder": "o_Bleaching.png",
    "ant chalk": "o_Antchalk.png",
    "soft broom": "o_Softbroom.png",
    "hard broom": "o_Hardbroom.png",
    "tissue pkt": "o_Tissuepacket.png",
    "box room spray": "o_RoomSpray_box.png",
    "bathing soap": "o_Bathsoap.png",
    "sambrani pcs": "o_sambrani_pcs.png",
    "sambrani pkt": "o_Sambrani.png",
    "naphthalene balls pkt": "o_Napthelene balls.png",
    "napthelene balls pkt": "o_Napthelene balls.png"
}

def auto_map_product_photo(product_name: str, requested_image: str = None) -> str:
    """
    Given a product name (e.g. 'Comfort 1 Ltr') and an optional requested image from CSV/form,
    returns the best matching image filename from KNOWN_PHOTO_MAP or formats a valid filename.
    """
    clean_name = product_name.strip().lower()
    
    # Check exact match in known dictionary
    if clean_name in KNOWN_PHOTO_MAP:
        return KNOWN_PHOTO_MAP[clean_name]

    # Check substring match
    for key, filename in KNOWN_PHOTO_MAP.items():
        if key in clean_name or clean_name in key:
            return filename

    # If user provided a specific image name that ends with an image extension, keep it
    if requested_image and requested_image.strip():
        img = requested_image.strip()
        img_clean = img.lower().replace(" ", "_").replace("-", "")
        if not any(img_clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            img_clean += ".png"
        return img_clean

    # Fallback slug name with .png
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", clean_name).strip("_")
    return f"{slug}.png"
