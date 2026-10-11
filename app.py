"""
PlagiaScan - Flask Backend Application
Team: Innovators Hub | H4T-019

Install:
    pip install flask flask-cors mysql-connector-python bcrypt anthropic python-dotenv requests

Run:
    python app.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import anthropic
import os, json, re, requests, difflib, random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "plagiascan_secret_2024")
CORS(app, supports_credentials=True, origins=["*"])

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME",     "plagiascan"),
}
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY",  "AIzaSyCA77O_ZX6bNqFmjkUWwN27XVCNnECbV4Q")
GOOGLE_CX         = os.getenv("GOOGLE_CX",       "84ed576e948c04777")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


# ─────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return pw == hashed   # plain-text fallback for dev accounts


# ─────────────────────────────────────────────────────────
# GOOGLE CUSTOM SEARCH
# ─────────────────────────────────────────────────────────
def google_search_code(query: str, num: int = 5):
    """Search using Google Custom Search API, fallback to mock if API fails."""
    if GOOGLE_API_KEY and GOOGLE_CX and GOOGLE_API_KEY != "AIzaSyCA77O_ZX6bNqFmjkUWwN27XVCNnECbV4Q":
        try:
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CX,
                'q': query,
                'num': min(num, 10)
            }
            resp = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('items', [])
                results = []
                for item in items[:num]:
                    results.append({
                        "title": item.get('title', 'Google Result'),
                        "link": item.get('link', ''),
                        "snippet": item.get('snippet', '')
                    })
                if results:
                    return results
        except Exception as e:
            print(f"[Google API Error] {e}")
            
    # Try DuckDuckGo Fallback
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get('https://html.duckduckgo.com/html/', params={'q': query}, headers=headers, timeout=10)
        results = []
        snippets = re.findall(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.DOTALL | re.IGNORECASE)
        for link, snip in snippets[:num]:
            clean_snip = re.sub(r'<[^>]+>', '', snip).strip()
            results.append({
                "title": "DuckDuckGo Result",
                "link": link,
                "snippet": clean_snip
            })
        if results:
            return results
    except Exception as e:
        print(f"[DuckDuckGo Error] {e}")

    # Final Fallback
    return [{
        "title": "Similar Code Found Online",
        "link": "https://github.com/search",
        "snippet": query
    }]

def compute_similarity(a: str, b: str) -> float:
    a = re.sub(r'\s+', ' ', a.strip().lower())
    b = re.sub(r'\s+', ' ', b.strip().lower())
    return difflib.SequenceMatcher(None, a, b).ratio()

def build_search_query(code: str) -> str:
    keywords = []
    for line in code.split('\n')[:30]:
        line = line.strip()
        if re.match(r'^(import|from|#include|using|require|package)', line):
            keywords.append(line[:60])
        elif re.match(r'^(def |class |function |void |int |public |private |static )', line):
            keywords.append(line[:60])
    return (' '.join(keywords[:4]) if keywords else code[:120]) + " code example"


def check_and_fix_code(code: str) -> dict:
    import ast, builtins, difflib, re
    errors = []
    fixed = ""
    lines = code.split('\n')
    is_python = not bool(re.search(r'(#include|using namespace|#define|<iostream>|public static void|function |\s*\{\s*$|\s*\}\s*$)', code, re.MULTILINE))

    if is_python:
        try:
            compile(code, "<string>", "exec")
            # Custom AST Name checking for NameError since compile() succeeds on undefined names
            tree = ast.parse(code)
            defined = set(dir(builtins))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    defined.add(node.id)
                elif isinstance(node, ast.arg):
                    defined.add(node.arg)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    defined.add(node.name)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined:
                        errors.append({"line": getattr(node, "lineno", 1), "type": "NameError", "description": f"Name '{node.id}' is not defined"})
                        curr_code = fixed if fixed else code
                        # Try to find a close match in declared variables or builtins
                        matches = difflib.get_close_matches(node.id, defined, n=1, cutoff=0.7)
                        
                        if matches and matches[0] not in ["help", "hash", "hex", "id"]:
                            fixed = re.sub(r'\b' + node.id + r'\b', matches[0], curr_code)
                        else:
                            # Assume it's a missing string literal
                            fixed = re.sub(r'\b' + node.id + r'\b', f'"{node.id}"', curr_code)
        except SyntaxError as e:
            errors.append({"line": getattr(e, "lineno", len(lines)), "type": "SyntaxError", "description": str(getattr(e, "msg", e))})
            if hasattr(e, "lineno") and e.lineno and e.lineno <= len(lines):
                idx = e.lineno - 1
                if re.match(r'^\s*(def|class|if|elif|else|for|while|try|except|finally|with)\b.*[^:]\s*$', lines[idx]):
                    lines[idx] = lines[idx] + ":"
                    try:
                        compile('\n'.join(lines), "<string>", "exec")
                        fixed = '\n'.join(lines)
                    except SyntaxError:
                        fixed = ""
                elif "EOF" in str(getattr(e, "msg", "")):
                    lines[-1] = lines[-1] + ")"
                    fixed = '\n'.join(lines)
    else:
        o_braces = code.count('{')
        c_braces = code.count('}')
        if o_braces > c_braces:
            errors.append({"line": len(lines), "type": "SyntaxError", "description": "Missing closing brace '}'"})
            fixed = code + "\n}"
        if lines and not code.strip().endswith(";") and not code.strip().endswith("}") and not lines[-1].strip().startswith("//"):
            if not errors:
                errors.append({"line": len(lines), "type": "SyntaxError", "description": "Missing semicolon"})
                lines[-1] = lines[-1].rstrip() + ";"
                fixed = '\n'.join(lines)

    return {"errors": errors, "fixed": fixed}

# ─────────────────────────────────────────────────────────
# PLAGIARISM ANALYSIS  (Google Search + optional Claude)
# ─────────────────────────────────────────────────────────
def analyze_code(code: str) -> dict:
    # Step 1 — Google Search
    query          = build_search_query(code)
    search_results = google_search_code(query, num=5)
    accessed_urls  = [r["link"] for r in search_results]
    combined       = "\n\n".join(
        [f"Source: {r['link']}\nSnippet: {r['snippet']}" for r in search_results]
    )

    # Step 2 — Rough similarity from snippets
    max_sim = max((compute_similarity(code, r["snippet"]) for r in search_results), default=0.0)
    google_est = round(max_sim * 100, 1)

    # Step 3 — Claude deep analysis (if API key present)
    claude_result = {}
    if ANTHROPIC_API_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            system = """You are PlagiaScan AI — expert code plagiarism detector.
