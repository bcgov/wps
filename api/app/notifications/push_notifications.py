"""
iOS Push Notification Service using Apple Push Notification Service (APNs)

This module provides functionality to send push notifications to iOS devices
through Apple's Push Notification Service (APNs) using the HTTP/2 provider API.
"""

import json
import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path
import aiohttp
import asyncio
from dataclasses import dataclass
from enum import Enum

from wps_shared.config import config

logger = logging.getLogger(__name__)


class APNsPriority(Enum):
    """APNs notification priority levels"""

    IMMEDIATE = 10  # Send immediately. For notifications that trigger an alert, sound, or badge.
    CONSERVE_POWER = 5  # Send at a time that conserves power on the device


class APNsEnvironment(Enum):
    """APNs environment types"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


@dataclass
class APNsPayload:
    """APNs notification payload structure"""

    alert: Optional[Dict[str, Any]] = None
    badge: Optional[int] = None
    sound: Optional[str] = None
    category: Optional[str] = None
    thread_id: Optional[str] = None
    content_available: Optional[int] = None
    mutable_content: Optional[int] = None
    custom_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary for JSON serialization"""
        payload = {"aps": {}}

        if self.alert:
            payload["aps"]["alert"] = self.alert
        if self.badge is not None:
            payload["aps"]["badge"] = self.badge
        if self.sound:
            payload["aps"]["sound"] = self.sound
        if self.category:
            payload["aps"]["category"] = self.category
        if self.thread_id:
            payload["aps"]["thread-id"] = self.thread_id
        if self.content_available:
            payload["aps"]["content-available"] = self.content_available
        if self.mutable_content:
            payload["aps"]["mutable-content"] = self.mutable_content

        if self.custom_data:
            payload.update(self.custom_data)

        return payload


@dataclass
class APNsNotification:
    """Represents a complete APNs notification"""

    device_token: str
    payload: APNsPayload
    topic: str  # Your app's bundle ID
    priority: APNsPriority = APNsPriority.IMMEDIATE
    expiration: Optional[int] = None
    collapse_id: Optional[str] = None
    apns_id: Optional[str] = None


class APNsClient:
    """
    Apple Push Notification Service (APNs) HTTP/2 client

    This client uses JWT authentication with your Apple Developer key.
    """

    def __init__(
        self,
        key_id: str,
        team_id: str,
        auth_key_path: str,
        environment: APNsEnvironment = APNsEnvironment.PRODUCTION,
        default_topic: Optional[str] = None,
    ):
        self.key_id = key_id
        self.team_id = team_id
        self.auth_key_path = Path(auth_key_path)
        self.environment = environment
        self.default_topic = default_topic

        # APNs endpoints
        if environment == APNsEnvironment.PRODUCTION:
            self.apns_host = "https://api.push.apple.com"
        else:
            self.apns_host = "https://api.sandbox.push.apple.com"

        self._auth_token: Optional[str] = None
        self._token_issued_at: Optional[datetime] = None

    async def send_notification(self, notification: APNsNotification) -> Dict[str, Any]:
        """
        Send a single push notification to APNs

        Returns:
            Dict containing response information including success status
        """
        try:
            headers = await self._get_headers(notification)
            payload = json.dumps(notification.payload.to_dict())

            url = f"{self.apns_host}/3/device/{notification.device_token}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, data=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = {
                        "status_code": response.status,
                        "apns_id": response.headers.get("apns-id"),
                        "device_token": notification.device_token,
                        "success": response.status == 200,
                    }

                    if response.status != 200:
                        try:
                            error_body = await response.json()
                            response_data["error"] = error_body
                            logger.warning(
                                f"APNs error for device {notification.device_token}: "
                                f"{response.status} - {error_body}"
                            )
                        except Exception:
                            response_data["error"] = await response.text()
                    else:
                        logger.info(
                            f"Successfully sent notification to device {notification.device_token}"
                        )

                    return response_data

        except Exception as e:
            logger.error(f"Failed to send notification to {notification.device_token}: {e}")
            return {
                "status_code": 0,
                "device_token": notification.device_token,
                "success": False,
                "error": str(e),
            }

    async def send_notifications(
        self, notifications: List[APNsNotification]
    ) -> List[Dict[str, Any]]:
        """
        Send multiple push notifications concurrently

        Returns:
            List of response dictionaries for each notification
        """
        tasks = [self.send_notification(notification) for notification in notifications]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert any exceptions to error dictionaries
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "status_code": 0,
                        "device_token": notifications[i].device_token,
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _get_headers(self, notification: APNsNotification) -> Dict[str, str]:
        """Generate headers for APNs request"""
        token = await self._get_auth_token()

        headers = {
            "authorization": f"bearer {token}",
            "apns-topic": notification.topic or self.default_topic,
            "apns-priority": str(notification.priority.value),
            "content-type": "application/json",
        }

        if notification.expiration:
            headers["apns-expiration"] = str(notification.expiration)
        if notification.collapse_id:
            headers["apns-collapse-id"] = notification.collapse_id
        if notification.apns_id:
            headers["apns-id"] = notification.apns_id

        return headers

    async def _get_auth_token(self) -> str:
        """Generate or return cached JWT token for APNs authentication"""
        now = datetime.now(timezone.utc)

        # Reuse token if it's still valid (tokens are valid for 1 hour, we refresh every 50 minutes)
        if (
            self._auth_token
            and self._token_issued_at
            and (now - self._token_issued_at).total_seconds() < 3000
        ):
            return self._auth_token

        # Read the private key
        with open(self.auth_key_path, "r") as f:
            private_key = f.read()

        # JWT payload
        issued_at = int(now.timestamp())
        payload = {"iss": self.team_id, "iat": issued_at}

        # JWT header
        headers = {"kid": self.key_id}

        # Generate JWT token
        self._auth_token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
        self._token_issued_at = now

        logger.debug("Generated new APNs JWT token")
        return self._auth_token


