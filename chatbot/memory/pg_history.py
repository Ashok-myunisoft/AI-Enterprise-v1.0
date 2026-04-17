import psycopg2
import logging
from config import DATABASE_URL, HISTORY_LIMIT

logger = logging.getLogger(__name__)


def _conn():
    return psycopg2.connect(DATABASE_URL)


def ensure_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_history (
            id          BIGSERIAL PRIMARY KEY,
            session_id  VARCHAR(255) NOT NULL,
            tenant_id   INTEGER      NOT NULL,
            user_id     INTEGER,
            role        VARCHAR(20)  NOT NULL,
            message     TEXT         NOT NULL,
            bot_used    VARCHAR(50),
            created_at  TIMESTAMP    DEFAULT NOW()
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_chatbot_session ON chatbot_history(session_id)"
    )
    conn.commit()
    cur.close()
    conn.close()


def save_message(session_id: str, tenant_id: int, user_id: int,
                 role: str, message: str, bot_used: str = None):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO chatbot_history
               (session_id, tenant_id, user_id, role, message, bot_used)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (session_id, tenant_id, user_id, role, message, bot_used)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_history(session_id: str) -> list:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT role, message FROM chatbot_history
           WHERE session_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (session_id, HISTORY_LIMIT)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # reverse so oldest is first (chronological for LLM context)
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
