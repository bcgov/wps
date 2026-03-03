""" Unit tests for FCM endpoints.
"""
from starlette.testclient import TestClient
import app.main
from unittest.mock import patch
from datetime import datetime


def test_register_device_success():
    """Test that device registration returns 200/OK."""
    client = TestClient(app.main.app)
    
    # Test data
    request_data = {
        "user_id": "test-user-123",
        "token": "test-fcm-token-456",
        "platform": "android"
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch('app.routers.fcm.get_device_by_token', return_value=None), \
             patch('app.routers.fcm.save_device_token'):
            
            response = client.post("/api/device/register", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.headers["content-type"] == "application/json"


def test_register_device_already_exists():
    """Test that existing device registration updates successfully."""
    client = TestClient(app.main.app)
    
    request_data = {
        "user_id": "test-user-123",
        "token": "existing-fcm-token",
        "platform": "ios"
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        
        existing_device = type('', (object,), {
            'is_active': False,
            'token': 'existing-fcm-token',
            'updated_at': datetime(2026, 1, 1)
        })()
        
        with patch('app.routers.fcm.get_device_by_token', return_value=existing_device), \
             patch('app.routers.fcm.save_device_token'):
            
            response = client.post("/api/device/register", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert existing_device.is_active == True  # Should be updated


def test_register_device_missing_fields():
    """Test that missing fields in registration request returns 422."""
    client = TestClient(app.main.app)
    
    # Missing 'token' field which is required
    request_data = {
        "user_id": "test-user-123",
        "platform": "android"
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        
        response = client.post("/api/device/register", json=request_data)
        
        assert response.status_code == 422


def test_register_device_invalid_platform():
    """Test that invalid platform returns 422."""
    client = TestClient(app.main.app)
    
    request_data = {
        "user_id": "test-user-123",
        "token": "test-fcm-token",
        "platform": "invalid-platform",
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        
        response = client.post("/api/device/register", json=request_data)
        
        assert response.status_code == 422


def test_register_device_short_token():
    """Test that short token returns 422."""
    client = TestClient(app.main.app)
    
    request_data = {
        "user_id": "test-user-123",
        "token": "short",  # Less than 10 characters
        "platform": "android",
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        
        response = client.post("/api/device/register", json=request_data)
        
        assert response.status_code == 422


def test_unregister_device_success():
    """Test that device unregistration returns 200/OK."""
    client = TestClient(app.main.app)
    
    request_data = {
        "token": "test-fcm-token-456"
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch('app.routers.fcm.update_device_token_is_active'):
            
            response = client.request("DELETE", "/api/device/unregister", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["success"] == True


def test_unregister_device_missing_token():
    """Test that missing token field returns 422."""
    client = TestClient(app.main.app)
    
    request_data = {}
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        
        response = client.request("DELETE", "/api/device/unregister", json=request_data)
        
        assert response.status_code == 422


def test_register_device_without_user_id():
    """Test that device registration without user_id is allowed (null user)."""
    client = TestClient(app.main.app)
    
    request_data = {
        "token": "test-fcm-token-789",
        "platform": "android",
    }
    
    with patch('app.routers.fcm.get_async_write_session_scope') as mock_session_scope:
        mock_session = mock_session_scope.return_value.__aenter__.return_value
        with patch('app.routers.fcm.get_device_by_token', return_value=None), \
             patch('app.routers.fcm.save_device_token'):
            
            response = client.post("/api/device/register", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["success"] == True
