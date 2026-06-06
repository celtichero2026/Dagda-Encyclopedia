import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("grimoire.db")
RAW_DIR = Path("data/raw")
MOBS_JSON = Path("mobs.json")  # optional fallback/extra enriched data

DAMAGE_KEYS = {
    0: "pierce",
    1: "slash",
    2: "crush",
    3: "heat",
    4: "cold",
    5: "magic",
    6: "poison",
    7: "divine",
    8: "chaos",
    9: "true",
}

EVADE_KEYS = {
    0: "physical",
    1: "spell",
    2: "move",
    3: "wound",
    4: "weak",
    5: "mental",
}


def raw_file(name: str) -> Path:
    return RAW_DIR / name


def to_int(value) -> Optional[int]:
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    if value.lower() in {"immune", "inf", "infinite"}:
        return -1
    try:
        return int(value)
    except ValueError:
        try:
            return int(float(value))
        except ValueError:
            return None


def to_float(value) -> Optional[float]:
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def clean_name(value: str) -> str:
    return (value or "").strip()


def search_name(value: str) -> str:
    return clean_name(value).lower()


def read_lines(path: Path):
    if not path.exists():
        print(f"Skipping missing file: {path}")
        return []
    return [line.rstrip("\n\r") for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def parse_key_values(raw: str) -> dict[int, Optional[int]]:
    """
    Parses Celtic Heroes style packed stat lists like:
      1,5000;3,2000
      0,4500;1,4500;7,Immune
    """
    out: dict[int, Optional[int]] = {}
    if not raw:
        return out
    for piece in raw.split(";"):
        piece = piece.strip()
        if not piece:
            continue
        if "," in piece:
            k, v = piece.split(",", 1)
        elif "|" in piece:
            k, v = piece.split("|", 1)
        else:
            continue
        key = to_int(k)
        if key is not None:
            out[key] = to_int(v)
    return out


def parse_gold_range(raw: str) -> tuple[Optional[int], Optional[int]]:
    raw = (raw or "").strip()
    if "-" in raw:
        a, b = raw.split("-", 1)
        return to_int(a), to_int(b)
    val = to_int(raw)
    return val, val


def parse_time_to_seconds(raw: str) -> Optional[int]:
    raw = (raw or "").strip().lower()
    if not raw:
        return None

    total = 0
    found = False

    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(sec|secs|second|seconds|min|mins|minute|minutes|h|hr|hrs|hour|hours)", raw):
        found = True
        n = float(num)
        if unit.startswith("sec"):
            total += n
        elif unit.startswith("min"):
            total += n * 60
        else:
            total += n * 3600

    if found:
        return int(total)

    return to_int(raw)


def parse_time_range(raw: str) -> tuple[Optional[int], Optional[int]]:
    raw = (raw or "").strip()
    if "-" in raw:
        left, right = raw.split("-", 1)
        return parse_time_to_seconds(left), parse_time_to_seconds(right)
    val = parse_time_to_seconds(raw)
    return val, val


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    DROP TABLE IF EXISTS mob_drops;
    DROP TABLE IF EXISTS mob_spawns;
    DROP TABLE IF EXISTS mob_scripts;
    DROP TABLE IF EXISTS scripts;
    DROP TABLE IF EXISTS items;
    DROP TABLE IF EXISTS zones;
    DROP TABLE IF EXISTS mobs;

    CREATE TABLE mobs (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        search_name TEXT NOT NULL,
        range REAL,
        follow_range REAL,
        opinion TEXT,
        level INTEGER,
        health INTEGER,
        gold_min INTEGER,
        gold_max INTEGER,
        attack INTEGER,
        defence INTEGER,
        attack_speed INTEGER,
        energy INTEGER,
        radius REAL,
        stars INTEGER,
        attack_range REAL,
        missile_speed REAL,
        xp INTEGER,
        fishing_damage INTEGER,

        damage_pierce INTEGER,
        damage_slash INTEGER,
        damage_crush INTEGER,
        damage_heat INTEGER,
        damage_cold INTEGER,
        damage_magic INTEGER,
        damage_poison INTEGER,
        damage_divine INTEGER,
        damage_chaos INTEGER,
        damage_true INTEGER,

        resist_pierce INTEGER,
        resist_slash INTEGER,
        resist_crush INTEGER,
        resist_heat INTEGER,
        resist_cold INTEGER,
        resist_magic INTEGER,
        resist_poison INTEGER,
        resist_divine INTEGER,
        resist_chaos INTEGER,
        resist_true INTEGER,

        physical_evade INTEGER,
        spell_evade INTEGER,
        move_evade INTEGER,
        wound_evade INTEGER,
        weak_evade INTEGER,
        mental_evade INTEGER,

        raw_text TEXT
    );

    CREATE INDEX idx_mobs_search_name ON mobs(search_name);
    CREATE INDEX idx_mobs_level_stars ON mobs(level, stars);

    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        search_name TEXT NOT NULL,
        description TEXT,
        raw_text TEXT
    );

    CREATE INDEX idx_items_search_name ON items(search_name);

    CREATE TABLE zones (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        map_key TEXT,
        min_x REAL,
        max_x REAL,
        min_z REAL,
        max_z REAL,
        raw_text TEXT
    );

    CREATE TABLE mob_spawns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spawn_id INTEGER,
        mob_id INTEGER NOT NULL,
        zone_id INTEGER,
        zone_key TEXT,
        min_spawn_secs INTEGER,
        max_spawn_secs INTEGER,
        x REAL,
        y REAL,
        z REAL,
        movement TEXT,
        weight INTEGER,
        raw_text TEXT,
        FOREIGN KEY (mob_id) REFERENCES mobs(id)
    );

    CREATE INDEX idx_mob_spawns_mob_id ON mob_spawns(mob_id);
    CREATE INDEX idx_mob_spawns_zone_id ON mob_spawns(zone_id);

    CREATE TABLE scripts (
        id INTEGER PRIMARY KEY,
        message TEXT,
        raw_text TEXT NOT NULL
    );

    CREATE TABLE mob_scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mob_id INTEGER NOT NULL,
        script_id INTEGER NOT NULL,
        extra TEXT,
        raw_text TEXT,
        FOREIGN KEY (mob_id) REFERENCES mobs(id),
        FOREIGN KEY (script_id) REFERENCES scripts(id)
    );

    CREATE INDEX idx_mob_scripts_mob_id ON mob_scripts(mob_id);

    CREATE TABLE mob_drops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mob_id INTEGER NOT NULL,
        item_id INTEGER,
        item_name TEXT NOT NULL,
        loot_set_id INTEGER,
        loot_table_id INTEGER,
        loot_table_chance INTEGER,
        item_chance INTEGER,
        raw_text TEXT NOT NULL,
        FOREIGN KEY (mob_id) REFERENCES mobs(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    );

    CREATE INDEX idx_mob_drops_mob_id ON mob_drops(mob_id);
    CREATE INDEX idx_mob_drops_item_id ON mob_drops(item_id);
    CREATE INDEX idx_mob_drops_item_name ON mob_drops(item_name);
    """)


def insert_mob_from_parts(conn: sqlite3.Connection, parts: list[str], raw: str) -> None:
    if len(parts) < 22:
        return

    mob_id = to_int(parts[0])
    if mob_id is None:
        return

    name = clean_name(parts[1]) or f"Mob {mob_id}"
    gold_min, gold_max = parse_gold_range(parts[7] if len(parts) > 7 else "")
    damage = parse_key_values(parts[13] if len(parts) > 13 else "")
    resist = parse_key_values(parts[15] if len(parts) > 15 else "")
    evades = parse_key_values(parts[21] if len(parts) > 21 else "")

    def dmg(key: str):
        idx = next((i for i, k in DAMAGE_KEYS.items() if k == key), None)
        return damage.get(idx, 0) if idx is not None else 0

    def res(key: str):
        idx = next((i for i, k in DAMAGE_KEYS.items() if k == key), None)
        return resist.get(idx, 0) if idx is not None else 0

    def evade(key: str):
        idx = next((i for i, k in EVADE_KEYS.items() if k == key), None)
        return evades.get(idx, 0) if idx is not None else 0

    conn.execute(
        """
        INSERT OR REPLACE INTO mobs (
            id, name, search_name, range, follow_range, opinion, level, health,
            gold_min, gold_max, attack, defence, attack_speed, energy, radius, stars,
            attack_range, missile_speed, xp, fishing_damage,
            damage_pierce, damage_slash, damage_crush, damage_heat, damage_cold,
            damage_magic, damage_poison, damage_divine, damage_chaos, damage_true,
            resist_pierce, resist_slash, resist_crush, resist_heat, resist_cold,
            resist_magic, resist_poison, resist_divine, resist_chaos, resist_true,
            physical_evade, spell_evade, move_evade, wound_evade, weak_evade, mental_evade,
            raw_text
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            mob_id,
            name,
            search_name(name),
            to_float(parts[2]),
            to_float(parts[3]),
            clean_name(parts[4]).lower(),
            to_int(parts[5]),
            to_int(parts[6]),
            gold_min,
            gold_max,
            to_int(parts[8]),
            to_int(parts[9]),
            to_int(parts[10]),
            to_int(parts[11]),
            to_float(parts[12]),
            to_int(parts[16]),
            to_float(parts[17]),
            to_float(parts[18]),
            to_int(parts[20]),
            to_int(parts[14]),
            dmg("pierce"), dmg("slash"), dmg("crush"), dmg("heat"), dmg("cold"),
            dmg("magic"), dmg("poison"), dmg("divine"), dmg("chaos"), dmg("true"),
            res("pierce"), res("slash"), res("crush"), res("heat"), res("cold"),
            res("magic"), res("poison"), res("divine"), res("chaos"), res("true"),
            evade("physical"), evade("spell"), evade("move"), evade("wound"), evade("weak"), evade("mental"),
            raw,
        ),
    )


