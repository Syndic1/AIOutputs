#!/usr/bin/env python3
"""
Bangor Roundtable — Memory Server
RAG (Retrieval Augmented Generation) service for the Roundtable.

Runs on the Pi at 192.168.1.154:3001
Handles: embedding via OpenAI, storage in MariaDB, similarity retrieval.

Install deps:
    pip install flask flask-cors pymysql openai numpy

Run:
    python3 memory_server.py --config /path/to/config.json

Or set env vars:
    ROUNDTABLE_DB_HOST, ROUNDTABLE_DB_USER, ROUNDTABLE_DB_PASS,
    ROUNDTABLE_DB_NAME, ROUNDTABLE_OPENAI_KEY
"""

import argparse
import json
import logging
import math
import os
import struct
import sys
import threading
import time
from datetime import datetime

import numpy as np

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("ERROR: pymysql not found. Run: pip install pymysql")
    sys.exit(1)

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("ERROR: flask/flask-cors not found. Run: pip install flask flask-cors")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai not found. Run: pip install openai")
    sys.exit(1)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('roundtable')

# ── Config ───────────────────────────────────────────────────────────────────

def load_config(path=None):
    cfg = {}
    if path and os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)
        log.info(f"Loaded config from {path}")

    db = cfg.get('database', {})
    return {
        'db_host':     os.environ.get('ROUNDTABLE_DB_HOST', db.get('host', '192.168.1.154')),
        'db_port':     int(os.environ.get('ROUNDTABLE_DB_PORT', db.get('port', 3306))),
        'db_user':     os.environ.get('ROUNDTABLE_DB_USER', db.get('user', 'roundtable')),
        'db_pass':     os.environ.get('ROUNDTABLE_DB_PASS', db.get('password', '')),
        'db_name':     os.environ.get('ROUNDTABLE_DB_NAME', db.get('database', 'roundtable')),
        'openai_key':  os.environ.get('ROUNDTABLE_OPENAI_KEY',
                           cfg.get('keys', {}).get('openai', '')),
        'port':        int(os.environ.get('ROUNDTABLE_PORT', 3001)),
        'host':        os.environ.get('ROUNDTABLE_HOST', '0.0.0.0'),
        'top_k':       int(os.environ.get('ROUNDTABLE_TOP_K', 5)),
        'chunk_size':  int(os.environ.get('ROUNDTABLE_CHUNK_SIZE', 400)),  # tokens approx
        'chunk_overlap': int(os.environ.get('ROUNDTABLE_CHUNK_OVERLAP', 50)),
        'queue_interval': float(os.environ.get('ROUNDTABLE_QUEUE_INTERVAL', 0.3)),  # seconds between queue items
    }

CONFIG = {}

# ── Database ─────────────────────────────────────────────────────────────────