class PushNotificationService:
    """
    High-level push notification service for WPS application

    This service provides convenient methods for sending different types
    of notifications to users.
    """

    def __init__(self):
        # Load configuration from environment
        self.apns_client = APNsClient(
            key_id=config.get("APNS_KEY_ID"),
            team_id=config.get("APNS_TEAM_ID"),
            auth_key_path=config.get("APNS_AUTH_KEY_PATH"),
            environment=APNsEnvironment(config.get("APNS_ENVIRONMENT", "production")),
            default_topic=config.get("APNS_DEFAULT_TOPIC"),
        )

    async def send_weather_alert(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        weather_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send weather alert notification to specified devices

        Args:
            device_tokens: List of iOS device tokens
            title: Alert title
            body: Alert message body
            weather_data: Optional weather data to include

        Returns:
            List of response dictionaries
        """
        payload = APNsPayload(
            alert={"title": title, "body": body},
            sound="default",
            badge=1,
            category="WEATHER_ALERT",
            custom_data={"type": "weather_alert", "weather_data": weather_data or {}},
        )

        notifications = [
            APNsNotification(
                device_token=token,
                payload=payload,
                topic=self.apns_client.default_topic,
                priority=APNsPriority.IMMEDIATE,
            )
            for token in device_tokens
        ]

        return await self.apns_client.send_notifications(notifications)

    async def send_fire_alert(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        fire_data: Optional[Dict[str, Any]] = None,
        high_priority: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Send fire alert notification to specified devices

        Args:
            device_tokens: List of iOS device tokens
            title: Alert title
            body: Alert message body
            fire_data: Optional fire-related data
            high_priority: Whether to send with high priority

        Returns:
            List of response dictionaries
        """
        payload = APNsPayload(
            alert={"title": title, "body": body},
            sound="emergency_alert.caf",  # Custom emergency sound
            badge=1,
            category="FIRE_ALERT",
            custom_data={
                "type": "fire_alert",
                "fire_data": fire_data or {},
                "priority": "high" if high_priority else "normal",
            },
        )

        notifications = [
            APNsNotification(
                device_token=token,
                payload=payload,
                topic=self.apns_client.default_topic,
                priority=APNsPriority.IMMEDIATE if high_priority else APNsPriority.CONSERVE_POWER,
            )
            for token in device_tokens
        ]

        return await self.apns_client.send_notifications(notifications)

    async def send_general_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        custom_data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None,
        sound: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Send general notification to specified devices

        Args:
            device_tokens: List of iOS device tokens
            title: Notification title
            body: Notification body
            custom_data: Optional custom data
            badge: Optional badge count
            sound: Notification sound

        Returns:
            List of response dictionaries
        """
        payload = APNsPayload(
            alert={"title": title, "body": body},
            sound=sound,
            badge=badge,
            category="GENERAL",
            custom_data={"type": "general", **(custom_data or {})},
        )

        notifications = [
            APNsNotification(
                device_token=token, payload=payload, topic=self.apns_client.default_topic
            )
            for token in device_tokens
        ]

        return await self.apns_client.send_notifications(notifications)

    async def send_silent_notification(
        self, device_tokens: List[str], custom_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Send silent background notification (for app refresh, data updates, etc.)

        Args:
            device_tokens: List of iOS device tokens
            custom_data: Data to send to the app

        Returns:
            List of response dictionaries
        """
        payload = APNsPayload(
            content_available=1,  # This makes it a silent notification
            custom_data={"type": "background_update", **custom_data},
        )

        notifications = [
            APNsNotification(
                device_token=token,
                payload=payload,
                topic=self.apns_client.default_topic,
                priority=APNsPriority.CONSERVE_POWER,
            )
            for token in device_tokens
        ]

        return await self.apns_client.send_notifications(notifications)


# Global service instance
_notification_service: Optional[PushNotificationService] = None


def get_notification_service() -> PushNotificationService:
    """Get or create the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = PushNotificationService()
    return _notification_service


# Convenience functions
async def send_weather_alert(
    device_tokens: List[str], title: str, body: str, weather_data: Optional[Dict[str, Any]] = None
):
    """Convenience function to send weather alert"""
    service = get_notification_service()
    return await service.send_weather_alert(device_tokens, title, body, weather_data)


async def send_fire_alert(
    device_tokens: List[str],
    title: str,
    body: str,
    fire_data: Optional[Dict[str, Any]] = None,
    high_priority: bool = True,
):
    """Convenience function to send fire alert"""
    service = get_notification_service()
    return await service.send_fire_alert(device_tokens, title, body, fire_data, high_priority)


async def send_general_notification(
    device_tokens: List[str], title: str, body: str, custom_data: Optional[Dict[str, Any]] = None
):
    """Convenience function to send general notification"""
    service = get_notification_service()
    return await service.send_general_notification(device_tokens, title, body, custom_data)
