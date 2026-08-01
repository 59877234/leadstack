from pathlib import Path

import pandas as pd

from src.column_mapper import map_headers
from src.normalizer import build_standard_row, normalize_address


def load_and_standardize(csv_file, source_name: str) -> list[dict]:
    """csv_file can be a path or any file-like object pandas.read_csv
    accepts (e.g. a Streamlit UploadedFile) — the source name is passed in
    explicitly so callers aren't forced to have a real filesystem path.
    """
    df = pd.read_csv(csv_file, dtype=str).fillna("")
    mapping = map_headers(list(df.columns))

    rows = []
    for _, raw_row in df.iterrows():
        row = build_standard_row(raw_row.to_dict(), mapping)
        row["_source"] = source_name
        rows.append(row)
    return rows


def dedup_key(row: dict) -> str:
    """Two rows are the same lead if they resolve to the same property
    (preferred) or, failing that, the same owner name. Property address is
    the stronger signal since list stacking is fundamentally about finding
    properties that show up on multiple lists.
    """
    addr = row["property_address"] or row["mail_address"]
    key_addr = normalize_address(addr)
    if key_addr:
        zip_code = row["property_zip"] or row["mail_zip"]
        return f"addr::{key_addr}::{zip_code}"
    return f"name::{row['owner_first'].lower()}::{row['owner_last'].lower()}"


def merge_group(rows: list[dict]) -> dict:
    merged = {}
    for field in rows[0]:
        if field == "_source":
            continue
        values = [r[field] for r in rows if r[field]]
        merged[field] = values[0] if values else ""
    sources = sorted({r["_source"] for r in rows})
    merged["source_lists"] = ", ".join(sources)
    merged["list_count"] = len(sources)
    return merged


def _stack(named_files: list[tuple[str, object]]) -> pd.DataFrame:
    all_rows = []
    for source_name, file_obj in named_files:
        all_rows.extend(load_and_standardize(file_obj, source_name))

    if not all_rows:
        raise ValueError("No rows found across the provided CSV files")

    groups: dict[str, list[dict]] = {}
    for row in all_rows:
        groups.setdefault(dedup_key(row), []).append(row)

    merged_rows = [merge_group(group) for group in groups.values()]
    df = pd.DataFrame(merged_rows)
    return df.sort_values("list_count", ascending=False).reset_index(drop=True)


def stack_lists(csv_paths: list[str]) -> pd.DataFrame:
    """Entry point for filesystem paths (CLI usage)."""
    return _stack([(Path(p).stem, p) for p in csv_paths])


def stack_uploaded_files(uploaded_files: list) -> pd.DataFrame:
    """Entry point for file-like uploads (Streamlit UI usage) — each object
    is expected to have a `.name` attribute, as Streamlit's UploadedFile does.
    """
    return _stack([(Path(f.name).stem, f) for f in uploaded_files])
