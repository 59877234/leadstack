import requests

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"

# Real product_id from the LeadStack Gumroad listing's license key block
# (product content page -> Insert -> License key). Not a secret — Gumroad's
# docs have this embedded directly in client apps.
GUMROAD_PRODUCT_ID = "fN76g8r8evNMckCt9kBXcA=="


def verify_license(license_key: str, product_id: str = GUMROAD_PRODUCT_ID) -> tuple[bool, str]:
    """Check a license key against Gumroad's own verification API.

    Returns (is_valid, error_message). error_message is empty when valid.
    Refunded/disputed purchases are treated as invalid even though Gumroad's
    API itself still reports them as a successful verification — enforcement
    is left entirely to the caller per Gumroad's docs.
    """
    license_key = license_key.strip()
    if not license_key:
        return False, "Enter your license key."

    try:
        response = requests.post(
            GUMROAD_VERIFY_URL,
            data={
                "product_id": product_id,
                "license_key": license_key,
                "increment_uses_count": "false",
            },
            timeout=15,
        )
    except requests.RequestException:
        return False, "Couldn't reach the license server. Please try again."

    if response.status_code != 200:
        return False, "That license key wasn't recognized. Double-check it and try again."

    purchase = response.json().get("purchase", {})
    if purchase.get("refunded") or purchase.get("disputed"):
        return False, "This purchase has been refunded or disputed, so the license is no longer active."

    return True, ""
