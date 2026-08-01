import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Local dev reads GEMINI_API_KEY from .env (via load_dotenv above). Streamlit
# Community Cloud has no .env file — secrets are set in its dashboard and
# exposed via st.secrets instead, so bridge that into the same env var the
# rest of the code already reads. st.secrets raises rather than returning
# empty when no secrets.toml exists at all (e.g. local dev), hence the guard.
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    pass

from src.dedup import stack_uploaded_files

st.set_page_config(page_title="LeadStack", page_icon="🏚️")
st.title("LeadStack")
st.write(
    "Upload two or more lead-list CSV exports (PropStream, ListSource, "
    "BatchLeads, or similar). LeadStack merges them, removes duplicates, "
    "and ranks leads by how many lists they appeared on — the ones on "
    "multiple lists are your hottest prospects."
)

uploaded_files = st.file_uploader(
    "Upload CSV files", type="csv", accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("Upload at least 2 files to see the stacking effect.")
    elif st.button("Stack lists", type="primary"):
        with st.spinner("Processing..."):
            try:
                df = stack_uploaded_files(uploaded_files)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
            else:
                st.success(f"Stacked {len(uploaded_files)} lists into {len(df)} unique leads.")
                st.dataframe(df, width="stretch")
                st.download_button(
                    "Download clean CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="stacked_leads.csv",
                    mime="text/csv",
                )
