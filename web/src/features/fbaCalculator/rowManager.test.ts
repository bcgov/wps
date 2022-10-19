import { FBAStation } from 'api/fbaCalcAPI'
import { FBATableRow, RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'

describe('RowManager', () => {
  const firstInputRow = {
    id: 0,
    weatherStation: { value: '322', label: 'AFTON' },
    fuelType: { value: 'c1', label: 'C1' },
    grassCure: 1,
    windSpeed: 1,
    wind_speed: undefined
  }

  const firstCalculatedRow = {
    id: 0,
    station_code: 322,
    station_name: 'AFTON',
    zone_code: 'a',
    date: '',
    elevation: 1,
    fuel_type: 'c1',
    status: 'a',
    temp: 1,
    rh: 1,
    wind_direction: 1,
    wind_speed: 1,
    precipitation: 1,
    grass_cure: 1,
    fine_fuel_moisture_code: 1,
    drought_code: 1,
    initial_spread_index: 1,
    build_up_index: 1,
    duff_moisture_code: 1,
    fire_weather_index: 1,
    head_fire_intensity: 1,
    critical_hours_hfi_4000: { start: 9.0, end: 2.0 },
    critical_hours_hfi_10000: { start: 14.0, end: 18.0 },
    rate_of_spread: 1,
    fire_type: 'a',
    percentage_crown_fraction_burned: 1,
    flame_length: 1,
    sixty_minute_fire_size: 1,
    thirty_minute_fire_size: 1
  }

  const secondInputRow = {
    id: 1,
    station_code: 2,
    weatherStation: { value: '209', label: 'ALEXIS CREEK' },
    fuelType: { value: 'c2', label: 'C2' },
    grassCure: 2,
    windSpeed: 2,
    wind_speed: undefined
  }

  const secondCalculatedRow = {
    id: 1,
    station_code: 209,
    station_name: 'ALEXIS CREEK',
    zone_code: 'b',
    date: '',
    elevation: 2,
    fuel_type: 'c2',
    status: 'b',
    temp: 2,
    rh: 2,
    wind_direction: 2,
    wind_speed: 2,
    precipitation: 2,
    grass_cure: 2,
    fine_fuel_moisture_code: 2,
    drought_code: 2,
    initial_spread_index: 2,
    build_up_index: 2,
    duff_moisture_code: 2,
    fire_weather_index: 2,
    head_fire_intensity: 2,
    critical_hours_hfi_4000: { start: 14.0, end: 19.0 },
    critical_hours_hfi_10000: { start: 15.0, end: 18.0 },
    rate_of_spread: 2,
    fire_type: 'b',
    percentage_crown_fraction_burned: 2,
    flame_length: 2,
    sixty_minute_fire_size: 2,
    thirty_minute_fire_size: 2
  }

  const emptyInputRow = {
    id: 2,
    weatherStation: null,
    fuelType: null,
    grassCure: undefined,
    windSpeed: undefined,
    wind_speed: undefined
  }

  const emptyCalculatedRow: Partial<FBAStation> = {
    id: 2,
    station_code: 1,
    station_name: undefined,
    zone_code: undefined,
    elevation: undefined,
    fuel_type: undefined,
    status: undefined,
    temp: undefined,
    rh: undefined,
    wind_direction: undefined,
    wind_speed: undefined,
    precipitation: undefined,
    grass_cure: undefined,
    fine_fuel_moisture_code: undefined,
    drought_code: undefined,
    initial_spread_index: undefined,
    build_up_index: undefined,
    duff_moisture_code: undefined,
    fire_weather_index: undefined,
    head_fire_intensity: undefined,
    critical_hours_hfi_4000: undefined,
    critical_hours_hfi_10000: undefined,
    rate_of_spread: undefined,
    fire_type: undefined,
    percentage_crown_fraction_burned: undefined,
    flame_length: undefined,
    thirty_minute_fire_size: undefined,
    sixty_minute_fire_size: undefined
  }

  const inputRows = [emptyInputRow, firstInputRow, secondInputRow]

  const calculatedRows = [emptyCalculatedRow, firstCalculatedRow, secondCalculatedRow]
  it('should merge input rows and calculated rows correctly', () => {
    const nonEmptyInputRows = [firstInputRow, secondInputRow]
    const nonEmptyCalculatedRows = [firstCalculatedRow, secondCalculatedRow]
    const mergedRows = RowManager.updateRows(nonEmptyInputRows, nonEmptyCalculatedRows)

    // Maintains row order
    expect(mergedRows[0].id).toBe(nonEmptyInputRows[0].id)
    expect(mergedRows[1].id).toBe(nonEmptyInputRows[1].id)

    // Sets calculated values
    expect(mergedRows[0].wind_speed).toEqual(nonEmptyCalculatedRows[0].wind_speed)
    expect(mergedRows[0].windSpeed).toEqual(nonEmptyCalculatedRows[0].wind_speed)

    // Set values remain
    expect(mergedRows[0].windSpeed).toEqual(nonEmptyInputRows[0].windSpeed)

    // Builds GridMenuOptions based on user selected options
    expect(mergedRows[0].weatherStation).toEqual({
      value: nonEmptyInputRows[0].weatherStation?.value,
      label: nonEmptyInputRows[0].weatherStation?.label
    })
    expect(mergedRows[0].fuelType).toEqual({
      value: nonEmptyInputRows[0].fuelType?.value,
      label: nonEmptyInputRows[0].fuelType?.label
    })

    // No rows are lost
    expect(mergedRows.length).toEqual(nonEmptyInputRows.length)
  })
  describe('Sorting columns', () => {
    let mergedRows: FBATableRow[]
    beforeEach(() => {
      // mergedRows = RowManager.updateRows(inputRows, calculatedRows)
    })
    it('sorts by zone code', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Zone, 'asc', mergedRows)
      expect(sortedRowsAsc[0].zone_code).toBe('a')
      expect(sortedRowsAsc[2].zone_code).toBe(emptyCalculatedRow.zone_code)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Zone, 'desc', mergedRows)
      expect(sortedRowsDesc[0].zone_code).toBe('b')
      expect(sortedRowsDesc[2].zone_code).toBe(emptyCalculatedRow.zone_code)
    })
    it('sorts by station name', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Station, 'asc', mergedRows)
      expect(sortedRowsAsc[0].station_name).toBe('AFTON')
      expect(sortedRowsAsc[2].station_name).toBe(emptyCalculatedRow.station_name)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Station, 'desc', mergedRows)
      expect(sortedRowsDesc[0].station_name).toBe('ALEXIS CREEK')
      expect(sortedRowsDesc[2].station_name).toBe(emptyCalculatedRow.station_name)
    })
    it('sorts by elevation', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Elevation, 'asc', mergedRows)
      expect(sortedRowsAsc[0].elevation).toBe(1)
      expect(sortedRowsAsc[2].elevation).toBe(emptyCalculatedRow.elevation)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Elevation, 'desc', mergedRows)
      expect(sortedRowsDesc[0].elevation).toBe(2)
      expect(sortedRowsDesc[2].elevation).toBe(emptyCalculatedRow.elevation)
    })
    it('sorts by fuel type', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FuelType, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fuel_type).toBe('c1')
      expect(sortedRowsAsc[2].fuel_type).toBe(emptyCalculatedRow.fuel_type)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FuelType, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fuel_type).toBe('c2')
      expect(sortedRowsDesc[2].fuel_type).toBe(emptyCalculatedRow.fuel_type)
    })
    it('sorts by grass cure', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.GrassCure, 'asc', mergedRows)
      expect(sortedRowsAsc[0].grass_cure).toBe(1)
      expect(sortedRowsAsc[2].grass_cure).toBe(emptyCalculatedRow.grass_cure)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.GrassCure, 'desc', mergedRows)
      expect(sortedRowsDesc[0].grass_cure).toBe(2)
      expect(sortedRowsDesc[2].grass_cure).toBe(emptyCalculatedRow.grass_cure)
    })
    it('sorts by status', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Status, 'asc', mergedRows)
      expect(sortedRowsAsc[0].status).toBe('a')
      expect(sortedRowsAsc[2].status).toBe(emptyCalculatedRow.status)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Status, 'desc', mergedRows)
      expect(sortedRowsDesc[0].status).toBe('b')
      expect(sortedRowsDesc[2].status).toBe(emptyCalculatedRow.status)
    })
    it('sorts by temperature', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Temperature, 'asc', mergedRows)
      expect(sortedRowsAsc[0].temp).toBe(1)
      expect(sortedRowsAsc[2].temp).toBe(emptyCalculatedRow.temp)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Temperature, 'desc', mergedRows)
      expect(sortedRowsDesc[0].temp).toBe(2)
      expect(sortedRowsDesc[2].temp).toBe(emptyCalculatedRow.temp)
    })
    it('sorts by rh', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.RelativeHumidity, 'asc', mergedRows)
      expect(sortedRowsAsc[0].rh).toBe(1)
      expect(sortedRowsAsc[2].rh).toBe(emptyCalculatedRow.rh)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.RelativeHumidity, 'desc', mergedRows)
      expect(sortedRowsDesc[0].rh).toBe(2)
      expect(sortedRowsDesc[2].rh).toBe(emptyCalculatedRow.rh)
    })
    it('sorts by wind direction', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.WindDirection, 'asc', mergedRows)
      expect(sortedRowsAsc[0].wind_direction).toBe(1)
      expect(sortedRowsAsc[2].wind_direction).toBe(emptyCalculatedRow.wind_direction)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.WindDirection, 'desc', mergedRows)
      expect(sortedRowsDesc[0].wind_direction).toBe(2)
      expect(sortedRowsDesc[2].wind_direction).toBe(emptyCalculatedRow.wind_direction)
    })
    it('sorts by wind speed', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.WindSpeed, 'asc', mergedRows)
      expect(sortedRowsAsc[0].wind_speed).toBe(1)
      expect(sortedRowsAsc[2].wind_speed).toBe(emptyCalculatedRow.wind_speed)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.WindSpeed, 'desc', mergedRows)
      expect(sortedRowsDesc[0].wind_speed).toBe(2)
      expect(sortedRowsDesc[2].wind_speed).toBe(emptyCalculatedRow.wind_speed)
    })

    it('sorts by precipitation', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Precipitation, 'asc', mergedRows)
      expect(sortedRowsAsc[0].precipitation).toBe(1)
      expect(sortedRowsAsc[2].precipitation).toBe(emptyCalculatedRow.precipitation)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Precipitation, 'desc', mergedRows)
      expect(sortedRowsDesc[0].precipitation).toBe(2)
      expect(sortedRowsDesc[2].precipitation).toBe(emptyCalculatedRow.precipitation)
    })

    it('sorts by ffmc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FFMC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fine_fuel_moisture_code).toBe(1)
      expect(sortedRowsAsc[2].fine_fuel_moisture_code).toBe(emptyCalculatedRow.fine_fuel_moisture_code)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FFMC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fine_fuel_moisture_code).toBe(2)
      expect(sortedRowsDesc[2].fine_fuel_moisture_code).toBe(emptyCalculatedRow.fine_fuel_moisture_code)
    })
    it('sorts by dmc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.DMC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].duff_moisture_code).toBe(1)
      expect(sortedRowsAsc[2].duff_moisture_code).toBe(emptyCalculatedRow.duff_moisture_code)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.DMC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].duff_moisture_code).toBe(2)
      expect(sortedRowsDesc[2].duff_moisture_code).toBe(emptyCalculatedRow.duff_moisture_code)
    })
    it('sorts by dc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.DC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].drought_code).toBe(1)
      expect(sortedRowsAsc[2].drought_code).toBe(emptyCalculatedRow.drought_code)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.DC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].drought_code).toBe(2)
      expect(sortedRowsDesc[2].drought_code).toBe(emptyCalculatedRow.drought_code)
    })

    it('sorts by isi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.ISI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].initial_spread_index).toBe(1)
      expect(sortedRowsAsc[2].initial_spread_index).toBe(emptyCalculatedRow.initial_spread_index)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.ISI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].initial_spread_index).toBe(2)
      expect(sortedRowsDesc[2].initial_spread_index).toBe(emptyCalculatedRow.initial_spread_index)
    })
    it('sorts by bui', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.BUI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].build_up_index).toBe(1)
      expect(sortedRowsAsc[2].build_up_index).toBe(emptyCalculatedRow.build_up_index)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.BUI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].build_up_index).toBe(2)
      expect(sortedRowsDesc[2].build_up_index).toBe(emptyCalculatedRow.build_up_index)
    })
    it('sorts by fwi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FWI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fire_weather_index).toBe(1)
      expect(sortedRowsAsc[2].fire_weather_index).toBe(emptyCalculatedRow.fire_weather_index)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FWI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fire_weather_index).toBe(2)
      expect(sortedRowsDesc[2].fire_weather_index).toBe(emptyCalculatedRow.fire_weather_index)
    })

    it('sorts by hfi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.HFI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].head_fire_intensity).toBe(1)
      expect(sortedRowsAsc[2].head_fire_intensity).toBe(emptyCalculatedRow.head_fire_intensity)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.HFI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].head_fire_intensity).toBe(2)
      expect(sortedRowsDesc[2].head_fire_intensity).toBe(emptyCalculatedRow.head_fire_intensity)
    })

    it('sorts by 4000 kW/m critical hours', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.CriticalHours4000, 'asc', mergedRows)
      expect(sortedRowsAsc[0].critical_hours_hfi_4000).toStrictEqual({
        end: 19,
        start: 14
      })
      expect(sortedRowsAsc[2].critical_hours_hfi_4000).toStrictEqual(emptyCalculatedRow.critical_hours_hfi_4000)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.CriticalHours4000, 'desc', mergedRows)
      expect(sortedRowsDesc[0].critical_hours_hfi_4000).toStrictEqual({
        start: 9,
        end: 2
      })
      expect(sortedRowsDesc[2].critical_hours_hfi_4000).toBe(emptyCalculatedRow.critical_hours_hfi_4000)
    })

    it('sorts by 10000 kW/m critical hours', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.CriticalHours10000, 'asc', mergedRows)
      expect(sortedRowsAsc[0].critical_hours_hfi_10000).toStrictEqual({
        start: 15.0,
        end: 18.0
      })
      expect(sortedRowsAsc[2].critical_hours_hfi_10000).toStrictEqual(emptyCalculatedRow.critical_hours_hfi_10000)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.CriticalHours10000, 'desc', mergedRows)
      expect(sortedRowsDesc[0].critical_hours_hfi_10000).toStrictEqual({
        start: 14.0,
        end: 18.0
      })
      expect(sortedRowsDesc[2].critical_hours_hfi_10000).toBe(emptyCalculatedRow.critical_hours_hfi_10000)
    })

    it('sorts by 30 minute fire size', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.ThirtyMinFireSize, 'asc', mergedRows)
      expect(sortedRowsAsc[0].thirty_minute_fire_size).toBe(1)
      expect(sortedRowsAsc[2].thirty_minute_fire_size).toBe(emptyCalculatedRow.thirty_minute_fire_size)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.ThirtyMinFireSize, 'desc', mergedRows)
      expect(sortedRowsDesc[0].thirty_minute_fire_size).toBe(2)
      expect(sortedRowsDesc[2].thirty_minute_fire_size).toBe(emptyCalculatedRow.thirty_minute_fire_size)
    })
    it('sorts by 60 minute fire size', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.SixtyMinFireSize, 'asc', mergedRows)
      expect(sortedRowsAsc[0].sixty_minute_fire_size).toBe(1)
      expect(sortedRowsAsc[2].sixty_minute_fire_size).toBe(emptyCalculatedRow.sixty_minute_fire_size)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.SixtyMinFireSize, 'desc', mergedRows)
      expect(sortedRowsDesc[0].sixty_minute_fire_size).toBe(2)
      expect(sortedRowsDesc[2].sixty_minute_fire_size).toBe(emptyCalculatedRow.sixty_minute_fire_size)
    })
    it('sorts by rate of spread', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.ROS, 'asc', mergedRows)
      expect(sortedRowsAsc[0].rate_of_spread).toBe(1)
      expect(sortedRowsAsc[2].rate_of_spread).toBe(emptyCalculatedRow.rate_of_spread)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.ROS, 'desc', mergedRows)
      expect(sortedRowsDesc[0].rate_of_spread).toBe(2)
      expect(sortedRowsDesc[2].rate_of_spread).toBe(emptyCalculatedRow.rate_of_spread)
    })
    it('sorts by fire type', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FireType, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fire_type).toBe('a')
      expect(sortedRowsAsc[2].fire_type).toBe(emptyCalculatedRow.fire_type)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FireType, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fire_type).toBe('b')
      expect(sortedRowsDesc[2].fire_type).toBe(emptyCalculatedRow.fire_type)
    })
    it('sorts by crown fire burned percentage', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.CFB, 'asc', mergedRows)
      expect(sortedRowsAsc[0].percentage_crown_fraction_burned).toBe(1)
      expect(sortedRowsAsc[2].percentage_crown_fraction_burned).toBe(
        emptyCalculatedRow.percentage_crown_fraction_burned
      )

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.CFB, 'desc', mergedRows)
      expect(sortedRowsDesc[0].percentage_crown_fraction_burned).toBe(2)
      expect(sortedRowsDesc[2].percentage_crown_fraction_burned).toBe(
        emptyCalculatedRow.percentage_crown_fraction_burned
      )
    })
    it('sorts by flame length', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FlameLength, 'asc', mergedRows)
      expect(sortedRowsAsc[0].flame_length).toBe(1)
      expect(sortedRowsAsc[2].flame_length).toBe(emptyCalculatedRow.flame_length)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FlameLength, 'desc', mergedRows)
      expect(sortedRowsDesc[0].flame_length).toBe(2)
      expect(sortedRowsDesc[2].flame_length).toBe(emptyCalculatedRow.flame_length)
    })
  })
})
