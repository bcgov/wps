import { GridPreProcessEditCellProps, GridValueFormatterParams } from '@mui/x-data-grid-pro'
import { DEFAULT_COLUMN_WIDTH } from 'features/moreCast2/components/ColumnDefBuilder'
import {
  StationForecastField,
  DateForecastField,
  tempForecastField,
  rhForecastField,
  windDirForecastField,
  windSpeedForecastField,
  precipForecastField,
  gcForecastField
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
      expect(tempForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: tempForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerAlign: 'center',
          headerName: tempForecastField.headerName,
          sortable: false,
          type: tempForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should have correct validation logic', () => {
      expect(tempForecastField.validator && tempForecastField.validator('61')).toEqual(
        'Temp must be between -60°C and 60°C'
      )

      expect(tempForecastField.validator && tempForecastField.validator('-61')).toEqual(
        'Temp must be between -60°C and 60°C'
      )

      expect(tempForecastField.validator && tempForecastField.validator('0')).toEqual('')
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
          headerAlign: 'center',
          headerName: rhForecastField.headerName,
          sortable: false,
          type: rhForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should have correct validation logic', () => {
      expect(rhForecastField.validator && rhForecastField.validator('101')).toEqual('RH must be between 0 and 100')

      expect(rhForecastField.validator && rhForecastField.validator('-1')).toEqual('RH must be between 0 and 100')

      expect(rhForecastField.validator && rhForecastField.validator('0')).toEqual('')
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
          headerAlign: 'center',
          headerName: windDirForecastField.headerName,
          sortable: false,
          type: windDirForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should have correct validation logic', () => {
      expect(windDirForecastField.validator && windDirForecastField.validator('361')).toEqual(
        'Wind direction must be between 0 and 360 degrees'
      )

      expect(windDirForecastField.validator && windDirForecastField.validator('-1')).toEqual(
        'Wind direction must be between 0 and 360 degrees'
      )

      expect(windDirForecastField.validator && windDirForecastField.validator('0')).toEqual('')
    })
  })
  describe('WindSpeedForecastField', () => {
    it('should have the desired configuration', () => {
      const instance = windSpeedForecastField
      expect(windSpeedForecastField.precision).toEqual(0)
      expect(JSON.stringify(instance.generateColDef())).toEqual(
        JSON.stringify({
          field: windSpeedForecastField.field,
          disableColumnMenu: true,
          disableReorder: true,
          headerAlign: 'center',
          headerName: windSpeedForecastField.headerName,
          sortable: false,
          type: windSpeedForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should have correct validation logic', () => {
      expect(windSpeedForecastField.validator && windSpeedForecastField.validator('121')).toEqual(
        'Wind speed must be between 0 and 120 kph'
      )

      expect(windSpeedForecastField.validator && windSpeedForecastField.validator('-1')).toEqual(
        'Wind speed must be between 0 and 120 kph'
      )

      expect(windSpeedForecastField.validator && windSpeedForecastField.validator('0')).toEqual('')
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
          headerAlign: 'center',
          headerName: precipForecastField.headerName,
          sortable: false,
          type: precipForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should have correct validation logic', () => {
      expect(precipForecastField.validator && precipForecastField.validator('201')).toEqual(
        'Precip must be between 0 and 200 mm'
      )

      expect(precipForecastField.validator && precipForecastField.validator('-1')).toEqual(
        'Precip must be between 0 and 200 mm'
      )

      expect(precipForecastField.validator && precipForecastField.validator('0')).toEqual('')
    })
  })
  describe('GrassCuringForecastField', () => {
    it('should have correct validation logic', () => {
      expect(gcForecastField.validator && gcForecastField.validator('101')).toEqual(
        'Grass curing must be between 0 and 100'
      )

      expect(gcForecastField.validator && gcForecastField.validator('-1')).toEqual(
        'Grass curing must be between 0 and 100'
      )

      expect(gcForecastField.validator && gcForecastField.validator('0')).toEqual('')
    })
  })
})
