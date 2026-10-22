import re  # the standard library module that understands regex patterns


# ---------------------------------------------------------------------------
# CORE EXTRACTORS (slide 12, step 3) - one function per required pattern.
# Each takes the raw tip text and returns a LIST of every match, because a
# single tip could in theory mention more than one phone number or date.
# ---------------------------------------------------------------------------


def extract_phones(text):
    """Return every phone number in text, matching (214) 555-1234 or 214-555-1234."""
    # \(? optional "(" / \d{3} area code / \)? optional ")" / [ -] one space-or-dash
    # separator / \d{3}-\d{4} exchange+line (always dash-joined) - one pattern
    # catches BOTH required formats at once (slide 13), no merging needed.
    pattern = r"\(?\d{3}\)?[ -]\d{3}-\d{4}"
    # quirk: a few tips wrap the WHOLE number in one "(...)", e.g. "(784-550-8605)"
    # instead of "(784) 550-8605". \(? only looks for a paren right after the area
    # code, so that shape matches "(784-550-8605" (leading paren kept, trailing one
    # left behind) - still correctly counted as a callback below, just prints oddly.
    return re.findall(pattern, text)


def extract_case_refs(text):
    """Return every case reference in text, e.g. CC-14589."""
    pattern = r"CC-\d{5}"  # literal "CC-" then exactly 5 digits (slide 7's decoder ring)
    return re.findall(pattern, text)


def extract_beats(text):
    """Return every beat number mentioned in text, e.g. '341' from 'beat 341'."""
    pattern = r"[Bb]eat (\d{3})"  # [Bb]eat = "beat"/"Beat"; (\d{3}) is a CAPTURE GROUP
    return re.findall(pattern, text)  # a capture group makes findall return just "341", not "beat 341"


def extract_iso_dates(text):
    """Return every ISO-format date in text, e.g. 2019-02-19 (YYYY-MM-DD)."""
    pattern = r"\d{4}-\d{2}-\d{2}"
    return re.findall(pattern, text)


def extract_us_dates(text):
    """Return every US numeric date in text, e.g. 4/7/2019 (M/D/YYYY)."""
    pattern = r"\d{1,2}/\d{1,2}/\d{4}"  # \d{1,2} = 1 OR 2 digits, so "4/7/2019" and "10/22/2020" both match
    return re.findall(pattern, text)


# ---------------------------------------------------------------------------
# STRETCH EXTRACTORS (slide 14, "Done Early? / Next Week" - not required to
# hit the deliverable numbers, but the squad lab called them out as the
# natural next step once the four core extractors existed). Left in so the
# reviewer can see the same one-function-one-job rule applied to harder
# shapes, but the "Results To Achieve" numbers below never depend on them.
# ---------------------------------------------------------------------------


def extract_month_name_dates(text):
    """Return every month-name date, e.g. 'February 15, 2017' or '4 April 2024'."""
    months = (r"January|February|March|April|May|June|July|August|"
              r"September|October|November|December")  # all 12 names, OR'd together
    month_day_year = rf"(?:{months}) \d{{1,2}}, \d{{4}}"   # shape 1: "February 15, 2017"
    day_month_year = rf"\d{{1,2}} (?:{months}) \d{{4}}"    # shape 2: "4 April 2024"
    pattern = rf"{month_day_year}|{day_month_year}"  # "|" = regex OR, so either shape matches
    return re.findall(pattern, text)


def extract_addresses(text):
    """Return every street address in text, e.g. '591 haskell avenue'."""
    suffixes = r"avenue|road|drive|street|lane|boulevard|way|court|circle"  # real street-type words
    # requiring one of those suffixes at the end stops a bare "\d+ word" pattern
    # from also grabbing "341 area" out of "beat 341 area" (not an address)
    pattern = rf"\d+ [a-z]+ (?:{suffixes})"
    return re.findall(pattern, text)


def unique_phones(text):
    """Return extract_phones(text) with duplicate numbers removed, order kept."""
    seen = set()   # week-4 dedupe trick: O(1) membership check for "have we seen this phone?"
    deduped = []    # a set alone would scramble order, so matches are appended here instead
    for phone in extract_phones(text):
        if phone not in seen:
            seen.add(phone)
            deduped.append(phone)
    return deduped


# ---------------------------------------------------------------------------
# SUMMARY (slide 12, step 4) - one function that calls every extractor and
# formats a single report line per tip.
# ---------------------------------------------------------------------------


def summarize_tip(tip_number, text):
    """Run every extractor on one tip; return (formatted line, has_callback)."""
    phones = extract_phones(text)
    case_refs = extract_case_refs(text)
    beats = extract_beats(text)
    iso_dates = extract_iso_dates(text)
    us_dates = extract_us_dates(text)
    month_dates = extract_month_name_dates(text)   # stretch, shown for free

    has_callback = len(phones) >= 1  # slide 13: "has a callback" = at least 1 phone found
    # (verified by hand against all 24 tips: reproduces the required 15/9 split)
    callback_tag = "YES" if has_callback else "NO"  # just a display label for has_callback

    line = (
        f"TIP {tip_number:>2}: phones={phones} case_refs={case_refs} "
        f"beats={beats} iso_dates={iso_dates} us_dates={us_dates} "
        f"month_dates={month_dates} callback={callback_tag}"
    )
    return line, has_callback


# ---------------------------------------------------------------------------
# MAIN - reads the tip file, runs the pipeline over every line, and prints
# the exact "Results To Achieve" report required on slide 13.
# ---------------------------------------------------------------------------


def main():
    filename = input(
        "Enter the tip-line file name with extension (default wk05_data_tipline.txt): "
    ).strip()
    if filename == "":                      # Enter alone picks the default file
        filename = "wk05_data_tipline.txt"

    data_file = open(filename, "r", encoding="utf-8")
    lines = data_file.readlines()           # read every tip into memory at once
    data_file.close()                       # close the file immediately after

    # accumulators created BEFORE the loop starts (same habit as week-3/week-4 labs)
    tips_processed = 0         # how many non-blank tips actually got processed
    tips_with_callback = 0     # tips containing >= 1 phone number
    tips_without_callback = 0  # tips with no phone number - leads that die, per slide 13

    print("=== Per-Tip Extraction ===")
    tip_number = 0
    for raw_line in lines:
        line = raw_line.strip()             # drop the trailing newline/whitespace

        if line == "":                      # guard against a stray blank line
            continue                        # skip it instead of crashing

        tip_number += 1                     # each remaining line is one more tip

        summary_line, has_callback = summarize_tip(tip_number, line)
        print(summary_line)

        tips_processed += 1
        if has_callback:
            tips_with_callback += 1
        else:
            tips_without_callback += 1

    # --- slide 13's "Results To Achieve" report - numbers must match ---
    print()
    print("=== Results To Achieve ===")
    print(f"Tips processed:       {tips_processed}")
    print(f"Tips with a callback: {tips_with_callback}")
    print(f"Tips with NO callback: {tips_without_callback}  <- these leads die without follow-up")


if __name__ == "__main__":
    main()
