import { GridValueFormatterParams } from '@mui/x-data-grid'
import {
  StationForecastField,
  DateForecastField,
  TempForecastField,
  RHForecastField,
  WindDirForecastField,
  WindSpeedForecastField,
  PrecipForecastField,
  Morecast2Field,
  Morecast2Field
} from 'features/moreCast2/components/MoreCast2Field'
import { DateTime } from 'luxon'

describe('MoreCast2Field', () => {
  const expectFields = (
    instance: Morecast2Field,
    field: Morecast2Field,
    headerName: string,
    precision: number,
    type: string,
    colDefJsonString: string
  ) => {
    expect(instance.field).toEqual(field)
    expect(instance.headerName).toEqual(headerName)
    expect(instance.precision).toEqual(precision)
    expect(instance.type).toBe(type)
    expect(JSON.stringify(instance.generateColDef())).toEqual(colDefJsonString)
  }
  describe('StationForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = StationForecastField.getInstance()
      expectFields(
        instance,
        'stationName',
        'Station',
        0,
        'string',
        JSON.stringify({ field: 'stationName', flex: 1, headerName: 'Station', maxWidth: 200 })
      )
    })
  })
  describe('DateForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = DateForecastField.getInstance()
      expectFields(
        instance,
        'forDate',
        'Date',
        0,
        'string',
        JSON.stringify({
          field: 'forDate',
          disableColumnMenu: true,
          disableReorder: true,
          flex: 1,
          headerName: 'Date',
          maxWidth: 250,
          sortable: false,
          valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
            return params.value.toLocaleString(DateTime.DATE_MED)
          }
        })
      )
    })
  })
  describe('TempForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = TempForecastField.getInstance()
      expect(instance.field).toEqual('temp')
      expect(instance.headerName).toEqual('Temp')
      expect(instance.precision).toEqual(1)
      expect(instance.type).toBe('number')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: 'temp',
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: 'Temp',
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })
  })
  describe('RHForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = RHForecastField.getInstance()
      expectFields(
        instance,
        'rh',
        'RH',
        0,
        'number',
        JSON.stringify({
          field: 'rh',
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: 'RH',
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })
  })
  describe('WindDirForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = WindDirForecastField.getInstance()
      expectFields(
        instance,
        'windDirection',
        'Wind Dir',
        0,
        'number',
        JSON.stringify({
          field: 'windDirection',
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: 'Wind Dir',
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })
  })
  describe('WindSpeedForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = WindSpeedForecastField.getInstance()
      expectFields(
        instance,
        'windSpeed',
        'Wind Speed',
        1,
        'number',
        JSON.stringify({
          field: 'windSpeed',
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: 'Wind Speed',
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })
  })
  describe('PrecipForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = PrecipForecastField.getInstance()
      expectFields(
        instance,
        'precip',
        'Precip',
        1,
        'number',
        JSON.stringify({
          field: 'precip',
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: 'Precip',
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })
  })
})
