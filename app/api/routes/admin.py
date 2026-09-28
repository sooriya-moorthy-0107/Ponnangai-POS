from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, date, time
from typing import List, Optional
import os, csv, io, uuid, secrets

from app.models.database import get_db, SessionLocal
from app.models.domain import User, Product, ShopInventory, Bill, BillItem, CashTransaction
from app.utils.helpers import get_product_sort_key, clean_csv_val, parse_csv_int
from app.core.config import SECRET_KEY
from app.core.security import pwd_context
from app.api.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def seed_db():
    db = SessionLocal()
    if db.query(User).count() == 0:
        # Create initial users
        admin = User(username="admin", password=pwd_context.hash("Somuponn"), role="Admin")
        manager = User(username="manager", password=pwd_context.hash("manager123"), role="Manager")
        owner = User(username="owner", password=pwd_context.hash("owner123"), role="Owner")
        db.add_all([admin, manager, owner])
        db.commit()
    else:
        owner = db.query(User).filter(User.role == "Owner").first()
        if not owner:
            owner = User(username="owner", password=pwd_context.hash("owner123"), role="Owner")
            db.add(owner)
            db.commit()

        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            # Only hash if it's currently the plaintext password
            if not admin.password.startswith("$2"):
                admin.password = pwd_context.hash("Somuponn")
                db.commit()
    db.close()

