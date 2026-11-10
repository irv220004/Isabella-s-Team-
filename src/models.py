# src/models.py - the Case class (week 7)
from src.intake import (
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
        self.case_id = case_id
        self.victim_name = victim_name
        self.sex = sex
        self.age = age
        self.incident_date = incident_date   # a date object, not a string
        self.beat = beat
        self.status = status
        self.callback_phone = callback_phone

    @classmethod
    def from_row(cls, row):
        """Build a Case from one raw 9-field row, or raise ValueError with a reason."""
        if len(row) != RAW_COLUMNS:
            raise ValueError("wrong field count")
        return cls(
            case_id=clean_case_id(row[0]),
            victim_name=clean_name(row[1]),
            sex=clean_sex(row[2]),
            age=clean_age(row[3]),
            incident_date=clean_date(row[4]),   # row[5] (address) is dropped on purpose
            beat=clean_beat(row[6]),
            status=clean_status(row[7]),
            callback_phone=extract_callback_phone(row[8]),
        )

    @property
    def year(self):
        return self.incident_date.year

    @property
    def years_unsolved(self):
        return TODAY.year - self.incident_date.year

    @property
    def is_stale(self):
        """True if this case is still OPEN after 5+ years."""
        return self.status == "OPEN" and self.years_unsolved >= 5

    def to_row(self):
        """This case's fields in cases_clean.csv column order."""
        return [self.case_id, self.victim_name, self.sex, self.age,
                self.incident_date.isoformat(), self.year, self.beat,
                self.status, self.callback_phone]
