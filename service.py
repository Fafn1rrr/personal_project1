from datetime import datetime
from mood_db import get_conn

# Creates an entry in db
def create_entry(valence, arousal, energy, social, note, emotions, factors):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con, cur = get_conn()

    try:
        cur.execute(
            "INSERT INTO entries (ts, valence, arousal, energy, social, note) VALUES (?,?,?,?,?,?)",
            (ts, valence, arousal, energy, social, note)
        )
        entry_id = cur.lastrowid

        link_tags(cur, entry_id,emotions,"emotions","entry_emotions","emotion_id")
        link_tags(cur,entry_id,factors,"factors", "entry_factors","factor_id")

        con.commit()
        return entry_id

    except:
        con.rollback()
        raise
    finally:
        con.close()

# Whitelist
_ALLOWED_REF = {"emotions", "factors"}
_ALLOWED_LINK = {"entry_emotions", "entry_factors"}
_ALLOWED_COL = {"emotion_id", "factor_id"}

# Many-to-many link implementation
def link_tags(cur,entry_id,names,ref_table,link_table,column_name):
    if ref_table not in _ALLOWED_REF or link_table not in _ALLOWED_LINK or column_name not in _ALLOWED_COL:
        raise ValueError("Bad table/column name")
    ids = []

    for name in names:
        name = name.strip().lower()
        if not name:
            continue

        cur.execute(f"SELECT id FROM {ref_table} WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            ids.append(row[0])
        else:
            cur.execute(f"INSERT INTO {ref_table} (name) VALUES (?)", (name,))
            ids.append(cur.lastrowid)

    cur.executemany(
        f"INSERT OR IGNORE INTO {link_table} (entry_id, {column_name}) VALUES (?, ?)",
        [(entry_id, _id) for _id in ids]
    )

# Shows entries' history - last 30 entries
def get_recent_entries():
    con, cur = get_conn()
    try:
        cur.execute("SELECT id, ts, valence, arousal, energy, social FROM entries ORDER BY ts DESC LIMIT 30")
        rows = cur.fetchall()
        result = [
            {
                "id": r[0],
                "ts": r[1],
                "valence": r[2],
                "arousal": r[3],
                "energy": r[4],
                "social": r[5],
            }
            for r in rows
        ]

        return result

    finally:
        con.close()

# Returns certain entry's full details - time, values of parameters and emotions + factors as a dict
def get_entry_details(entry_id):
    con, cur = get_conn()
    try:
        # Getting the main information
        cur.execute("SELECT id, ts, valence, arousal, energy, social, note FROM entries WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        if not row:
            return None

        # Getting the emotions linked to this entry
        cur.execute("SELECT e.name FROM entry_emotions ee JOIN emotions e ON e.id = ee.emotion_id WHERE ee.entry_id = ?", (entry_id,))
        emotions = [r[0] for r in cur.fetchall()]

        # Getting the factors linked to this entry
        cur.execute("SELECT f.name FROM entry_factors ef JOIN factors f ON f.id = ef.factor_id WHERE ef.entry_id = ?", (entry_id,))
        factors = [r[0] for r in cur.fetchall()]

        result = {
            "entry": {
                "id": row[0],
                "ts": row[1],
                "valence": row[2],
                "arousal": row[3],
                "energy": row[4],
                "social": row[5],
                "note": row[6],
            },
            "emotions": emotions,
            "factors": factors
        }
        return result

    finally:
        con.close()