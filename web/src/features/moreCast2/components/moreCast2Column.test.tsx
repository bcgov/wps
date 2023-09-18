import { GridValueFormatterParams } from '@mui/x-data-grid'
import { DEFAULT_COLUMN_WIDTH } from 'features/moreCast2/components/ColumnDefBuilder'
import {
  StationForecastField,
  DateForecastField,
  tempForecastField,
  rhForecastField,
  windDirForecastField,
  windSpeedForecastField,
  precipForecastField
} from 'features/moreCast2/components/MoreCast2Column'
import { DateTime } from 'luxon'

describe('MoreCast2Column', () => {
  describe('StationForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = StationForecastField.getInstance()
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: 'stationName',
          flex: 1,
          headerName: 'Station',
          maxWidth: 200,
          minWidth: 200,
          width: 200,
          valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
            return params.value.toLocaleString(DateTime.DATE_MED)
          }
        })
      )
    })
  })
  describe('DateForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = DateForecastField.getInstance()
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: 'forDate',
          disableColumnMenu: true,
          disableReorder: true,
          flex: 1,
          headerName: 'Date',
          maxWidth: 150,
          minWidth: 150,
          width: 150,
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
      const instance = tempForecastField
      expect(tempForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: tempForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: tempForecastField.headerName,
          sortable: false,
          type: tempForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('RHForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = rhForecastField
      expect(rhForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: rhForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: rhForecastField.headerName,
          sortable: false,
          type: rhForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('WindDirForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = windDirForecastField
      expect(windDirForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: windDirForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: windDirForecastField.headerName,
          sortable: false,
          type: windDirForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('WindSpeedForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = windSpeedForecastField
      expect(windSpeedForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: windSpeedForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: windSpeedForecastField.headerName,
          sortable: false,
          type: windSpeedForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('PrecipForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = precipForecastField
      expect(precipForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: precipForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: precipForecastField.headerName,
          sortable: false,
          type: precipForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
})