You receive: (1) user's code, (2) Google search results showing similar online code.
Respond ONLY with valid JSON (no markdown, no extra text):
{
  "plagiarism_percentage": <0-100 float>,
  "is_plagiarized": <true if >65>,
  "confidence": <"high"|"medium"|"low">,
  "plagiarized_sections": [{"line_start":int,"line_end":int,"reason":"string","source_hint":"URL"}],
  "errors_found": [{"line":int,"type":"string","description":"string"}],
  "fixed_code": "<corrected full code or empty string>",
  "replacement_code": "<rewritten alternative if plagiarised >65%, else empty string>",
  "summary": "<2-3 sentence summary>",
  "accessed_websites": ["url1","url2"]
}"""
            user_msg = (
                f"Code:\n```\n{code[:3000]}\n```\n\n"
                f"Google Results:\n{combined[:2000]}\n\n"
                f"Google similarity estimate: {google_est}%"
            )
            resp = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=4000,
                system=system,
                messages=[{"role":"user","content":user_msg}]
            )
            raw = re.sub(r"```json\s*|\s*```","",resp.content[0].text).strip()
            claude_result = json.loads(raw)
        except Exception as e:
            print(f"[Claude Error] {e}")

    # Step 4 — Merge
    pct = claude_result.get("plagiarism_percentage", google_est)
    is_plagiarized = pct > 65
    
    plagiarized_sections = claude_result.get("plagiarized_sections", [])
    replacement_code = claude_result.get("replacement_code", "")
    
    # NEW FEATURE: Fallback for plagiarism sections if Claude skipped or didn't return them
    if not plagiarized_sections and is_plagiarized and search_results:
        s = difflib.SequenceMatcher(None, code.lower(), search_results[0]['snippet'].lower())
        match = s.find_longest_match(0, len(code), 0, len(search_results[0]['snippet']))
        
        if match.size > 10:
            start_str = code[:match.a]
            start_line = start_str.count('\n') + 1
            match_str = code[match.a:match.a+match.size]
            end_line = start_line + match_str.count('\n')
            
            plagiarized_sections.append({
                "line_start": start_line,
                "line_end": max(start_line, end_line),
                "reason": "High similarity substring detected locally.",
                "source_hint": search_results[0]['link']
            })
            replacement_code = "// Consider rewriting this section using your own logic, avoiding publicly indexed snippets."

    errors_found = claude_result.get("errors_found", [])
    fixed_code = claude_result.get("fixed_code", "")
    
    # NEW FEATURE: Check and fix errors (always run if Claude skipped)
    if not errors_found and not fixed_code:
        fix_data = check_and_fix_code(code)
        if fix_data["errors"]:
            errors_found = fix_data["errors"]
            fixed_code = fix_data["fixed"]

    return {
        "plagiarism_percentage": pct,
        "is_plagiarized":        is_plagiarized,
        "confidence":            claude_result.get("confidence", "low" if not claude_result else "medium"),
        "plagiarized_sections":  plagiarized_sections,
        "errors_found":          errors_found,
        "fixed_code":            fixed_code,
        "replacement_code":      replacement_code,
        "summary":               claude_result.get("summary",
                                    f"Checked {len(search_results)} similar sources. Similarity: {google_est}%."),
        "accessed_websites":     accessed_urls,
        "google_results":        search_results,
    }


@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/index.html")
def serve_index_html():
    return send_from_directory(".", "index.html")

@app.route("/visualizer")
def serve_visualizer():
    return send_from_directory(".", "plagiarism-visualizer.html")

@app.route("/backend.html")
def serve_backend():
    return send_from_directory(".", "backend.html")

@app.route("/logo.jpg")
def serve_logo():
    return send_from_directory(".", "logo.jpg")

@app.before_request
def track_traffic():
    if not request.path.startswith("/api/"):
        return
    if request.path.startswith("/api/admin/"):
        return # don't track the admin traffic polling itself
    
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO web_traffic (active_users, page_visited) VALUES (1, %s)", (request.path,))
        db.commit()
        cur.close()
        db.close()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════

@app.route("/api/login", methods=["POST"])
def login():
    data  = request.json
    email = data.get("email","").strip()
    pw    = data.get("password","")

    db  = get_db()
    cur = db.cursor(dictionary=True)

    # Developer check
    cur.execute("SELECT * FROM backend_developers WHERE email=%s", (email,))
    dev = cur.fetchone()
    if dev and check_password(pw, dev["password"]):
        cur.close(); db.close()
        return jsonify({"success":True,"role":"developer","user":{
            "id":dev["bd_id"],"name":dev["name"],
            "email":dev["email"],"designation":dev["designation"]
        }})

    # User check
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    if user and check_password(pw, user["password"]):
        cur.close(); db.close()
        return jsonify({"success":True,"role":"user","user":{
            "id":user["u_id"],"name":user["name"],
            "email":user["email"],"phone":user["phone_number"]
        }})

    cur.close(); db.close()
    return jsonify({"success":False,"message":"Invalid email or password"}), 401


@app.route("/api/signup", methods=["POST"])
def signup():
    data  = request.json
    name  = data.get("name","").strip()
    email = data.get("email","").strip()
    phone = data.get("phone","").strip()
    pw    = data.get("password","")

    if not all([name,email,phone,pw]):
        return jsonify({"success":False,"message":"All fields are required"}), 400
    if len(pw) < 8:
        return jsonify({"success":False,"message":"Password must be at least 8 characters"}), 400

    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email,name,phone_number,password) VALUES (%s,%s,%s,%s)",
            (email, name, phone, hash_password(pw))
        )
        db.commit()
        uid = cur.lastrowid
        cur.close(); db.close()
        return jsonify({"success":True,"message":"Account created!","u_id":uid})
    except mysql.connector.IntegrityError:
        cur.close(); db.close()
        return jsonify({"success":False,"message":"Email already registered"}), 409


# ══════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════

@app.route("/api/profile/<int:u_id>", methods=["GET"])
def get_profile(u_id):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT u_id,name,email,phone_number FROM users WHERE u_id=%s", (u_id,))
    user = cur.fetchone()
    if not user:
        cur.close(); db.close()
        return jsonify({"success":False,"message":"Not found"}), 404

    cur.execute("SELECT COUNT(*) AS t FROM plagiarism_history WHERE u_id=%s", (u_id,))
    total = cur.fetchone()["t"]
    cur.execute("SELECT COUNT(*) AS p FROM plagiarism_history WHERE u_id=%s AND status='Plagiarized'", (u_id,))
    plagiarized = cur.fetchone()["p"]

    cur.execute("SELECT AVG(score) AS avg_pct FROM plagiarism_history WHERE u_id=%s", (u_id,))
    avg_res = cur.fetchone()
    avg_plag_pct = float(avg_res["avg_pct"]) if avg_res and avg_res["avg_pct"] is not None else 0.0

    cur.execute(
        "SELECT project_name,date,score,status FROM plagiarism_history WHERE u_id=%s ORDER BY date DESC LIMIT 2",
        (u_id,)
    )
    recent = cur.fetchall()
    for r in recent:
        r["date"] = r["date"].strftime("%Y-%m-%d %H:%M")
    cur.close(); db.close()

    return jsonify({
        "success": True,
        "user": user,
        "stats": {
            "total_files":       total,
            "plagiarized_files": plagiarized,
            "avg_score":         round(avg_plag_pct, 1),
            "impact_factor":     round(10.0 * (1.0 - (avg_plag_pct / 100.0)), 1) if total > 0 else 10.0,
        },
        "recent_history": recent,
    })

@app.route("/api/profile/<int:u_id>", methods=["DELETE"])
def delete_profile(u_id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE u_id=%s", (u_id,))
    db.commit()
    cur.close(); db.close()
    return jsonify({"success":True})


# ══════════════════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════════════════

@app.route("/api/history/<int:u_id>", methods=["GET"])
def get_history(u_id):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM plagiarism_history WHERE u_id=%s ORDER BY date DESC", (u_id,))
    rows = cur.fetchall()
    for r in rows:
        r["date"] = r["date"].strftime("%Y-%m-%d %H:%M")
    cur.close(); db.close()
    return jsonify({"success":True,"history":rows})

@app.route("/api/history/<int:hid>", methods=["DELETE"])
def delete_history(hid):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM plagiarism_history WHERE history_id=%s", (hid,))
    db.commit()
    cur.close(); db.close()
    return jsonify({"success":True})


# ══════════════════════════════════════════════════════════
# PLAGIARISM CHECK
# ══════════════════════════════════════════════════════════

@app.route("/api/check-plagiarism", methods=["POST"])
def check_plagiarism():
    data         = request.json
    code         = data.get("code","")
    project_name = data.get("project_name","Untitled")
    u_id         = data.get("u_id")

    if not code.strip():
        return jsonify({"success":False,"message":"No code provided"}), 400

    result = analyze_code(code)
    pct    = result["plagiarism_percentage"]
    status = "Plagiarized" if pct > 65 else "Clean"

    if u_id:
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO plagiarism_history (u_id,project_name,score,status,plagiarized_percentage,file_content,result_details) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (u_id, project_name, pct, status, pct, code[:5000], json.dumps(result))
        )
        db.commit()
        for url in result.get("accessed_websites",[])[:10]:
            cur.execute("INSERT INTO accessed_websites (website_url,relevance_score) VALUES (%s,%s)",
                        (url, round(random.uniform(0.5,1.0),2)))
        db.commit()
        cur.close(); db.close()


    return jsonify({"success":True,"result":result,"status":status,"percentage":pct})


# ══════════════════════════════════════════════════════════
# ADMIN DASHBOARD APIs
# ══════════════════════════════════════════════════════════

@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT u_id,name,email,phone_number,created_at FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    for u in users: u["created_at"] = u["created_at"].strftime("%Y-%m-%d")
    cur.close(); db.close()
    return jsonify({"success":True,"users":users})

@app.route("/api/admin/traffic", methods=["GET"])
def admin_traffic():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""SELECT DATE_FORMAT(timestamp,'%H:00') AS hour, SUM(active_users) AS avg_users
                   FROM web_traffic WHERE timestamp >= NOW()-INTERVAL 12 HOUR
                   GROUP BY hour ORDER BY hour""")
    rows = cur.fetchall()
    cur.close(); db.close()
    return jsonify({"success":True,"traffic":rows})

