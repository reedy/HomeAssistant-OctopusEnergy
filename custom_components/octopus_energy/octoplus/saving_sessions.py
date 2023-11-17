import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import generate_entity_id

from homeassistant.util.dt import (now)
from homeassistant.helpers.update_coordinator import (
  CoordinatorEntity
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.helpers.restore_state import RestoreEntity

from . import (
  current_saving_sessions_event,
  get_next_saving_sessions_event
)

from ..coordinators.saving_sessions import SavingSessionsCoordinatorResult
from ..utils.attributes import dict_to_typed_dict

_LOGGER = logging.getLogger(__name__)

class OctopusEnergySavingSessions(CoordinatorEntity, BinarySensorEntity, RestoreEntity):
  """Sensor for determining if a saving session is active."""

  def __init__(self, hass: HomeAssistant, coordinator, account_id: str):
    """Init sensor."""

    CoordinatorEntity.__init__(self, coordinator)
  
    self._account_id = account_id
    self._state = None
    self._events = []
    self._attributes = {
      "current_joined_event_start": None,
      "current_joined_event_end": None,
      "current_joined_event_duration_in_minutes": None,
      "next_joined_event_start": None,
      "next_joined_event_end": None,
      "next_joined_event_duration_in_minutes": None
    }

    self.entity_id = generate_entity_id("binary_sensor.{}", self.unique_id, hass=hass)

  @property
  def unique_id(self):
    """The id of the sensor."""
    return f"octopus_energy_{self._account_id}_octoplus_saving_sessions"
    
  @property
  def name(self):
    """Name of the sensor."""
    return f"Octopus Energy {self._account_id} Octoplus Saving Session"

  @property
  def icon(self):
    """Icon of the sensor."""
    return "mdi:leaf"

  @property
  def extra_state_attributes(self):
    """Attributes of the sensor."""
    return self._attributes

  @property
  def is_on(self):
    """Determine if the user is in a saving session."""
    saving_session: SavingSessionsCoordinatorResult = self.coordinator.data if self.coordinator is not None else None
    if (saving_session is not None):
      self._events = saving_session.joined_events
    else:
      self._events = []
    
    self._attributes = {
      "current_joined_event_start": None,
      "current_joined_event_end": None,
      "current_joined_event_duration_in_minutes": None,
      "next_joined_event_start": None,
      "next_joined_event_end": None,
      "next_joined_event_duration_in_minutes": None
    }

    current_date = now()
    current_event = current_saving_sessions_event(current_date, self._events)
    if (current_event is not None):
      self._state = True
      self._attributes["current_joined_event_start"] = current_event.start
      self._attributes["current_joined_event_end"] = current_event.end
      self._attributes["current_joined_event_duration_in_minutes"] = current_event.duration_in_minutes
    else:
      self._state = False

    next_event = get_next_saving_sessions_event(current_date, self._events)
    if (next_event is not None):
      self._attributes["next_joined_event_start"] = next_event.start
      self._attributes["next_joined_event_end"] = next_event.end
      self._attributes["next_joined_event_duration_in_minutes"] = next_event.duration_in_minutes

    return self._state

  async def async_added_to_hass(self):
    """Call when entity about to be added to hass."""
    # If not None, we got an initial value.
    await super().async_added_to_hass()
    state = await self.async_get_last_state()

    if state is not None:
      self._state = state.state
      self._attributes = dict_to_typed_dict(state.attributes)
    
    if (self._state is None):
      self._state = False
    
    _LOGGER.debug(f'Restored state: {self._state}')
