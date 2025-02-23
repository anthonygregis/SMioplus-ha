DEFAULT_ICONS = {
        "on": "mdi:numeric",
        "off": "mdi:numeric-0",
}

import voluptuous as vol
import logging
import time
import types
import inspect
from inspect import signature
import asyncio

import libioplus as SMioplus

from homeassistant.components.light import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from . import (
        DOMAIN, CONF_STACK, CONF_TYPE, CONF_CHAN, CONF_NAME,
        SM_MAP, SM_API
)
SM_MAP = SM_MAP["sensor"]

#SCHEMA_EXTEND = {
#	vol.Optional(CONF_NAME, default=""): cv.string,
#	vol.Optional(CONF_STACK, default="0"): cv.string,
#}
#for key in SM_SENSOR_MAP:
#    SCHEMA_EXTEND[vol.Optional(key, default="-1")] = cv.string
#PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(SCHEMA_EXTEND)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    # We want this platform to be setup via discovery
    if discovery_info == None:
        return
    add_devices([Sensor(
		name=discovery_info.get(CONF_NAME, ""),
        stack=discovery_info.get(CONF_STACK, 0),
        type=discovery_info.get(CONF_TYPE),
        chan=discovery_info.get(CONF_CHAN),
        hass=hass
	)])

class Sensor(SensorEntity):
    def __init__(self, name, stack, type, chan, hass):
        generated_name = DOMAIN + str(stack) + "_" + type + "_" + str(chan)
        self._unique_id = generate_entity_id("sensor.{}", generated_name, hass=hass)
        self._name = name or generated_name
        self._stack = int(stack)
        self._type = type
        self._chan = int(chan)
        # Altering class so alln functions have the same format
        self._short_timeout = .05
        self._icons = DEFAULT_ICONS | SM_MAP[self._type].get("icon", {})
        self._icon = self._icons["off"]
        self._uom = SM_MAP[self._type]["uom"]
        self._value = 0
        self.__SM__init()

        # Custom setup
        # I Don't like this hardcoded setup, maybe add a setup com in data.py
        if self._type == "opto_cnt":
            self._SM.rstOptoCount(self._stack, self._chan)
            ## THIS DOESN"T WORK IDK WHY
            res = self._SM.cfgOptoEdgeCount(self._stack, self._chan, 1)
            _LOGGER.error(res) # res is 1, so it SHOULD be working
        ## END

        self._update_interval = 0.1  # Set to 0.1 seconds for testing
        self._remove_update_interval = None
        _LOGGER.debug(f"Sensor {self._name} initialized with update interval: {self._update_interval}")

    async def async_added_to_hass(self):
        """Set up a timer to update the sensor periodically."""
        self._remove_update_interval = async_track_time_interval(
            self.hass, self.async_update_ha_state, timedelta(seconds=self._update_interval)
        )
        _LOGGER.debug(f"Sensor {self._name} added to hass with update interval: {self._update_interval}")

    async def async_will_remove_from_hass(self):
        """Remove the update timer when the entity is removed."""
        if self._remove_update_interval:
            self._remove_update_interval()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    async def async_update(self):
        """Update the entity."""
        await self.hass.async_add_executor_job(self.update)
        _LOGGER.debug(f"Sensor {self._name} updated with value: {self._value}")

    def __SM__init(self):
        com = SM_MAP[self._type]["com"]
        self._SM = SM_API
        if inspect.isclass(self._SM):
            self._SM = self._SM(self._stack)
            self._SM_get = getattr(self._SM, com["get"])
        else:
            def _aux_SM_get(*args):
                return getattr(self._SM, com["get"])(self._stack, *args)
            self._SM_get = _aux_SM_get

    def update(self):
        if self._type == "opto_cnt":
            ## IT DOESN"T WORK WITHOUT THIS IDK WHY
            self._SM.cfgOptoEdgeCount(self._stack, self._chan, 1)
        try:
            self._value = self._SM_get(self._chan)
        except Exception as ex:
            _LOGGER.error(DOMAIN + " %s update() failed, %e, %s, %s", self._type, ex, str(self._stack), str(self._chan))
            return
        if self._value != 0:
            self._icon = self._icons["on"]
        else:
            self._icon = self._icons["off"]

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def native_unit_of_measurement(self):
        return self._uom

    @property
    def native_value(self):
        return self._value
