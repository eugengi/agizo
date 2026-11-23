"""Serializer tests for the `accounts` app.

Define serializers to support data validation and serialization/deserialization
for the `accounts.models`.

For more details about this file
See: https://www.django-rest-framework.org/api-guide/serializers/
"""

from typing import TypedDict

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from accounts.profiles import CustomerProfile
from accounts.serializers import (
    CreateCustomerSerializer,
    CreateUserAndCustomerSerializer,
)

CUSTOMER_ENDPOINT: str = reverse("accounts:create_customer")


User = get_user_model()


class TUser(TypedDict):
    """Type structure for a single user data."""

    user_email: str
    user_password: str


class TCustomer(TypedDict):
    """Type structure for a single customer data."""

    name: str
    phone_number: str


class TUserAndCustomer(TUser, TCustomer):
    """Type union structure for a single user and customer data."""



@pytest.fixture
def user_data() -> TUser:
    """Represents valid client data for a user."""
    return TUser(user_email="johndoe@email.example", user_password="jd-secret-pwd")


@pytest.fixture
def user() -> AbstractBaseUser:
    """Represents a user instance persisted in the DB."""
    return User.objects.create_user(
        email="johndoe@email.example", password="jd-secret-pwd"
    )


@pytest.fixture
def customer_data() -> TCustomer:
    """Represents valid client data for a customer."""
    return TCustomer(name="John Doe", phone_number="+254000000000")


@pytest.fixture
def user_customer_data(user_data: TUser, customer_data: TCustomer) -> TUserAndCustomer:
    """Represents valid client data for a user and customer."""
    return TUserAndCustomer(**user_data, **customer_data)


@pytest.fixture
def request_factory() -> APIRequestFactory:
    """Represents a request instance from DRF's test utilities."""
    factory = APIRequestFactory(format="json")
    return factory


@pytest.fixture
def customer_post_request(
    request_factory: APIRequestFactory,
    user: AbstractBaseUser,
    customer_data: TCustomer,
) -> WSGIRequest:
    """Represents a POST request to an API view to create a customer."""
    request = request_factory.post(path=CUSTOMER_ENDPOINT, data=customer_data)
    request.user = user
    return request


@pytest.mark.django_db
class TestCreateCustomerSerializer:
    """Tests to cover and isolate logic for `CreateCustomerSerializer`.

    @TODO(eugengi): Mock request context.
    The `owner` field on the serializer under test introduces dependencies to
    setup a `User` and request for each test. This required `request` context
    should be mocked for simple validation tests that should be DB independent.
    """

    _under_test: serializers.Serializer = CreateCustomerSerializer

    @pytest.mark.unit
    def test_should_raise_validation_error_on_invalid_customer_data(
        self, customer_post_request: WSGIRequest
    ) -> None:
        # Given
        payload = TCustomer(name="", phone_number="+254000000000")
        serializer = self._under_test(
            data=payload, context={"request": customer_post_request}
        )

        with pytest.raises(serializers.ValidationError, match="blank"):  # Then
            _ = serializer.is_valid(raise_exception=True)  # When

    @pytest.mark.unit
    def test_should_accept_and_serialize_valid_customer_data(
        self,
        customer_data: TCustomer,  # Given
        customer_post_request: WSGIRequest,
    ) -> None:
        # When
        serializer = self._under_test(
            data=customer_data, context={"request": customer_post_request}
        )

        # Then
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.unit
    def test_should_create_customer_related_to_user_email_from_incoming_request(
        self,
        customer_data: TCustomer,
        customer_post_request: WSGIRequest,  # Given
    ) -> None:
        # When
        serializer = self._under_test(
            data=customer_data, context={"request": customer_post_request}
        )

        # Then
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["owner"] == customer_post_request.user


class TestCreateUserAndCustomerSerializer:
    """Tests to cover and isolate logic for `CreateUserAndCustomerSerializer`."""

    _under_test: serializers.Serializer = CreateUserAndCustomerSerializer

    # TODO(eugengi): Use parametrization to target single fields.
    # This design is not flexible, hence why `match` is blank.
    # Handle invalid fields one per test to resolve this.
    def test_should_raise_validation_error_on_invalid_user_data(
        self, customer_data: TCustomer
    ) -> None:

        # Given
        payload = TUserAndCustomer(
            user_email="nonexistent", user_password="tooshort", **customer_data
        )

        with pytest.raises(serializers.ValidationError, match=""):  # Then
            _ = self._under_test(data=payload).is_valid(raise_exception=True)  # When

    @pytest.mark.unit
    def test_should_accept_valid_serializer_user_and_customer_client_data(
        self, user_customer_data: TUserAndCustomer  # Given
    ) -> None:

        # When
        serializer = self._under_test(data=user_customer_data)

        # Then
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_should_persist_valid_user_and_customer_models_in_serializer(
        self, user_customer_data: TUserAndCustomer
    ) -> None:
        # Given
        serializer = self._under_test(data=user_customer_data)
        assert serializer.is_valid(), serializer.errors

        # When
        customer = serializer.save()

        # Then
        assert isinstance(customer, CustomerProfile)
        assert User.objects.filter(email=user_customer_data["user_email"]).exists()
        assert CustomerProfile.objects.filter(
            phone_number=user_customer_data["phone_number"]
        ).exists()
