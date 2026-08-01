from unittest.mock import Mock, patch

from src.license import verify_license


def _mock_response(status_code=200, purchase=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"success": True, "purchase": purchase or {}}
    return response


def test_valid_key_is_accepted():
    with patch("src.license.requests.post", return_value=_mock_response()):
        is_valid, error = verify_license("some-key")
    assert is_valid
    assert error == ""


def test_invalid_key_is_rejected():
    with patch("src.license.requests.post", return_value=_mock_response(status_code=404)):
        is_valid, error = verify_license("wrong-key")
    assert not is_valid
    assert "recognized" in error


def test_refunded_purchase_is_rejected():
    with patch(
        "src.license.requests.post",
        return_value=_mock_response(purchase={"refunded": True}),
    ):
        is_valid, error = verify_license("refunded-key")
    assert not is_valid
    assert "refunded" in error


def test_disputed_purchase_is_rejected():
    with patch(
        "src.license.requests.post",
        return_value=_mock_response(purchase={"disputed": True}),
    ):
        is_valid, error = verify_license("disputed-key")
    assert not is_valid
    assert "disputed" in error


def test_empty_key_is_rejected_without_network_call():
    with patch("src.license.requests.post") as mock_post:
        is_valid, error = verify_license("   ")
    assert not is_valid
    mock_post.assert_not_called()
