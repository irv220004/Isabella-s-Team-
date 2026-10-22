# Week 8 Supplement — The Pro Workflow: Branching, Packages, Sealed Environments

Companion to deck 08. Read before class. Lab: Operation Renovation.

**Data this week:** none. You restructure the code you already have. No downloads.

---

## 1. Before class (10 minutes, each detective)

- `git pull` on your squad repo. Confirm `pytest` is green from the repo root as it stands today.
- Confirm Python 3.11 or newer: `python --version` (Windows) or `python3 --version` (Mac/Linux).
- Know which squad reviews yours today: 1→2→3→4→1.

## 2. Target repo layout (what "done" looks like)

```
squad-N/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ data/              # raw inputs. Gitignored from week 9 on.
│   └─ .gitkeep
├─ src/
│   ├─ __init__.py
│   ├─ intake.py      # parse_row, load_cases (wk2–6)
│   ├─ models.py      # the Case class (wk7)
│   └─ patterns.py    # regex extractors (wk5)
├─ tests/
│   ├─ __init__.py
│   └─ test_intake.py
└─ reports/           # outputs: CSVs, charts, maps (wk9+)
    └─ .gitkeep
```

`.gitkeep` is an empty file. Git does not track empty folders, so this keeps `data/` and `reports/` in the repo.

## 3. The steps, with the commands

**Step 1. Branch and skeleton**

```bash
git checkout main && git pull
git checkout -b feature/wk8-renovation
mkdir -p src tests data reports
touch src/__init__.py tests/__init__.py data/.gitkeep reports/.gitkeep
```

Windows PowerShell: `New-Item src/__init__.py, tests/__init__.py, data/.gitkeep, reports/.gitkeep -ItemType File`

**Step 2. Move modules with history**

```bash
git mv intake.py src/intake.py
git mv case_model.py src/models.py
git mv pattern_hunt.py src/patterns.py
git mv test_intake.py tests/test_intake.py
```

Use your real filenames. `git mv` keeps the file's history attached. A plain move plus add shows up as delete + create, and `git log --follow` loses the trail.

**Step 3. Fix imports**

Inside `tests/test_intake.py`, change `from intake import ...` to `from src.intake import ...`. Inside `src/models.py`, if it imports from intake, use `from src.intake import ...` as well.

Run `pytest` from the repo root. If you see `ModuleNotFoundError: No module named 'src'`, you are not in the repo root, or `src/__init__.py` is missing.

Any data path inside your code that said `"raw_cases.txt"` now says `"data/raw_cases.txt"`. Move the data files into `data/` with `git mv` too.

**Step 4. Virtual environment and lockfile**

```bash
python -m venv .venv
# Mac/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows cmd
.venv\Scripts\activate.bat

pip install pytest pandas
pip freeze > requirements.txt
```

If PowerShell refuses to run the activate script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again.

Your prompt should now start with `(.venv)`. Every `pip install` from here on happens inside it, followed by `pip freeze > requirements.txt`.

**Step 5. .gitignore**

Create `.gitignore` at the repo root:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
data/*.csv
data/*.json
data/*.db
!data/.gitkeep
```

The `data/` rules matter next week when a 12.8 MB file lands in that folder.

**Step 6. Commit, push, open the PR**

```bash
git add -A
git commit -m "wk8: package structure, venv, requirements"
git push -u origin feature/wk8-renovation
```

Open the PR on GitHub. Title: `wk8 renovation`. In the description paste the output of `pytest` and `tree` (or `ls -R`).

## 4. Cross-squad review: the checklist you use on their PR

Pull their branch and run it. Do not review from the diff view alone.

```bash
git fetch origin
git checkout feature/wk8-renovation   # on THEIR repo, cloned locally
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Then, in order:

1. Does it run? Did `pip install -r requirements.txt` succeed on your machine?
2. Do the tests pass from the new structure?
3. Can the author explain every line? Ask about one.
4. Names: would a stranger understand `src/intake.py` versus `src/stuff.py`?
5. Any bare `except:`? Any magic numbers?
6. Does each module do one thing?

Leave at least two substantive comments. "LGTM" with nothing else does not count. Critique the code, never the coder.

## 5. Results checklist (before you leave)

- [ ] Repo tree matches section 2
- [ ] `pytest` green, imported from `src/`
- [ ] `requirements.txt` committed, `.venv/` ignored
- [ ] PR has 2 or more review comments from another squad, all addressed
- [ ] Your squad left 2 or more substantive comments on the squad you reviewed
- [ ] Merged to `main`

## 6. Install ahead for week 9

Inside your venv: `pip install pandas numpy` then `pip freeze > requirements.txt`, commit. Week 9 downloads two real datasets. Read `wk09_supplement_real_data.md` before class so the downloads are done.

## 7. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `No module named 'src'` | pytest run from wrong folder, or no `src/__init__.py` | `cd` to repo root; create the file |
| Tests pass locally, fail for reviewer | A package you installed is not in `requirements.txt` | `pip freeze > requirements.txt`, commit |
| `.venv` shows up in `git status` | `.gitignore` missing or misspelled | Check filename is exactly `.gitignore` at the root |
| `pip` installs to the system Python | venv not activated | Look for `(.venv)` in your prompt |
