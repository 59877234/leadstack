import json
import os

from src.schema import STANDARD_FIELDS

# Real header strings verified against actual provider export formats/code
# (see CLAUDE.md for sourcing/confidence per provider). Checking these first
# means known providers never need an LLM call — faster, free, and exact.
KNOWN_HEADERS = {
    # PropStream marketing list
    "owner 1 first name": "owner_first",
    "owner 1 last name": "owner_last",
    "mailing address": "mail_address",
    "mailing city": "mail_city",
    "mailing state": "mail_state",
    "mailing zip": "mail_zip",
    # PropStream skip-traced contacts list
    "first name": "owner_first",
    "last name": "owner_last",
    "mail street address": "mail_address",
    "mail city": "mail_city",
    "mail state": "mail_state",
    "mail zip": "mail_zip",
    "street address": "property_address",
    "city": "property_city",
    "state": "property_state",
    "zip": "property_zip",
    "cell": "phone",
    "email 1": "email",
    # ListSource (2010 data card — lower confidence, kept as a fallback)
    "owner 1 name": "owner_full",
    "property address": "property_address",
    "complete phone": "phone",
    # Generic synonyms not tied to a specific verified provider — plain
    # English fallbacks, not a guessed provider-specific format.
    "address": "property_address",
    "property city": "property_city",
    "property state": "property_state",
    "property zip": "property_zip",
}

# Targets the LLM is allowed to map a header to, beyond STANDARD_FIELDS.
# "owner_full" covers providers (like ListSource) that give one combined
# name field instead of separate first/last columns.
MAPPING_TARGETS = STANDARD_FIELDS + ["owner_full"]


def map_headers(raw_headers: list[str]) -> dict[str, str | None]:
    """Map raw CSV headers to the standard schema.

    Returns {raw_header: standard_field_or_None}. Known headers are matched
    exactly (case-insensitive); anything left over is resolved with one LLM
    call so unfamiliar provider formats still work.
    """
    mapping: dict[str, str | None] = {}
    unresolved = []

    for header in raw_headers:
        key = header.strip().lower()
        if key in KNOWN_HEADERS:
            mapping[header] = KNOWN_HEADERS[key]
        else:
            unresolved.append(header)

    if unresolved:
        mapping.update(_map_with_llm(unresolved))

    return mapping


GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-lite-latest:generateContent"
)


def _map_with_llm(headers: list[str]) -> dict[str, str | None]:
    import requests

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set — needed to map unrecognized CSV headers"
        )

    prompt = f"""You are mapping CSV column headers from a real-estate lead
list export to a fixed standard schema.

Standard schema fields: {MAPPING_TARGETS}
- "owner_full" is only for a single combined owner-name column.
- Use null for a header that doesn't correspond to any of these fields
  (e.g. property characteristics, mortgage details, dates).

Headers to map: {json.dumps(headers)}

Respond with ONLY a JSON object mapping each input header to one of the
schema fields above or null. No other text."""

    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    result = json.loads(text)

    for header, field in result.items():
        if field is not None and field not in MAPPING_TARGETS:
            raise ValueError(f"LLM returned invalid field {field!r} for header {header!r}")

    return result
