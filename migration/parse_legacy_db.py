#!/usr/bin/env python3
"""
AUM Legacy Database → PlayFab Migration Parser

Reads DatabaseBackupAUM.sql and exports structured JSON for PlayFab migration.
Only processes aum_users_oauth (Google) accounts.
Only includes Completed=1 AND Enabled=1 avatars.
Cross-references aum_users by email to find avatars under old AccountIDs.

Usage:
    python3 parse_legacy_db.py /path/to/DatabaseBackupAUM.sql
    python3 parse_legacy_db.py  # uses default path
"""

import re
import sys
import json
import uuid
import hashlib
from collections import defaultdict
from datetime import datetime, timezone

# === Configuration ===
DEFAULT_SQL_PATH = "/Users/mac/Downloads/DatabaseBackupAUM.sql"
OUTPUT_JSON = "/Users/mac/Documents/GitHub/AUM-Documentation/migration/legacy_migration.json"
OUTPUT_REPORT = "/Users/mac/Documents/GitHub/AUM-Documentation/migration/migration_report.txt"
EXCLUDE_ADMIN = True
NUM_CHUNKS = 10


def parse_sql_file(filepath):
    """Read SQL file and return raw content."""
    print(f"Reading SQL file: {filepath}")
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    print(f"  File size: {len(content):,} bytes")
    return content


def extract_rows_robust(content, table_name):
    """
    Extract INSERT rows using a state machine that correctly handles
    multi-line strings with newlines (e.g., JSON in RegInfo).
    Returns list of raw row strings.
    """
    # Find the INSERT INTO statement
    insert_pattern = rf"INSERT INTO `{table_name}`\s+\([^)]+\)\s+VALUES\s*\n"
    match = re.search(insert_pattern, content)
    if not match:
        print(f"  WARNING: No INSERT data found for {table_name}")
        return []

    start = match.end()
    rows = []
    i = start
    length = len(content)

    while i < length:
        # Skip whitespace/tabs
        while i < length and content[i] in (' ', '\t', '\n', '\r'):
            i += 1

        if i >= length or content[i] != '(':
            break

        # Found start of a row — parse until matching closing paren
        i += 1  # skip opening (
        row_start = i
        in_string = False
        escape_next = False
        depth = 1

        while i < length and depth > 0:
            ch = content[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if ch == '\\' and in_string:
                escape_next = True
                i += 1
                continue

            if ch == "'" and not escape_next:
                in_string = not in_string
                i += 1
                continue

            if not in_string:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        break
            i += 1

        raw_row = content[row_start:i]
        rows.append(raw_row)
        i += 1  # skip closing )

        # Skip comma or semicolon
        while i < length and content[i] in (' ', '\t', '\n', '\r'):
            i += 1
        if i < length and content[i] == ',':
            i += 1
        elif i < length and content[i] == ';':
            break

    print(f"  {table_name}: {len(rows)} rows parsed")
    return rows


def split_sql_row(raw_row):
    """
    Split a SQL INSERT row into individual values, handling quoted strings
    and nested content correctly.
    """
    values = []
    current = []
    in_string = False
    escape_next = False
    paren_depth = 0

    for ch in raw_row:
        if escape_next:
            current.append(ch)
            escape_next = False
            continue

        if ch == '\\' and in_string:
            current.append(ch)
            escape_next = True
            continue

        if ch == "'" and not escape_next:
            in_string = not in_string
            current.append(ch)
            continue

        if not in_string:
            if ch == '(':
                paren_depth += 1
                current.append(ch)
            elif ch == ')':
                paren_depth -= 1
                current.append(ch)
            elif ch == ',' and paren_depth == 0:
                values.append(''.join(current).strip())
                current = []
                continue
            else:
                current.append(ch)
        else:
            current.append(ch)

    remainder = ''.join(current).strip()
    if remainder:
        values.append(remainder)

    return values


def parse_sql_value(val):
    """Parse a single SQL value into a Python type."""
    val = val.strip()
    if val == 'NULL':
        return None
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1].replace("\\'", "'").replace("\\\\", "\\").replace("\\n", "\n").replace("\\r", "\r")
    if val.startswith("_binary 0x"):
        hex_str = val[len("_binary 0x"):]
        return bytes.fromhex(hex_str)
    if val.startswith("b'") and val.endswith("'"):
        bit_str = val[2:-1]
        return int(bit_str, 2) if bit_str else 0
    try:
        if '.' in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def parse_table_rows(raw_rows, column_names):
    """Parse raw SQL rows into list of dicts."""
    parsed = []
    skipped = 0
    for raw_row in raw_rows:
        vals = split_sql_row(raw_row)
        if len(vals) != len(column_names):
            skipped += 1
            continue
        row_dict = {}
        for col, val in zip(column_names, vals):
            row_dict[col] = parse_sql_value(val)
        parsed.append(row_dict)
    if skipped:
        print(f"    (skipped {skipped} rows with column mismatch)")
    return parsed


