# Quiz Master Pro

A modern, fully-featured **Quiz Web Application** built with **Flask** (Python), **SQLite**, and **Vanilla JavaScript**.

- 4 categories (Science, Mathematics, General Knowledge, Computer)
- 5 difficulty levels per category (Very Easy to Expert) = **20 levels**
- 10 questions per level = **200 hand-written questions**
- 10 questions per quiz, 10-minute timer, auto-submit
- Unlock system, leaderboard, achievements, answer review, PDF export

![Stack](https://img.shields.io/badge/Flask-3.x-000000?logo=flask) ![Database](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite) ![JS](https://img.shields.io/badge/Vanilla%20JS-ES2020-f7df1e?logo=javascript) ![CSS](https://img.shields.io/badge/Glassmorphism-UI-8b5cf6)

---

## Features

### User features
- Animated glassmorphism UI with **light/dark mode**, gradient backgrounds and smooth animations
- Sign up / login / logout with **hashed passwords** and **session authentication**
- Forgot password flow (demo reset code)
- **Unlock system** - pass a level (60% or more) to unlock the next one
- Quiz player with:
  - live **countdown timer** (10:00) and **auto-submit**
  - **question palette** (jump between questions)
  - Previous / Next / Submit buttons + **submit confirmation**
  - **answer highlighting** and sound effects
  - **auto-save** - refresh the page and your quiz resumes
- **Randomized** question order and shuffled options on every attempt
- Result page: animated **circular score ring**, correct/wrong, percentage, time taken, **rank**, letter grade (A+ ... Fail), performance message
- **Answer review** after submission
- **PDF export** of results
- **Dashboard**: completed/locked levels, highest/average score, recent attempts, Chart.js charts, category progress, achievement badges
- **Leaderboard** ranked by score, percentage and speed
- **Search** for categories and levels

### Admin panel (`/admin/`)
- Dashboard analytics (users, questions, attempts, average score) with charts
- Questions CRUD with category/level filtering
- Categories CRUD
- Levels CRUD
- User list + **reset progress**
- All scores view + delete

### Security
- Password hashing (Werkzeug `generate_password_hash`)
- **CSRF protection** on all state-changing requests (forms + AJAX)
- **Prepared SQL statements** (SQL injection safe)
- **Session protection** (HttpOnly cookies, SameSite=Lax)
- Input validation and length capping
- Auto-escaping in templates (XSS safe)

---

## Project Structure

```text
quiz-master/
├── app.py                  # Flask app factory + entry point
├── requirements.txt
├── database.db             # SQLite database (auto-created & seeded on first run)
│
├── database/
│   ├── schema.py           # Table definitions + default metadata
│   ├── questions_data.py   # 200 seed questions
│   └── seed.py             # DB init / seeding logic
│
├── models/                 # Data-access layer
│   ├── db.py               # Connection management
│   ├── users.py            # Account queries
│   ├── questions.py        # Categories, levels, questions CRUD
│   ├── results.py          # Result storage + leaderboard + rank
│   ├── progress.py         # Unlock logic
│   └── attempts.py         # In-progress quiz attempts (resume/review)
│
├── routes/                 # Flask blueprints
│   ├── auth.py             # signup / login / logout / forgot / reset
│   ├── main.py             # home, categories, levels, dashboard, result...
│   ├── quiz.py             # quiz start / play / autosave / submit
│   ├── api.py              # JSON endpoints (charts, leaderboard, badges)
│   └── admin.py            # admin panel
│
├── utils/
│   ├── security.py         # CSRF, validation helpers
│   ├── decorators.py       # login_required / admin_required / public_only
│   └── grading.py          # grades, messages, pass logic
│
├── static/
│   ├── css/style.css       # global design system
│   ├── css/dashboard.css   # dashboard extras
│   ├── css/quiz.css        # quiz + result page
│   ├── js/script.js        # theme, loader, nav, helpers, sounds
│   ├── js/quiz.js          # quiz engine
│   └── js/dashboard.js     # charts + badges
│
└── templates/              # Jinja2 templates
    ├── base.html  index.html  login.html  signup.html
    ├── forgot.html  reset.html  categories.html  levels.html
    ├── quiz.html  result.html  leaderboard.html  dashboard.html
    ├── search.html  404.html  500.html
    └── admin*.html
```

---

## Setup & Installation

Requirements: **Python 3.10+**

```bash
# 1. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```


> The SQLite database `database.db` is created automatically on first run and
> seeded with the admin account and all 200 questions. Delete `database.db`
> to reset everything.



## How it works

1. **Create an account** and log in.
2. Pick a **category**, then choose **Level 1** (the only unlocked level initially).
3. Answer 10 questions within **10 minutes**.
4. Score **60% or more** to **pass** and unlock the **next level**.
5. Track progress on the **Dashboard**, compare with others on the **Leaderboard**.

### Grading

| Percentage | Grade |
|------------|-------|
| 90 - 100   | A+    |
| 80 - 89    | A     |
| 70 - 79    | B     |
| 60 - 69    | C     |
| < 60       | Fail  |

---

## Key Endpoints

| Method | Path                          | Description                          |
|--------|-------------------------------|--------------------------------------|
| GET    | `/`                           | Home                                 |
| GET/POST | `/signup`, `/login`         | Authentication                       |
| GET    | `/categories`                 | Category grid (requires login)       |
| GET    | `/levels/<category>`          | Levels for a category                |
| POST   | `/quiz/start`                 | Start a quiz                         |
| GET    | `/quiz`                       | Active quiz page (resumes)           |
| GET    | `/quiz/state`                 | Quiz state JSON                      |
| POST   | `/quiz/answer`                | Autosave one answer (JSON)           |
| POST   | `/quiz/submit`                | Grade & submit (JSON)                |
| GET    | `/result/<id>`                | Result + review                      |
| GET    | `/dashboard`, `/leaderboard`  | User dashboard / global leaderboard  |
| GET    | `/api/*`                      | JSON endpoints (stats, badges, admin)|
| GET/POST | `/admin/*`                  | Admin panel                          |

---

## Notes on production readiness

- All DB access uses **parameterized queries**; user input is **validated** and **length-capped**.
- Every mutation (login, signup, quiz submit, admin CRUD, logout) is **CSRF-protected**.
- Passwords are **hashed**; sessions use HttpOnly + SameSite cookies.
- For real deployment: use `waitress`/`gunicorn`, set a random `SECRET_KEY`,
  force HTTPS, and disable debug mode.

---

## Testing

A quick smoke test of the core flows (auth, quiz, grading, unlock, admin, CSRF):

```bash
python - <<'PY'
import re, json
from app import app
app.config['TESTING'] = True
c = app.test_client()
def csrf(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None

t = csrf(c.get('/signup').get_data(as_text=True))
assert c.post('/signup', data={'username':'tester','email':'t@test.com',
    'password':'secret1','confirm_password':'secret1','csrf_token':t}, follow_redirects=True).status_code == 200
print('signup OK')
PY
```

---

