import os
import sys
import json
import threading
import subprocess
import re
import unicodedata
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.easymp4 import EasyMP4
from mutagen.oggvorbis import OggVorbis
from mutagen.asf import ASF
from collections import defaultdict

# --- Configuration ---
MUSIC_DIR = "I:\\music"
SAFE_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".wma"}
FORMAT_PRIORITY = {".flac": 10, ".m4a": 5, ".mp3": 1, ".ogg": 1, ".wma": 1}
MAX_WORKERS = 64  # Safer for handle limits

def normalize(text):
    if not text: return ""
    # NFKC normalization handles composite characters better for Japanese/Unicode
    text = unicodedata.normalize('NFKC', text)
    text = text.lower()
    text = text.replace("’", "'").replace("“", "\"").replace("”", "\"")
    text = re.sub(r'^the\s+', '', text)
    text = text.replace("feat.", "").replace("ft.", "").strip()
    # Keep any alphanumeric character (preserves Japanese, Cyrillic, etc.)
    return "".join(c for c in text if c.isalnum())

def get_metadata(path):
    # ... (rest of get_metadata remains same)
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".mp3":
            audio = MP3(path)
            bitrate = audio.info.bitrate // 1000 if audio.info.bitrate else 0
            length = audio.info.length
            tags = audio.tags
            if tags:
                artist = str(tags.get("TPE1", "Unknown"))
                album = str(tags.get("TALB", "Unknown"))
                title = str(tags.get("TIT2", "Unknown"))
                mbid = str(tags.get("UFID:http://musicbrainz.org", ""))
            else:
                artist, album, title, mbid = "Unknown", "Unknown", "Unknown", ""
        elif ext == ".flac":
            audio = FLAC(path)
            bitrate = audio.info.sample_rate * audio.info.bits_per_sample * audio.info.channels // 1000
            length = audio.info.length
            artist = audio.get("artist", ["Unknown"])[0]
            album = audio.get("album", ["Unknown"])[0]
            title = audio.get("title", ["Unknown"])[0]
            mbid = audio.get("musicbrainz_trackid", [""])[0]
        elif ext == ".m4a":
            audio = EasyMP4(path)
            bitrate = audio.info.bitrate // 1000 if audio.info.bitrate else 0
            length = audio.info.length
            artist = audio.get("artist", ["Unknown"])[0]
            album = audio.get("album", ["Unknown"])[0]
            title = audio.get("title", ["Unknown"])[0]
            mbid = audio.get("musicbrainz_trackid", [""])[0]
        elif ext == ".wma":
            audio = ASF(path)
            bitrate = audio.info.bitrate // 1000 if audio.info.bitrate else 0
            length = audio.info.length
            artist = str(audio.get("Author", ["Unknown"])[0])
            album = str(audio.get("WM/AlbumTitle", ["Unknown"])[0])
            title = str(audio.get("Title", ["Unknown"])[0])
            mbid = str(audio.get("MusicBrainz/Track Id", [""])[0])
        else:
            return None

        return {
            "path": path,
            "artist": artist.strip(),
            "album": album.strip(),
            "title": title.strip(),
            "length": length,
            "bitrate": bitrate,
            "mbid": mbid,
            "ext": ext,
            "score": (bitrate, FORMAT_PRIORITY.get(ext, 0), length)
        }
    except Exception:
        return None

