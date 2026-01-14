def count_questions_for_sap(sap_full_path):
    """
    Returns the number of questions in the database for the given SAP full path.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions WHERE SAPFullPath = ?", (sap_full_path,))
    count = c.fetchone()[0]
    conn.close()
    return count
def delete_questions_for_sap(sap_full_path):
    """
    Deletes all questions from the database for the given SAP full path.
    Returns the number of deleted questions.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions WHERE SAPFullPath = ?", (sap_full_path,))
    count = c.fetchone()[0]
    c.execute("DELETE FROM questions WHERE SAPFullPath = ?", (sap_full_path,))
    conn.commit()
    conn.close()
    return count
import csv
import sqlite3
import datetime
import uuid
from pathlib import Path

DB_FILE = "questions.db"

CATEGORIES = [
    "Scoping",
    "Advisory",
    "Advisory+ARG",
    "Troubleshooting",
    "Skip",
    "Case Handling",
    "Another Product",
    "N/A"
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE,
            question TEXT,
            category TEXT,
            aI_response TEXT,
            evaluation_text TEXT,
            extra_column1 TEXT,
            extra_column2 TEXT,
            extra_column3 TEXT,
            SAPFullPath TEXT,
            timestamp TEXT
        )
    """)
    c.execute("PRAGMA table_info(questions)")
    columns = [col[1] for col in c.fetchall()]
    if "SAPFullPath" not in columns:
        c.execute("ALTER TABLE questions ADD COLUMN SAPFullPath TEXT")
    conn.commit()
    conn.close()

def get_categorized_guids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid FROM questions WHERE category IS NOT NULL AND category != ''")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)

def save_to_db(row):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE questions
        SET category = ?, aI_response = ?, evaluation_text = ?, extra_column1 = ?, extra_column2 = ?, extra_column3 = ?, timestamp = ?
        WHERE guid = ?
    """, (row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[0]))
    conn.commit()
    conn.close()

def read_questions(csv_file):
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [row[0] for row in reader if row and row[0].strip()]

def import_questions_to_db(csv_file):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            question = row[0].strip()
            if not question:
                continue
            c.execute("SELECT guid FROM questions WHERE question = ?", (question,))
            result = c.fetchone()
            if not result:
                guid = str(uuid.uuid4())
                c.execute(
                    "INSERT INTO questions (guid, question, category, aI_response, evaluation_text, extra_column1, extra_column2, extra_column3, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (guid, question, '', '', '', '', '', '', '')
                )
    conn.commit()
    conn.close()

def get_uncategorized_questions_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT guid, question, SAPFullPath FROM questions WHERE category IS NULL OR category = ''")
    rows = c.fetchall()
    conn.close()
    return [{"guid": row[0], "question": row[1], "sap": row[2]} for row in rows]

def init_config_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS configuration (
            key TEXT PRIMARY KEY,
            value TEXT,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

def config_exists():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM configuration")
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def save_config(alias, advisory_sap, technical_sap, advisory_resource_sap):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("alias", alias, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("advisory_sap", advisory_sap, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("technical_sap", technical_sap, now))
    c.execute("INSERT OR REPLACE INTO configuration (key, value, last_updated) VALUES (?, ?, ?)", ("advisory_resource_sap", advisory_resource_sap, now))
    conn.commit()
    conn.close()

def get_saps_from_config():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM configuration WHERE key IN ('advisory_sap', 'technical_sap', 'advisory_resource_sap')")
    saps = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return saps

def get_config_values():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM configuration")
    values = dict(c.fetchall())
    conn.close()
    return values

def import_questions_to_db_with_sap(csv_file, sap_full_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            question = row[0].strip()
            if not question:
                continue
            c.execute("SELECT guid FROM questions WHERE question = ?", (question,))
            result = c.fetchone()
            if not result:
                guid = str(uuid.uuid4())
                c.execute(
                    "INSERT INTO questions (guid, question, category, aI_response, evaluation_text, extra_column1, extra_column2, extra_column3, SAPFullPath, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (guid, question, '', '', '', '', '', '', sap_full_path, '')
                )
            else:
                c.execute(
                    "UPDATE questions SET SAPFullPath = ? WHERE question = ?",
                    (sap_full_path, question)
                )
    conn.commit()
    conn.close()

def import_questions_list_to_db(questions, sap_full_path):
    """
    Imports a list of questions into the database, associating each with the given SAP path.
    Only inserts questions that do not already exist in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for question in questions:
        # Check if question already exists (case-insensitive match)
        c.execute("SELECT guid FROM questions WHERE LOWER(question) = LOWER(?)", (question,))
        result = c.fetchone()
        if not result:
            guid = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            c.execute(
                "INSERT INTO questions (guid, question, category, aI_response, evaluation_text, extra_column1, extra_column2, extra_column3, SAPFullPath, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guid, question, '', '', '', '', '', '', sap_full_path, timestamp)
            )
    conn.commit()
    conn.close()
