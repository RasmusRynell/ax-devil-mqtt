# Module: client
File: `src/ax_devil/client.py`
Main client interface for Axis cameras.
## Imports
- `from typing import Optional`
- `from core.client import CameraClient`
- `from core.config import CameraConfig`
- `from features.device import DeviceClient`
- `from features.network import NetworkClient`
- `from features.media import MediaClient`
- `from features.geocoordinates import GeoCoordinatesClient`
- `from features.mqtt_client import MqttClientFeature`
- `from features.analytics_mqtt import AnalyticsMqttClient`
## Class: Client
Main client interface for Axis cameras.

This is the primary entry point for interacting with Axis cameras.
It provides access to all features through a unified interface and
handles lazy loading of feature clients.

Example:
    ```python
    from ax_devil import Client, CameraConfig
    
    # Create a client
    config = CameraConfig.https("camera.local", "user", "pass")
    client = Client(config)
    
    # Access features
    info = client.device.get_info()
    ```
### Methods:
#### def __init__(self, config: CameraConfig) -> None
Initialize with camera configuration.
#### @property
def device(self) -> DeviceClient
Access device operations.
#### @property
def network(self) -> NetworkClient
Access network operations.
#### @property
def media(self) -> MediaClient
Access media operations.
#### @property
def geocoordinates(self) -> GeoCoordinatesClient
Access geographic coordinates and orientation operations.
#### @property
def mqtt_client(self) -> MqttClientFeature
Access MQTT client operations.
#### @property
def analytics_mqtt(self) -> AnalyticsMqttClient
Access analytics MQTT operations.
# Module: __init__
File: `src/ax_devil/__init__.py`
ax-devil: Axis Camera Development Utilities A Python library that provides a unified interface for Axis network cameras. It simplifies camera integration and management through a well-structured API that emphasizes type safety, error handling, and consistent behavior. Example: ```python from ax_devil import Client, CameraConfig # Create a client config = CameraConfig.https("camera.local", "user", "pass") client = Client(config) # Access features info = client.device.get_info() ```
## Imports
- `from core.config import CameraConfig`
- `from client import Client`
# Module: errors
File: `src/ax_devil/utils/errors.py`
## Imports
- `from typing import Optional`
- `from typing import Dict`
- `from typing import Any`
## Class: AxDevilError(Exception)
Base exception for all ax-devil errors.
### Instance Attributes:
- code = code
- message = message
- details = details or {}
### Methods:
#### def __init__(self, code: str, message: str, details: Optional[Dict[(str, Any)]] = None)
## Class: AuthenticationError(AxDevilError)
Authentication related errors.
## Class: ConfigurationError(AxDevilError)
Configuration related errors.
## Class: NetworkError(AxDevilError)
Network communication errors.
### Methods:
#### def __init__(self, code: str, message: str = None)
## Class: SecurityError(AxDevilError)
Security-related errors like SSL/TLS issues.
### Methods:
#### def __init__(self, code: str, message: str = None, details: Optional[Dict[(str, Any)]] = None)
## Class: FeatureError(AxDevilError)
Feature-specific errors.
# Module: __init__
File: `src/ax_devil/utils/__init__.py`
# Module: geocoordinates
File: `src/ax_devil/features/geocoordinates.py`
Geographic coordinates and orientation features for Axis cameras.
## Imports
- `from dataclasses import dataclass`
- `from typing import Optional`
- `from typing import Dict`
- `from typing import Tuple`
- `from typing import TypeVar`
- `from typing import Protocol`
- `from typing import cast`
- `from typing import Union`
- `import xml.etree.ElementTree as ET`
- `from base import FeatureClient`
- `from core.types import TransportResponse`
- `from core.types import FeatureResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: XMLParseable(Protocol)
Protocol for types that can be created from XML.
### Methods:
#### @classmethod
def from_xml(cls, xml_text: str) -> XMLParseable
Create instance from XML text.
## Function: def safe_float(value: Optional[str]) -> Optional[float]
Safely convert string to float, returning None if invalid.
## Function: def extract_xml_value(element: Optional[ET.Element], path: str) -> Optional[str]
Safely extract text value from XML element.
## Function: def extract_xml_bool(element: Optional[ET.Element], path: str) -> bool
Safely extract boolean value from XML element.
## Function: def parse_xml_root(xml_text: str) -> ET.Element
Parse XML text into root element with error handling.
### Raises:
- `ValueError`
## Function: def format_iso6709_coordinate(latitude: float, longitude: float) -> Tuple[(str, str)]
Format coordinates according to ISO 6709 standard.

Format:
    Latitude: ±DD.DDDDDD (2 digits before decimal, 6 after)
    Longitude: ±DDD.DDDDDD (3 digits before decimal, 6 after)
## Function: def parse_iso6709_coordinate(coord_str: str) -> float
Parse an ISO 6709 coordinate string to float.
### Raises:
- `ValueError`
## Class: GeoCoordinatesLocation
Camera location information.
### Class Attributes:
- latitude: float
- longitude: float
- is_valid: bool
### Methods:
#### @classmethod
def from_params(cls, params: Dict[(str, str)]) -> GeoCoordinatesLocation
Create instance from parameter dictionary.
#### @classmethod
def from_xml(cls, xml_text: str) -> GeoCoordinatesLocation
Create instance from XML response.
## Class: GeoCoordinatesOrientation
Camera orientation information.
### Class Attributes:
- heading: Optional[float]
- tilt: Optional[float]
- roll: Optional[float]
- installation_height: Optional[float]
- is_valid: bool
### Methods:
#### @classmethod
def from_params(cls, params: Dict[(str, str)]) -> GeoCoordinatesOrientation
Create instance from parameter dictionary.
#### @classmethod
def from_xml(cls, xml_text: str) -> GeoCoordinatesOrientation
Create instance from XML response.
## Class: GeoCoordinatesClient(FeatureClient)
Client for camera geocoordinates and orientation features.
### Class Attributes:
- LOCATION_GET_ENDPOINT
- LOCATION_SET_ENDPOINT
- ORIENTATION_ENDPOINT
### Methods:
#### def get_location(self) -> FeatureResponse[GeoCoordinatesLocation]
Get current camera location.
#### def set_location(self, latitude: float, longitude: float) -> FeatureResponse[bool]
Set camera location.
#### def get_orientation(self) -> FeatureResponse[GeoCoordinatesOrientation]
Get current camera orientation.
#### def set_orientation(self, orientation: GeoCoordinatesOrientation) -> FeatureResponse[bool]
Set camera orientation.
#### def apply_settings(self) -> FeatureResponse[bool]
Apply pending orientation settings.
# Module: mqtt_client
File: `src/ax_devil/features/mqtt_client.py`
MQTT client feature for managing broker configuration and client lifecycle on Axis cameras.
## Imports
- `from dataclasses import dataclass`
- `from dataclasses import asdict`
- `import json`
- `from typing import Dict`
- `from typing import Any`
- `from typing import Optional`
- `from typing import ClassVar`
- `from typing import Tuple`
- `from typing import Union`
- `from base import FeatureClient`
- `from core.types import FeatureResponse`
- `from core.types import TransportResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: BrokerConfig
MQTT broker configuration settings.
### Class Attributes:
- host: str
- port: int
- username: Optional[str]
- password: Optional[str]
- use_tls: bool
- keep_alive_interval: int
- client_id: str
- clean_session: bool
- auto_reconnect: bool
- device_topic_prefix: Optional[str]
### Methods:
#### def validate(self) -> Optional[str]
Validate configuration values.
#### def to_dict(self) -> Dict[(str, Any)]
Convert to dictionary representation.
#### def to_payload(self) -> Dict[(str, Any)]
Convert configuration to API payload.
#### @classmethod
def from_response(cls, data: Dict[(str, Any)]) -> BrokerConfig
Create broker config from API response data.
## Class: MqttStatus
MQTT client status with connection details and error information.
### Class Attributes:
- STATUS_CONNECTED: ClassVar[str]
- STATUS_CONNECTING: ClassVar[str]
- STATUS_DISCONNECTED: ClassVar[str]
- STATUS_INACTIVE: ClassVar[str]
- STATUS_ERROR: ClassVar[str]
- STATUS_UNKNOWN: ClassVar[str]
- VALID_STATUSES: ClassVar[set[str]]
- STATE_ACTIVE: ClassVar[str]
- STATE_INACTIVE: ClassVar[str]
- STATE_ERROR: ClassVar[str]
- status: str
- state: str
- connected_to: Optional[Dict[(str, Any)]]
- error: Optional[str]
- config: Optional[BrokerConfig]
### Methods:
#### def __post_init__(self)
Validate status value.
#### def to_dict(self) -> Dict[(str, Any)]
Convert to dictionary representation.
#### @classmethod
def from_response(cls, data: Dict[(str, Any)]) -> MqttStatus
Create status instance from API response data. Raises ValueError if status is invalid.
## Class: MqttClientFeature(FeatureClient)
Client for managing MQTT operations.
### Class Attributes:
- API_VERSION: ClassVar[str]
- MQTT_ENDPOINT
### Methods:
#### def get_feature_name(self) -> str
Get feature identifier.
#### def activate(self) -> FeatureResponse[Dict[(str, Any)]]
Start MQTT client.
#### def deactivate(self) -> FeatureResponse[Dict[(str, Any)]]
Stop MQTT client.
#### def configure(self, config: BrokerConfig) -> FeatureResponse[Dict[(str, Any)]]
Configure MQTT broker settings. Raises FeatureError if config is invalid.
#### def get_status(self) -> FeatureResponse[MqttStatus]
Get MQTT connection status. Raises FeatureError if response parsing fails.
# Module: analytics_mqtt
File: `src/ax_devil/features/analytics_mqtt.py`
Analytics MQTT feature for managing analytics data publishers. This module implements Layer 2 functionality for analytics MQTT operations, providing a clean interface for managing analytics data publishers while handling data normalization and error abstraction.
## Imports
- `from dataclasses import dataclass`
- `from typing import Dict`
- `from typing import Any`
- `from typing import Optional`
- `from typing import List`
- `from typing import ClassVar`
- `from typing import Generic`
- `from typing import TypeVar`
- `from base import AxisFeatureClient`
- `from core.types import FeatureResponse`
- `from core.types import TransportResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: DataSource
Analytics data source information.

Attributes:
    key: Unique identifier for the data source
    name: Human-readable name
    description: Optional description of the data source
    type: Type of analytics data
    format: Data format (e.g., "json")
### Class Attributes:
- key: str
- name: str
- description: Optional[str]
- type: str
- format: str
### Methods:
#### @classmethod
def from_response(cls, data: Dict[(str, Any)]) -> DataSource
Create instance from API response data.
## Class: PublisherConfig
MQTT analytics publisher configuration.

Attributes:
    id: Unique identifier for the publisher
    data_source_key: Key identifying the analytics data source
    mqtt_topic: MQTT topic to publish to
    qos: Quality of Service level (0-2)
    retain: Whether to retain messages on the broker
    use_topic_prefix: Whether to use device topic prefix
### Class Attributes:
- id: str
- data_source_key: str
- mqtt_topic: str
- qos: int
- retain: bool
- use_topic_prefix: bool
### Methods:
#### def validate(self) -> Optional[str]
Validate configuration values.
#### def to_payload(self) -> Dict[(str, Any)]
Convert to API request payload.
#### @classmethod
def from_response(cls, data: Dict[(str, Any)]) -> PublisherConfig
Create publisher config from API response data.
## Class: AnalyticsMqttClient(AxisFeatureClient[PublisherConfig])
Client for analytics MQTT operations.

Provides functionality for:
- Managing analytics data publishers
- Retrieving available data sources
- Configuring MQTT publishing settings
### Class Attributes:
- API_VERSION: ClassVar[str]
- BASE_PATH: ClassVar[str]
- DATA_SOURCES_ENDPOINT
- PUBLISHERS_ENDPOINT
- CREATE_PUBLISHER_ENDPOINT
- REMOVE_PUBLISHER_ENDPOINT
- JSON_HEADERS
### Methods:
#### def get_feature_name(self) -> str
Get feature identifier.
#### def get_data_sources(self) -> FeatureResponse[List[DataSource]]
Get available analytics data sources.

Returns:
    FeatureResponse containing list of data sources
#### def list_publishers(self) -> FeatureResponse[List[PublisherConfig]]
List configured MQTT publishers.

Returns:
    FeatureResponse containing list of publisher configurations
#### def create_publisher(self, config: PublisherConfig) -> FeatureResponse[PublisherConfig]
Create new MQTT publisher.

Args:
    config: Publisher configuration
    
Returns:
    FeatureResponse containing created publisher configuration
#### def remove_publisher(self, publisher_id: str) -> FeatureResponse[bool]
Delete MQTT publisher by ID.

Args:
    publisher_id: ID of publisher to remove
    
Returns:
    FeatureResponse indicating success/failure
# Module: device
File: `src/ax_devil/features/device.py`
## Imports
- `from dataclasses import dataclass`
- `from typing import Dict`
- `from typing import List`
- `from base import AxisFeatureClient`
- `from core.types import FeatureResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: DeviceInfo
Camera device information.

