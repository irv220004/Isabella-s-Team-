# src/models.py - the Case class (week 7)
from src.intake import (                     # pull in everything the Case class needs to clean a row
    TODAY,
    RAW_COLUMNS,
    clean_case_id,
    clean_name,
    clean_sex,
    clean_age,
    clean_date,
    clean_beat,
    clean_status,
    extract_callback_phone,
)


class Case:
    """One cold case, built from a cleaned row of the raw CSV."""

    def __init__(self, case_id, victim_name, sex, age, incident_date, beat, status, callback_phone):
        # __init__ runs automatically every time Case(...) is called.
        # self.something = value stores a value ON this specific object.
        self.case_id = case_id                      # e.g. "CC-10003"
        self.victim_name = victim_name               # e.g. "Ramirez, K"
        self.sex = sex                                # "M", "F", or "U"
        self.age = age                                # an int, or "" if unknown
        self.incident_date = incident_date            # a real date object, not a string
        self.beat = beat                              # 3-digit beat string, or ""
        self.status = status                          # "OPEN" or "CLOSED"
        self.callback_phone = callback_phone          # "214-555-1234", or ""

    @classmethod
    def from_row(cls, row):
        """Build a Case from one raw 9-field row, or raise ValueError with a reason."""
        # @classmethod means we call this on the CLASS itself: Case.from_row(row).
        # "cls" is the Case class, so cls(...) below is the same as Case(...).
        if len(row) != RAW_COLUMNS:                  # a truncated or extra-field row can't be trusted
            raise ValueError("wrong field count")
        return cls(                                   # cls(...) builds and returns the new Case object
            case_id=clean_case_id(row[0]),            # row[0] = case_id column; may raise "bad case_id"
            victim_name=clean_name(row[1]),           # row[1] = victim_name column; never raises
            sex=clean_sex(row[2]),                    # row[2] = sex column; never raises
            age=clean_age(row[3]),                    # row[3] = age column; never raises
            incident_date=clean_date(row[4]),         # row[4] = date column; may raise 3 different reasons
            beat=clean_beat(row[6]),                  # row[6] = beat column; row[5] (address) is skipped on purpose
            status=clean_status(row[7]),              # row[7] = status column; may raise "unknown status"
            callback_phone=extract_callback_phone(row[8]),  # row[8] = tip_notes column; never raises
        )

    # @property lets us call these WITHOUT parentheses, like case.year instead
    # of case.year(). Each one is recalculated fresh from incident_date every
    # time, so it can never fall out of sync with the stored data.

    @property
    def year(self):
        return self.incident_date.year               # date objects already know their own year

    @property
    def years_unsolved(self):
        return TODAY.year - self.incident_date.year   # how many years between the incident and "today"

    @property
    def is_stale(self):
        """True if this case is still OPEN after 5+ years."""
        return self.status == "OPEN" and self.years_unsolved >= 5   # both conditions must hold

    def to_row(self):
        """This case's fields in cases_clean.csv column order."""
        return [self.case_id, self.victim_name, self.sex, self.age,       # first 4 clean columns
                self.incident_date.isoformat(), self.year, self.beat,     # date as text, year, beat
                self.status, self.callback_phone]                         # last 2 clean columns
