import json

content = open('main.py').read()

new_mapping = {
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
  "Eytex Zipper": "o_eyetex_zipper.png",
  "Eytex Cake": "o_eyetex_zipper.png",
  "Comfort 5 ltr can": "5L_Comfort_blue.png",
  "Dish wash 5 ltr can": "5L_Dishwash.png",
  "Toilet cleaner  5 ltr can": "5L_Toiletcleaner.png",
  "Floor Cleaner 5 ltr can": "5L_Floorcleaner_yellow.png",
  "Cloth wash  5 ltr can": "5L_Clothwash.png",
  "Tiles Cleaner  5 ltr can": "5L_Tilescleaner.png",
  "Glass cleaner  5 ltr can": "5L_Glasscleaner.png",
  "Hand wash 5 ltr can": "S_Handwash_green.png",
  "Phenoyl  5 ltr can": "5L_Phenyol.png",
  "Comfort STICKER": "S_Comfort_blue.png",
  "Cloth wash  STICKER": "S_Clothwash.png",
  "Tiles Cleaner STICKER": "S_Tilescleaner.png",
  "Sanitizer STICKER": "o_Silvershine.png",
  "Phenoyl compound STICKER": "o_MopStick.png",
  "Soapoil": "o_Rat_poison.png",
  "Multi purpose": "o_multicake.png",
  "Comfort": "S_Comfort_pink.png",
  "Dish wash": "S_Dishwash.png",
  "Toilet cleaner": "S_Toiletcleaner.png",
  "Floor Cleaner": "5L_Floorcleaner_yellow.png",
  "Cloth wash": "S_Clothwash.png",
  "Tiles Cleaner": "S_Tilescleaner.png",
  "Glass cleaner": "S_Glasscleaner.png",
  "Hand wash": "S_Handwash_pink.png",
  "Phenoyl": "S_Phenyol.png",
  "Phenoyl compound": "S_Phenyol.png",
  "Peethambari": "o_Sambrani.png",
  "Odonil zipper": "o_odonil_zipper.png",
  "Checked cloth": "o_checked_cloth.png",
  "Odonil cake": "o_odonil_Airfreshner.png",
  "Dustbin cover small": "o_Garbage_cover_Small.png",
  "Dustbin cover medium": "o_Garbage_cover_Medium.png",
  "Dustbin cover large": "o_Garbage_cover_Large.png",
  "Dustbin cover Extra large": "o_Garbage_cover_Extra_large.png",
  "Silver polish": "o_Silvershine.png",
  "Mini scent": "o_MiniScent.png",
  "Dish wash soap": "o_Dishsoap.png",
  "Multi cake": "o_multicake.png",
  "Sambrani Box": "o_Sambrani.png",
  "Agarbatthi": "o_oodubathi1.png",
  "Sink cleaner drainex powder": "o_Drain_cleaner.png",
  "Mop stick": "o_MopStick.png",
  "Hand wash 1/2 Ltr STICKER": "S_Handwash_pink.png",
  "Dish wash  1/2 ltr  STICKER": "S_Dishwash.png",
  "Floor cleaner 1/2 ltr  STICKER": "S_Floorwash_pink.png",
  "Toilet cleaner 1/2 ltr STICKER": "S_Toiletcleaner.png",
  "Glass Cleaner (colin) 1/2 ltr STICKER": "S_Glasscleaner.png",
  "Black Phenoyl 1/2 Ltr STICKER": "S_Blackphenyol.png",
  "Floor cleaner WATER BOTTLE": "WOS_Floorwash_pink.png",
  "Dish wash WATER BOTTLE": "WOS_Dishwash.png",
  "Ala  WATER BOTTLE": "WOS_Ala.png",
  "Phenoyl  WATER BOTTLE": "S_Phenyol.png",
  "Comfort  WATER BOTTLE": "WOS_Comfort_blue.png",
  "Cloth wash  WATER BOTTLE": "WOS_Clothwash.png",
  "Toilet Cleaner  WATER BOTTLE": "WOS_Toiletcleaner.png",
  "Dustbin vover Extra large": "o_Garbage_cover_Extra_large.png",
  "Sambrani pkt": "o_Sambrani.png"
}