Attributes:
    model: Camera model name (e.g., "AXIS Q1656")
    product_type: Type of camera (e.g., "Box Camera")
    product_number: Short product number (e.g., "Q1656")
    serial_number: Unique serial number
    hardware_id: Hardware identifier
    firmware_version: Current firmware version
    build_date: Firmware build date
    ptz_support: List of supported PTZ modes
    analytics_support: Whether analytics are supported
### Class Attributes:
- model: str
- product_type: str
- product_number: str
- serial_number: str
- hardware_id: str
- firmware_version: str
- build_date: str
- ptz_support: List[str]
- analytics_support: bool
### Methods:
#### @classmethod
def from_params(cls, params: Dict[(str, str)]) -> DeviceInfo
Create instance from parameter dictionary.
## Class: DeviceClient(AxisFeatureClient[DeviceInfo])
Client for basic device operations.
### Class Attributes:
- PARAMS_ENDPOINT
- RESTART_ENDPOINT
### Methods:
#### def get_info(self) -> FeatureResponse[DeviceInfo]
Get basic device information.
#### def restart(self) -> FeatureResponse[bool]
Restart the camera.
#### def check_health(self) -> FeatureResponse[bool]
Check if the camera is responsive.
# Module: network
File: `src/ax_devil/features/network.py`
## Imports
- `from dataclasses import dataclass`
- `from typing import Optional`
- `from typing import Dict`
- `from typing import List`
- `from base import AxisFeatureClient`
- `from core.types import TransportResponse`
- `from core.types import FeatureResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: NetworkInfo
Network interface information.

Attributes:
    interface_name: Name of the network interface (e.g., "eth0")
    mac_address: MAC address of the interface
    ip_address: Current IP address
    subnet_mask: Network subnet mask
    gateway: Default gateway
    dns_servers: List of configured DNS servers
    link_status: Whether the link is up
    link_speed: Current link speed in Mbps
    duplex_mode: Full or half duplex
### Class Attributes:
- interface_name: str
- mac_address: str
- ip_address: str
- subnet_mask: str
- gateway: str
- dns_servers: List[str]
- link_status: bool
- link_speed: Optional[int]
- duplex_mode: Optional[str]
### Methods:
#### @classmethod
def from_params(cls, params: Dict[(str, str)], interface: str = 'eth0') -> NetworkInfo
Create instance from parameter dictionary.
## Class: NetworkClient(AxisFeatureClient)
Client for network configuration operations.
### Class Attributes:
- PARAMS_ENDPOINT
- NETWORK_ENDPOINT
### Methods:
#### def get_network_info(self, interface: str = 'eth0') -> FeatureResponse[NetworkInfo]
Get network interface information.
# Module: __init__
File: `src/ax_devil/features/__init__.py`
Feature-specific clients for camera operations.
## Imports
- `from device import DeviceClient`
- `from device import DeviceInfo`
- `from network import NetworkClient`
- `from network import NetworkInfo`
# Module: base
File: `src/ax_devil/features/base.py`
Base classes for feature modules.
## Imports
- `from typing import Dict`
- `from typing import TypeVar`
- `from typing import Generic`
- `from core.client import FeatureClient`
- `from core.types import TransportResponse`
- `from core.types import FeatureResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: AxisFeatureClient(FeatureClient, Generic[T])
Base class for Axis camera feature clients.

