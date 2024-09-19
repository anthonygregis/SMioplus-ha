from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_POWER
import logging
import time

from . import data
DOMAIN = data.DOMAIN
SM_API = data.API

_LOGGER = logging.getLogger(__name__)

class SMioplusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, SM, stack, chan, type, name, unit, icons):
        super().__init__(coordinator)
        self._SM = SM
        self._stack = stack
        self._chan = chan
        self._type = type
        self._name = name
        self._unit = unit
        self._icons = icons
        self._value = None
        self._icon = icons["off"]
        self._short_timeout = .05
        self._SM_get = getattr(SM, SM_API[type]["get"])

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return DEVICE_CLASS_POWER

    @property
    def native_value(self):
        self.update()
        return self._value

    def update(self):
        if self._type == "opto_cnt":
            time.sleep(self._short_timeout)
            self._SM.cfgOptoEdgeCount(self._stack, self._chan, 1)
        time.sleep(self._short_timeout)
        try:
            self._value = self._SM_get(self._chan)
        except Exception as ex:
            _LOGGER.error(DOMAIN + " %s update() failed, %e, %s, %s", self._type, ex, str(self._stack), str(self._chan))
            return
        if self._value != 0:
            self._icon = self._icons["on"]
        else:
            self._icon = self._icons["off"]

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    SM = hass.data[DOMAIN][config_entry.entry_id]["SM"]
    stack = config_entry.data["stack"]
    sensors = [
        SMioplusSensor(coordinator, SM, stack, chan+1, type, 
                       f"{data.NAME_PREFIX}{stack}_{type}_{chan+1}", 
                       attr.get("unit", ""),
                       attr.get("icons", {"on": "mdi:flash", "off": "mdi:flash-off"}))
        for type, attr in data.SM_MAP["sensor"].items()
        for chan in range(int(attr["chan_no"]))
    ]
    async_add_entities(sensors, True)
