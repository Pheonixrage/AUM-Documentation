#!/usr/bin/env python3
"""
AUM Legacy Migration → PlayFab Upload Script

Reads legacy_migration.json, splits players into 10 chunks by email hash,
and uploads each chunk to PlayFab Title Internal Data via Admin API.

Also uploads metadata and initializes the claimed registry.

Usage:
    python3 upload_to_playfab.py                    # Upload to DEV (default)
    python3 upload_to_playfab.py --env prod          # Upload to PROD
    python3 upload_to_playfab.py --dry-run            # Preview without uploading
    python3 upload_to_playfab.py --clear              # Remove migration data from PlayFab
"""

import json
import sys
import hashlib
import argparse
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# === PlayFab Configuration ===
PLAYFAB_CONFIG = {
    "dev": {
        "title_id": "15F2B7",
        "secret_key": "JOAWWZ87KNU9KIXBTRG1PFXUHMGBSMQNSSMKKIR6F76GIIAFW3",
        "label": "DEV"
    },
    "prod": {
        "title_id": "158C02",
        "secret_key": "3YET9HU3F5ZBZ5FUQ3DEUOZECKPFDP1FEND8TKKUY5466DESZH",
        "label": "PROD"
    }
}

INPUT_JSON = "/Users/mac/Documents/GitHub/AUM-Documentation/migration/legacy_migration.json"
NUM_CHUNKS = 10


def playfab_admin_call(title_id, secret_key, endpoint, body):
    """Make a PlayFab Admin API call. Returns parsed JSON response."""
    url = f"https://{title_id}.playfabapi.com/Admin/{endpoint}"
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-SecretKey", secret_key)

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"  HTTP {e.code}: {error_body[:500]}")
        raise
    except URLError as e:
        print(f"  Network error: {e.reason}")
        raise


def hash_email(email):
    """Deterministic chunk assignment: hash(email) % NUM_CHUNKS."""
    return int(hashlib.md5(email.lower().encode()).hexdigest(), 16) % NUM_CHUNKS


def split_into_chunks(players_dict):
    """Split players dict into NUM_CHUNKS buckets by email hash."""
    chunks = [{} for _ in range(NUM_CHUNKS)]
    for email, data in players_dict.items():
        chunk_idx = hash_email(email)
        chunks[chunk_idx][email] = data
    return chunks