def decode_elementals(binary_data):
    """Decode elemental binary blob to byte array."""
    if binary_data is None:
        return [0, 0, 0, 0]
    if isinstance(binary_data, bytes):
        padded = binary_data.ljust(4, b'\x00')
        return list(padded[:4])
    return [0, 0, 0, 0]


def generate_default_wear_item_codes(fighting_style, fighter_class):
    """
    Generate default tier-1 wearItemCodes for an avatar.
    Encoding: style * 160 + class * 80 + type * 10 + identifier
    Types: Head=0, Torso=1, Hands=2, Pants=3, Legs=4, Weapons=5
    Default identifier = 1
    """
    codes = []
    for item_type in range(6):
        code = fighting_style * 160 + fighter_class * 80 + item_type * 10 + 1
        codes.append(code)
    return codes


def hash_email(email):
    """Deterministic hash for email -> chunk bucket."""
    return int(hashlib.md5(email.lower().encode()).hexdigest(), 16) % NUM_CHUNKS


def build_avatar_entry(av, items_by_avatar, daily_by_avatar, stats, email):
    """Build a single avatar entry in 2.0 format."""
    avatar_uuid = av["UniqueID"]
    nickname = av.get("Nickname") or ""
    fighting_style = av.get("FightingStyle", 0) or 0
    fighter_class = av.get("FighterClass", 0) or 0

    avatar_items = items_by_avatar.get(avatar_uuid, [])
    item_codes = [it["ItemCode"] for it in avatar_items if it.get("ItemCode") is not None]
    if not item_codes:
        item_codes = generate_default_wear_item_codes(fighting_style, fighter_class)

    elementals = decode_elementals(av.get("Elementals"))

    daily_rewards = daily_by_avatar.get(avatar_uuid, [])
    daily_reward_data = None
    if daily_rewards:
        daily_reward_data = {
            "rewardType": daily_rewards[0].get("RewardType", 0),
            "day": daily_rewards[0].get("Day", 0),
            "lastRewardTime": daily_rewards[0].get("LastRewardTime", 0)
        }

    bronze = av.get("Bronze", 0) or 0
    silver = av.get("Silver", 0) or 0
    lives = av.get("Lives", 5) or 5
    time_shards = av.get("TimeShards", 0) or 0
    hell_shards = av.get("HellShards", 0) or 0
    bhakti_tokens = av.get("BakthiTokens", 0) or 0
    gnana_tokens = av.get("GnanaTokens", 0) or 0
    wins = av.get("Wins", 0) or 0
    losses = av.get("Loss", 0) or 0

    # Per-avatar karma data
    sattva = av.get("Sattva", 0) or 0
    rajas = av.get("Rajas", 0) or 0
    tamas = av.get("Tamas", 0) or 0
    guna = av.get("Guna", 0) or 0  # 0=Sattva, 1=Rajas, 2=Tamas
    rajas_actions = av.get("RajasActions", 0) or 0
    tamas_actions = av.get("TamasActions", 0) or 0
    sattva_actions = av.get("SattvaActions", 0) or 0

    # Per-avatar hell progress
    hell_time = av.get("HellTime", 0) or 0
    max_hell_time = av.get("MaxHellTime", 0) or 0

    if bronze > 50000:
        stats["outlier_accounts"].append({
            "email": email, "nickname": nickname, "bronze": bronze
        })

    stats["total_avatars"] += 1
    stats["total_items"] += len(item_codes)
    stats["style_distribution"][fighting_style] += 1
    stats["god_distribution"][av.get("GodSelection", 0) or 0] += 1

    entry = {
        "uniqueID": str(uuid.uuid4()),
        "oldUniqueID": avatar_uuid,
        "nickName": nickname,
        "fightingStyle": fighting_style,
        "fighterClass": fighter_class,
        "godSelected": av.get("GodSelection", 0) or 0,
        "elementalSelected": elementals,
        "weaponVariant": av.get("WeaponVariant", 0) or 0,
        "lastActive": av.get("LastActive", 0) or 0,
        "isCompleted": 1,
        "isDeleted": 0,
        "deletedAt": "",
        "wearItemCodes": item_codes,
        "currencies": {
            "bronze": bronze,
            "silver": silver,
            "gold": 0,
            "lives": min(lives, 99),
            "timeShards": time_shards,
            "hellShards": hell_shards,
            "bhaktiTokens": bhakti_tokens,
            "gnanaTokens": gnana_tokens,
            "wins": wins,
            "losses": losses,
            "sattva": sattva,
            "rajas": rajas,
            "tamas": tamas,
            "guna": guna,
            "rajasActions": rajas_actions,
            "tamasActions": tamas_actions,
            "sattvaActions": sattva_actions,
            "hellTime": hell_time,
            "maxHellTime": max_hell_time
        }
    }
    if daily_reward_data:
        entry["dailyReward"] = daily_reward_data

    return entry


