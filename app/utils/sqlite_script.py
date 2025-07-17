import sqlite3
from pathlib import Path
import os
import pandas as pd
import logging

# Create a logger specific to this module
logger = logging.getLogger(__name__)

DB_FILE = os.path.join(Path(__file__).resolve().parents[2],"data","giftcode_system.db")
WORKING_COPY_DB = os.path.join(Path(__file__).resolve().parents[2],"data","working_copy.db")

def get_connection():
    return sqlite3.connect(WORKING_COPY_DB)

def copy_captcha_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        conn.execute(f"ATTACH DATABASE '{WORKING_COPY_DB}' AS work")

        # Create table structure in working copy (adjust columns as needed)
        conn.execute("CREATE TABLE IF NOT EXISTS work.captchas AS SELECT * FROM main.captchas")

        cursor.execute("PRAGMA main.table_info(captchas)")
        columns_main = cursor.fetchall()

        cursor.execute("PRAGMA work.table_info(captchas)")
        columns_work = cursor.fetchall()

        if len(columns_main) != len(columns_work):
            # Insert only the data you want
            conn.execute("INSERT INTO work.captchas (id, name, img, feedback, corrected_text, status, last_updated, updated_by) SELECT id, name, img, feedback, NULL, 0, NULL, NULL FROM main.captchas WHERE NOT EXISTS (SELECT 1 FROM work.captchas WHERE work.captchas.id = main.captchas.id)")
        else:
            conn.execute("INSERT INTO work.captchas SELECT * FROM main.captchas WHERE NOT EXISTS (SELECT 1 FROM work.captchas WHERE work.captchas.id = main.captchas.id)")
            # Optional: Add new column to the copied table
            conn.execute("ALTER TABLE work.captchas ADD COLUMN corrected_text TEXT")
            conn.execute("ALTER TABLE work.captchas ADD COLUMN status INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE work.captchas ADD COLUMN last_updated TIMESTAMP")
            conn.execute("ALTER TABLE work.captchas ADD COLUMN locked_at TIMESTAMP")
            conn.execute("ALTER TABLE work.captchas ADD COLUMN updated_by TEXT")

        conn.commit()
        conn.execute("DETACH DATABASE work")

        logger.info("Captcha table copied to working copy database.")
    except Exception as e:
        logger.info(f"An error occurred on copy_captcha_table: {e}")
    finally:
        conn.close()
        return None

def get_next_uncorrected():
    result = None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            result = conn.execute("SELECT id, img FROM captchas WHERE corrected_text IS NULL AND (status = 0 OR (status = 1 AND DATETIME(locked_at) < DATETIME('now', '-5 minutes'))) ORDER BY RANDOM() LIMIT 1").fetchone()
            captcha_id, _ = result
            logger.info(f"Next uncorrected captcha ID: {captcha_id}")
            cursor.execute("UPDATE captchas SET status = 1, locked_at = CURRENT_TIMESTAMP WHERE id = ?", (captcha_id,))
    except Exception as e:
        logger.info(f"An error occurred: {e}")
    finally:
        return result
    
def get_history(offset, limit):
    df = None
    try:
        with get_connection() as conn:
            df = pd.read_sql_query(
                f"SELECT id, corrected_text, img FROM captchas WHERE status = 2 ORDER BY last_updated DESC LIMIT {limit} OFFSET {offset}",
                conn
            )
    except Exception as e:
        logger.info(f"An error occurred: {e}")
    return df
    
def update_corrected_text(info):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE captchas
                SET corrected_text = :corrected_text,
                    status = :status,
                    last_updated = CURRENT_TIMESTAMP,
                    updated_by = :updated_by
                WHERE id = :captcha_id
            """, {**info})
            conn.commit()
            logger.info(f"Updated corrected_text for id {info['captcha_id']}.")
    except Exception as e:
        logger.info(f"An error occurred: {e}")
    finally:
        return None

if __name__ == "__main__":
    copy_captcha_table()