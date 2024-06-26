import logging

from homeassistant.core import HomeAssistant

from homeassistant.components.text import TextEntity

from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.helpers.entity import generate_entity_id, DeviceInfo

from homeassistant.helpers import issue_registry as ir

from ..const import (DOMAIN, REGEX_TARIFF_PARTS)

from . import get_gas_tariff_override_key

from ..utils.tariff_check import check_tariff_override_valid

from ..api_client import OctopusEnergyApiClient

from .base import (OctopusEnergyGasSensor)
from ..utils.attributes import dict_to_typed_dict

_LOGGER = logging.getLogger(__name__)

class OctopusEnergyPreviousAccumulativeGasCostTariffOverride(OctopusEnergyGasSensor, TextEntity, RestoreEntity):
  """Sensor for the tariff for the previous days accumulative gas cost looking at a different tariff."""

  _attr_pattern = REGEX_TARIFF_PARTS

  def __init__(self, hass: HomeAssistant, account_id: str, client: OctopusEnergyApiClient, tariff_code, meter, point):
    """Init sensor."""
    OctopusEnergyGasSensor.__init__(self, hass, meter, point)

    self.entity_id = generate_entity_id("text.{}", self.unique_id, hass=hass)

    self._hass = hass

    self._client = client
    self._tariff_code = tariff_code
    self._attr_native_value = tariff_code
    self._account_id = account_id
  
  @property
  def entity_registry_enabled_default(self) -> bool:
    """Return if the entity should be enabled when first added.

    This only applies when fist added to the entity registry.
    """
    return False

  @property
  def unique_id(self):
    """The id of the sensor."""
    return f"octopus_energy_gas_{self._serial_number}_{self._mprn}_previous_accumulative_cost_override_tariff"
    
  @property
  def name(self):
    """Name of the sensor."""
    return f"Previous Cost Override Tariff Gas ({self._serial_number}/{self._mprn})"
  
  @property
  def icon(self):
    """Icon of the sensor."""
    return "mdi:currency-gbp"

  async def async_set_value(self, value: str) -> None:
    """Update the value."""
    result = await check_tariff_override_valid(self._client, self._tariff_code, value)
    if (result is not None):
      raise Exception(result)

    self._attr_native_value = value
    self._hass.data[DOMAIN][self._account_id][get_gas_tariff_override_key(self._serial_number, self._mprn)] = value
    self.async_write_ha_state()
    await self.async_check_is_used()

  async def async_added_to_hass(self):
    """Call when entity about to be added to hass."""
    # If not None, we got an initial value.
    await super().async_added_to_hass()
    state = await self.async_get_last_state()
    
    if state is not None:

      if state.state is not None:
        self._attr_native_value = state.state
        self._attr_state = state.state
        self._hass.data[DOMAIN][self._account_id][get_gas_tariff_override_key(self._serial_number, self._mprn)] = self._attr_native_value
      
      self._attributes = dict_to_typed_dict(state.attributes)
    
      _LOGGER.debug(f'Restored OctopusEnergyPreviousAccumulativeGasCostTariffOverride state: {self._attr_state}')

    await self.async_check_is_used()

  async def async_check_is_used(self):
    key = f"cost_override_obsolete_{self._serial_number}_{self._mprn}"
    if self._tariff_code != self._attr_native_value:
      ir.async_create_issue(
        self._hass,
        DOMAIN,
        key,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        learn_more_url="https://bottlecapdave.github.io/HomeAssistant-OctopusEnergy/repairs/cost_override_obsolete",
        translation_key="cost_override_obsolete",
        translation_placeholders={ "type": "gas", "account_id": self._account_id, "mpan_mprn": self._mprn, "serial_number": self._serial_number },
      )
    else:
      ir.async_delete_issue(self._hass, DOMAIN, key)