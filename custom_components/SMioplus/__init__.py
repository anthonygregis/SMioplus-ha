"""Sequent Microsystems Home Automation Integration"""

import logging
import voluptuous as vol
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import asyncio
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
	CONF_NAME
)

from . import data
DOMAIN = data.DOMAIN
NAME_PREFIX = data.NAME_PREFIX
SM_MAP = data.SM_MAP
SM_API = data.API

CONF_NAME = CONF_NAME
CONF_STACK = "stack"
CONF_TYPE = "type"
CONF_CHAN = "chan"
COM_NOGET = "__NOGET__"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema(vol.Any([vol.Schema({
        vol.Optional(CONF_STACK, default="0"): cv.string,
    }, extra=vol.ALLOW_EXTRA)], {}))
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

def load_platform(hass, entity_config):
    for platform_type, attr in SM_MAP.items():
        if entity_config[CONF_TYPE] in attr:
            hass.helpers.discovery.load_platform(
                platform_type, DOMAIN, entity_config, {}
            )

def load_all_platforms(hass, stack=0):
    for platform_type, platform in SM_MAP.items():
        for type, attr in platform.items():
            if attr.get("optional", False):
                continue
            for chan in range(int(attr["chan_no"])):
                entity_config = {
                    CONF_NAME: NAME_PREFIX+str(stack)+"_"+type+"_"+str(chan+1),
                    CONF_STACK: stack,
                    CONF_TYPE: type,
                    CONF_CHAN: chan+1
                }
                hass.helpers.discovery.load_platform(
                    platform_type, DOMAIN, entity_config, {}
                )

def setup(hass, config):
    hass.data[DOMAIN] = []
    card_configs = config.get(DOMAIN)
    if not card_configs:
        load_all_platforms(hass, stack=0)
        return True
    for card_config in card_configs:
        stack = int(card_config.pop(CONF_STACK, 0))
        if not card_config:
            load_all_platforms(hass, stack=stack)
            continue
        for entity in card_config:
            try:
                [type, chan] = entity.rsplit("_", 1)
                chan = int(chan)
            except:
                _LOGGER.error(entity, " doesn't respect type_channel format")
                continue
            entity_config = card_config[entity] or {}
            entity_config |= {
                CONF_NAME: NAME_PREFIX + str(stack) + "_" + entity,
                CONF_STACK: stack,
                CONF_TYPE: type,
                CONF_CHAN: chan
            }
            load_platform(hass, entity_config)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SMioplus from a config entry."""
    async def async_update_data():
        return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SMioplus sensors",
        update_method=async_update_data,
        update_interval=timedelta(seconds=1),
    )

    await coordinator.async_config_entry_first_refresh()

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    for platform in SM_MAP:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in SM_MAP
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