def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except: pass

    commit = "--commit" in sys.argv
    
    library = defaultdict(list)
    lock = threading.Lock()
    processed_count = 0
    errors = []
    
    print(f"[*] Starting scan with {MAX_WORKERS} workers on {MUSIC_DIR}...", flush=True)
    
    file_list = []
    for root, dirs, files in os.walk(MUSIC_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SAFE_EXTENSIONS:
                file_list.append(os.path.join(root, f))
    
    total_files = len(file_list)
    print(f"[*] Found {total_files} candidate files. Indexing...", flush=True)

    def worker(path):
        nonlocal processed_count
        try:
            file_hash = None
            try:
                with open(path, "rb") as f:
                    file_hash = hashlib.md5(f.read(1024*1024)).hexdigest()
            except: pass

            meta = get_metadata(path)
            
            with lock:
                if not meta:
                    if file_hash:
                        h_key = f"RAW_HASH:{file_hash}"
                        library[h_key].append({"path": path, "length": 0, "album": "Unknown", "score": (0,0,0)})
                    processed_count += 1
                    return

                # Normalization
                clean_title = re.sub(r'^\d+\s*[-._]\s*', '', meta['title'])
                norm_title = normalize(clean_title)
                norm_artist = normalize(meta['artist'])
                norm_album = normalize(meta['album'])
                
                # Deduplication Keys - STRICTLY LOCAL (Same Album)
                keys = []
                if meta.get('mbid'):
                    keys.append(f"MBID:{meta['mbid']}")
                
                # LOCAL key includes album name to force same-album grouping
                keys.append(f"LOCAL:{norm_artist}|{norm_album}|{norm_title}")
                
                if file_hash:
                    keys.append(f"HASH:{norm_album}|{file_hash}")

                for k in keys:
                    library[k].append(meta)
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    print(f"    Progress: {processed_count}/{total_files} files ({(processed_count/total_files)*100:.1f}%)", flush=True)
        except Exception as e:
            with lock:
                errors.append(f"{path}: {e}")
                processed_count += 1

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(executor.map(worker, file_list))

    print(f"\n[*] Indexing Complete. Total processed: {processed_count}", flush=True)
    print(f"[*] Total unique groups: {len(library)}", flush=True)
    
    duplicates_found = 0
    potential_savings = 0
    global_marked_paths = set()

    for key in sorted(library.keys()):
        group_items = library[key]
        if len(group_items) < 2: continue

        def get_path_pref(meta):
            p = meta.get('path', '').lower()
            if "compilation" in p or "various" in p or "unknown" in p: return 0
            return 1
        
        remaining = sorted(group_items, key=lambda x: (x.get("score", (0,0,0)), get_path_pref(x)), reverse=True)
        
        while remaining:
            winner = remaining.pop(0)
            if winner['path'] in global_marked_paths: continue
            
            to_remove = []
            for i, loser in enumerate(remaining):
                if loser['path'] in global_marked_paths:
                    to_remove.append(i)
                    continue

                # STRICT COMPARISON: Must be Same Album
                same_album = loser.get('album', '').lower() == winner.get('album', '').lower()
                try:
                    len_diff = abs(float(loser['length']) - float(winner['length']))
                except: len_diff = 999

                is_duplicate = False
                reason = "Exact Match"
                
                # Perfect Metadata Match (LOCAL group) means we can trust the metadata string 
                # and allow for major duration jitter (common in legacy WMA/header corruption).
                duration_tolerance = 5
                if key.startswith("LOCAL"):
                    duration_tolerance = 450 # 7.5 minutes to catch even severe WMA length errors

                if (key.startswith("HASH") or key.startswith("MBID")) and same_album:
                    is_duplicate = True
                elif same_album and len_diff < duration_tolerance:
                    is_duplicate = True
                    reason = "Same Album"
                
                if is_duplicate:
                    global_marked_paths.add(loser['path'])
                    to_remove.append(i)
                    duplicates_found += 1
                    try:
                        size = os.path.getsize(loser['path'])
                        potential_savings += size
                    except: size = 0
                    
                    print(f"\n[GROUP] {key} ({reason})", flush=True)
                    print(f"  [KEEP]   {winner.get('bitrate', 0)}kbps {winner.get('ext', '')} | {winner.get('album')} | {winner['path']}", flush=True)
                    print(f"  [DELETE] {loser.get('bitrate', 0)}kbps {loser.get('ext', '')} | {loser.get('album')} | {loser['path']}", flush=True)
                    
                    if commit:
                        try:
                            os.remove(loser['path'])
                            print(f"    -> DELETED", flush=True)
                        except Exception as e:
                            print(f"    -> ERROR: {e}")
            
            for index in sorted(to_remove, reverse=True):
                remaining.pop(index)

    print("\n" + "="*40, flush=True)
    print(f"[*] Scan complete.", flush=True)
    print(f"[*] Unique duplicates identified: {duplicates_found}", flush=True)
    print(f"[*] Total potential savings (Phase 2): {potential_savings / (1024*1024*1024):.2f} GB", flush=True)
    
    if not commit:
        print("[!] This was a DRY RUN. No files were deleted.", flush=True)
        print("[!] Run with --commit to execute deletions.", flush=True)
    else:
        print("[*] DELETIONS COMPLETE.", flush=True)

if __name__ == "__main__":
    main()
