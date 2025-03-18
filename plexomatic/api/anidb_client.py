"""AniDB API client for retrieving anime metadata.

This module provides clients for both the UDP API (for detailed anime data) and the HTTP API
(for titles and descriptions). The main client combines both to provide a comprehensive interface.
"""

import socket
import hashlib
import logging
import time
import difflib
import requests
from typing import Dict, List, Any, Optional, cast
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET
from functools import lru_cache

logger = logging.getLogger(__name__)

# AniDB API endpoints and settings
ANIDB_UDP_HOST = "api.anidb.net"
ANIDB_UDP_PORT = 9000
ANIDB_HTTP_BASE_URL = "https://anidb.net/api"
ANIDB_CLIENT_VER = 1
ANIDB_PROTOCOL_VER = 3
ANIDB_RETRY_WAIT = 2  # seconds
ANIDB_MAX_PACKET_SIZE = 1400


class AniDBError(Exception):
    """Base class for AniDB API errors."""

    pass


class AniDBAuthenticationError(AniDBError):
    """Raised when authentication with AniDB fails."""

    pass


class AniDBRateLimitError(AniDBError):
    """Raised when AniDB rate limit is reached."""

    pass


class AniDBUDPClient:
    """Client for interacting with the AniDB UDP API."""

    def __init__(
        self,
        username: str,
        password: str,
        client_name: str = "plexomatic",
        client_version: str = "1",
    ):
        """Initialize the AniDB UDP client.

        Args:
            username: AniDB username.
            password: AniDB password.
            client_name: Name of the client software.
            client_version: Version of the client software.
        """
        self.username = username
        self.password = password
        self.client_name = client_name
        self.client_version = client_version
        self.socket: Optional[socket.socket] = None
        self.session: Optional[str] = None
        self.session_expires_at: Optional[datetime] = None
        self.last_command_time: float = 0
        self._banned_until: Optional[datetime] = None

    def _connect(self) -> None:
        """Connect to the AniDB UDP API."""
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(10)  # 10 seconds timeout

    def _disconnect(self) -> None:
        """Disconnect from the AniDB UDP API."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None

    def _encode_command(self, command: str) -> bytes:
        """Encode an AniDB command.

        Args:
            command: The command to encode.

        Returns:
            The encoded command as bytes.
        """
        return command.encode("utf-8")

    def _parse_response(self, response: bytes) -> Dict[str, Any]:
        """Parse an AniDB response.

        Args:
            response: The response to parse.

        Returns:
            A dictionary with the parsed response.

        Raises:
            AniDBAuthenticationError: If authentication fails.
            AniDBRateLimitError: If rate limit is reached.
            AniDBError: For other AniDB errors.
        """
        response_str = response.decode("utf-8")
        code = int(response_str.split(" ")[0])

        # Handle error codes
        if code == 500 or code == 501:
            logger.error(f"AniDB authentication failed: {response_str}")
            raise AniDBAuthenticationError(f"Authentication failed: {response_str}")
        elif code == 555 or code == 601:
            logger.warning(f"AniDB rate limit exceeded: {response_str}")
            self._banned_until = datetime.now(timezone.utc) + timedelta(hours=1)
            raise AniDBRateLimitError(f"Rate limit exceeded: {response_str}")
        elif code >= 500:
            logger.error(f"AniDB error: {response_str}")
            raise AniDBError(f"AniDB error: {response_str}")

        # Extract session from login response
        if "LOGIN ACCEPTED" in response_str and "s=" in response_str:
            session_key = response_str.split("s=")[1].strip()
            return {"code": code, "session": session_key}

        # Parse data responses (format: key|value|key|value...)
        if "\n" in response_str:
            # Remove the status line
            data_line = response_str.split("\n", 1)[1]
            if "|" in data_line:
                data: Dict[str, Any] = {}
                parts = data_line.split("|")
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        data[parts[i]] = parts[i + 1]
                return data
            return {"raw": data_line}

        # Simple status response
        return {"code": code, "message": response_str}

    def _send_cmd(self, command: str) -> Dict[str, Any]:
        """Send a command to the AniDB UDP API.

        Args:
            command: The command to send.

        Returns:
            The parsed response.

        Raises:
            AniDBError: If the command fails.
        """
        # Check if we're banned
        if self._banned_until and datetime.now(timezone.utc) < self._banned_until:
            ban_time = (self._banned_until - datetime.now(timezone.utc)).total_seconds()
            logger.warning(f"AniDB client is banned for {ban_time:.1f} more seconds")
            raise AniDBRateLimitError(f"Client is banned for {ban_time:.1f} more seconds")

        # Respect rate limiting
        wait_time = self.last_command_time + ANIDB_RETRY_WAIT - time.time()
        if wait_time > 0:
            logger.debug(f"Rate limiting - waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)

        try:
            self._connect()

            if self.socket is None:
                raise AniDBError("Socket not connected")

            encoded_cmd = self._encode_command(command)
            self.socket.sendto(encoded_cmd, (ANIDB_UDP_HOST, ANIDB_UDP_PORT))
            self.last_command_time = time.time()

            response, _ = self.socket.recvfrom(ANIDB_MAX_PACKET_SIZE)
            return self._parse_response(response)

        except socket.timeout:
            logger.error("AniDB connection timed out")
            raise AniDBError("Connection timed out")
        except socket.error as e:
            logger.error(f"AniDB socket error: {e}")
            raise AniDBError(f"Socket error: {e}")
        finally:
            # We don't close the socket between commands to maintain session
            pass

    def authenticate(self) -> None:
        """Authenticate with the AniDB API.

        Raises:
            AniDBAuthenticationError: If authentication fails.
        """
        # Skip if already authenticated with a valid session
        if (
            self.session
            and self.session_expires_at
            and self.session_expires_at > datetime.now(timezone.utc)
        ):
            return

        # Generate password hash
        password_hash = hashlib.md5(self.password.encode("utf-8")).hexdigest()

        # Build authentication command
        cmd = (
            f"AUTH user={self.username}&pass={password_hash}&"
            f"protover={ANIDB_PROTOCOL_VER}&client={self.client_name}&"
            f"clientver={self.client_version}"
        )

        # Send the command
        response = self._send_cmd(cmd)

        if "session" in response:
            self.session = response["session"]
            # Session expires in 1 hour
            self.session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            logger.info("Successfully authenticated with AniDB")
        else:
            raise AniDBAuthenticationError("Authentication failed - no session key received")

    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated, re-authenticating if necessary."""
        if (
            not self.session
            or not self.session_expires_at
            or self.session_expires_at <= datetime.now(timezone.utc)
        ):
            self.authenticate()

    def get_anime_by_name(self, name: str) -> Dict[str, Any]:
        """Search for anime by name.

        Args:
            name: The name of the anime to search for.

        Returns:
            A dictionary with anime data.
        """
        self._ensure_authenticated()
        cmd = f"ANIME aname={name}&s={self.session}"
        return self._send_cmd(cmd)

    def get_anime_by_id(self, anime_id: int) -> Dict[str, Any]:
        """Get anime details by ID.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A dictionary with anime data.
        """
        self._ensure_authenticated()
        cmd = f"ANIME aid={anime_id}&s={self.session}"
        return self._send_cmd(cmd)

    def get_episodes(self, anime_id: int) -> List[Dict[str, Any]]:
        """Get episodes for an anime.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A list of episode data dictionaries.
        """
        self._ensure_authenticated()
        cmd = f"EPISODE aid={anime_id}&s={self.session}"

        try:
            data = self._send_cmd(cmd)

            # If this is a single episode (unlikely but possible)
            if isinstance(data, dict) and "eid" in data:
                return [data]

            # Handle the case where there are multiple episodes
            # This might need adjustment based on actual response format
            episodes: List[Dict[str, Any]] = []
            if isinstance(data, dict) and "raw" in data:
                # Parse the raw data if it's returned as a single string
                episode_lines = data["raw"].split("\n")
                for line in episode_lines:
                    if not line.strip():
                        continue
                    episode_data: Dict[str, Any] = {}
                    parts = line.split("|")
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            episode_data[parts[i]] = parts[i + 1]
                    if episode_data:
                        episodes.append(episode_data)
            return episodes
        except AniDBError as e:
            logger.error(f"Error fetching episodes for anime {anime_id}: {e}")
            return []

    def close(self) -> None:
        """Close the connection and logout."""
        if self.socket and self.session:
            try:
                # Send logout command
                cmd = f"LOGOUT s={self.session}"
                self.socket.sendto(self._encode_command(cmd), (ANIDB_UDP_HOST, ANIDB_UDP_PORT))
                logger.info("Sent logout command to AniDB")
            except Exception as e:
                logger.warning(f"Error during logout: {e}")
            finally:
                self._disconnect()
                self.session = None
                self.session_expires_at = None
                logger.info("Closed AniDB connection")


