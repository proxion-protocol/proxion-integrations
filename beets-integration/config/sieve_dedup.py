import os
import sys
import hashlib
import threading
import csv
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# --- Configuration ---
ROOT_DIR = "/mnt/host/i/music"
CSV_PATH = "/storage/stash/music_sizes_full.csv"
SAFE_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".wma"}
MAX_WORKERS = 128  # High concurrency for NVMe/Thunderbolt

def get_partial_hash(path, chunk_size=16384):
    """Computes a hash of the first and last chunks of a file."""
    try:
        with open(path, 'rb') as f:
            head = f.read(chunk_size)
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size > chunk_size:
                f.seek(max(0, size - chunk_size))
                tail = f.read(chunk_size)
            else:
                tail = b""
        return hashlib.md5(head + tail).hexdigest()
    except Exception:
        return None

def main():
    commit = "--commit" in sys.argv
    
    if not os.path.exists(CSV_PATH):
        print(f"[!] Error: Stage 1 CSV not found at {CSV_PATH}")
        return

    print(f"[*] Sieve Stage 1: Loading Size Census from {CSV_PATH}...", flush=True)
    
    size_groups = defaultdict(list)
    total_indexed = 0
    
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                size = int(row['Length'])
                host_path = row['FullName']
                # Path Mapping: I:\music\Foo -> /mnt/host/i/music/Foo
                container_path = host_path.replace("I:\\music\\", "/mnt/host/i/music/").replace("\\", "/")
                
                size_groups[size].append(container_path)
                total_indexed += 1
                if total_indexed % 10000 == 0:
                    print(f"    Loaded {total_indexed} files...", end="\r", flush=True)
            except Exception:
                continue

    print(f"\n[*] Stage 1 Complete. Loaded {total_indexed} files.", flush=True)
    
    # Candidates for Stage 2 (collisions in size)
    candidates = []
    unique_count = 0
    for size, paths in size_groups.items():
        if len(paths) > 1:
            candidates.extend(paths)
        else:
            unique_count += 1
            
    print(f"[*] Found {unique_count} unique sizes. {len(candidates)} files require Stage 2 (Partial Hashing).", flush=True)
    
    if not candidates:
        print("[*] No potential bitwise duplicates found. exiting.")
        return

    print(f"[*] Sieve Stage 2: Starting Partial Hashing with {MAX_WORKERS} workers...", flush=True)
    
    hash_groups = defaultdict(list)
    lock = threading.Lock()
    processed_count = 0
    total_candidates = len(candidates)

    def hash_worker(path):
        nonlocal processed_count
        h = get_partial_hash(path)
        if h:
            try:
                # Combine size and partial hash for collision avoidance
                size = os.path.getsize(path)
                key = f"{size}_{h}"
                with lock:
                    hash_groups[key].append(path)
            except:
                pass
        
        with lock:
            processed_count += 1
            if processed_count % 1000 == 0:
                print(f"    Hashed {processed_count}/{total_candidates} files ({(processed_count/total_candidates)*100:.1f}%)", end="\r", flush=True)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(hash_worker, candidates)

    print(f"\n[*] Stage 2 Complete.", flush=True)
    
    library_stats = {'groups': 0, 'deleted_count': 0, 'savings': 0}
    
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    
    for key, paths in hash_groups.items():
        if len(paths) > 1:
            # Special Handling for Art: Only deduplicate if in the same directory
            ext = os.path.splitext(paths[0])[1].lower()
            if ext in image_extensions:
                # Group by directory
                dirs = defaultdict(list)
                for p in paths:
                    dirs[os.path.dirname(p)].append(p)
                
                # For each directory, keep one image and delete the rest
                for d, d_paths in dirs.items():
                    if len(d_paths) > 1:
                        d_paths.sort(key=len)
                        winner = d_paths[0]
                        losers = d_paths[1:]
                        process_group(key + f"_dir_{d}", winner, losers, commit, library_stats)
            else:
                # Standard Junk/Files: Global deduplication
                paths.sort(key=len)
                winner = paths[0]
                losers = paths[1:]
                process_group(key, winner, losers, commit, library_stats)

    print("\n" + "="*40)
    print(f"[*] Multi-Stage Sieve Result:")
    print(f"[*] Total Duplicate Groups: {library_stats['groups']}")
    print(f"[*] Total Redundant Files: {library_stats['deleted_count']}")
    print(f"[*] Total Reclaimable Space: {library_stats['savings'] / (1024*1024*1024):.2f} GB")
    
    if not commit:
        print("[!] This was a DRY RUN (Content-based + Safe Art Protection).")
        print("[!] Run with --commit to execute deletions.")
    else:
        print("[*] CLEANUP COMPLETE.")

def process_group(key, winner, losers, commit, stats):
    stats['groups'] += 1
    print(f"\n[GROUP] {key}")
    print(f"  [KEEP]   {winner}")
    
    for loser in losers:
        try:
            size = os.path.getsize(loser)
            stats['savings'] += size
            stats['deleted_count'] += 1
            print(f"  [DELETE] {loser}")
            
            if commit:
                os.remove(loser)
                print(f"    -> DELETED")
        except Exception as e:
            print(f"    -> ERROR: {e}")

if __name__ == "__main__":
    main()
