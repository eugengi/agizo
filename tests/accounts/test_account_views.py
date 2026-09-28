"""View tests for the `accounts` app.

Prefer to mark all REST API endpoint tests as `integration` tests.
Whenever possible, prefer to use DRF over standard Django test tools.

Note:
    - Given no mechanism to pass valid OAuth2 tokens from an OIDC auth flow as
    credentials to the API test client, we simply force authenticate.

For more details about testing views
See (Django): https://docs.djangoproject.com/en/4.2/topics/testing/tools/#the-test-client
See (DRF): https://www.django-rest-framework.org/api-guide/testing/
"""

import re
from collections.abc import Generator
from typing import TypeAlias, TypedDict, TypeVar

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

# Leverage global variable to apply custom marker at the module level
# for all tests. Add markers by assigning values of type: list.
# For example: [pytest.mark.smoke, pytest.mark.unit, ...]
pytestmark = [pytest.mark.integration, pytest.mark.django_db]

CUSTOMER_ENDPOINT: str = reverse("accounts:create_customer")

# typing.
T = TypeVar("T")
TGenerator: TypeAlias = Generator[T, None, None]

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
def customer_data() -> TCustomer:
    """Represents valid client data for a customer."""
    return TCustomer(name="John Doe", phone_number="+254000000000")


@pytest.fixture
def user_customer_data(user_data: TUser, customer_data: TCustomer) -> TUserAndCustomer:
    """Represents valid client data for a user and customer."""
    return TUserAndCustomer(**user_data, **customer_data)


@pytest.fixture
def client() -> APIClient:
    """Represents an API client from DRF's test utilities."""
    client = APIClient()
    client.headers = {
        "Content-Type": "application/json",
    }
    client.raise_request_exception = True
    return client


@pytest.fixture
def user(user_data: TUser) -> TGenerator[AbstractBaseUser]:
    """Represents a user instance persisted in the DB."""
    user = User.objects.create_user(
        email=user_data["user_email"], password=user_data["user_password"]
    )
    yield user
    user.delete()


@pytest.fixture
def auth_client(client: APIClient, user: AbstractBaseUser) -> TGenerator[APIClient]:
    """Represents an authenticated API client from DRF's test utilities."""
    client.force_authenticate(user=user)
    yield client
    client.force_authenticate(user=None)


def test_should_render_index_template_on_request_to_accounts_home_view(
    client: APIClient,  # Given
) -> None:
    # When
    response = client.get(path=reverse("home"))
    expected = "accounts/index.html"

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert any(template.name == expected for template in response.templates)
    assert re.search(r"login", response.content.decode("utf-8"), re.IGNORECASE)


class TestCreateCustomerAPIView:
    """Tests to cover behavior for API view, `create_customer`."""

    def test_should_return_401_for_unauthenticated_client_requests(
        self,
        client: APIClient,
        customer_data: TCustomer,  # Given
    ) -> None:
        # When
        response = client.post(path=CUSTOMER_ENDPOINT, data=customer_data)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not_authenticated" in response.data["detail"].code

    def test_should_return_400_for_invalid_customer_request_data(
        self,
        auth_client: APIClient,
    ) -> None:
        # Given
        payload = TCustomer(name="", phone_number="123")

        # When
        response = auth_client.post(path=CUSTOMER_ENDPOINT, data=payload)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["name"], response.data["phone_number"]
        assert all(isinstance(v[0], ErrorDetail) for v in response.data.values())

    def test_should_return_201_from_user_request_with_valid_customer_data(
        self,
        user: AbstractBaseUser,
        auth_client: APIClient,
        customer_data: TCustomer,  # Given
    ) -> None:
        # When
        response = auth_client.post(path=CUSTOMER_ENDPOINT, data=customer_data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"
        assert response.data["customer"]["email"] == user.email


@pytest.mark.skip("not implemented - add API view `create_user_and_customer`")
class TestCreateUserAndCustomerAPIView:
    """Tests to cover behavior for API view, `create_user_and_customer`."""

    def test_should_return_400_for_invalid_user_request_data(
        self,
        auth_client: APIClient,
        customer_data: TCustomer,
    ) -> None:
        # Given
        invalid_user_data = TUser(user_email="nonexistent", user_password="tooshort")
        payload = TUserAndCustomer(**invalid_user_data, **customer_data)

        # When
        response = auth_client.post(path=CUSTOMER_ENDPOINT, data=payload)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["user_email"], response.data["user_password"]
        assert all(isinstance(v[0], ErrorDetail) for v in response.data.values())

    @pytest.mark.xfail(reason="bug - test passes when using the wrong serializer")
    def test_should_return_201_on_created_user_and_customer_profile(
        self,
        user: AbstractBaseUser,
        auth_client: APIClient,
        user_customer_data: TUserAndCustomer,  # Given
    ) -> None:
        # When
        response = auth_client.post(path=CUSTOMER_ENDPOINT, data=user_customer_data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"
        assert response.data["customer"]["email"] == user.email