class AniDBHTTPClient:
    """Client for interacting with the AniDB HTTP API."""

    def __init__(self, client_name: str = "plexomatic"):
        """Initialize the AniDB HTTP client.

        Args:
            client_name: Name of the client software.
        """
        self.client_name = client_name

    @lru_cache(maxsize=1)
    def get_anime_titles(self) -> List[Dict[str, Any]]:
        """Get a list of all anime titles.

        Returns:
            A list of dictionaries with anime ID and titles.
        """
        url = f"{ANIDB_HTTP_BASE_URL}/animetitles.xml"

        try:
            response = requests.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to fetch anime titles: {response.status_code}")
                return []

            # Parse XML
            root = ET.fromstring(response.content)

            anime_list = []
            for anime_elem in root.findall("anime"):
                anime_id = anime_elem.get("aid")
                titles = []

                for title_elem in anime_elem.findall("title"):
                    title_text = title_elem.text
                    lang = title_elem.get("{http://www.w3.org/XML/1998/namespace}lang")
                    title_type = title_elem.get("type")

                    titles.append({"title": title_text, "lang": lang, "type": title_type})

                anime_list.append({"aid": anime_id, "titles": titles})

            return anime_list

        except requests.RequestException as e:
            logger.error(f"Error fetching anime titles: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return []

    def get_anime_description(self, anime_id: int) -> Dict[str, Any]:
        """Get detailed description for an anime.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A dictionary with anime description data.
        """
        url = f"{ANIDB_HTTP_BASE_URL}/anime-desc.xml?aid={anime_id}&client={self.client_name}"

        try:
            response = requests.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to fetch anime description: {response.status_code}")
                return {}

            # Parse XML
            root = ET.fromstring(response.content)

            anime_data: Dict[str, Any] = {"id": root.get("id")}

            # Extract titles
            titles: List[Dict[str, Optional[str]]] = []
            titles_elem = root.find("titles")
            if titles_elem is not None:
                for title_elem in titles_elem.findall("title"):
                    title_text = title_elem.text
                    lang = title_elem.get("{http://www.w3.org/XML/1998/namespace}lang")
                    title_type = title_elem.get("type")

                    titles.append({"title": title_text, "lang": lang, "type": title_type})

            anime_data["titles"] = titles

            # Extract description and picture
            description_elem = root.find("description")
            if description_elem is not None and description_elem.text:
                anime_data["description"] = description_elem.text

            picture_elem = root.find("picture")
            if picture_elem is not None and picture_elem.text:
                anime_data["picture"] = picture_elem.text

            return anime_data

        except requests.RequestException as e:
            logger.error(f"Error fetching anime description: {e}")
            return {}
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return {}


class AniDBClient:
    """Main client for interacting with the AniDB API.

    This client combines both the UDP and HTTP clients to provide
    a comprehensive interface to the AniDB API.
    """

    def __init__(
        self,
        username: str,
        password: str,
        client_name: str = "plexomatic",
        client_version: str = "1",
    ):
        """Initialize the AniDB client.

        Args:
            username: AniDB username.
            password: AniDB password.
            client_name: Name of the client software.
            client_version: Version of the client software.
        """
        self.udp_client = AniDBUDPClient(
            username=username,
            password=password,
            client_name=client_name,
            client_version=client_version,
        )
        self.http_client = AniDBHTTPClient(client_name=client_name)

    def get_anime_by_name(self, name: str) -> Dict[str, Any]:
        """Search for anime by name.

        Args:
            name: The name of the anime to search for.

        Returns:
            A dictionary with anime data.
        """
        return self.udp_client.get_anime_by_name(name)

    def get_anime_by_id(self, anime_id: int) -> Dict[str, Any]:
        """Get anime details by ID.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A dictionary with anime data.
        """
        return self.udp_client.get_anime_by_id(anime_id)

    def get_anime_details(self, anime_id: int) -> Dict[str, Any]:
        """Get comprehensive anime details combining UDP and HTTP data.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A dictionary with complete anime data.
        """
        # Get basic info from UDP API
        basic_info = self.udp_client.get_anime_by_id(anime_id)

        # Get detailed description from HTTP API
        description_info = self.http_client.get_anime_description(anime_id)

        # Merge the data
        merged_data = {**basic_info}

        # Add description if available
        if "description" in description_info:
            merged_data["description"] = description_info["description"]

        # Add picture if available
        if "picture" in description_info:
            merged_data["picture"] = description_info["picture"]

        return merged_data

    def get_episodes_with_titles(self, anime_id: int) -> List[Dict[str, Any]]:
        """Get episodes with titles for an anime.

        Args:
            anime_id: The AniDB anime ID.

        Returns:
            A list of episode data dictionaries.
        """
        return self.udp_client.get_episodes(anime_id)

    def map_title_to_series(self, title: str, threshold: float = 0.8) -> Optional[str]:
        """Find the AniDB ID for a series based on its title.

        Args:
            title: The series title to search for.
            threshold: The similarity threshold for fuzzy matching (0.0-1.0).

        Returns:
            The AniDB anime ID if found, None otherwise.
        """
        anime_list = self.http_client.get_anime_titles()

        # Normalize the search title
        search_title = title.lower()

        # First try exact match
        for anime in anime_list:
            for t in anime["titles"]:
                if t["title"].lower() == search_title:
                    return cast(str, anime["aid"])

        # If no exact match, try fuzzy matching
        best_match: Optional[str] = None
        best_score: float = 0.0

        for anime in anime_list:
            for t in anime["titles"]:
                # Only consider English and Romaji titles for fuzzy matching
                if t.get("lang") in ["en", "x-jat"]:
                    score = difflib.SequenceMatcher(None, search_title, t["title"].lower()).ratio()
                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = cast(str, anime["aid"])

        return best_match

    def close(self) -> None:
        """Close the connection."""
        self.udp_client.close()
