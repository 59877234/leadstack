from unittest.mock import Mock, patch

from src.license import verify_license


def _gumroad_response(status_code=200, purchase=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"success": True, "purchase": purchase or {}}
    return response


def _payhip_response(status_code=200, data=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"data": data}
    return response


def test_valid_gumroad_key_is_accepted():
    with patch("src.license.requests.post", return_value=_gumroad_response()):
        is_valid, error = verify_license("some-key")
    assert is_valid
    assert error == ""


def test_gumroad_invalid_falls_through_to_payhip_not_configured():
    # No PAYHIP_PRODUCT_SECRET_KEY set in the test environment, so the
    # Payhip check short-circuits without a real network call.
    with patch("src.license.requests.post", return_value=_gumroad_response(status_code=404)):
        is_valid, error = verify_license("wrong-key")
    assert not is_valid
    assert "recognized" in error


def test_refunded_gumroad_purchase_is_rejected():
    with patch(
        "src.license.requests.post",
        return_value=_gumroad_response(purchase={"refunded": True}),
    ):
        is_valid, error = verify_license("refunded-key")
    assert not is_valid
    assert "refunded" in error


def test_disputed_gumroad_purchase_is_rejected():
    with patch(
        "src.license.requests.post",
        return_value=_gumroad_response(purchase={"disputed": True}),
    ):
        is_valid, error = verify_license("disputed-key")
    assert not is_valid
    assert "disputed" in error


def test_empty_key_is_rejected_without_network_call():
    with patch("src.license.requests.post") as mock_post, patch("src.license.requests.get") as mock_get:
        is_valid, error = verify_license("   ")
    assert not is_valid
    mock_post.assert_not_called()
    mock_get.assert_not_called()


def test_valid_payhip_key_is_accepted_when_gumroad_rejects():
    with (
        patch("src.license.requests.post", return_value=_gumroad_response(status_code=404)),
        patch("src.license.requests.get", return_value=_payhip_response(data={"enabled": True})),
        patch.dict("os.environ", {"PAYHIP_PRODUCT_SECRET_KEY": "test-secret"}),
    ):
        is_valid, error = verify_license("payhip-key")
    assert is_valid
    assert error == ""


def test_disabled_payhip_key_is_rejected():
    with (
        patch("src.license.requests.post", return_value=_gumroad_response(status_code=404)),
        patch("src.license.requests.get", return_value=_payhip_response(data={"enabled": False})),
        patch.dict("os.environ", {"PAYHIP_PRODUCT_SECRET_KEY": "test-secret"}),
    ):
        is_valid, error = verify_license("disabled-key")
    assert not is_valid
    assert "refunded" in error
