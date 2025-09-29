import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import API_URL
from .types.DeviceState import DeviceState
from .types.SystemInfo import SystemInfo

TIMEOUT = 10
_LOGGER: logging.Logger = logging.getLogger(__package__)
HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class CompitAPI:
    def __init__(self, email, password, session: aiohttp.ClientSession):
        self.email = email
        self.password = password
        self.token = None
        self._api_wrapper = ApiWrapper(session)

    async def authenticate(self):
        """
        Handles user authentication asynchronously by interacting with an API endpoint.

        Raises:
            Exception: Captures and logs any exception encountered during the
            authentication process.

        Returns:
            SystemInfo | bool: Returns a SystemInfo object created from the successful
            response data, or False in case of an error or failure during the
            authentication process.
        """
        try:
            response = await self._api_wrapper.post(
                f"{API_URL}/authorize",
                {
                    "email": self.email,
                    "password": self.password,
                    "uid": "HomeAssistant",
                    "label": "HomeAssistant",
                },
            )

            if response.status == 422:
                result = await self.get_result(response, ignore_response_code=True)
                self.token = result["token"]
                response = await self._api_wrapper.post(
                    f"{API_URL}/clients",
                    {
                        "fcm_token": None,
                        "uid": "HomeAssistant",
                        "label": "HomeAssistant",
                    },
                    auth=self.token,
                )

                result = await self.get_result(response)
                return self.authenticate()

            result = await self.get_result(response)
            self.token = result["token"]
            return SystemInfo.from_json(result)
        except Exception as e:
            _LOGGER.error(e)
            return False

    async def get_gates(self):
        """
        Retrieves the gates information asynchronously.

        This method interacts with an external API to fetch the information about
        available gates. In case of an error during the fetching process, it logs
        the exception and returns False.

        Raises:
            Exception: General exception raised during API communication or data
            transformation.

        Returns:
            SystemInfo: A SystemInfo object populated with data fetched from the
            API if successful.
            bool: Returns False when an error occurs.
        """
        try:
            response = await self._api_wrapper.get(f"{API_URL}/gates", {}, self.token)

            return SystemInfo.from_json(await self.get_result(response))
        except Exception as e:
            _LOGGER.error(e)
            return False

    async def get_state(self, device_id: int):
        """
        Fetches the state of a device using its unique device identifier asynchronously.

        This method interacts with an external API to retrieve the current state of
        the specified device. It uses an internal API wrapper to perform the HTTP GET
        request to the desired endpoint and processes the response to return a
        DeviceState object representing the device's state. In case of an error, it
        logs the exception and returns False.

        Args:
            device_id (int): The unique identifier of the device for which the state
                is to be fetched.

        Returns:
            DeviceState | bool: A DeviceState object parsed from the API response if
                successful, otherwise False.

        Raises:
            Any exception occurring during the API call or response processing will
            be logged and returned as False without being re-raised.
        """
        try:
            response = await self._api_wrapper.get(
                f"{API_URL}/devices/{device_id}/state", {}, self.token
            )

            return DeviceState.from_json(await self.get_result(response))

        except Exception as e:
            _LOGGER.error(e)
            return False

    async def update_device_parameter(
        self, device_id: int, parameter: str, value: str | int
    ):
        """
        Updates a device parameter by sending a request to the device API.

        This method allows updating the configuration parameter of a specific device
        with the given value. It logs the request and processes the response from the
        API upon completion. If the operation fails, it logs the error and returns
        False.

        Parameters:
            device_id (int): The unique identifier of the device.
            parameter (str): The name of the parameter to be updated.
            value (str | int): The new value to set for the specified parameter.

        Returns:
            bool: Returns a boolean indicating the success of the operation. If the
            operation is successful, it returns the result of the API response, else
            returns False.
        """
        try:
            _LOGGER.info("Set %s to %s for device %s", parameter, value, device_id)
            data = {"values": [{"code": parameter, "value": value}]}

            response = await self._api_wrapper.put(
                f"{API_URL}/devices/{device_id}/params", data=data, auth=self.token
            )
            return await self.get_result(response)

        except Exception as e:
            _LOGGER.error(e)
            return False

    async def get_result(
        self, response: aiohttp.ClientResponse, ignore_response_code: bool = False
    ) -> Any:
        """
        Asynchronously retrieves and processes the JSON response from an aiohttp.ClientResponse
        object. Allows for optional ignoring of response status codes.

        Parameters:
        response: aiohttp.ClientResponse
            The HTTP response object received from the aiohttp request.
        ignore_response_code: bool, optional
            A boolean indicating whether to ignore the response status code. Defaults to False.

        Returns:
        Any
            The JSON-decoded response content.

        Raises:
        Exception
            If the response status code is not successful (non-2xx) and ignore_response_code
            is False.
        """
        if response.ok or ignore_response_code:
            return await response.json()

        raise Exception(f"Server returned: {response.status} {response.reason}")


class ApiWrapper:
    """Helper class"""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get(
        self, url: str, headers=None, auth: Any = None
    ) -> aiohttp.ClientResponse:
        """Run http GET method"""
        if headers is None:
            headers = {}
        if auth:
            headers["Authorization"] = auth

        return await self.api_wrapper("get", url, headers=headers, auth=None)

    async def post(
        self, url: str, data=None, headers=None, auth: Any = None
    ) -> aiohttp.ClientResponse:
        """Run http POST method"""
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        if auth:
            headers["Authorization"] = auth

        return await self.api_wrapper(
            "post", url, data=data, headers=headers, auth=None
        )

    async def put(
        self, url: str, data=None, headers=None, auth: Any = None
    ) -> aiohttp.ClientResponse:
        """Run http PUT method"""
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        if auth:
            headers["Authorization"] = auth

        return await self.api_wrapper("put", url, data=data, headers=headers, auth=None)

    async def api_wrapper(
        self,
        method: str,
        url: str,
        data: dict = None,
        headers: dict = None,
        auth: Any = None,
    ) -> Any:
        """Get information from the API."""
        # Use None as default and create a new dict if needed
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        try:
            async with async_timeout.timeout(TIMEOUT):
                if method.lower() == "get":
                    response = await self._session.get(url, headers=headers, auth=auth)
                    return response
                elif method.lower() == "post":
                    response = await self._session.post(
                        url,
                        headers=headers,
                        json=data,
                        auth=auth,  # Use JSON for consistency
                    )
                    return response
                elif method.lower() == "put":
                    response = await self._session.put(
                        url, headers=headers, json=data, auth=auth
                    )
                    return response
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
            raise  # Re-raise the exception instead of returning None
        except Exception as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
            raise  # Re-raise the exception
