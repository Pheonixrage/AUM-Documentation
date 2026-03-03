#!/usr/bin/env python3
"""
AUM Legacy Migration Progress Report

Queries PlayFab for migration status — how many legacy accounts have been
claimed, which ones are pending, and any errors from PlayStream events.

Usage:
    python3 generate_report.py              # DEV (default)
    python3 generate_report.py --env prod   # PROD
"""

import json
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timezone

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

NUM_CHUNKS = 10


def playfab_admin_call(title_id, secret_key, endpoint, body):
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


def main():
    parser = argparse.ArgumentParser(description="AUM Legacy Migration Progress Report")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    args = parser.parse_args()

    config = PLAYFAB_CONFIG[args.env]
    title_id = config["title_id"]
    secret_key = config["secret_key"]
    label = config["label"]

    print(f"{'=' * 60}")
    print(f"AUM LEGACY MIGRATION PROGRESS REPORT — {label}")
    print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'=' * 60}")

    # 1. Read metadata
    print("\n--- Migration Data Status ---")
    try:
        result = playfab_admin_call(title_id, secret_key, "GetTitleInternalData", {
            "Keys": ["LegacyMigration_Meta"]
        })
        meta_value = result.get("data", {}).get("Data", {}).get("LegacyMigration_Meta")
        if meta_value:
            meta = json.loads(meta_value)
            print(f"  Total legacy players: {meta.get('totalPlayers', '?')}")
            print(f"  Total legacy avatars: {meta.get('totalAvatars', '?')}")
            print(f"  Total reserved names: {meta.get('totalNames', '?')}")
            print(f"  Data exported: {meta.get('exportDate', '?')}")
            print(f"  Data uploaded: {meta.get('uploadDate', '?')}")
            print(f"  Chunks: {meta.get('numChunks', '?')}")
        else:
            print("  No migration data found! Run upload_to_playfab.py first.")
            return
    except Exception as e:
        print(f"  Failed to read migration meta: {e}")
        return

    # 2. Read claimed registry
    print("\n--- Claim Status ---")
    try:
        result = playfab_admin_call(title_id, secret_key, "GetTitleInternalData", {
            "Keys": ["LegacyMigration_Claimed"]
        })
        claimed_value = result.get("data", {}).get("Data", {}).get("LegacyMigration_Claimed", "{}")
        claimed = json.loads(claimed_value) if claimed_value else {}

        total = meta.get("totalPlayers", 0)
        claimed_count = len(claimed)
        remaining = total - claimed_count
        pct = (claimed_count / total * 100) if total > 0 else 0

        print(f"  Claimed: {claimed_count} / {total} ({pct:.1f}%)")
        print(f"  Remaining: {remaining}")

        if claimed:
            print(f"\n--- Claimed Accounts ({claimed_count}) ---")
            for email, info in sorted(claimed.items()):
                parts = info.split("|")
                pfid = parts[0] if len(parts) > 0 else "?"
                date = parts[1] if len(parts) > 1 else "?"
                print(f"  {email} → {pfid} (claimed: {date})")

    except Exception as e:
        print(f"  Failed to read claimed registry: {e}")

    # 3. Chunk health check
    print(f"\n--- Chunk Health ---")
    total_in_chunks = 0
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
                total_in_chunks += count
                size_kb = len(value) / 1024
                print(f"  {key}: {count} players ({size_kb:.1f} KB) ✓")
            else:
                print(f"  {key}: MISSING!")
        except Exception as e:
            print(f"  {key}: ERROR — {e}")

    if total_in_chunks == meta.get("totalPlayers", 0):
        print(f"  Total: {total_in_chunks} — matches meta ✓")
    else:
        print(f"  Total: {total_in_chunks} — MISMATCH (expected {meta.get('totalPlayers', '?')})")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
