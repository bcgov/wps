import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { FBCTableRow, RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'
describe('RowManager', () => {
  const stationCodeMap = new Map<string, string>()
  stationCodeMap.set('322', 'AFTON')
  stationCodeMap.set('209', 'ALEXIS CREEK')
  const rowManager = new RowManager(stationCodeMap)

  const firstInputRow = {
    id: 0,
    weatherStation: '322',
    fuelType: 'c1',
    grassCure: 1,
    windSpeed: 1
  }

  const firstCalculatedRow = {
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
    critical_hours_hfi_4000: '',
    critical_hours_hfi_10000: '',
    rate_of_spread: 1,
    fire_type: 'a',
    percentage_crown_fraction_burned: 1,
    flame_length: 1,
    sixty_minute_fire_size: 1,
    thirty_minute_fire_size: 1
  }

  const secondInputRow = {
    id: 1,
    weatherStation: '209',
    fuelType: 'c2',
    grassCure: 2,
    windSpeed: 2
  }

  const secondCalculatedRow = {
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
    critical_hours_hfi_4000: '',
    critical_hours_hfi_10000: '',
    rate_of_spread: 2,
    fire_type: 'b',
    percentage_crown_fraction_burned: 2,
    flame_length: 2,
    sixty_minute_fire_size: 2,
    thirty_minute_fire_size: 2
  }

  const inputRows = [firstInputRow, secondInputRow]

  const calculatedRows = [firstCalculatedRow, secondCalculatedRow]
  it('should merge input rows and calculated rows in correctly', () => {
    const mergedRows = rowManager.mergeFBARows(inputRows, calculatedRows)

    // Maintains row order
    expect(mergedRows[0].id).toBe(inputRows[0].id)
    expect(mergedRows[1].id).toBe(inputRows[1].id)

    // Sets calculated values
    expect(mergedRows[0].wind_speed).toEqual(calculatedRows[0].wind_speed)

    // Builds GridMenuOptions based on user selected options
    expect(mergedRows[0].weatherStation).toEqual({
      value: inputRows[0].weatherStation,
      label: stationCodeMap.get(inputRows[0].weatherStation)
    })
    expect(mergedRows[0].fuelType).toEqual({
      value: inputRows[0].fuelType,
      label: FuelTypes.lookup(inputRows[0].fuelType)?.friendlyName
    })
  })
  describe('Sorting columns', () => {
    let mergedRows: FBCTableRow[]
    beforeEach(() => {
      mergedRows = rowManager.mergeFBARows(inputRows, calculatedRows)
    })
    it('sorts by zone code', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Zone, 'asc', mergedRows)
      expect(sortedRowsAsc[0].zone_code).toBe('a')

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Zone, 'desc', mergedRows)
      expect(sortedRowsDesc[0].zone_code).toBe('b')
    })
    it('sorts by station name', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Station, 'asc', mergedRows)
      expect(sortedRowsAsc[0].station_name).toBe('AFTON')

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Station, 'desc', mergedRows)
      expect(sortedRowsDesc[0].station_name).toBe('ALEXIS CREEK')
    })
    it('sorts by elevation', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Elevation, 'asc', mergedRows)
      expect(sortedRowsAsc[0].elevation).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.Elevation,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].elevation).toBe(2)
    })
    it('sorts by fuel type', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FuelType, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fuel_type).toBe('c1')

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.FuelType,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].fuel_type).toBe('c2')
    })
    it('sorts by grass cure', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.GrassCure, 'asc', mergedRows)
      expect(sortedRowsAsc[0].grass_cure).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.GrassCure,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].grass_cure).toBe(2)
    })
    it('sorts by status', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Status, 'asc', mergedRows)
      expect(sortedRowsAsc[0].status).toBe('a')

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Status, 'desc', mergedRows)
      expect(sortedRowsDesc[0].status).toBe('b')
    })
    it('sorts by temperatue', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.Temperature,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].temp).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.Temperature,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].temp).toBe(2)
    })
    it('sorts by rh', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.RelativeHumidity,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].rh).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.RelativeHumidity,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].rh).toBe(2)
    })
    it('sorts by wind direction', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.WindDirection,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].wind_direction).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.WindDirection,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].wind_direction).toBe(2)
    })
    it('sorts by wind speed', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.WindSpeed, 'asc', mergedRows)
      expect(sortedRowsAsc[0].wind_speed).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.WindSpeed,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].wind_speed).toBe(2)
    })

    it('sorts by precipitation', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.Precipitation,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].precipitation).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.Precipitation,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].precipitation).toBe(2)
    })

    it('sorts by ffmc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FFMC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fine_fuel_moisture_code).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FFMC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fine_fuel_moisture_code).toBe(2)
    })
    it('sorts by dmc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.DMC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].duff_moisture_code).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.DMC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].duff_moisture_code).toBe(2)
    })
    it('sorts by dc', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.DC, 'asc', mergedRows)
      expect(sortedRowsAsc[0].drought_code).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.DC, 'desc', mergedRows)
      expect(sortedRowsDesc[0].drought_code).toBe(2)
    })

    it('sorts by isi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.ISI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].initial_spread_index).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.ISI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].initial_spread_index).toBe(2)
    })
    it('sorts by bui', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.BUI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].build_up_index).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.BUI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].build_up_index).toBe(2)
    })
    it('sorts by fwi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.FWI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].fire_weather_index).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.FWI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].fire_weather_index).toBe(2)
    })

    it('sorts by hfi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.HFI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].head_fire_intensity).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.HFI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].head_fire_intensity).toBe(2)
    })
    it('sorts by 30 minute fire size', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.ThirtyMinFireSize,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].thirty_minute_fire_size).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.ThirtyMinFireSize,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].thirty_minute_fire_size).toBe(2)
    })
    it('sorts by 60 minute fire size', () => {
      const sortedRowsAsc = RowManager.sortRows(
        SortByColumn.SixtyMinFireSize,
        'asc',
        mergedRows
      )
      expect(sortedRowsAsc[0].sixty_minute_fire_size).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(
        SortByColumn.SixtyMinFireSize,
        'desc',
        mergedRows
      )
      expect(sortedRowsDesc[0].sixty_minute_fire_size).toBe(2)
    })
  })
})