@router.post("/api/system/reset")
async def reset_system(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # ONLY Admin
    if not user or user.role != "Admin":
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin can reset the system."})
        
    # Delete all operational data (preserving users) and reset auto-increment IDs
    db.execute(text("TRUNCATE TABLE bill_items, bills, shop_inventories, products, cash_transactions RESTART IDENTITY CASCADE"))
    db.query(User).filter(User.is_deleted == True).delete()
    
    # Also clean up any uploaded product image files starting with "product_" to free disk space
    try:
        if os.path.exists("photos"):
            for filename in os.listdir("photos"):
                if filename.startswith("product_"):
                    os.remove(os.path.join("photos", filename))
    except Exception:
        pass
        
    db.commit()
    return {"status": "success", "detail": "System, products, and sales successfully reset."}

@router.get("/api/debug/photos")
async def debug_photos(db: Session = Depends(get_db)):
    try:
        import os
        files = os.listdir("photos") if os.path.exists("photos") else []
    except Exception as e:
        files = str(e)
    
    db_products = db.query(Product.id, Product.name, Product.image_filename).all()
    
    return {
        "photos_directory_contents": files,
        "database_products": [{"id": p.id, "name": p.name, "image": p.image_filename} for p in db_products]
    }

@router.get("/api/system/fix_photos")
async def fix_all_photos(db: Session = Depends(get_db)):
    import os
    import re
    
    results = {"fixed_links": 0, "cleared_links": 0, "logs": []}
    
    try:
        files_on_disk = os.listdir("photos") if os.path.exists("photos") else []
    except Exception as e:
        return {"error": str(e)}
        
    # Step 1: Re-link any existing product_ID images
    for file in files_on_disk:
        match = re.match(r'^product_(\d+)(?:_.*)?\.(?:png|jpg|jpeg|gif)$', file, re.IGNORECASE)
        if match:
            product_id = int(match.group(1))
            product = db.query(Product).filter(Product.id == product_id).first()
            if product and product.image_filename != file:
                product.image_filename = file
                results["fixed_links"] += 1
                results["logs"].append(f"Linked Product {product_id} to file {file}")
                
    # Step 2: Clear missing images
    all_products = db.query(Product).all()
    for product in all_products:
        if product.image_filename and product.image_filename not in files_on_disk:
            results["logs"].append(f"Cleared missing image {product.image_filename} from Product {product.id}")
            product.image_filename = None
            results["cleared_links"] += 1
            
    db.commit()
    return {"status": "success", "results": results}

@router.get("/api/system/map_photos")
async def map_all_wobg_photos(db: Session = Depends(get_db)):
    mapping = {
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
        "Soapoil": "o_Rat_poison.png",
        "Multi purpose": "o_multicake.png",
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
        "Sambrani pkt": "o_Sambrani.png",
        "Naphthalene balls pkt": "o_Napthelene balls.png",
        "Multi Loose": "o_multicake.png",
        "Soap oil Loose": "o_Rat_poison.png"
    }

    group_map = {
        'clothwash': 'Clothwash',
        'comfort': 'Comfort_pink',
        'dishwash': 'Dishwash',
        'floorwash': 'Floorwash_pink',
        'toilet cleaner': 'Toiletcleaner',
        'tiles cleaner': 'Tilescleaner',
        'handwash': 'Handwash_pink',
        'phenoyl': 'Phenyol',
        'phenoyl compound': 'Phenyol_Compund',
        'glass cleaner': 'Glasscleaner'
    }

    logs = []
    mapped = 0
    import os
    files = os.listdir("photos") if os.path.exists("photos") else []
    
    products = db.query(Product).all()
    
    for product in products:
        name_exact = product.name.strip()
        name_lower = name_exact.lower()
        
        # 1. Exact custom overrides
        if name_exact in mapping:
            product.image_filename = mapping[name_exact]
            mapped += 1
            logs.append(f"Mapped exact {name_exact} to {mapping[name_exact]}")
            continue
            
        # 2. Dynamic Parsing logic
        prefix = None
        group_name = name_lower
        
        if name_lower.endswith(' 5 ltr') or name_lower.endswith(' 5 ltr can'):
            prefix = '5L_'
            group_name = name_lower.replace(' 5 ltr can', '').replace(' 5 ltr', '').strip()
        elif name_lower.endswith(' sticker'):
            prefix = 'S_'
            group_name = name_lower.replace(' sticker', '').strip()
        elif name_lower.endswith(' 1 ltr'):
            prefix = 'WOS_'
            group_name = name_lower.replace(' 1 ltr', '').strip()
        elif name_lower.endswith(' water bottle'):
            prefix = 'WOS_'
            group_name = name_lower.replace(' water bottle', '').strip()
        elif name_lower.endswith(' loose'):
            prefix = 'WOS_'
            group_name = name_lower.replace(' loose', '').strip()

        if prefix:
            mapped_group = group_map.get(group_name, group_name.capitalize().replace(' ', ''))
            
            # Exceptional hardcodes
            if group_name == 'floorwash' and prefix == '5L_':
                filename = '5L_Floorcleaner_yellow.png'
            elif group_name == 'glass cleaner' and prefix == 'WOS_':
                filename = 'S_Glasscleaner.png'
            elif group_name == 'handwash' and prefix == 'WOS_':
                filename = 'S_Handwash_pink.png'
            elif group_name == 'phenoyl compound' and prefix == 'WOS_':
                filename = '5L_Phenyol_Compund.png'
            elif group_name == 'phenoyl compound' and prefix == 'S_':
                filename = '5L_Phenyol_Compund.png'
            elif group_name == 'phenoyl compound' and prefix == '5L_':
                filename = '5L_Phenyol_Compund.png'
            elif group_name == 'phenoyl' and prefix == 'WOS_':
                filename = 'C_Phenyol.png'
            elif group_name == 'tiles cleaner' and prefix == 'WOS_':
                filename = 'C_Tilescleaner.png'
            else:
                filename = f'{prefix}{mapped_group}.png'

            if filename not in files and files:
                if prefix == 'WOS_' and f'C_{mapped_group}.png' in files:
                    filename = f'C_{mapped_group}.png'
                elif prefix == 'WOS_' and f'S_{mapped_group}.png' in files:
                    filename = f'S_{mapped_group}.png'
                elif prefix == 'S_' and f'C_{mapped_group}.png' in files:
                    filename = f'C_{mapped_group}.png'
                
            product.image_filename = filename
            mapped += 1
            logs.append(f"Mapped parsed {name_exact} to {filename}")

    db.commit()
    return {"status": "success", "mapped_count": mapped, "logs": logs}


