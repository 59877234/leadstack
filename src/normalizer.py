import re

STREET_ABBREVIATIONS = {
    "street": "st", "st.": "st",
    "avenue": "ave", "ave.": "ave",
    "boulevard": "blvd", "blvd.": "blvd",
    "drive": "dr", "dr.": "dr",
    "lane": "ln", "ln.": "ln",
    "road": "rd", "rd.": "rd",
    "court": "ct", "ct.": "ct",
    "place": "pl", "pl.": "pl",
    "circle": "cir", "cir.": "cir",
    "terrace": "ter", "ter.": "ter",
    "apartment": "apt", "apt.": "apt",
    "suite": "ste", "ste.": "ste",
    "unit": "unit", "#": "unit",
    "north": "n", "south": "s", "east": "e", "west": "w",
}


def normalize_address(text: str | None) -> str:
    """Collapse an address to a comparable form: lowercase, punctuation
    stripped, common street/unit words abbreviated consistently. This is
    the string duplicates get matched on, not what's shown in the output.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    words = [STREET_ABBREVIATIONS.get(w, w) for w in text.split(" ")]
    return " ".join(words)


def normalize_phone(text: str | None) -> str:
    if not text:
        return ""
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def normalize_zip(text: str | None) -> str:
    if not text:
        return ""
    digits = re.sub(r"\D", "", text)
    return digits[:5]


def split_owner_full(full_name: str) -> tuple[str, str]:
    """Split a combined owner-name column into (first, last).

    Handles "Last, First" (comma present) and "First Last" (last token wins)
    since real exports use both conventions.
    """
    full_name = (full_name or "").strip()
    if not full_name:
        return "", ""
    if "," in full_name:
        last, _, first = full_name.partition(",")
        return first.strip(), last.strip()
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


def build_standard_row(raw_row: dict, mapping: dict[str, str | None]) -> dict:
    """Apply a header->field mapping to one CSV row, producing a dict keyed
    by the standard schema, with names/addresses/phone/zip normalized.
    """
    from src.schema import STANDARD_FIELDS

    row = {field: "" for field in STANDARD_FIELDS}
    owner_full = ""

    for raw_header, value in raw_row.items():
        field = mapping.get(raw_header)
        if field is None:
            continue
        value = (value or "").strip()
        if field == "owner_full":
            owner_full = value
        elif field in row:
            row[field] = value

    if owner_full and not (row["owner_first"] or row["owner_last"]):
        row["owner_first"], row["owner_last"] = split_owner_full(owner_full)

    row["owner_first"] = row["owner_first"].strip().title()
    row["owner_last"] = row["owner_last"].strip().title()
    row["mail_zip"] = normalize_zip(row["mail_zip"])
    row["property_zip"] = normalize_zip(row["property_zip"])
    row["phone"] = normalize_phone(row["phone"])
    row["email"] = row["email"].strip().lower()

    return row
