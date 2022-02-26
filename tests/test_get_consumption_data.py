from datetime import datetime, timedelta
import pytest
import mock

from tests import (create_consumption_data, get_test_context)

from custom_components.octopus_energy.sensor_utils import async_get_consumption_data
from custom_components.octopus_energy.api_client import OctopusEnergyApiClient

@pytest.mark.asyncio
async def test_when_now_is_not_at_30_minute_mark_and_previous_data_is_available_then_previous_data_returned():
  # Arrange
  context = get_test_context()
  client = OctopusEnergyApiClient(context["api_key"])

  sensor_identifier = context["gas_mprn"]
  sensor_serial_number = context["gas_serial_number"]
  is_electricity = False
  
  period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  expected_result = []

  for minute in range(0, 59):
    if (minute == 0 or minute == 30):
      continue
    
    minuteStr = f'{minute}'.zfill(2)
    current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minuteStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

    store = {
      f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': expected_result
    }

    # Act
    result = await async_get_consumption_data(
      store,
      client,
      current_utc_timestamp,
      period_from,
      period_to,
      sensor_identifier,
      sensor_serial_number,
      is_electricity
    )

    # Assert
    assert result != None
    assert len(result) == 0

@pytest.mark.asyncio
@pytest.mark.parametrize("minutes",[
  (0),
  (30),
])
async def test_when_now_is_at_30_minute_mark_and_previous_data_is_in_requested_period_then_previous_data_returned(minutes):
  # Arrange
  context = get_test_context()
  client = OctopusEnergyApiClient(context["api_key"])

  sensor_identifier = context["gas_mprn"]
  sensor_serial_number = context["gas_serial_number"]
  is_electricity = False

  period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  expected_result = create_consumption_data(period_from, period_to)
    
  minutesStr = f'{minutes}'.zfill(2)
  current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minutesStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

  store = {
    f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': expected_result
  }

  # Act
  result = await async_get_consumption_data(
    store,
    client,
    current_utc_timestamp,
    period_from,
    period_to,
    sensor_identifier,
    sensor_serial_number,
    is_electricity
  )

  # Assert
  assert result != None
  assert len(result) == len(expected_result)

  # Make sure our data is returned in 30 minute increments
  expected_valid_from = period_from
  for item in result:
    expected_valid_to = expected_valid_from + timedelta(minutes=30)

    assert "interval_start" in item
    assert item["interval_start"] == expected_valid_from
    assert "interval_end" in item
    assert item["interval_end"] == expected_valid_to
    assert "consumption" in item
    assert item["consumption"] == 1

    expected_valid_from = expected_valid_to

@pytest.mark.asyncio
@pytest.mark.parametrize("minutes,previous_data_available",[
  (0, True),
  (0, False),
  (30, True),
  (30, False),
])
async def test_when_now_is_at_30_minute_mark_and_gas_sensor_then_requested_data_returned(minutes, previous_data_available):
  # Arrange
  context = get_test_context()
  client = OctopusEnergyApiClient(context["api_key"])

  sensor_identifier = context["gas_mprn"]
  sensor_serial_number = context["gas_serial_number"]
  is_electricity = False

  period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  previous_data = None
  if previous_data_available == True:
    # Make our previous data for the previous period
    previous_data = create_consumption_data(
      datetime.strptime("2022-02-09T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z"),
      datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    )
  
  minutesStr = f'{minutes}'.zfill(2)
  current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minutesStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

  store = {
    f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': previous_data
  }

  # Act
  result = await async_get_consumption_data(
    store,
    client,
    current_utc_timestamp,
    period_from,
    period_to,
    sensor_identifier,
    sensor_serial_number,
    is_electricity
  )

  # Assert
  assert result != None
  assert len(result) == 48

  # Make sure our data is returned in 30 minute increments
  expected_valid_from = period_from
  for item in result:
    expected_valid_to = expected_valid_from + timedelta(minutes=30)

    assert "interval_start" in item
    assert item["interval_start"] == expected_valid_from
    assert "interval_end" in item
    assert item["interval_end"] == expected_valid_to

    expected_valid_from = expected_valid_to