def main():
    sql_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SQL_PATH
    content = parse_sql_file(sql_path)

    # ============================================================
    # 1. Parse all tables using robust state-machine parser
    # ============================================================
    print("\n=== Parsing tables ===")

    # aum_users_oauth (has multi-line JSON in RegInfo)
    oauth_columns = [
        "RegDate", "AccountID", "EmailID", "Name", "Photo", "Provider",
        "RegInfo", "UserAgent", "IPAddr", "AccountStatus", "IsAdmin", "RegSource"
    ]
    oauth_rows = extract_rows_robust(content, "aum_users_oauth")
    oauth_data = parse_table_rows(oauth_rows, oauth_columns)

    # aum_users (for cross-referencing emails → AccountIDs that own avatars)
    users_columns = [
        "RegisterDate", "AccountID", "LoginID", "Password", "AccountStatus",
        "Name", "EmailID", "Phone", "IPAddr", "UserAgent", "IsAdmin", "IsBot"
    ]
    users_rows = extract_rows_robust(content, "aum_users")
    users_data = parse_table_rows(users_rows, users_columns)

    # aum_avatar
    avatar_columns = [
        "AccountID", "UniqueID", "Nickname", "FightingStyle", "FighterClass",
        "GodSelection", "Elementals", "WeaponVariant", "LastActive", "Completed",
        "Enabled", "Wins", "Loss", "TimeShards", "Lives", "Tamas", "Rajas",
        "Sattva", "Guna", "Bronze", "Silver", "RajasActions", "TamasActions",
        "SattvaActions", "HellShards", "HellTime", "MaxHellTime",
        "MeditationSetTime", "MeditationTrigBakthi", "MeditationTrigGnana",
        "MeditationTotalBakthi", "MeditationTotalGnana", "MeditationStartBakthi",
        "MeditationStartGnana", "MeditationElapsedBakthi", "MeditationElapsedGnana",
        "MeditationState", "MeditationCompleteBakthi", "MeditationCompleteGnana",
        "BakthiTokens", "GnanaTokens"
    ]
    avatar_rows = extract_rows_robust(content, "aum_avatar")
    avatar_data = parse_table_rows(avatar_rows, avatar_columns)

    # aum_items
    items_columns = [
        "AccountID", "ItemUUID", "ItemCode", "AvatarUUID",
        "ItemInformation", "Used", "Active", "GenerateDate"
    ]
    items_rows = extract_rows_robust(content, "aum_items")
    items_data = parse_table_rows(items_rows, items_columns)

    # aum_currency
    currency_columns = ["AccountID", "Gold"]
    currency_rows = extract_rows_robust(content, "aum_currency")
    currency_data = parse_table_rows(currency_rows, currency_columns)

    # aum_social
    social_columns = ["AccountID", "ProfileName", "FriendID", "ProfileImageID"]
    social_rows = extract_rows_robust(content, "aum_social")
    social_data = parse_table_rows(social_rows, social_columns)

    # aum_daily_reward
    daily_columns = ["AvatarID", "RewardType", "Day", "LastRewardTime"]
    daily_rows = extract_rows_robust(content, "aum_daily_reward")
    daily_data = parse_table_rows(daily_rows, daily_columns)

    # aum_settings
    settings_columns = ["AccountID", "Settings"]
    settings_rows = extract_rows_robust(content, "aum_settings")
    settings_data = parse_table_rows(settings_rows, settings_columns)

    # ============================================================
    # 2. Build lookup indices
    # ============================================================
    print("\n=== Building indices ===")

    # OAuth: email → OAuth row (most recent by RegDate)
    email_to_oauth = {}
    for row in oauth_data:
        email = (row.get("EmailID") or "").lower().strip()
        if not email:
            continue
        if EXCLUDE_ADMIN and row.get("IsAdmin") == 1:
            continue
        if email in email_to_oauth:
            if (row.get("RegDate") or "") > (email_to_oauth[email].get("RegDate") or ""):
                email_to_oauth[email] = row
        else:
            email_to_oauth[email] = row
    print(f"  Unique OAuth emails: {len(email_to_oauth)}")

    # aum_users: email → list of AccountIDs (for cross-reference)
    users_email_to_accounts = defaultdict(list)
    for row in users_data:
        email = (row.get("EmailID") or "").lower().strip()
        if not email:
            continue
        aid = row.get("AccountID")
        if aid:
            users_email_to_accounts[email].append(aid)
    print(f"  Unique user emails (aum_users): {len(users_email_to_accounts)}")

    # Avatars by AccountID
    avatars_by_account = defaultdict(list)
    for row in avatar_data:
        aid = row.get("AccountID")
        if aid:
            avatars_by_account[aid].append(row)
    print(f"  Accounts with avatars: {len(avatars_by_account)}")

    # Items by AvatarUUID
    items_by_avatar = defaultdict(list)
    for row in items_data:
        auuid = row.get("AvatarUUID")
        if auuid:
            items_by_avatar[auuid].append(row)
    print(f"  Avatars with items: {len(items_by_avatar)}")

    # Currency by AccountID
    gold_by_account = {}
    for row in currency_data:
        aid = row.get("AccountID")
        if aid:
            gold_by_account[aid] = row.get("Gold", 0)

    # Social by AccountID
    social_by_account = {}
    for row in social_data:
        aid = row.get("AccountID")
        if aid:
            social_by_account[aid] = row

    # Daily rewards by AvatarID
    daily_by_avatar = defaultdict(list)
    for row in daily_data:
        avid = row.get("AvatarID")
        if avid:
            daily_by_avatar[avid].append(row)

    # Settings by AccountID
    settings_by_account = {}
    for row in settings_data:
        aid = row.get("AccountID")
        if aid:
            settings_by_account[aid] = row.get("Settings")

    # ============================================================
    # 3. Build migration data per player
    #    Cross-reference: for each OAuth email, find ALL AccountIDs
    #    (both OAuth AccountID and aum_users AccountIDs) that have avatars
    # ============================================================
    print("\n=== Building migration data ===")

    players = {}
    all_names = []
    stats = {
        "total_oauth_emails": len(email_to_oauth),
        "players_with_avatars": 0,
        "players_without_avatars": 0,
        "players_from_oauth_aid": 0,
        "players_from_users_aid": 0,
        "players_from_both": 0,
        "total_avatars": 0,
        "skipped_incomplete": 0,
        "skipped_disabled": 0,
        "total_items": 0,
        "outlier_accounts": [],
        "avatar_counts": defaultdict(int),
        "style_distribution": defaultdict(int),
        "god_distribution": defaultdict(int),
    }

    for email, oauth_row in email_to_oauth.items():
        oauth_account_id = oauth_row["AccountID"]

        # Collect ALL AccountIDs for this email
        all_account_ids = set()
        all_account_ids.add(oauth_account_id)

        # Also check aum_users for same email → additional AccountIDs
        for aid in users_email_to_accounts.get(email, []):
            all_account_ids.add(aid)

        # Gather avatars from ALL AccountIDs
        all_avatars = []
        source_oauth = False
        source_users = False
        for aid in all_account_ids:
            avs = avatars_by_account.get(aid, [])
            if avs and aid == oauth_account_id:
                source_oauth = True
            elif avs:
                source_users = True
            all_avatars.extend(avs)

        if not all_avatars:
            stats["players_without_avatars"] += 1
            continue

        stats["players_with_avatars"] += 1
        if source_oauth and source_users:
            stats["players_from_both"] += 1
        elif source_oauth:
            stats["players_from_oauth_aid"] += 1
        else:
            stats["players_from_users_aid"] += 1

        # Filter: Completed=1 AND Enabled=1
        valid_avatars = []
        seen_nicknames = set()
        for av in all_avatars:
            if av.get("Completed") != 1:
                stats["skipped_incomplete"] += 1
                continue
            if av.get("Enabled") != 1:
                stats["skipped_disabled"] += 1
                continue
            # Deduplicate by nickname (same avatar might appear under multiple AccountIDs)
            nick = (av.get("Nickname") or "").lower()
            uid = av.get("UniqueID", "")
            dedup_key = uid  # Use UniqueID as dedup key
            if dedup_key in seen_nicknames:
                continue
            seen_nicknames.add(dedup_key)
            valid_avatars.append(av)

        if not valid_avatars:
            continue

        stats["avatar_counts"][len(valid_avatars)] += 1

        # Build avatar list
        avatar_list = []
        for av in valid_avatars:
            entry = build_avatar_entry(av, items_by_avatar, daily_by_avatar, stats, email)
            avatar_list.append(entry)
            if entry["nickName"]:
                all_names.append(entry["nickName"])

        # Use most recently active avatar for account-level aggregation
        # (sorted by LastActive descending, then by most wins as tiebreaker)
        best_av = max(valid_avatars, key=lambda a: (
            a.get("LastActive", 0) or 0,
            a.get("Wins", 0) or 0
        ))

        # Karma data (from most active avatar — also stored per-avatar in currencies)
        karma = {
            "tamas": best_av.get("Tamas", 0) or 0,
            "rajas": best_av.get("Rajas", 0) or 0,
            "sattva": best_av.get("Sattva", 0) or 0,
            "guna": best_av.get("Guna", 0) or 0,
            "rajasActions": best_av.get("RajasActions", 0) or 0,
            "tamasActions": best_av.get("TamasActions", 0) or 0,
            "sattvaActions": best_av.get("SattvaActions", 0) or 0,
        }

        # Meditation data (from most active avatar)
        meditation = {
            "meditationState": best_av.get("MeditationState", 0) or 0,
            "meditationSetTime": best_av.get("MeditationSetTime", 0) or 0,
            "bhaktiTimerTotal": best_av.get("MeditationTotalBakthi", 3600) or 3600,
            "gnanaTimerTotal": best_av.get("MeditationTotalGnana", 3600) or 3600,
            "bhaktiTimerRemaining": max(0, (best_av.get("MeditationTotalBakthi", 3600) or 3600)
                                        - (best_av.get("MeditationElapsedBakthi", 0) or 0)),
            "gnanaTimerRemaining": max(0, (best_av.get("MeditationTotalGnana", 3600) or 3600)
                                        - (best_av.get("MeditationElapsedGnana", 0) or 0)),
            "meditationCompleteBhakti": bool(best_av.get("MeditationCompleteBakthi", 0)),
            "meditationCompleteGnana": bool(best_av.get("MeditationCompleteGnana", 0)),
        }

        # Social data — check all AccountIDs
        social_info = None
        for aid in all_account_ids:
            social = social_by_account.get(aid)
            if social:
                social_info = {
                    "friendCode": social.get("FriendID", ""),
                    "profileName": social.get("ProfileName", ""),
                    "profileImageId": social.get("ProfileImageID", 0) or 0
                }
                break

        # Settings — check all AccountIDs
        settings_parsed = None
        for aid in all_account_ids:
            settings_raw = settings_by_account.get(aid)
            if settings_raw:
                try:
                    settings_parsed = json.loads(settings_raw)
                except (json.JSONDecodeError, TypeError):
                    pass
                break

        # Account gold — sum from all AccountIDs
        account_gold = 0
        for aid in all_account_ids:
            account_gold += gold_by_account.get(aid, 0) or 0

        # Hell state (from most active avatar)
        hell_state = {
            "hellShards": best_av.get("HellShards", 0) or 0,
            "hellTime": best_av.get("HellTime", 0) or 0,
            "maxHellTime": best_av.get("MaxHellTime", 0) or 0,
        }

        player_entry = {
            "oldAccountId": oauth_account_id,
            "allAccountIds": list(all_account_ids),
            "oauthName": oauth_row.get("Name", ""),
            "avatars": avatar_list,
            "karma": karma,
            "meditation": meditation,
            "hellState": hell_state,
            "accountGold": account_gold,
        }
        if social_info:
            player_entry["social"] = social_info
        if settings_parsed:
            player_entry["settings"] = settings_parsed

        players[email] = player_entry

    # ============================================================
    # 4. Output migration JSON
    # ============================================================
    now = datetime.now(timezone.utc).isoformat()
    print(f"\n=== Output ===")
    print(f"  Total players to migrate: {len(players)}")

    migration_data = {
        "players": players,
        "nameList": sorted(set(all_names)),
        "totalPlayers": len(players),
        "totalAvatars": stats["total_avatars"],
        "exportDate": now,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(migration_data, f, indent=2, ensure_ascii=False)
    file_size = os.path.getsize(OUTPUT_JSON) if 'os' in dir() else 0
    print(f"  Written: {OUTPUT_JSON}")

    # ============================================================
    # 5. Generate report
    # ============================================================
    style_names = {0: "Amuktha", 1: "MukthaMuktha", 2: "MantraMuktha", 3: "PaniMuktha", 4: "Yantramuktha"}
    god_names = {0: "Brahma", 1: "Vishnu", 2: "Shiva"}

    report_lines = [
        "=" * 60,
        "AUM LEGACY -> PLAYFAB MIGRATION REPORT",
        f"Generated: {now}",
        "=" * 60,
        "",
        "--- Summary ---",
        f"Total OAuth emails:            {stats['total_oauth_emails']}",
        f"Players with valid avatars:     {stats['players_with_avatars']}",
        f"Players without avatars:        {stats['players_without_avatars']}",
        f"  Avatars from OAuth AccountID: {stats['players_from_oauth_aid']}",
        f"  Avatars from Users AccountID: {stats['players_from_users_aid']}",
        f"  Avatars from BOTH:            {stats['players_from_both']}",
        f"Total avatars to migrate:       {stats['total_avatars']}",
        f"Skipped (incomplete):           {stats['skipped_incomplete']}",
        f"Skipped (disabled):             {stats['skipped_disabled']}",
        f"Total inventory items:          {stats['total_items']}",
        "",
        "--- Avatar Count Distribution ---",
    ]
    for count in sorted(stats["avatar_counts"].keys()):
        report_lines.append(f"  {count} avatar(s): {stats['avatar_counts'][count]} players")

    report_lines.extend(["", "--- Fighting Style Distribution ---"])
    for style, count in sorted(stats["style_distribution"].items()):
        report_lines.append(f"  {style_names.get(style, f'Unknown({style})')}: {count}")

    report_lines.extend(["", "--- God Selection Distribution ---"])
    for god, count in sorted(stats["god_distribution"].items()):
        report_lines.append(f"  {god_names.get(god, f'Unknown({god})')}: {count}")

    report_lines.extend(["", "--- Currency Outliers (Bronze > 50,000) ---"])
    if stats["outlier_accounts"]:
        for out in stats["outlier_accounts"]:
            report_lines.append(f"  {out['email']} ({out['nickname']}): {out['bronze']:,} Bronze")
    else:
        report_lines.append("  None")

    report_lines.extend(["", "--- PlayFab Chunk Estimates ---"])
    chunk_sizes = defaultdict(int)
    for em in players:
        chunk_sizes[hash_email(em)] += 1
    for i in range(NUM_CHUNKS):
        report_lines.append(f"  Chunk {i}: {chunk_sizes.get(i, 0)} players")

    # JSON size estimate
    import os
    json_size = os.path.getsize(OUTPUT_JSON)
    report_lines.extend([
        "",
        "--- Data Size ---",
        f"  Total JSON size: {json_size:,} bytes ({json_size/1024:.1f} KB)",
        f"  Avg per player:  {json_size // max(len(players), 1):,} bytes",
        f"  Est per chunk:   {json_size // NUM_CHUNKS:,} bytes",
    ])

    report_lines.extend(["", "--- Sample Players (first 10) ---"])
    for i, (em, data) in enumerate(list(players.items())[:10]):
        av_names = [a["nickName"] for a in data["avatars"]]
        total_bronze = sum(a["currencies"]["bronze"] for a in data["avatars"])
        aids = len(data.get("allAccountIds", []))
        report_lines.append(
            f"  {em}: {len(data['avatars'])} avatar(s) [{', '.join(av_names)}], "
            f"{total_bronze:,} bronze, {aids} AccountID(s)"
        )

    report_lines.extend(["", "=" * 60])

    report_text = "\n".join(report_lines)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report_text)
    print(f"  Written: {OUTPUT_REPORT}")
    print(f"\n{report_text}")


if __name__ == "__main__":
    import os
    main()