def format_size(size_bytes):
    """Human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def upload_chunks(config, chunks, name_list, meta, dry_run=False):
    """Upload all chunks + meta + claimed registry to PlayFab."""
    title_id = config["title_id"]
    secret_key = config["secret_key"]
    label = config["label"]

    print(f"\n{'=' * 60}")
    print(f"UPLOADING TO PLAYFAB {label} (Title: {title_id})")
    print(f"{'=' * 60}")

    total_uploaded = 0
    total_bytes = 0

    # Upload each chunk
    for i, chunk in enumerate(chunks):
        chunk_data = {"players": chunk}
        chunk_json = json.dumps(chunk_data, separators=(",", ":"))
        chunk_size = len(chunk_json.encode("utf-8"))
        total_bytes += chunk_size

        key = f"LegacyMigration_{i}"
        player_count = len(chunk)

        if chunk_size > 200_000:
            print(f"  WARNING: {key} is {format_size(chunk_size)} — exceeds 200KB limit!")
            print(f"           {player_count} players. Consider increasing NUM_CHUNKS.")
            continue

        print(f"  {key}: {player_count} players, {format_size(chunk_size)}", end="")

        if dry_run:
            print(" [DRY RUN — skipped]")
        else:
            try:
                playfab_admin_call(title_id, secret_key, "SetTitleInternalData", {
                    "Key": key,
                    "Value": chunk_json
                })
                print(" ✓")
                total_uploaded += 1
                time.sleep(0.3)  # Rate limit courtesy
            except Exception as e:
                print(f" FAILED: {e}")

    # Upload name list
    name_json = json.dumps(name_list, separators=(",", ":"))
    name_size = len(name_json.encode("utf-8"))
    total_bytes += name_size
    print(f"  LegacyMigration_Names: {len(name_list)} names, {format_size(name_size)}", end="")

    if dry_run:
        print(" [DRY RUN — skipped]")
    else:
        try:
            playfab_admin_call(title_id, secret_key, "SetTitleInternalData", {
                "Key": "LegacyMigration_Names",
                "Value": name_json
            })
            print(" ✓")
            total_uploaded += 1
            time.sleep(0.3)
        except Exception as e:
            print(f" FAILED: {e}")

    # Upload metadata
    meta_json = json.dumps(meta, separators=(",", ":"))
    meta_size = len(meta_json.encode("utf-8"))
    total_bytes += meta_size
    print(f"  LegacyMigration_Meta: {format_size(meta_size)}", end="")

    if dry_run:
        print(" [DRY RUN — skipped]")
    else:
        try:
            playfab_admin_call(title_id, secret_key, "SetTitleInternalData", {
                "Key": "LegacyMigration_Meta",
                "Value": meta_json
            })
            print(" ✓")
            total_uploaded += 1
            time.sleep(0.3)
        except Exception as e:
            print(f" FAILED: {e}")

    # Initialize empty claimed registry (only if not already present)
    print(f"  LegacyMigration_Claimed: initializing empty registry", end="")

    if dry_run:
        print(" [DRY RUN — skipped]")
    else:
        try:
            # Check if already exists
            existing = playfab_admin_call(title_id, secret_key, "GetTitleInternalData", {
                "Keys": ["LegacyMigration_Claimed"]
            })
            if existing.get("data", {}).get("Data", {}).get("LegacyMigration_Claimed"):
                print(" [already exists — preserved]")
            else:
                playfab_admin_call(title_id, secret_key, "SetTitleInternalData", {
                    "Key": "LegacyMigration_Claimed",
                    "Value": "{}"
                })
                print(" ✓")
            total_uploaded += 1
        except Exception as e:
            print(f" FAILED: {e}")

    print(f"\n--- Upload Summary ---")
    print(f"  Keys uploaded: {total_uploaded}")
    print(f"  Total data size: {format_size(total_bytes)}")
    if dry_run:
        print(f"  Mode: DRY RUN (nothing was uploaded)")


def clear_migration_data(config, dry_run=False):
    """Remove all migration keys from PlayFab Title Internal Data."""
    title_id = config["title_id"]
    secret_key = config["secret_key"]
    label = config["label"]

    print(f"\n{'=' * 60}")
    print(f"CLEARING MIGRATION DATA FROM PLAYFAB {label} (Title: {title_id})")
    print(f"{'=' * 60}")

    keys_to_clear = [f"LegacyMigration_{i}" for i in range(NUM_CHUNKS)]
    keys_to_clear += ["LegacyMigration_Names", "LegacyMigration_Meta", "LegacyMigration_Claimed"]

    for key in keys_to_clear:
        print(f"  Deleting {key}...", end="")
        if dry_run:
            print(" [DRY RUN — skipped]")
        else:
            try:
                # Setting value to None/empty deletes the key
                playfab_admin_call(title_id, secret_key, "SetTitleInternalData", {
                    "Key": key,
                    "Value": None
                })
                print(" ✓")
                time.sleep(0.3)
            except Exception as e:
                print(f" FAILED: {e}")

    print(f"\n  Done. All migration keys cleared from {label}.")


def verify_upload(config):
    """Read back uploaded data and verify chunk integrity."""
    title_id = config["title_id"]
    secret_key = config["secret_key"]
    label = config["label"]

    print(f"\n{'=' * 60}")
    print(f"VERIFYING UPLOAD ON PLAYFAB {label} (Title: {title_id})")
    print(f"{'=' * 60}")

    # Read meta
    try:
        result = playfab_admin_call(title_id, secret_key, "GetTitleInternalData", {
            "Keys": ["LegacyMigration_Meta"]
        })
        meta_value = result.get("data", {}).get("Data", {}).get("LegacyMigration_Meta")
        if meta_value:
            meta = json.loads(meta_value)
            print(f"  Meta: {json.dumps(meta, indent=2)}")
        else:
            print("  WARNING: LegacyMigration_Meta not found!")
            return False
    except Exception as e:
        print(f"  Failed to read meta: {e}")
        return False

    # Read each chunk and count players
    total_players = 0
    for i in range(NUM_CHUNKS):
        key = f"LegacyMigration_{i}"
        try:
            result = playfab_admin_call(title_id, secret_key, "GetTitleInternalData", {
                "Keys": [key]
            })
            value = result.get("data", {}).get("Data", {}).get(key)
            if value:
                chunk = json.loads(value)
                count = len(chunk.get("players", {}))
                total_players += count
                print(f"  {key}: {count} players, {format_size(len(value))}")
            else:
                print(f"  {key}: empty/missing")
            time.sleep(0.2)
        except Exception as e:
            print(f"  {key}: FAILED to read — {e}")

    print(f"\n  Total players across all chunks: {total_players}")
    expected = meta.get("totalPlayers", 0) if meta_value else "unknown"
    print(f"  Expected from meta: {expected}")

    if total_players == expected:
        print(f"  VERIFICATION: PASSED ✓")
        return True
    else:
        print(f"  VERIFICATION: MISMATCH — check chunks!")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload AUM legacy migration data to PlayFab")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev",
                        help="Target environment (default: dev)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview upload without making API calls")
    parser.add_argument("--clear", action="store_true",
                        help="Remove all migration data from PlayFab")
    parser.add_argument("--verify", action="store_true",
                        help="Verify uploaded data integrity")
    parser.add_argument("--input", default=INPUT_JSON,
                        help=f"Input JSON file (default: {INPUT_JSON})")

    args = parser.parse_args()
    config = PLAYFAB_CONFIG[args.env]

    if args.clear:
        if not args.dry_run:
            print(f"\n  WARNING: This will delete ALL migration data from {config['label']}!")
            confirm = input("  Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("  Aborted.")
                return
        clear_migration_data(config, dry_run=args.dry_run)
        return

    if args.verify:
        verify_upload(config)
        return

    # Load migration JSON
    print(f"Loading {args.input}...")
    try:
        with open(args.input, "r") as f:
            migration_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.input}")
        print("Run parse_legacy_db.py first to generate the migration JSON.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    players = migration_data.get("players", {})
    name_list = migration_data.get("nameList", [])
    total_players = len(players)
    total_avatars = migration_data.get("totalAvatars", 0)
    export_date = migration_data.get("exportDate", "")

    print(f"  Players: {total_players}")
    print(f"  Avatars: {total_avatars}")
    print(f"  Names: {len(name_list)}")
    print(f"  Export date: {export_date}")

    # Split into chunks
    chunks = split_into_chunks(players)

    print(f"\nChunk distribution:")
    for i, chunk in enumerate(chunks):
        chunk_json = json.dumps({"players": chunk}, separators=(",", ":"))
        print(f"  Chunk {i}: {len(chunk)} players, {format_size(len(chunk_json.encode('utf-8')))}")

    # Build metadata
    meta = {
        "totalPlayers": total_players,
        "totalAvatars": total_avatars,
        "totalNames": len(name_list),
        "numChunks": NUM_CHUNKS,
        "exportDate": export_date,
        "uploadDate": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "hashFunction": "md5(email.lower()) % 10"
    }

    # Upload
    upload_chunks(config, chunks, name_list, meta, dry_run=args.dry_run)

    # Auto-verify after upload
    if not args.dry_run:
        print("\nRunning post-upload verification...")
        verify_upload(config)


if __name__ == "__main__":
    main()
