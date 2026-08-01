import os

import requests

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"

# Real product_id from the LeadStack Gumroad listing's license key block
# (product content page -> Insert -> License key). Not a secret — Gumroad's
# docs have this embedded directly in client apps.
GUMROAD_PRODUCT_ID = "fN76g8r8evNMckCt9kBXcA=="

PAYHIP_VERIFY_URL = "https://payhip.com/api/v2/license/verify"

# Payhip's product secret key is NOT embedded here like Gumroad's product_id
# is — Payhip's own docs warn it must not be exposed in a publicly
# accessible/decompilable app. This repo is public, so it's read from an
# environment variable (set as a Streamlit Cloud secret) instead.
PAYHIP_SECRET_KEY_ENV_VAR = "PAYHIP_PRODUCT_SECRET_KEY"


def _verify_gumroad(license_key: str) -> tuple[bool, str]:
    try:
        response = requests.post(
            GUMROAD_VERIFY_URL,
            data={
                "product_id": GUMROAD_PRODUCT_ID,
                "license_key": license_key,
                "increment_uses_count": "false",
            },
            timeout=15,
        )
    except requests.RequestException:
        return False, "network"

    if response.status_code != 200:
        return False, "not_found"

    purchase = response.json().get("purchase", {})
    if purchase.get("refunded") or purchase.get("disputed"):
        return False, "refunded"

    return True, ""


def _verify_payhip(license_key: str) -> tuple[bool, str]:
    secret_key = os.environ.get(PAYHIP_SECRET_KEY_ENV_VAR)
    if not secret_key:
        return False, "not_found"

    try:
        response = requests.get(
            PAYHIP_VERIFY_URL,
            params={"license_key": license_key},
            headers={"product-secret-key": secret_key},
            timeout=15,
        )
    except requests.RequestException:
        return False, "network"

    if response.status_code != 200:
        return False, "not_found"

    data = response.json().get("data")
    if not data or not data.get("enabled"):
        return False, "refunded"

    return True, ""


def verify_license(license_key: str) -> tuple[bool, str]:
    """Check a license key against Gumroad first, then Payhip, so buyers
    from either platform can use the same field. Refunded/disputed
    purchases are treated as invalid even though both platforms' APIs
    still report them as a valid lookup — enforcement is left entirely to
    the caller per their docs.
    """
    license_key = license_key.strip()
    if not license_key:
        return False, "Enter your license key."

    saw_refunded = False
    for verify in (_verify_gumroad, _verify_payhip):
        is_valid, reason = verify(license_key)
        if is_valid:
            return True, ""
        if reason == "refunded":
            saw_refunded = True

    if saw_refunded:
        return False, "This purchase has been refunded or disputed, so the license is no longer active."
    return False, "That license key wasn't recognized. Double-check it and try again."