@pytest.mark.asyncio
@pytest.mark.parametrize("minutes,previous_data_available",[
  (0, True),
  (0, False),
  (30, True),
  (30, False),
])
async def test_when_now_is_at_30_minute_mark_and_electricity_sensor_then_requested_data_returned(minutes, previous_data_available):
  # Arrange
  context = get_test_context()
  client = OctopusEnergyApiClient(context["api_key"])

  sensor_identifier = context["electricity_mpan"]
  sensor_serial_number = context["electricity_serial_number"]
  is_electricity = True

  period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
  previous_data = None
  if previous_data_available == True:
    # Make our previous data for the previous period
    previous_data = create_consumption_data(
      datetime.strptime("2022-02-09T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z"),
      datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    )
  
  minutesStr = f'{minutes}'.zfill(2)
  current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minutesStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

  store = {
    f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': previous_data
  }

  # Act
  result = await async_get_consumption_data(
    store,
    client,
    current_utc_timestamp,
    period_from,
    period_to,
    sensor_identifier,
    sensor_serial_number,
    is_electricity
  )

  # Assert
  assert result != None
  assert len(result) == 48

  # Make sure our data is returned in 30 minute increments
  expected_valid_from = period_from
  for item in result:
    expected_valid_to = expected_valid_from + timedelta(minutes=30)

    assert "interval_start" in item
    assert item["interval_start"] == expected_valid_from
    assert "interval_end" in item
    assert item["interval_end"] == expected_valid_to

    expected_valid_from = expected_valid_to

async def async_mocked_client_consumption(*args, **kwargs):
  return []

@pytest.mark.asyncio
@pytest.mark.parametrize("minutes",[
  (0),
  (30),
])
async def test_when_now_is_at_30_minute_mark_and_gas_sensor_and_returned_data_is_empty_then_previous_data_returned(minutes):
  # Arrange
  context = get_test_context()

  with mock.patch.object(OctopusEnergyApiClient, 'async_get_gas_consumption', new=async_mocked_client_consumption):
    client = OctopusEnergyApiClient(context["api_key"])

    sensor_identifier = context["gas_mprn"]
    sensor_serial_number = context["gas_serial_number"]
    is_electricity = False

    period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")

    previous_period_from = datetime.strptime("2022-02-09T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    previous_period_to = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    previous_data = create_consumption_data(
      previous_period_from,
      previous_period_to
    )
    
    minutesStr = f'{minutes}'.zfill(2)
    current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minutesStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

    store = {
      f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': previous_data
    }

    # Act
    result = await async_get_consumption_data(
      store,
      client,
      current_utc_timestamp,
      period_from,
      period_to,
      sensor_identifier,
      sensor_serial_number,
      is_electricity
    )

    # Assert
    assert result != None
    assert len(result) == 48

    # Make sure our data is returned in 30 minute increments
    expected_valid_from = previous_period_from
    for item in result:
      expected_valid_to = expected_valid_from + timedelta(minutes=30)

      assert "interval_start" in item
      assert item["interval_start"] == expected_valid_from
      assert "interval_end" in item
      assert item["interval_end"] == expected_valid_to
      assert "consumption" in item
      assert item["consumption"] == 1

      expected_valid_from = expected_valid_to

@pytest.mark.asyncio
@pytest.mark.parametrize("minutes",[
  (0),
  (30),
])
async def test_when_now_is_at_30_minute_mark_and_electricity_sensor_and_returned_data_is_empty_then_previous_data_returned(minutes):
  # Arrange
  context = get_test_context()

  with mock.patch.object(OctopusEnergyApiClient, 'async_get_electricity_consumption', new=async_mocked_client_consumption):
    client = OctopusEnergyApiClient(context["api_key"])

    sensor_identifier = context["electricity_mpan"]
    sensor_serial_number = context["electricity_serial_number"]
    is_electricity = True

    period_from = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    period_to = datetime.strptime("2022-02-11T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")

    previous_period_from = datetime.strptime("2022-02-09T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    previous_period_to = datetime.strptime("2022-02-10T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
    previous_data = create_consumption_data(
      previous_period_from,
      previous_period_to
    )
    
    minutesStr = f'{minutes}'.zfill(2)
    current_utc_timestamp = datetime.strptime(f'2022-02-12T00:{minutesStr}:00Z', "%Y-%m-%dT%H:%M:%S%z")

    store = {
      f'{sensor_identifier}_{sensor_serial_number}_previous_consumption': previous_data
    }

    # Act
    result = await async_get_consumption_data(
      store,
      client,
      current_utc_timestamp,
      period_from,
      period_to,
      sensor_identifier,
      sensor_serial_number,
      is_electricity
    )

    # Assert
    assert result != None
    assert len(result) == 48

    # Make sure our data is returned in 30 minute increments
    expected_valid_from = previous_period_from
    for item in result:
      expected_valid_to = expected_valid_from + timedelta(minutes=30)

      assert "interval_start" in item
      assert item["interval_start"] == expected_valid_from
      assert "interval_end" in item
      assert item["interval_end"] == expected_valid_to
      assert "consumption" in item
      assert item["consumption"] == 1

      expected_valid_from = expected_valid_to