def load_mobs(conn: sqlite3.Connection) -> None:
    for raw in read_lines(raw_file("moblist.txt")):
        insert_mob_from_parts(conn, raw.split("~"), raw)


def load_items(conn: sqlite3.Connection) -> None:
    for raw in read_lines(raw_file("itemlist.txt")):
        parts = raw.split("~")
        item_id = to_int(parts[0]) if parts else None
        if item_id is None or len(parts) < 2:
            continue
        name = clean_name(parts[1]) or f"Item {item_id}"
        description = clean_name(parts[2]) if len(parts) > 2 else None
        conn.execute(
            """
            INSERT OR REPLACE INTO items (id, name, search_name, description, raw_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, name, search_name(name), description, raw),
        )


def load_zones(conn: sqlite3.Connection) -> None:
    for raw in read_lines(raw_file("zones.txt")):
        parts = raw.split("~")
        if len(parts) < 7:
            continue
        zone_id = to_int(parts[0])
        if zone_id is None:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO zones (id, name, map_key, min_x, max_x, min_z, max_z, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                zone_id,
                clean_name(parts[1]),
                clean_name(parts[2]),
                to_float(parts[3]),
                to_float(parts[4]),
                to_float(parts[5]),
                to_float(parts[6]),
                raw,
            ),
        )


def load_spawns(conn: sqlite3.Connection) -> None:
    zone_names = {r[0]: r[1] for r in conn.execute("SELECT id, name FROM zones").fetchall()}

    for raw in read_lines(raw_file("spawnpoints.txt")):
        parts = raw.split("~")
        if len(parts) < 8:
            continue

        spawn_id = to_int(parts[0])
        zone_id = to_int(parts[1])
        min_secs, max_secs = parse_time_range(parts[2])
        x = to_float(parts[3])
        y = to_float(parts[4])
        z = to_float(parts[5])
        movement = clean_name(parts[6])
        possible_mobs = parts[7]
        zone_key = f"{zone_names.get(zone_id, 'Unknown')}~{zone_id}" if zone_id is not None else None

        for entry in possible_mobs.split(";"):
            entry = entry.strip()
            if not entry:
                continue
            if "|" in entry:
                mob_raw, weight_raw = entry.split("|", 1)
            else:
                mob_raw, weight_raw = entry, None
            mob_id = to_int(mob_raw)
            if mob_id is None:
                continue
            conn.execute(
                """
                INSERT INTO mob_spawns (
                    spawn_id, mob_id, zone_id, zone_key, min_spawn_secs, max_spawn_secs,
                    x, y, z, movement, weight, raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (spawn_id, mob_id, zone_id, zone_key, min_secs, max_secs, x, y, z, movement, to_int(weight_raw), raw),
            )


def load_scripts(conn: sqlite3.Connection) -> None:
    for raw in read_lines(raw_file("scripts.txt")):
        parts = raw.split("~")
        script_id = to_int(parts[0]) if parts else None
        if script_id is None:
            continue
        message = None
        if len(parts) >= 4:
            # Most rows have the visible script message near the end.
            for candidate in reversed(parts):
                candidate = candidate.strip()
                if candidate and not candidate.isdigit() and "|" not in candidate and "^" not in candidate:
                    message = candidate
                    break
        conn.execute(
            "INSERT OR REPLACE INTO scripts (id, message, raw_text) VALUES (?, ?, ?)",
            (script_id, message, raw),
        )


def load_mob_scripts(conn: sqlite3.Connection) -> None:
    for raw in read_lines(raw_file("mobscripts.txt")):
        parts = raw.split("~")
        if len(parts) < 2:
            continue
        mob_id = to_int(parts[0])
        script_id = to_int(parts[1])
        if mob_id is None or script_id is None:
            continue
        extra = "~".join(parts[2:]) if len(parts) > 2 else None
        conn.execute(
            "INSERT INTO mob_scripts (mob_id, script_id, extra, raw_text) VALUES (?, ?, ?, ?)",
            (mob_id, script_id, extra, raw),
        )


def load_drops_from_loot_tables(conn: sqlite3.Connection) -> None:
    """
    Reconstructs mob -> item using:
      moblootsetlist: mob_id ~ loot_set_id ~ extra
      lootsetlist:    loot_set_id ~ loot_table_id ~ table_chance
      loottableitemlist: loot_table_id ~ item_id ~ item_chance
    """
    item_names = {r[0]: r[1] for r in conn.execute("SELECT id, name FROM items").fetchall()}

    loot_set_to_tables: dict[int, list[tuple[int, Optional[int], str]]] = {}
    for raw in read_lines(raw_file("lootsetlist.txt")):
        parts = raw.split("~")
        if len(parts) < 2:
            continue
        loot_set_id = to_int(parts[0])
        loot_table_id = to_int(parts[1])
        chance = to_int(parts[2]) if len(parts) > 2 else None
        if loot_set_id is None or loot_table_id is None:
            continue
        loot_set_to_tables.setdefault(loot_set_id, []).append((loot_table_id, chance, raw))

    table_to_items: dict[int, list[tuple[int, Optional[int], str]]] = {}
    for raw in read_lines(raw_file("loottableitemlist.txt")):
        parts = raw.split("~")
        if len(parts) < 2:
            continue
        loot_table_id = to_int(parts[0])
        item_id = to_int(parts[1])
        chance = to_int(parts[2]) if len(parts) > 2 else None
        if loot_table_id is None or item_id is None:
            continue
        table_to_items.setdefault(loot_table_id, []).append((item_id, chance, raw))

    inserted = set()
    for raw in read_lines(raw_file("moblootsetlist.txt")):
        parts = raw.split("~")
        if len(parts) < 2:
            continue
        mob_id = to_int(parts[0])
        loot_set_id = to_int(parts[1])
        if mob_id is None or loot_set_id is None:
            continue
        for loot_table_id, table_chance, set_raw in loot_set_to_tables.get(loot_set_id, []):
            for item_id, item_chance, item_raw in table_to_items.get(loot_table_id, []):
                item_name = item_names.get(item_id, f"Item {item_id}")
                key = (mob_id, item_id, loot_set_id, loot_table_id, table_chance, item_chance)
                if key in inserted:
                    continue
                inserted.add(key)
                conn.execute(
                    """
                    INSERT INTO mob_drops (
                        mob_id, item_id, item_name, loot_set_id, loot_table_id,
                        loot_table_chance, item_chance, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (mob_id, item_id, item_name, loot_set_id, loot_table_id, table_chance, item_chance, f"{raw} || {set_raw} || {item_raw}"),
                )


def load_extra_drops_from_mobs_json(conn: sqlite3.Connection) -> None:
    """Optional fallback from your previous curated JSON export."""
    if not MOBS_JSON.exists():
        return
    try:
        mobs = json.loads(MOBS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return

    for mob in mobs:
        mob_id = to_int(mob.get("id"))
        if mob_id is None:
            continue
        # Do not overwrite full moblist stats, but add missing enriched drops if needed.
        for raw_drop in mob.get("drops") or []:
            if "~" in raw_drop:
                item_name, item_id_raw = raw_drop.rsplit("~", 1)
                item_id = to_int(item_id_raw)
            else:
                item_name, item_id = raw_drop.strip(), None
            exists = conn.execute(
                "SELECT 1 FROM mob_drops WHERE mob_id = ? AND item_id IS ? AND item_name = ? LIMIT 1",
                (mob_id, item_id, item_name),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """
                INSERT INTO mob_drops (mob_id, item_id, item_name, raw_text)
                VALUES (?, ?, ?, ?)
                """,
                (mob_id, item_id, item_name, raw_drop),
            )


def build_db() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError("data/raw folder not found. Put the Master's Grimoire txt files in data/raw/.")

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        load_items(conn)
        load_mobs(conn)
        load_zones(conn)
        load_spawns(conn)
        load_scripts(conn)
        load_mob_scripts(conn)
        load_drops_from_loot_tables(conn)
        load_extra_drops_from_mobs_json(conn)
        conn.commit()

        counts = {
            "mobs": conn.execute("SELECT COUNT(*) FROM mobs").fetchone()[0],
            "items": conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
            "zones": conn.execute("SELECT COUNT(*) FROM zones").fetchone()[0],
            "spawns": conn.execute("SELECT COUNT(*) FROM mob_spawns").fetchone()[0],
            "drops": conn.execute("SELECT COUNT(*) FROM mob_drops").fetchone()[0],
            "scripts": conn.execute("SELECT COUNT(*) FROM scripts").fetchone()[0],
            "mob_scripts": conn.execute("SELECT COUNT(*) FROM mob_scripts").fetchone()[0],
        }
        print(
            f"Built {DB_PATH}: "
            f"{counts['mobs']:,} mobs, {counts['items']:,} items, {counts['zones']:,} zones, "
            f"{counts['spawns']:,} spawn rows, {counts['drops']:,} drop rows, "
            f"{counts['scripts']:,} scripts, {counts['mob_scripts']:,} mob-script links"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    build_db()
