"""Constants for the NGBS iCON integration."""

from datetime import timedelta

DOMAIN = "ngbs_icon"
DEFAULT_NAME = "NGBS iCON"
DEFAULT_PORT = 7992
DEFAULT_SCAN_INTERVAL = 15
DEFAULT_TIMEOUT = 5.0
UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

CONF_SYSID = "sysid"
CONF_SCAN_INTERVAL = "scan_interval"

PLATFORMS = ["climate", "sensor", "binary_sensor", "switch", "select"]
