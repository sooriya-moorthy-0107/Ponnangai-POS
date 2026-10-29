"""
Script to batch-upload all product photos to Supabase Storage Bucket ('products').
Usage:
    python scripts/upload_photos_to_supabase.py <SUPABASE_SERVICE_ROLE_KEY_OR_ANON_KEY>
"""
import os
import sys
import mimetypes
import httpx
from app.core.config import SUPABASE_URL, SUPABASE_STORAGE_BUCKET

def upload_all_photos(api_key: str):
    if not SUPABASE_URL:
        print("[ERROR] Could not determine SUPABASE_URL. Make sure DATABASE_URL or SUPABASE_URL is set in .env")
        return

    bucket = SUPABASE_STORAGE_BUCKET or "products"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "apiKey": api_key,
        "x-upsert": "true",  # Overwrite if exists
    }

    folders = ["photos", os.path.join("photos", "wobg")]
    uploaded = 0
    failed = 0

    print(f"Uploading photos to Supabase Storage: {SUPABASE_URL}/storage/v1/object/{bucket}/...")

    for folder in folders:
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            
            # Skip hidden / non-image files
            if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                continue

            content_type, _ = mimetypes.guess_type(fpath)
            content_type = content_type or "image/png"

            upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{fname}"
            try:
                with open(fpath, "rb") as f:
                    file_data = f.read()

                resp = httpx.post(
                    upload_url,
                    headers={**headers, "Content-Type": content_type},
                    content=file_data,
                    timeout=30.0
                )

                if resp.status_code in (200, 201):
                    print(f"  [OK] {fname}")
                    uploaded += 1
                else:
                    print(f"  [FAIL] {fname}: {resp.status_code} {resp.text}")
                    failed += 1
            except Exception as e:
                print(f"  [ERROR] {fname}: {e}")
                failed += 1

    print(f"\nUpload complete! Successfully uploaded: {uploaded}, Failed: {failed}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        api_key = os.getenv("SUPABASE_KEY", "")
        if not api_key:
            print("Usage: python scripts/upload_photos_to_supabase.py <SUPABASE_SERVICE_ROLE_KEY_OR_ANON_KEY>")
            sys.exit(1)
    else:
        api_key = sys.argv[1].strip()

    upload_all_photos(api_key)