Provides common functionality used across feature modules:
- Parameter parsing
- Error handling
- Response formatting
# Module: media
File: `src/ax_devil/features/media.py`
## Imports
- `from dataclasses import dataclass`
- `from typing import Optional`
- `from typing import Dict`
- `from base import AxisFeatureClient`
- `from core.types import TransportResponse`
- `from core.types import FeatureResponse`
- `from core.endpoints import CameraEndpoint`
- `from utils.errors import FeatureError`
## Class: MediaConfig
Media capture configuration.

Attributes:
    resolution: Image resolution in WxH format (e.g., "1920x1080")
    compression: JPEG compression level (1-100)
    camera_head: Camera head identifier for multi-sensor devices
    rotation: Image rotation in degrees (0, 90, 180, or 270)
### Class Attributes:
- resolution: Optional[str]
- compression: Optional[int]
- camera_head: Optional[int]
- rotation: Optional[int]
### Methods:
#### def validate(self) -> Optional[str]
Validate configuration parameters.

Returns:
    Error message if validation fails, None if valid.
#### def to_params(self) -> Dict[(str, str)]
Convert configuration to request parameters.
## Class: MediaClient(AxisFeatureClient)
Client for camera media operations.

Provides functionality for:
- Capturing JPEG snapshots
- Configuring media parameters
- Retrieving media capabilities
### Class Attributes:
- SNAPSHOT_ENDPOINT
### Methods:
#### def get_snapshot(self, config: Optional[MediaConfig] = None) -> FeatureResponse[bytes]
Capture a JPEG snapshot from the camera.

Args:
    config: Optional media configuration parameters
    
Returns:
    FeatureResponse containing the image data on success
