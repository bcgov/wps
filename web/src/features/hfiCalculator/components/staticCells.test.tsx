import { isError } from 'features/hfiCalculator/components/StaticCells'
import { FuelType, StationDaily } from 'api/hfiCalculatorAPI'
import { DateTime } from 'luxon'

describe('StaticCells', () => {
  it('should return isError = true if a fire index is null', () => {
    const fuelType: FuelType = {
      id: 1,
      abbrev: 'C1',
      description: 'C1',
      fuel_type_code: 'C1',
      percentage_conifer: 50,
      percentage_dead_fir: 50
    }
    const daily: StationDaily = {
      code: 322,
      status: 'FORECAST',
      temperature: 10,
      relative_humidity: 40,
      wind_speed: 5.0,
      wind_direction: 100,
      grass_cure_percentage: 1,
      precipitation: 0.0,
      ffmc: 1,
      dc: 1,
      bui: null,
      dmc: 12,
      isi: 10,
      fwi: 1,
      danger_class: 1,
      rate_of_spread: 0.5,
      hfi: 2,
      observation_valid: true,
      observation_valid_comment: '',
      intensity_group: 1,
      sixty_minute_fire_size: 0,
      fire_type: 'SUR',
      date: DateTime.fromObject({ year: 2021, month: 1, day: 1 }),
      last_updated: DateTime.fromObject({ year: 2021, month: 1, day: 1 })
    }
    expect(isError(daily, fuelType)).toEqual(true)
  })
})
