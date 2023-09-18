import { GridValueFormatterParams } from '@mui/x-data-grid'
import { DEFAULT_COLUMN_WIDTH } from 'features/moreCast2/components/ColumnDefBuilder'
import {
  StationForecastField,
  DateForecastField,
  TempForecastField,
  RHForecastField,
  WindDirForecastField,
  WindSpeedForecastField,
  PrecipForecastField
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
      const instance = TempForecastField
      expect(TempForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: TempForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: TempForecastField.headerName,
          sortable: false,
          type: TempForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('RHForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = RHForecastField
      expect(RHForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: RHForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: RHForecastField.headerName,
          sortable: false,
          type: RHForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('WindDirForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = WindDirForecastField
      expect(WindDirForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: WindDirForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: WindDirForecastField.headerName,
          sortable: false,
          type: WindDirForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('WindSpeedForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = WindSpeedForecastField
      expect(WindSpeedForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: WindSpeedForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: WindSpeedForecastField.headerName,
          sortable: false,
          type: WindSpeedForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
  describe('PrecipForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = PrecipForecastField
      expect(PrecipForecastField.precision).toEqual(1)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: PrecipForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerName: PrecipForecastField.headerName,
          sortable: false,
          type: PrecipForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
  })
})
