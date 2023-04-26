import { WeatherDeterminate } from 'api/moreCast2API'
import {
  ColumnDefBuilder,
  DEFAULT_COLUMN_WIDTH,
  ORDERED_COLUMN_HEADERS
} from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'
import { TempForecastField } from 'features/moreCast2/components/MoreCast2Column'

describe('ColDefBuilder', () => {
  const colDefBuilder = new ColumnDefBuilder(
    TempForecastField.field,
    TempForecastField.headerName,
    TempForecastField.type,
    TempForecastField.precision,
    new GridComponentRenderer()
  )

  const testField = 'testField'
  const testHeader = 'testHeader'
  const testPrecision = 1
  const testWidth = 1
  describe('generateColDef', () => {
    it('should generate the col def correctly', () => {
      const colDef = colDefBuilder.generateColDef()

      expect(JSON.stringify(colDef)).toEqual(
        JSON.stringify({
          field: 'temp',
          disableColumnMenu: true,
          disabledReorder: true,
          headerName: 'Temp',
          sortable: false,
          type: 'number',
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should generate all col defs correcty', () => {
      const colDefs = colDefBuilder.generateColDefs()

      const expected = [
        JSON.stringify({
          field: `${TempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: TempForecastField.headerName,
          sortable: false,
          type: 'number',
          width: DEFAULT_COLUMN_WIDTH
        })
      ].concat(
        ORDERED_COLUMN_HEADERS.map(determinate =>
          JSON.stringify({
            field: `${TempForecastField.field}${determinate}`,
            disableColumnMenu: true,
            disabledReorder: true,
            headerName: determinate,
            sortable: false,
            type: 'number',
            width: DEFAULT_COLUMN_WIDTH
          })
        )
      )

      expect(colDefs.map(def => JSON.stringify(def))).toEqual(expected)
    })

    it('should generate the col def correctly with a supplied header', () => {
      const forecastColDef = colDefBuilder.generateColDefWith(testField, testHeader, testPrecision, testWidth)

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: testField,
          disableColumnMenu: true,
          disabledReorder: true,
          headerName: testHeader,
          sortable: false,
          type: 'number',
          width: testWidth
        })
      )
    })
  })

  describe('generateForecastColDef', () => {
    it('should generate the forecast col def correctly', () => {
      const forecastColDef = colDefBuilder.generateForecastColDef()

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: `${TempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: TempForecastField.headerName,
          sortable: false,
          type: TempForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })

    it('should generate the forecast col def correctly with a supplied header', () => {
      const header = 'test'

      const forecastColDef = colDefBuilder.generateForecastColDef(header)

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: `${TempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: header,
          sortable: false,
          type: TempForecastField.type,
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })

    it('should generate col def with parameters correctly', () => {
      const forecastColDef = colDefBuilder.generateForecastColDefWith(testField, testHeader, testPrecision, testWidth)

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: testField,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: testHeader,
          sortable: false,
          type: 'number',
          width: testWidth
        })
      )
    })
  })
})
