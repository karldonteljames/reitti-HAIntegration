import logging
import aiohttp
import async_timeout
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change
from .const import DOMAIN, CONF_URL, CONF_DEVICE, CONF_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    """Legacy setup (ignore)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    url = entry.data[CONF_URL].rstrip("/")
    device_entity = entry.data[CONF_DEVICE]
    api_token = entry.data.get("api_key", "")
    port = entry.data.get(CONF_PORT, 8080)
    enable_debug = entry.options.get("enable_debug_logging", False)
    enable_push = entry.options.get("enable_push", True)
    interval_seconds = entry.options.get("interval_seconds", 30)

    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    full_url = f"{url}:{port}/api/v1/ingest/owntracks"
    session = aiohttp.ClientSession()

    async def push_location(_=None):
        if not enable_push:
            _LOGGER.debug("Push disabled; skipping update")
            return

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

    # Track state changes (lat/lon)
    state_listener = async_track_state_change(hass, device_entity, push_location)

    # Optional interval-based push
    interval_listener = async_track_time_interval(hass, push_location, timedelta(seconds=interval_seconds))

    # Manual push service
    if not hass.services.has_service(DOMAIN, "push_now"):
        hass.services.async_register(DOMAIN, "push_now", lambda call: hass.async_create_task(push_location(call)))

    # Close session when HA stops
    hass.bus.async_listen_once("homeassistant_stop", lambda _: session.close())

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "state_listener": state_listener,
        "interval_listener": interval_listener,
        "session": session
    }

    _LOGGER.info(
        "Reitti integration set up for device %s, push interval=%s seconds, debug=%s, push enabled=%s",
        device_entity, interval_seconds, enable_debug, enable_push
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not data:
        return True

    if listener := data.get("state_listener"):
        listener()
    if listener := data.get("interval_listener"):
        listener()

    if session := data.get("session"):
        await session.close()

    if hass.services.has_service(DOMAIN, "push_now"):
        hass.services.async_remove(DOMAIN, "push_now")

    return True

async def async_reload_entry(hass: HomeAssistant, entry):
    await async_unload_entry(hass, entry)
    return await async_setup_entry(hass, entry)