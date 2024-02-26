import React from 'react'
import { TextField } from '@mui/material'
import { ModelChoice, WeatherDeterminate } from 'api/moreCast2API'
import {
  ColumnDefBuilder,
  DEFAULT_COLUMN_WIDTH,
  DEFAULT_FORECAST_COLUMN_WIDTH,
  ORDERED_COLUMN_HEADERS
} from 'features/moreCast2/components/ColumnDefBuilder'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'
import { tempForecastField } from 'features/moreCast2/components/MoreCast2Column'
import { theme } from 'app/theme'

describe('ColDefBuilder', () => {
  const colDefBuilder = new ColumnDefBuilder(
    tempForecastField.field,
    tempForecastField.headerName,
    tempForecastField.type,
    tempForecastField.precision,
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
          disableReorder: true,
          headerName: 'Temp',
          sortable: false,
          type: 'number',
          width: DEFAULT_COLUMN_WIDTH
        })
      )
    })
    it('should generate all col defs correctly', () => {
      const colDefs = colDefBuilder.generateColDefs()

      const expected = [
        JSON.stringify({
          field: `${tempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: tempForecastField.headerName,
          sortable: false,
          type: 'number',
          width: DEFAULT_FORECAST_COLUMN_WIDTH
        })
      ].concat(
        ORDERED_COLUMN_HEADERS.map(determinate =>
          JSON.stringify({
            field: `${tempForecastField.field}${determinate}`,
            disableColumnMenu: true,
            disableReorder: true,
            headerName: determinate,
            sortable: false,
            type: 'number',
            width: determinate === WeatherDeterminate.ACTUAL ? DEFAULT_FORECAST_COLUMN_WIDTH : DEFAULT_COLUMN_WIDTH
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
          disableReorder: true,
          headerName: testHeader,
          sortable: false,
          type: 'number',
          width: testWidth
        })
      )

      expect(forecastColDef.renderCell({ formattedValue: 1 })).toEqual(
        <TextField
          sx={{ pointerEvents: 'none', backgroundColor: theme.palette.common.white, borderRadius: 1 }}
          disabled={true}
          size="small"
          value={1}
        ></TextField>
      )
      expect(forecastColDef.valueFormatter({ value: 1.11 })).toEqual('1.1')
    })
  })

  describe('generateForecastColDef', () => {
    it('should generate the forecast col def correctly', () => {
      const forecastColDef = colDefBuilder.generateForecastColDef()

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: `${tempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: tempForecastField.headerName,
          sortable: false,
          type: tempForecastField.type,
          width: DEFAULT_FORECAST_COLUMN_WIDTH
        })
      )
    })

    it('should generate the forecast col def correctly with a supplied header', () => {
      const header = 'test'

      const forecastColDef = colDefBuilder.generateForecastColDef(header)

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: `${tempForecastField.field}${WeatherDeterminate.FORECAST}`,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: header,
          sortable: false,
          type: tempForecastField.type,
          width: DEFAULT_FORECAST_COLUMN_WIDTH
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
      expect(
        forecastColDef.renderCell({ row: { testField: { choice: ModelChoice.GDPS, value: 1 } }, formattedValue: 1 })
      ).toEqual(
        <TextField
          disabled={false}
          InputLabelProps={{
            shrink: true
          }}
          label={ModelChoice.GDPS}
          size="small"
          value={1}
        />
      )

      expect(
        forecastColDef.renderCell({
          row: { testField: { choice: ModelChoice.GDPS, value: 1 } },
          formattedValue: 1
        })
      ).toEqual(
        <TextField
          disabled={false}
          InputLabelProps={{
            shrink: true
          }}
          label={ModelChoice.GDPS}
          size="small"
          value={1}
        />
      )
      expect(forecastColDef.valueFormatter({ value: 1.11 })).toEqual('1.1')
      expect(
        forecastColDef.valueGetter({
          row: { testField: { choice: ModelChoice.GDPS, value: 1 } },
          value: { choice: ModelChoice.GDPS, value: 1.11 }
        })
      ).toEqual('1.1')
      expect(
        forecastColDef.valueSetter({ row: { testField: { choice: ModelChoice.GDPS, value: 1 } }, value: 2 })
      ).toEqual({ testField: { choice: ModelChoice.MANUAL, value: 2 } })
    })

    it('should generate col def with parameters correctly with a default width', () => {
      const forecastColDef = colDefBuilder.generateForecastColDefWith(testField, testHeader, testPrecision)

      expect(JSON.stringify(forecastColDef)).toEqual(
        JSON.stringify({
          field: testField,
          disableColumnMenu: true,
          disableReorder: true,
          editable: true,
          headerName: testHeader,
          sortable: false,
          type: 'number',
          width: 120
        })
      )
    })

    it('should delegate to GridComponentRenderer', () => {
      expect(colDefBuilder.valueFormatterWith({ value: 1.11 }, 1)).toEqual('1.1')
      expect(
        colDefBuilder.valueGetter(
          {
            row: { testField: { choice: ModelChoice.GDPS, value: 1.11 } },
            value: { choice: ModelChoice.GDPS, value: 1.11 }
          },
          'testField',
          1,
          'testHeader'
        )
      ).toEqual('1.1')
      expect(
        colDefBuilder.valueSetterWith(
          { row: { testField: { choice: ModelChoice.GDPS, value: 1 } }, value: 2 },
          testField,
          testPrecision
        )
      ).toEqual({ testField: { choice: ModelChoice.MANUAL, value: 2 } })
    })
  })
})
