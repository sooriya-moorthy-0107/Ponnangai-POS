import json
import urllib.request
import os
import difflib

def get_product_data():
    req = urllib.request.urlopen("https://pos.ponnangai.com/api/debug/photos")
    return json.loads(req.read().decode("utf-8"))["database_products"]

def map_files():
    products = get_product_data()
    files = os.listdir("photos/wobg")
    
    mapping = {}
    
    # Custom exact mappings that fuzzy matching might miss
    custom = {
        "Comfort 5 ltr can": "5L_Comfort_blue.png",
        "Dish wash 5 ltr can": "5L_Dishwash.png",
        "Toilet cleaner  5 ltr can": "5L_Toiletcleaner.png",
        "Floor Cleaner 5 ltr can": "5L_Floorcleaner_yellow.png",
        "Cloth wash  5 ltr can": "5L_Clothwash.png",
        "Tiles Cleaner  5 ltr can": "5L_Tilescleaner.png",
        "Glass cleaner  5 ltr can": "5L_Glasscleaner.png",
        "Phenoyl  5 ltr can": "5L_Phenyol.png",
        
        "Comfort STICKER": "S_Comfort_blue.png",
        "Cloth wash  STICKER": "S_Clothwash.png",
        "Tiles Cleaner STICKER": "S_Tilescleaner.png",
        "Hand wash 1/2 Ltr STICKER": "S_Handwash_pink.png",
        "Dish wash  1/2 ltr  STICKER": "S_Dishwash.png",
        "Floor cleaner 1/2 ltr  STICKER": "S_Floorwash_pink.png",
        "Toilet cleaner 1/2 ltr STICKER": "S_Toiletcleaner.png",
        "Glass Cleaner (colin) 1/2 ltr STICKER": "S_Glasscleaner.png",
        "Black Phenoyl 1/2 Ltr STICKER": "S_Blackphenyol.png",
        
        "Floor cleaner WATER BOTTLE": "WOS_Floorwash_pink.png",
        "Dish wash WATER BOTTLE": "WOS_Dishwash.png",
        "Ala  WATER BOTTLE": "WOS_Ala.png",
        "Comfort  WATER BOTTLE": "WOS_Comfort_blue.png",
        "Cloth wash  WATER BOTTLE": "WOS_Clothwash.png",
        "Toilet Cleaner  WATER BOTTLE": "WOS_Toiletcleaner.png",
        
        "Odonil zipper": "o_odonil_zipper.png",
        "Checked cloth": "o_checked_cloth.png",
        "Odonil cake": "o_odonil_Airfreshner.png",
        "Dustbin cover small": "o_Garbage_cover_Small.png",
        "Dustbin cover medium": "o_Garbage_cover_Medium.png",
        "Dustbin cover large": "o_Garbage_cover_Large.png",
        "Dustbin vover Extra large": "o_Garbage_cover_Extra_large.png",
        "Silver polish": "o_Silvershine.png",
        "Mini scent": "o_MiniScent.png",
        "Dish wash soap": "o_Dishsoap.png",
        "Multi cake": "o_multicake.png",
        "Sambrani pkt": "o_Sambrani.png",
        "Agarbatthi": "o_oodubathi1.png",
        "Sink cleaner drainex powder": "o_Drain_cleaner.png",
        "Mop stick": "o_MopStick.png",
        "Mop base": "o_Mop_base.png",
        "Mat": "o_Mat.png",
        "Toilet brush double side": "o_Toiletbrush.png",
        "Napthelene balls pkt": "o_Napthelene balls.png",
        "Green Scrubber": "o_Greenscrubber.png",
        "Steel Scrubber": "o_Steelscrubber.png",
        "Bleaching powder": "o_Bleaching.png",
        "Ant chalk": "o_Antchalk.png",
        "Soft broom": "o_Softbroom.png",
        "Tissue pkt": "o_Tissuepacket.png",
        "Box Room Spray": "o_RoomSpray_box.png",
        "Bathing Soap": "o_Bathsoap.png",
        "Sambrani pcs": "o_sambrani_pcs.png",
    }
    
    for p in products:
        name = p["name"]
        
        if name in custom:
            if custom[name] in files:
                mapping[name] = custom[name]
        else:
            # Try fuzzy match
            norm_name = name.lower().replace(" ", "").replace("_", "")
            matches = difflib.get_close_matches(norm_name, [f.lower().replace(" ", "").replace("_", "").replace(".png", "").replace(".jpg", "") for f in files], n=1, cutoff=0.5)
            if matches:
                matched_idx = [f.lower().replace(" ", "").replace("_", "").replace(".png", "").replace(".jpg", "") for f in files].index(matches[0])
                mapping[name] = files[matched_idx]

    print(json.dumps(mapping, indent=2))

if __name__ == "__main__":
    map_files()