@app.route("/api/admin/errors", methods=["GET"])
def admin_errors():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 20")
    rows = cur.fetchall()
    for r in rows: r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M")
    cur.close(); db.close()
    return jsonify({"success":True,"errors":rows})

@app.route("/api/admin/plagiarism-stats", methods=["GET"])
def admin_plagiarism_stats():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM plagiarism_history")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS p FROM plagiarism_history WHERE status='Plagiarized'")
    plagiarized = cur.fetchone()["p"]
    cur.execute("SELECT project_name,date,score,status FROM plagiarism_history ORDER BY date DESC LIMIT 10")
    recent = cur.fetchall()
    for r in recent: r["date"] = r["date"].strftime("%Y-%m-%d %H:%M")
    cur.close(); db.close()
    return jsonify({"success":True,"total":total,"plagiarized":plagiarized,"recent":recent})

@app.route("/api/admin/accessed-websites", methods=["GET"])
def admin_websites():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""SELECT website_url, COUNT(*) AS access_count, MAX(timestamp) AS last_accessed
                   FROM accessed_websites GROUP BY website_url ORDER BY access_count DESC LIMIT 20""")
    rows = cur.fetchall()
    for r in rows: r["last_accessed"] = r["last_accessed"].strftime("%Y-%m-%d %H:%M")
    cur.close(); db.close()
    return jsonify({"success":True,"websites":rows})


if __name__ == "__main__":
    print("=" * 55)
    print("  PlagiaScan Flask API  —  http://localhost:5000")
    print(f"  Google CSE ID : {GOOGLE_CX}")
    print(f"  Claude AI     : {'✓ configured' if ANTHROPIC_API_KEY else '✗ not set (optional)'}")
    print("=" * 55)
    app.run(debug=True, port=5000)
