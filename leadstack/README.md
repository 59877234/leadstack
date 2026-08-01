# LeadStack

Merge and deduplicate real-estate lead lists from multiple providers
(PropStream, ListSource, BatchLeads, or similar) into one clean CSV,
ranked by how many source lists each lead appeared on.

Live app: https://leadstack.streamlit.app

## Running locally

```
pip install -r requirements.txt
streamlit run app.py
```

Requires a `GEMINI_API_KEY` environment variable (used to map unfamiliar
CSV column headers to the standard schema).

## Tests

```
pytest tests/
```