def get_db():
    return pymysql.connect(
        host=CONFIG['db_host'],
        port=CONFIG['db_port'],
        user=CONFIG['db_user'],
        password=CONFIG['db_pass'],
        database=CONFIG['db_name'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def db_ok():
    try:
        conn = get_db()
        conn.close()
        return True
    except Exception as e:
        log.error(f"DB connection failed: {e}")
        return False

# ── Embeddings ───────────────────────────────────────────────────────────────

_openai_client = None

def get_openai():
    global _openai_client
    if _openai_client is None:
        if not CONFIG.get('openai_key'):
            raise ValueError("No OpenAI API key configured")
        _openai_client = OpenAI(api_key=CONFIG['openai_key'])
    return _openai_client

def embed(text: str) -> np.ndarray:
    """Embed a string using text-embedding-3-small. Returns float32 numpy array."""
    client = get_openai()
    response = client.embeddings.create(
        model='text-embedding-3-small',
        input=text.strip()
    )
    vec = np.array(response.data[0].embedding, dtype=np.float32)
    return vec

def vec_to_blob(vec: np.ndarray) -> bytes:
    """Convert float32 numpy array to raw bytes for BLOB storage."""
    return vec.astype(np.float32).tobytes()

def blob_to_vec(blob: bytes) -> np.ndarray:
    """Convert raw bytes back to float32 numpy array."""
    return np.frombuffer(blob, dtype=np.float32)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks by approximate word count.
    chunk_size and overlap are in approximate tokens (1 token ≈ 0.75 words).
    """
    words = text.split()
    word_chunk = int(chunk_size * 0.75)
    word_overlap = int(overlap * 0.75)

    if len(words) <= word_chunk:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + word_chunk, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk.strip())
        if end == len(words):
            break
        start += word_chunk - word_overlap

    return [c for c in chunks if c]

# ── Core store & retrieve ─────────────────────────────────────────────────────

def store_chunk(content: str, source_type: str, source_ref: str = '',
                embedding: np.ndarray = None) -> int:
    """Embed and store a single chunk. Returns inserted ID."""
    if embedding is None:
        embedding = embed(content)

    token_count = len(content.split()) // 3 * 4  # rough token estimate

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO memory_chunks
                   (source_type, source_ref, content, embedding, token_count)
                   VALUES (%s, %s, %s, %s, %s)""",
                (source_type, source_ref, content, vec_to_blob(embedding), token_count)
            )
            return conn.insert_id()
    finally:
        conn.close()

def retrieve(query: str, top_k: int = None, source_type: str = None) -> list[dict]:
    """
    Embed query and return top_k most similar chunks.
    Optionally filter by source_type.
    """
    if top_k is None:
        top_k = CONFIG['top_k']

    query_vec = embed(query)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            if source_type:
                cur.execute(
                    "SELECT id, source_type, source_ref, content, embedding FROM memory_chunks WHERE source_type = %s",
                    (source_type,)
                )
            else:
                cur.execute(
                    "SELECT id, source_type, source_ref, content, embedding FROM memory_chunks"
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # Score all chunks
    scored = []
    for row in rows:
        chunk_vec = blob_to_vec(row['embedding'])
        score = cosine_similarity(query_vec, chunk_vec)
        scored.append({
            'id': row['id'],
            'source_type': row['source_type'],
            'source_ref': row['source_ref'],
            'content': row['content'],
            'score': round(score, 4)
        })

    # Sort by score descending, return top_k
    scored.sort(key=lambda x: x['score'], reverse=True)
    results = scored[:top_k]

    # Filter out low-relevance results (score < 0.3)
    results = [r for r in results if r['score'] >= 0.3]

    return results

# ── Ingestion queue processor ─────────────────────────────────────────────────

queue_running = False

def process_queue():
    """Background thread: processes embedding_queue one item at a time."""
    global queue_running
    queue_running = True
    log.info("Queue processor started")

    while queue_running:
        try:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    # Grab one pending item
                    cur.execute(
                        """SELECT id, source_type, source_ref, content
                           FROM embedding_queue
                           WHERE status = 'pending'
                           ORDER BY created_at ASC
                           LIMIT 1"""
                    )
                    item = cur.fetchone()

                if not item:
                    time.sleep(1)
                    continue

                item_id = item['id']

                # Mark as processing
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE embedding_queue SET status = 'processing' WHERE id = %s",
                        (item_id,)
                    )

            finally:
                conn.close()

            # Embed and store
            try:
                store_chunk(
                    content=item['content'],
                    source_type=item['source_type'],
                    source_ref=item['source_ref']
                )

                # Mark done
                conn = get_db()
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE embedding_queue SET status = 'done' WHERE id = %s",
                            (item_id,)
                        )
                finally:
                    conn.close()

                log.info(f"Queue item {item_id} processed ({item['source_type']}: {item['source_ref'][:40]})")

            except Exception as e:
                log.error(f"Queue item {item_id} failed: {e}")
                conn = get_db()
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE embedding_queue SET status = 'error', error_msg = %s WHERE id = %s",
                            (str(e), item_id)
                        )
                finally:
                    conn.close()

            # Rate limiting — be gentle with OpenAI
            time.sleep(CONFIG['queue_interval'])

        except Exception as e:
            log.error(f"Queue processor error: {e}")
            time.sleep(5)

def queue_chunks(chunks: list[str], source_type: str, source_ref: str = ''):
    """Add multiple chunks to the embedding queue."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for chunk in chunks:
                cur.execute(
                    """INSERT INTO embedding_queue (source_type, source_ref, content)
                       VALUES (%s, %s, %s)""",
                    (source_type, source_ref, chunk)
                )
        log.info(f"Queued {len(chunks)} chunks ({source_type}: {source_ref[:40]})")
    finally:
        conn.close()

def queue_status() -> dict:
    """Return queue statistics."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT status, COUNT(*) as count
                   FROM embedding_queue
                   GROUP BY status"""
            )
            rows = cur.fetchall()
        return {r['status']: r['count'] for r in rows}
    finally:
        conn.close()

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)  # Allow requests from the Roundtable HTML

@app.route('/health', methods=['GET'])
def health():
    """Health check — used by Roundtable to show the memory server dot."""
    db_status = db_ok()
    qs = {}
    chunk_count = 0
    try:
        qs = queue_status()
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as n FROM memory_chunks")
            chunk_count = cur.fetchone()['n']
        conn.close()
    except:
        pass

    return jsonify({
        'status': 'ok' if db_status else 'degraded',
        'db': 'connected' if db_status else 'error',
        'chunks': chunk_count,
        'queue': qs,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/retrieve', methods=['POST'])
def retrieve_endpoint():
    """
    Retrieve relevant chunks for a query.
    Body: { "query": "...", "top_k": 5, "source_type": null }
    Returns: { "results": [...], "query": "..." }
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'query field required'}), 400

    query = data['query'].strip()
    if not query:
        return jsonify({'error': 'query is empty'}), 400

    top_k = data.get('top_k', CONFIG['top_k'])
    source_type = data.get('source_type', None)

    try:
        results = retrieve(query, top_k=top_k, source_type=source_type)
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        log.error(f"Retrieve error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/store', methods=['POST'])
def store_endpoint():
    """
    Immediately embed and store a single chunk.
    Body: { "content": "...", "source_type": "session", "source_ref": "..." }
    Use for small, time-sensitive items (session memory entries).
    """
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'content field required'}), 400

    content = data['content'].strip()
    source_type = data.get('source_type', 'manual')
    source_ref = data.get('source_ref', '')

    if not content:
        return jsonify({'error': 'content is empty'}), 400

    try:
        inserted_id = store_chunk(content, source_type, source_ref)
        return jsonify({'id': inserted_id, 'status': 'stored'})
    except Exception as e:
        log.error(f"Store error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ingest', methods=['POST'])
def ingest_endpoint():
    """
    Queue a document for chunked ingestion (lazy, background processing).
    Body: { "content": "...", "source_type": "document", "source_ref": "My Doc Title" }
    Use for larger documents — they get chunked and queued.
    """
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'content field required'}), 400

    content = data['content'].strip()
    source_type = data.get('source_type', 'document')
    source_ref = data.get('source_ref', '')

    if not content:
        return jsonify({'error': 'content is empty'}), 400

    chunks = chunk_text(content, CONFIG['chunk_size'], CONFIG['chunk_overlap'])
    queue_chunks(chunks, source_type, source_ref)

    return jsonify({
        'status': 'queued',
        'chunks': len(chunks),
        'source_ref': source_ref
    })

