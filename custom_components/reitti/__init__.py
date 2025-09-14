import logging
import aiohttp
import async_timeout
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, CONF_URL, CONF_DEVICE, CONF_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    """Set up the Reitti integration (legacy call)."""
    return True  # we use config entries

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Reitti from a config entry."""
    url = entry.data[CONF_URL].rstrip("/")
    device_entity = entry.data[CONF_DEVICE]
    api_token = entry.data.get("api_key", "")
    port = entry.data.get(CONF_PORT, 8080)
    enable_debug = entry.options.get("enable_debug_logging", False)

    # Ensure HTTP scheme
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    full_url = f"{url}:{port}/api/v1/ingest/owntracks"
    session = aiohttp.ClientSession()

    async def push_location(_=None):
        """Push the selected device's location to Reitti using POST JSON."""
        state = hass.states.get(device_entity)
        if not state:
            _LOGGER.warning("Device state not found: %s", device_entity)
            return

        attributes = state.attributes
        latitude = attributes.get("latitude")
        longitude = attributes.get("longitude")

        if latitude is None or longitude is None:
            _LOGGER.warning("Device has no latitude/longitude: %s", device_entity)
            return

        tid = state.object_id[:2].upper()
        payload = {
            "_type": "location",
            "tid": tid,
            "lat": latitude,
            "lon": longitude,
            "alt": attributes.get("altitude", 0),
            "acc": attributes.get("gps_accuracy", 0),
            "vel": attributes.get("speed", 0),
            "cog": attributes.get("course", 0),
            "tst": int(datetime.now().timestamp())
        }

        headers = {"Content-Type": "application/json"}

        if enable_debug:
            _LOGGER.debug("Pushing to Reitti URL: %s with payload: %s", full_url, payload)

        try:
            async with async_timeout.timeout(10):
                async with session.post(f"{full_url}?token={api_token}", json=payload, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status in (200, 202):
                        _LOGGER.info("Successfully pushed location to Reitti (status=%s)", resp.status)
                        if enable_debug:
                            _LOGGER.debug("Reitti response body: %s", text)
                    else:
                        _LOGGER.warning("Reitti push failed: status=%s, body=%s", resp.status, text)
        except Exception:
            _LOGGER.exception("Error pushing to Reitti")

    # Interval from options (default 30s)
    interval_seconds = entry.options.get("interval_seconds", 30)
    remove_listener = async_track_time_interval(hass, push_location, timedelta(seconds=interval_seconds))

    # Register a manual push service
    if not hass.services.has_service(DOMAIN, "push_now"):
        hass.services.async_register(
            DOMAIN,
            "push_now",
            lambda call: hass.async_create_task(push_location(call))
        )

    # Close session when HA stops
    hass.bus.async_listen_once("homeassistant_stop", lambda _: session.close())

    # Store references for unload
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "listener": remove_listener,
        "session": session
    }

    _LOGGER.info(
        "Reitti integration set up for device %s, pushing every %s seconds (debug=%s)",
        device_entity,
        interval_seconds,
        enable_debug
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a Reitti config entry."""
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not data:
        return True

    listener = data.get("listener")
    if listener:
        listener()

    session = data.get("session")
    if session:
        await session.close()

    if hass.services.has_service(DOMAIN, "push_now"):
        hass.services.async_remove(DOMAIN, "push_now")

    return True

async def async_reload_entry(hass: HomeAssistant, entry):
    """Reload a Reitti config entry."""
    await async_unload_entry(hass, entry)
    return await async_setup_entry(hass, entry)