old_map_str = """    mapping = {
      "99": "o_Rat_poison.png", "100": "o_multicake.png", "1": "S_Comfort_pink.png", "2": "S_Dishwash.png", "3": "S_Toiletcleaner.png",
      "4": "5L_Floorcleaner_yellow.png", "5": "S_Clothwash.png", "6": "S_Tilescleaner.png", "7": "S_Glasscleaner.png", "8": "S_Handwash_pink.png",
      "9": "S_Phenyol.png", "10": "S_Phenyol.png", "11": "o_Sambrani.png", "12": "o_odonil_zipper.png", "13": "o_checked_cloth.png",
      "14": "o_odonil_Airfreshner.png", "15": "o_Garbage_cover_Small.png", "16": "o_Garbage_cover_Medium.png", "17": "o_Garbage_cover_Large.png",
      "18": "o_Garbage_cover_Extra_large.png", "19": "o_Silvershine.png", "20": "o_MiniScent.png", "21": "o_Dishsoap.png", "22": "o_multicake.png",
      "23": "o_Sambrani.png", "24": "o_oodubathi1.png", "25": "o_Drain_cleaner.png", "26": "o_MopStick.png", "27": "o_Mop_base.png",
      "28": "o_Mat.png", "29": "o_Toiletbrush.png", "30": "o_Napthelene balls.png", "31": "o_Greenscrubber.png", "32": "o_Steelscrubber.png",
      "33": "o_Bleaching.png", "34": "o_Antchalk.png", "35": "o_Softbroom.png", "36": "o_Tissuepacket.png", "37": "o_RoomSpray_box.png",
      "38": "o_Bathsoap.png", "39": "o_sambrani_pcs.png", "40": "o_eyetex_zipper.png", "41": "o_eyetex_zipper.png", "42": "5L_Comfort_blue.png",
      "43": "5L_Dishwash.png", "44": "5L_Toiletcleaner.png", "45": "5L_Floorcleaner_yellow.png", "46": "5L_Clothwash.png", "47": "5L_Tilescleaner.png",
      "48": "5L_Glasscleaner.png", "49": "S_Handwash_green.png", "50": "5L_Phenyol.png", "52": "S_Comfort_blue.png", "53": "S_Clothwash.png",
      "54": "S_Tilescleaner.png", "55": "o_Silvershine.png", "56": "o_MopStick.png", "57": "S_Handwash_pink.png", "58": "S_Dishwash.png",
      "59": "S_Floorwash_pink.png", "60": "S_Toiletcleaner.png", "61": "S_Glasscleaner.png", "62": "S_Blackphenyol.png", "63": "WOS_Floorwash_pink.png",
      "64": "WOS_Dishwash.png", "65": "WOS_Ala.png", "66": "S_Phenyol.png", "67": "WOS_Comfort_blue.png", "68": "WOS_Clothwash.png",
      "69": "WOS_Toiletcleaner.png", "70": "o_Sambrani.png", "71": "o_odonil_zipper.png", "72": "o_checked_cloth.png", "73": "o_odonil_Airfreshner.png",
      "74": "o_Garbage_cover_Small.png", "75": "o_Garbage_cover_Medium.png", "76": "o_Garbage_cover_Large.png", "77": "o_Garbage_cover_Extra_large.png",
      "78": "o_Silvershine.png", "79": "o_MiniScent.png", "80": "o_Dishsoap.png", "81": "o_multicake.png", "82": "o_Sambrani.png",
      "83": "o_oodubathi1.png", "84": "o_Drain_cleaner.png", "85": "o_MopStick.png", "86": "o_Mop_base.png", "87": "o_Mat.png",
      "88": "o_Toiletbrush.png", "89": "o_Napthelene balls.png", "90": "o_Greenscrubber.png", "91": "o_Steelscrubber.png", "92": "o_Bleaching.png",
      "93": "o_Antchalk.png", "94": "o_Softbroom.png", "95": "o_Tissuepacket.png", "96": "o_RoomSpray_box.png", "97": "o_Bathsoap.png", "98": "o_sambrani_pcs.png"
    }"""

new_map_str = "    mapping = " + json.dumps(new_mapping, indent=4).replace("\n", "\n    ")

content = content.replace(old_map_str, new_map_str)

old_loop_str = """    for pid_str, filename in mapping.items():
        product = db.query(Product).filter(Product.id == int(pid_str)).first()
        if product:
            product.image_filename = filename
            mapped += 1
            logs.append(f"Mapped {product.name} to {filename}")"""

new_loop_str = """    # Map by product name, so it automatically works for new shops too!
    for product_name, filename in mapping.items():
        products = db.query(Product).filter(Product.name == product_name).all()
        for product in products:
            product.image_filename = filename
            mapped += 1
            logs.append(f"Mapped {product.name} (Shop {product.shopkeeper_id}) to {filename}")"""

content = content.replace(old_loop_str, new_loop_str)

open('main.py', 'w').write(content)
print("Patched main.py")
