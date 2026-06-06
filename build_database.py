import json
import sqlite3
from pathlib import Path

DB_PATH = Path('grimoire.db')
MOBS_JSON = Path('mobs.json')


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    DROP TABLE IF EXISTS mob_drops;
    DROP TABLE IF EXISTS mob_spawns;
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
        mental_evade INTEGER
    );

    CREATE INDEX idx_mobs_search_name ON mobs(search_name);
    CREATE INDEX idx_mobs_level_stars ON mobs(level, stars);

    CREATE TABLE mob_spawns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mob_id INTEGER NOT NULL,
        zone_key TEXT,
        min_spawn_secs INTEGER,
        max_spawn_secs INTEGER,
        FOREIGN KEY (mob_id) REFERENCES mobs(id)
    );

    CREATE INDEX idx_mob_spawns_mob_id ON mob_spawns(mob_id);

    CREATE TABLE mob_drops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mob_id INTEGER NOT NULL,
        item_id INTEGER,
        item_name TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        FOREIGN KEY (mob_id) REFERENCES mobs(id)
    );

    CREATE INDEX idx_mob_drops_mob_id ON mob_drops(mob_id);
    CREATE INDEX idx_mob_drops_item_id ON mob_drops(item_id);
    CREATE INDEX idx_mob_drops_item_name ON mob_drops(item_name);
    ''')


def to_int(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def to_float(value):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_drop(raw: str) -> tuple[int | None, str]:
    # Current format is usually "Item Name~12345".
    if '~' in raw:
        name, item_id = raw.rsplit('~', 1)
        return to_int(item_id), name.strip()
    return None, raw.strip()


def build_db() -> None:
    if not MOBS_JSON.exists():
        raise FileNotFoundError('mobs.json not found. Put build_database.py next to mobs.json.')

    with MOBS_JSON.open('r', encoding='utf-8') as f:
        mobs = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)

        for mob in mobs:
            damage = mob.get('damage') or {}
            resist = mob.get('resist') or {}

            conn.execute(
                '''
                INSERT INTO mobs (
                    id, name, search_name, range, follow_range, opinion, level, health,
                    gold_min, gold_max, attack, defence, attack_speed, energy, stars,
                    attack_range, missile_speed, xp, fishing_damage,
                    damage_pierce, damage_slash, damage_crush, damage_heat, damage_cold,
                    damage_magic, damage_poison, damage_divine, damage_chaos, damage_true,
                    resist_pierce, resist_slash, resist_crush, resist_heat, resist_cold,
                    resist_magic, resist_poison, resist_divine, resist_chaos, resist_true,
                    physical_evade, spell_evade, move_evade, wound_evade, weak_evade, mental_evade
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (
                    to_int(mob.get('id')),
                    mob.get('name', 'Unknown'),
                    mob.get('name', 'Unknown').lower(),
                    to_float(mob.get('range')),
                    to_float(mob.get('followRange')),
                    mob.get('opinion'),
                    to_int(mob.get('level')),
                    to_int(mob.get('health')),
                    to_int(mob.get('goldMin')),
                    to_int(mob.get('goldMax')),
                    to_int(mob.get('attack')),
                    to_int(mob.get('defence')),
                    to_int(mob.get('attackSpeed')),
                    to_int(mob.get('energy')),
                    to_int(mob.get('stars')),
                    to_float(mob.get('AttackRange')),
                    to_float(mob.get('missileSpeed')),
                    to_int(mob.get('xp')),
                    to_int(mob.get('fishingDamage')),
                    to_int(damage.get('pierce')),
                    to_int(damage.get('slash')),
                    to_int(damage.get('crush')),
                    to_int(damage.get('heat')),
                    to_int(damage.get('cold')),
                    to_int(damage.get('magic')),
                    to_int(damage.get('poison')),
                    to_int(damage.get('divine')),
                    to_int(damage.get('chaos')),
                    to_int(damage.get('truee')),
                    to_int(resist.get('pierce')),
                    to_int(resist.get('slash')),
                    to_int(resist.get('crush')),
                    to_int(resist.get('heat')),
                    to_int(resist.get('cold')),
                    to_int(resist.get('magic')),
                    to_int(resist.get('poison')),
                    to_int(resist.get('divine')),
                    to_int(resist.get('chaos')),
                    to_int(resist.get('truee')),
                    to_int(mob.get('physicalEvade')),
                    to_int(mob.get('spellEvade')),
                    to_int(mob.get('moveEvade')),
                    to_int(mob.get('woundEvade')),
                    to_int(mob.get('weakEvade')),
                    to_int(mob.get('mentalEvade')),
                ),
            )

            mob_id = to_int(mob.get('id'))

            for spawn in mob.get('spawns') or []:
                conn.execute(
                    '''
                    INSERT INTO mob_spawns (mob_id, zone_key, min_spawn_secs, max_spawn_secs)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (
                        mob_id,
                        spawn.get('zoneKey'),
                        to_int(spawn.get('minSpawnSecs')),
                        to_int(spawn.get('maxSpawnSecs')),
                    ),
                )

            for raw_drop in mob.get('drops') or []:
                item_id, item_name = parse_drop(raw_drop)
                conn.execute(
                    '''
                    INSERT INTO mob_drops (mob_id, item_id, item_name, raw_text)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (mob_id, item_id, item_name, raw_drop),
                )

        conn.commit()

        mob_count = conn.execute('SELECT COUNT(*) FROM mobs').fetchone()[0]
        spawn_count = conn.execute('SELECT COUNT(*) FROM mob_spawns').fetchone()[0]
        drop_count = conn.execute('SELECT COUNT(*) FROM mob_drops').fetchone()[0]
        print(f'Built {DB_PATH}: {mob_count} mobs, {spawn_count} spawns, {drop_count} drop rows')
    finally:
        conn.close()


if __name__ == '__main__':
    build_db()
