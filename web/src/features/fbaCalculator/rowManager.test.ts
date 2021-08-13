import { FBCStation } from 'api/fbCalcAPI'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { FBCTableRow, RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'
describe('RowManager', () => {
  const stationCodeMap = new Map<string, string>()
  stationCodeMap.set('322', 'AFTON')
  stationCodeMap.set('209', 'ALEXIS CREEK')
  const rowManager = new RowManager(stationCodeMap)

  const buildFBCStation = (
    station_code: number,
    station_name: string,
    wind_speed: number,
    fuel_type: string,
    zone_code: string,
    isi: number,
    hfi: number
  ): FBCStation => ({
    station_code,
    station_name,
    zone_code,
    date: '',
    elevation: 0,
    fuel_type,
    status: '',
    temp: 0,
    rh: 0,
    wind_direction: 0,
    wind_speed,
    precipitation: 0,
    grass_cure: 0,
    fine_fuel_moisture_code: 0,
    drought_code: 0,
    initial_spread_index: isi,
    build_up_index: 0,
    duff_moisture_code: 0,
    fire_weather_index: 0,
    head_fire_intensity: hfi,
    critical_hours_hfi_4000: '',
    critical_hours_hfi_10000: '',
    rate_of_spread: 0,
    fire_type: '',
    percentage_crown_fraction_burned: 0,
    flame_length: 0,
    sixty_minute_fire_size: 0,
    thirty_minute_fire_size: 0
  })

  const buildInputRow = (
    id: number,
    weatherStation: string,
    fuelType: string,
    windSpeed?: number
  ) => ({
    id,
    weatherStation,
    fuelType,
    grassCure: undefined,
    windSpeed
  })

  const inputRows = [buildInputRow(0, '322', 'c1'), buildInputRow(1, '209', 'c2')]

  const calculatedRows = [
    buildFBCStation(322, 'AFTON', 1, 'c1', 'a', 1, 1),
    buildFBCStation(209, 'ALEXIS CREEK', 2, 'c2', 'b', 2, 2)
  ]
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
    it('sorts by weather station', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Station, 'asc', mergedRows)
      expect(sortedRowsAsc[0].station_name).toBe('AFTON')

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Station, 'desc', mergedRows)
      expect(sortedRowsDesc[0].station_name).toBe('ALEXIS CREEK')
    })
    it('sorts by zone code', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.Zone, 'asc', mergedRows)
      expect(sortedRowsAsc[0].zone_code).toBe('a')

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.Zone, 'desc', mergedRows)
      expect(sortedRowsDesc[0].zone_code).toBe('b')
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

    it('sorts by isi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.ISI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].initial_spread_index).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.ISI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].initial_spread_index).toBe(2)
    })
    it('sorts by hfi', () => {
      const sortedRowsAsc = RowManager.sortRows(SortByColumn.HFI, 'asc', mergedRows)
      expect(sortedRowsAsc[0].head_fire_intensity).toBe(1)

      const sortedRowsDesc = RowManager.sortRows(SortByColumn.HFI, 'desc', mergedRows)
      expect(sortedRowsDesc[0].head_fire_intensity).toBe(2)
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
  })
})
