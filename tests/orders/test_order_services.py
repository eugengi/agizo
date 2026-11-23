"""Service tests for the `orders` app."""

import pytest

from orders.services import OrdersSMSService


class IncompatibleClient:
    """Stub to represent an unexpected client for the Order SMS service."""



@pytest.mark.unit
def test_should_raise_validation_error_for_unexpected_order_sms_client_type() -> None:
    # Given
    client = IncompatibleClient()

    with pytest.raises(TypeError, match="africastalking.SMS"):  # Then
        _ = OrdersSMSService(client=client)  # When
