"""
High-Performance Product Photo Optimizer & Supabase Syncer.
1. Compresses large photos (e.g. 6MB -> 25KB) using LANCZOS resizing (350x350) and 256-color palette quantization.
2. Preserves transparent backgrounds.
3. Optionally uploads optimized photos directly into Supabase Storage ('products' bucket) replacing heavy files.

Usage:
    python scripts/optimize_and_upload_photos.py [--upload <SUPABASE_KEY>]
"""
import os
import sys
import shutil
import mimetypes

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
import httpx
from app.core.config import SUPABASE_URL, SUPABASE_STORAGE_BUCKET

def optimize_image(src_path: str, dest_path: str, max_size=(350, 350)) -> tuple[int, int]:
    """Resizes and compresses an image while preserving format and transparency."""
    orig_bytes = os.path.getsize(src_path)
    with Image.open(src_path) as im:
        # Check if already small enough
        if orig_bytes < 40 * 1024 and max(im.size) <= max_size[0]:
            if src_path != dest_path:
                shutil.copy2(src_path, dest_path)
            return orig_bytes, orig_bytes

        # Create thumbnail preserving aspect ratio
        im.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Optimize based on image mode
        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
            # Quantize with alpha preservation
            im_opt = im.quantize(colors=256)
            im_opt.save(dest_path, 'PNG', optimize=True)
        elif im.mode == 'RGB':
            im.save(dest_path, 'PNG', optimize=True)
        else:
            im.convert('RGBA').quantize(colors=256).save(dest_path, 'PNG', optimize=True)

    new_bytes = os.path.getsize(dest_path)
    return orig_bytes, new_bytes

def run_optimizer(api_key: str = None):
    folders = ["photos", os.path.join("photos", "wobg")]
    backup_dir = "photos_backup"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    total_orig = 0
    total_opt = 0
    count = 0
    optimized_files = []

    print("=== Optimizing Product Photos ===")
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue

            # Backup original if not already backed up
            backup_path = os.path.join(backup_dir, fname)
            if not os.path.exists(backup_path):
                shutil.copy2(fpath, backup_path)

            try:
                orig_b, new_b = optimize_image(backup_path, fpath)
                total_orig += orig_b
                total_opt += new_b
                count += 1
                ratio = (1.0 - (new_b / orig_b)) * 100 if orig_b > 0 else 0
                print(f"  [COMPRESSED] {fname}: {orig_b / 1024:.1f} KB -> {new_b / 1024:.1f} KB ({ratio:.1f}% saved)")
                optimized_files.append((fpath, fname))
            except Exception as e:
                print(f"  [SKIP] Error processing {fname}: {e}")

    saved_mb = (total_orig - total_opt) / (1024 * 1024)
    print(f"\nOptimization Finished!")
    print(f"Total processed: {count} images")
    print(f"Original total size: {total_orig / (1024 * 1024):.2f} MB")
    print(f"Optimized total size: {total_opt / (1024 * 1024):.2f} MB")
    print(f"Total bandwidth saved: {saved_mb:.2f} MB")

    # If Supabase API key is provided, sync to bucket
    if api_key and SUPABASE_URL:
        bucket = SUPABASE_STORAGE_BUCKET or "products"
        print(f"\n=== Syncing {len(optimized_files)} files to Supabase Storage '{bucket}' bucket ===")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "apiKey": api_key,
            "x-upsert": "true",
        }
        uploaded = 0
        failed = 0
        with httpx.Client(timeout=30.0) as client:
            for fpath, fname in optimized_files:
                content_type, _ = mimetypes.guess_type(fpath)
                content_type = content_type or "image/png"
                upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{fname}"
                try:
                    with open(fpath, "rb") as f:
                        data = f.read()
                    resp = client.post(
                        upload_url,
                        headers={**headers, "Content-Type": content_type},
                        content=data
                    )
                    if resp.status_code in (200, 201):
                        print(f"  [SYNCED] {fname}")
                        uploaded += 1
                    else:
                        print(f"  [FAIL] {fname}: {resp.status_code} {resp.text}")
                        failed += 1
                except Exception as e:
                    print(f"  [ERROR] {fname}: {e}")
                    failed += 1
        print(f"\nSupabase Sync Done! Synced: {uploaded}, Failed: {failed}")
    elif not api_key:
        print("\n[NOTE] To automatically overwrite photos in Supabase Storage with these tiny files, run:")
        print("  python scripts/optimize_and_upload_photos.py --upload <YOUR_SUPABASE_SERVICE_OR_ANON_KEY>")

if __name__ == "__main__":
    api_key = None
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--upload" and len(sys.argv) >= 3:
            api_key = sys.argv[2].strip()
        elif not sys.argv[1].startswith("--"):
            api_key = sys.argv[1].strip()
    if not api_key:
        api_key = os.getenv("SUPABASE_KEY")

    run_optimizer(api_key)
