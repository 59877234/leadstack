from pathlib import Path

from src.dedup import stack_lists

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"


def test_stacks_and_dedupes_across_providers():
    df = stack_lists(
        [
            str(SAMPLE_DIR / "propstream_marketing.csv"),
            str(SAMPLE_DIR / "propstream_skiptraced.csv"),
        ]
    )

    assert len(df) == 3

    top = df.iloc[0]
    assert top["owner_last"] == "Smith"
    assert top["list_count"] == 2
    assert "propstream_marketing" in top["source_lists"]
    assert "propstream_skiptraced" in top["source_lists"]
    # phone/email only existed in the skip-traced file — confirm the merge
    # pulled them onto the combined record rather than dropping them.
    assert top["phone"] == "2175551234"
    assert top["email"] == "john.smith@example.com"

    assert set(df["owner_last"]) == {"Smith", "Johnson", "Garcia"}
    assert list(df["list_count"]) == [2, 1, 1]
