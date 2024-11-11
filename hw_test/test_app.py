import json
from enum import Enum

import pytest
from django.core.serializers import serialize
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers.user_serializers import UserListSerializer, RegisterUserSerializer, UserPositionsEncoder
from apps.users.choices.positions import UserPositions


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_list(db):
    return [
        User.objects.create(username='user1', email='user1@example.com'),
        User.objects.create(username='user2', email='user2@example.com')
    ]


def authenticate_admin(api_client):
    user = User.objects.create_user(username='admin2', email='admin2@admin.com', password='adminadmin')
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')


@pytest.mark.django_db
def test_get_all_users(api_client):
    # Create and authenticate the client
    authenticate_admin(api_client)
    url = reverse('user-list')
    response = api_client.get(url, format='json')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_users_by_project_name(api_client, user_list):
    authenticate_admin(api_client)
    url = reverse('user-list') + '?project_name=TestProject'
    response = api_client.get(url, format='json')
    assert response.status_code == (status.HTTP_204_NO_CONTENT or status.HTTP_200_OK)


@pytest.mark.django_db
def test_get_empty_user_list(api_client, mocker):
    authenticate_admin(api_client)
    url = reverse('user-list')
    mocker.patch('apps.users.models.User.objects.all', return_value=User.objects.none())
    response = api_client.get(url, format='json')
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.data == []


@pytest.mark.django_db
def test_user_list_serializer(user_list):
    serializer = UserListSerializer(user_list, many=True)
    data = serializer.data
    assert len(data) == 2
    assert data[0]['username'] == 'user1'
    assert data[1]['username'] == 'user2'


@pytest.mark.django_db
def test_create_user(api_client):
    # Create and authenticate the client
    authenticate_admin(api_client)
    url = reverse('user-register')
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword123',
        're_password': 'newpassword123',
        'last_name': 'New',
        'first_name': 'New',
        'position': UserPositions.PROGRAMMER.value,
    }

    # Post data directly
    response = api_client.post(url, data, format='json')

    # Check response status and user creation
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_create_user_with_invalid_data(api_client):
    authenticate_admin(api_client)
    url = reverse('user-register')
    data = {
        'username': 'newuser',
        'email': 'invalid-email',
        'password': 'short',
        're_password': 'short',
        'last_name': 'New',
        'first_name': 'New',
        'position': UserPositions.PROGRAMMER.value,
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_user_with_skip_data(api_client):
    # Create and authenticate the client with skip req data
    authenticate_admin(api_client)
    url = reverse('user-register')
    data = {
        'username': '',
        'email': 'newuser@example.com',
        'password': 'newpassword123',
        're_password': 'newpassword123',
        'last_name': 'New',
        'first_name': 'New',
        'position': UserPositions.PROGRAMMER.value,
    }

    # Post data directly
    response = api_client.post(url, data, format='json')

    # Check response status and user creation
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_register_user_serializer():
    # Define test data for creating a new user
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword123',
        're_password': 'newpassword123',
        'last_name': 'New',
        'first_name': 'New',
        'position': UserPositions.PROGRAMMER.value,  # Ensure this is a plain string value
    }

    # Initialize the serializer with data
    serializer = RegisterUserSerializer(data=data)

    # Validate the serializer
    assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"

    # Save the user instance if needed for further checks
    user = serializer.save()

    # Assert that the user was created with the expected data
    assert user.username == 'newuser'
    assert user.email == 'newuser@example.com'
    assert user.position == UserPositions.PROGRAMMER.value  # Enum should be stored correctly
