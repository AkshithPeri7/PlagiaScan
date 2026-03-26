# PlagiaScan — Complete VS Code Setup Guide
### Team: Innovators Hub | H4T-019 | Keerthana P N

---

## Project Files
```
plagascan/
├── index.html       ← Frontend (Login + User App)
├── backend.html     ← Developer Dashboard
├── app.py           ← Flask API (Python backend)
├── plagascan.sql    ← MySQL database schema + seed
├── .env             ← Your config (create this)
└── README.md
```

---

## STEP 1 — Install VS Code Extensions

Open VS Code → Extensions (Ctrl+Shift+X) → Search and install:

| Extension | Purpose |
|---|---|
| **Python** (by Microsoft) | Run Python files |
| **Live Server** (by Ritwick Dey) | Open HTML with auto-refresh |
| **MySQL** (by cweijan) | View your database inside VS Code |

---

## STEP 2 — Install Python

1. Download Python 3.10+ from https://python.org/downloads
2. During install → ✅ check **"Add Python to PATH"**
3. Verify: open VS Code Terminal (`Ctrl+backtick`) → type:
   ```
   python --version
   ```
   Should show: `Python 3.10.x` or higher

---

## STEP 3 — Install MySQL

1. Download MySQL Community from https://dev.mysql.com/downloads/installer/
2. Install with default settings
3. Set root password (remember this — you'll need it)
4. After install, open **MySQL Workbench**

---

## STEP 4 — Set Up the Database

**Option A — MySQL Workbench:**
1. Open MySQL Workbench → connect to localhost
2. Click File → Open SQL Script → select `plagascan.sql`
3. Click the lightning bolt ⚡ button to run it

**Option B — VS Code Terminal:**
```bash
mysql -u root -p < plagascan.sql
```
Enter your MySQL root password when prompted.

✅ You should see: `PlagiaScan DB setup complete!`

---

## STEP 5 — Create Your .env File

In VS Code, create a new file named `.env` (in same folder as app.py):

```
SECRET_KEY=plagascan_hackathon_2024
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_root_password_here
DB_NAME=plagascan
GOOGLE_API_KEY=AIzaSyCA77O_ZX6bNqFmjkUWwN27XVCNnECbV4Q
GOOGLE_CX=84ed576e948c04777
ANTHROPIC_API_KEY=
```

> Replace `your_mysql_root_password_here` with your actual MySQL password.
> Leave ANTHROPIC_API_KEY empty for now (Google Search works without it).

---

## STEP 6 — Install Python Packages

In VS Code Terminal (`Ctrl+backtick`):
```bash
pip install flask flask-cors mysql-connector-python bcrypt anthropic python-dotenv requests
```

Wait for all packages to install. If `pip` not found, try `pip3`.

---

## STEP 7 — Run the Flask Server

In VS Code Terminal:
```bash
python app.py
```

You should see:
```
=======================================================
  PlagiaScan Flask API  —  http://localhost:5000
  Google CSE ID : 84ed576e948c04777
  Claude AI     : ✗ not set (optional)
=======================================================
```

🟢 Keep this terminal open while working.

---

## STEP 8 — Open the Frontend

**Method 1 — Live Server (Recommended):**
1. Right-click `index.html` in VS Code Explorer
2. Click **"Open with Live Server"**
3. Browser opens at `http://127.0.0.1:5500/index.html`

**Method 2 — Double-click:**
Just double-click `index.html` in File Explorer to open in browser.

---

## Developer Login Credentials

| BD_ID | Name | Email | Password | Role |
|---|---|---|---|---|
| PS001 | Akshith | akshith@ps | akshith001 | Cr.Dev |
| PS002 | Joel | joel@ps | joel002 | Cr.Dev |
| PS003 | Mufaddal | mufaddal@ps | mufaddal003 | Admin |
| PS004 | George | george@ps | george004 | Jr.Dev |
| PS005 | David | david@ps | david005 | Jr.Dev |

> Logging in with any of these emails → redirects to `backend.html` (developer dashboard)

---

## How Plagiarism Check Works

```
User pastes code
      ↓
Flask extracts keywords from code
      ↓
Google Custom Search API searches online for similar code
      ↓
difflib computes text similarity with search snippets
      ↓
(Optional) Claude AI does deep line-by-line analysis
      ↓
If plagiarism > 65% → generate replacement code
      ↓
Check for errors → generate fixed code
      ↓
Save result to MySQL → show to user
```

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| `ModuleNotFoundError: flask` | Run `pip install flask flask-cors mysql-connector-python bcrypt anthropic python-dotenv requests` |
| `Access denied for user 'root'` | Check DB_PASSWORD in .env matches your MySQL password |
| `Connection refused` (frontend) | Make sure `python app.py` is running in terminal |
| `CORS error` in browser | Flask is not running — start it first |
| Google search returns empty | Check GOOGLE_API_KEY and GOOGLE_CX in .env |

---

## Folder Structure to Create in VS Code

```
📁 PlagiaScan/           ← Create this folder
   ├── index.html
   ├── backend.html
   ├── app.py
   ├── plagascan.sql
   ├── .env             ← Create this manually
   └── README.md
```

Open this folder in VS Code: File → Open Folder → select PlagiaScan

---

*Built for HIRE-4-THON National Level Hackathon*
