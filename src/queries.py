"""Three questions asked of data/case.db. Run: python -m src.queries"""
import sqlite3                               # built-in SQLite driver
import pandas as pd                          # read_sql returns query results as DataFrames

# Q1: murders per year. Years outside 2014-2026 are bad data (e.g. 1011, 1429, 1967-1991) and are excluded here.
q1 = """SELECT servyr AS year, COUNT(*) AS murders
        FROM incidents WHERE servyr BETWEEN 2014 AND 2026
        GROUP BY servyr ORDER BY servyr"""

# Q2: the five police beats with the most murders.
q2 = """SELECT beat, COUNT(*) AS n FROM incidents
        WHERE beat IS NOT NULL GROUP BY beat ORDER BY n DESC LIMIT 5"""

# Q3 (our squad's slice): what share of murders happened at a residence?
# Chosen because the premise field is populated on most rows and "at home" is a meaningful split for clearance.
q3 = """SELECT ROUND(100.0 * SUM(premise LIKE '%RESIDENCE%') / COUNT(*), 1) AS pct_residence
        FROM incidents"""

# Data-quality check (not in the handout): rows quarantined by the year filter in Q1, so they are not dropped silently.
q_bad_years = """SELECT servyr, COUNT(*) AS n FROM incidents
                 WHERE servyr IS NULL OR servyr NOT BETWEEN 2014 AND 2026
                 GROUP BY servyr ORDER BY servyr"""


def main() -> None:
    con = sqlite3.connect("data/case.db")
    for q in (q1, q2, q3, q_bad_years):
        print(pd.read_sql(q, con), "\n")
    con.close()


if __name__ == "__main__":
    main()