@app.route('/queue', methods=['GET'])
def queue_endpoint():
    """Return current queue status."""
    try:
        return jsonify(queue_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/queue/retry', methods=['POST'])
def queue_retry():
    """Retry all errored queue items."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE embedding_queue SET status = 'pending', error_msg = NULL WHERE status = 'error'"
            )
            affected = cur.rowcount
    finally:
        conn.close()
    return jsonify({'retried': affected})

@app.route('/stats', methods=['GET'])
def stats():
    """Return memory store statistics."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT source_type, COUNT(*) as count,
                   SUM(token_count) as total_tokens
                   FROM memory_chunks
                   GROUP BY source_type
                   ORDER BY count DESC"""
            )
            by_type = cur.fetchall()

            cur.execute("SELECT COUNT(*) as total FROM memory_chunks")
            total = cur.fetchone()['total']

            cur.execute(
                "SELECT created_at, source_type, source_ref FROM memory_chunks ORDER BY created_at DESC LIMIT 5"
            )
            recent = cur.fetchall()
            # Convert datetime to string for JSON
            for r in recent:
                r['created_at'] = str(r['created_at'])

        return jsonify({
            'total_chunks': total,
            'by_type': by_type,
            'recent': recent,
            'queue': queue_status()
        })
    finally:
        conn.close()

@app.route('/clear', methods=['POST'])
def clear():
    """
    Clear memory chunks by source_type (or all if source_type='ALL').
    Body: { "source_type": "session" }  or  { "source_type": "ALL" }
    Requires confirmation token.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'body required'}), 400

    source_type = data.get('source_type', '')
    confirm = data.get('confirm', '')

    if confirm != 'BANGOR_ARCHIVE':
        return jsonify({'error': 'confirmation token required: BANGOR_ARCHIVE'}), 403

    conn = get_db()
    try:
        with conn.cursor() as cur:
            if source_type == 'ALL':
                cur.execute("DELETE FROM memory_chunks")
                cur.execute("DELETE FROM embedding_queue")
            else:
                cur.execute("DELETE FROM memory_chunks WHERE source_type = %s", (source_type,))
        affected = cur.rowcount
    finally:
        conn.close()

    log.warning(f"Cleared {affected} chunks (source_type={source_type})")
    return jsonify({'cleared': affected, 'source_type': source_type})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bangor Roundtable Memory Server')
    parser.add_argument('--config', default='config.json', help='Path to config.json')
    parser.add_argument('--port', type=int, default=None, help='Port to listen on')
    parser.add_argument('--host', default=None, help='Host to bind to')
    args = parser.parse_args()

    CONFIG.update(load_config(args.config))
    if args.port: CONFIG['port'] = args.port
    if args.host: CONFIG['host'] = args.host

    if not CONFIG['openai_key']:
        log.error("No OpenAI key configured. Set keys.openai in config.json")
        sys.exit(1)

    if not CONFIG['db_pass']:
        log.error("No database password configured. Set database.password in config.json")
        sys.exit(1)

    # Test DB connection
    log.info(f"Connecting to MariaDB at {CONFIG['db_host']}:{CONFIG['db_port']}...")
    if not db_ok():
        log.error("Cannot connect to database. Check config and that MariaDB is running.")
        sys.exit(1)
    log.info("Database connection OK")

    # Start queue processor in background
    queue_thread = threading.Thread(target=process_queue, daemon=True)
    queue_thread.start()

    # Start Flask
    log.info(f"Bangor Roundtable Memory Server starting on {CONFIG['host']}:{CONFIG['port']}")
    log.info(f"Treaty of Bangor — MISC-2026-001 — All shall be well.")
    app.run(
        host=CONFIG['host'],
        port=CONFIG['port'],
        debug=False,
        threaded=True
    )
