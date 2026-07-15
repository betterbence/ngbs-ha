# NGBS iCON for Home Assistant

A local Home Assistant custom integration for NGBS iCON heating/cooling controllers. It uses the controller's local JSON-over-TCP service on port `7992`; no cloud account is required.

## Initial features

- Automatic SYSID discovery through the config flow
- One climate entity per enabled thermostat
- Current temperature and humidity
- Comfort/Eco preset per room
- Target-temperature control
- Heat/cool control from the configured master thermostat
- Global Eco switch
- Parental-lock switches
- Humidity and dew-point sensors
- Valve, online, frost, and dew-protection binary sensors
- Controller water/outside temperatures, pump, overheat, uptime, and mixing-valve state

## HACS installation

1. Create a GitHub repository and push this project to it.
2. In HACS, open **Integrations**.
3. Open the menu and choose **Custom repositories**.
4. Add the GitHub repository URL and select **Integration**.
5. Install **NGBS iCON** and restart Home Assistant.
6. Open **Settings → Devices & services → Add integration**, search for **NGBS iCON**, and enter the controller IP address. Port `7992` is the default.

## Manual installation

Copy `custom_components/ngbs_icon` into Home Assistant's `custom_components` directory and restart Home Assistant.

## Development status

This is an early `0.1.1` release. Test control operations carefully. The protocol implementation is based on the local NGBS service behavior and the open-source `ngbs-icon` project.
