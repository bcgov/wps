import { GridValueFormatterParams } from '@mui/x-data-grid'
import {
  StationForecastField,
  DateForecastField,
  TempForecastField,
  RHForecastField,
  WindDirForecastField,
  WindSpeedForecastField,
  PrecipForecastField
} from 'features/moreCast2/components/MoreCast2Field'
import { DateTime } from 'luxon'

describe('MoreCast2Field', () => {
  describe('StationForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = StationForecastField.getInstance()
      expect(instance.field).toEqual('stationName')
      expect(instance.headerName).toEqual('Station')
      expect(instance.precision).toEqual(0) // Unused for station, doesn't really matter
      expect(instance.type).toBe('string')
      expect(instance.generateColDef()).toEqual({ field: 'stationName', flex: 1, headerName: 'Station', maxWidth: 200 })
    })
  })
  describe('DateForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = DateForecastField.getInstance()
      expect(instance.field).toEqual('forDate')
      expect(instance.headerName).toEqual('Date')
      expect(instance.precision).toEqual(0) // Unused for station, doesn't really matter
      expect(instance.type).toBe('string')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
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
      expect(instance.field).toEqual('rh')
      expect(instance.headerName).toEqual('RH')
      expect(instance.precision).toEqual(0)
      expect(instance.type).toBe('number')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
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
      expect(instance.field).toEqual('windDirection')
      expect(instance.headerName).toEqual('Wind Dir')
      expect(instance.precision).toEqual(0)
      expect(instance.type).toBe('number')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
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
      expect(instance.field).toEqual('windSpeed')
      expect(instance.headerName).toEqual('Wind Speed')
      expect(instance.precision).toEqual(1)
      expect(instance.type).toBe('number')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
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
      expect(instance.field).toEqual('precip')
      expect(instance.headerName).toEqual('Precip')
      expect(instance.precision).toEqual(1)
      expect(instance.type).toBe('number')
      expect(JSON.stringify(instance.generateColDef())).toEqual(
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
