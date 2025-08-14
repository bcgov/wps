import { buildTestStore } from '@/features/moreCast2/components/testHelper'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { GridColumnHeaderParams, GridValueSetterParams } from '@mui/x-data-grid-pro'
import { GridStateColDef } from '@mui/x-data-grid-pro/internals'
import { render } from '@testing-library/react'
import { ModelChoice, WeatherDeterminate, WeatherDeterminateChoices, weatherModelsWithTooltips } from 'api/moreCast2API'
import { GC_HEADER } from 'features/moreCast2/components/ColumnDefBuilder'
import {
  GridComponentRenderer,
  NOT_AVAILABLE,
  NOT_REPORTING
} from 'features/moreCast2/components/GridComponentRenderer'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import { theme } from 'app/theme'
import { MoreCast2Row } from '@/features/moreCast2/interfaces'

describe('GridComponentRenderer', () => {
  const gridComponentRenderer = new GridComponentRenderer()
  const mockColumnClickHandlerProps: ColumnClickHandlerProps = {
    colDef: null,
    contextMenu: null,
    updateColumnWithModel: vi.fn(),
    handleClose: vi.fn()
  }

  // Mock factory for GridColumnHeaderParams
  const createMockGridColumnHeaderParams = (
    field = 'test',
    colDefOverrides: Partial<GridStateColDef> = {}
  ): GridColumnHeaderParams => {
    const defaultColDef: GridStateColDef = {
      field: field,
      headerName: 'Test Header',
      width: 100,
      type: 'string',
      computedWidth: 100,
      ...colDefOverrides
    }

    return {
      field,
      colDef: defaultColDef
    } as GridColumnHeaderParams
  }

  it('should render the header with the forecast button', () => {
    const columnHeaderParams = createMockGridColumnHeaderParams('testID', {
      field: 'testID',
      headerName: 'Test ID'
    })

    const { getByTestId } = render(
      gridComponentRenderer.renderForecastHeaderWith(columnHeaderParams, mockColumnClickHandlerProps)
    )

    const headerButton = getByTestId(`${columnHeaderParams.colDef.field}-column-header`)
    expect(headerButton).toBeInTheDocument()
    expect(headerButton).toBeEnabled()
  })

  it('should render an empty cell (no N/A) if the cell is enabled and can have a forecast entered', () => {
    const field = 'tempForecast'
    const fieldActual = 'tempActual'
    const row = { [field]: NaN, [fieldActual]: NaN, forDate: DateTime.now().plus({ days: 2 }) }
    const formattedValue = gridComponentRenderer.valueGetter({ row: row, value: NaN }, 1, field, 'Forecast')
    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith(
          {
            row: row,
            formattedValue: formattedValue
          },
          field
        )}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue('')
    expect(renderedCell).toBeEnabled()
  })

  it('should render N/A and be disabled if the cell is from a previous date', () => {
    const field = 'tempForecast'
    const row = { [field]: NaN, forDate: DateTime.now().minus({ days: 2 }) }
    const formattedValue = gridComponentRenderer.valueGetter({ row: row, value: NaN }, 1, field, 'Forecast')
    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith(
          {
            row: row,
            formattedValue: formattedValue
          },
          field
        )}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue(NOT_AVAILABLE)
    expect(renderedCell).toBeDisabled()
  })

  it('should render N/A and be disabled if the row has an actual', () => {
    const field = 'tempForecast'
    const fieldActual = 'tempActual'
    const row = { [field]: NaN, [fieldActual]: 2, forDate: DateTime.now() }
    const formattedValue = gridComponentRenderer.valueGetter({ row: row, value: NaN }, 1, field, 'Forecast')
    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith(
          {
            row: row,
            formattedValue: formattedValue
          },
          field
        )}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue(NOT_AVAILABLE)
    expect(renderedCell).toBeDisabled()
  })

  it('should render N/R and be disabled if the cell is from a previous date and has no actual in the actual column', () => {
    const field = 'tempForecast'
    const fieldActual = 'tempActual'
    const row = { [field]: NaN, [fieldActual]: NaN, forDate: DateTime.now().minus({ days: 2 }) }
    const formattedValue = gridComponentRenderer.valueGetter({ row: row, value: NaN }, 1, field, 'Actual')
    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith(
          {
            row: row,
            formattedValue: formattedValue
          },
          field
        )}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue(NOT_REPORTING)
    expect(renderedCell).toBeDisabled()
  })

  it('should render N/R as ActualCell and have red border if no actual for row with forDate earlier than today', () => {
    const field = 'tempActual'
    const row = { [field]: NaN, forDate: DateTime.now().minus({ days: 2 }) }
    const formattedValue = gridComponentRenderer.valueGetter({ row: row, value: NaN }, 1, field, 'Actual')
    const { getByTestId } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderCellWith({
          row: row,
          formattedValue: formattedValue,
          field
        })}
      </Provider>
    )
    const renderedCell = getByTestId('actual-cell')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveStyle(`borderColor: ${theme.palette.error.main}`)
  })

  it('should render the cell with the formatted value', () => {
    const field = 'tempForecast'
    const fieldActual = 'tempActual'
    const row = { [field]: NaN, [fieldActual]: 2, forDate: DateTime.now() }
    const { getByRole } = render(gridComponentRenderer.renderCellWith({ formattedValue: 1, field: fieldActual, row }))

    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue('1')
    expect(renderedCell).toBeDisabled()
  })

  it('should render the forecast cell as editable with no actual', () => {
    const field = 'tempForecast'
    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith({ row: { [field]: 1 }, formattedValue: 1 }, field)}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue('1')
    expect(renderedCell).not.toBeDisabled()
  })

  it('should render any cell as disabled if any other cell has an actual', () => {
    const field = 'grassCuringForecast'
    const actual = 'tempActual'
    const { getByRole } = render(
      gridComponentRenderer.renderForecastCellWith({ row: { [field]: 10, [actual]: 15 } }, field)
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toBeDisabled()
  })

  it('should render the forecast cell as uneditable with an actual', () => {
    const field = 'tempForecast'
    const actualField = `tempActual`

    const { getByRole } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith(
          { row: { [field]: 1, [actualField]: 2 }, formattedValue: 1 },
          field
        )}
      </Provider>
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue('1')
    expect(renderedCell).toBeDisabled()
  })

  it('should render the wind direction forecast cell', () => {
    const field = 'windDirectionForecast'

    const { getByTestId } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith({ row: { [field]: 1 }, formattedValue: 1 }, field)}
      </Provider>
    )
    const renderedCell = getByTestId('validated-winddir-forecast-cell')
    expect(renderedCell).toBeInTheDocument()
  })

  it('should render the grass curing forecast cell', () => {
    const field = 'grassCuringForecast'

    const { getByTestId } = render(
      <Provider store={buildTestStore(initialState)}>
        {gridComponentRenderer.renderForecastCellWith({ row: { [field]: 1 }, formattedValue: 1 }, field)}
      </Provider>
    )
    const renderedCell = getByTestId('validated-gc-forecast-cell')
    expect(renderedCell).toBeInTheDocument()
  })

  it('should set the row correctly', () => {
    const mockValueSetterParams: GridValueSetterParams = {
      value: 2,
      row: {
        temp: {
          value: 2,
          choice: ModelChoice.GDPS
        }
      }
    }

    const updatedRow = gridComponentRenderer.predictionItemValueSetter(mockValueSetterParams, 'temp', 1)

    expect(updatedRow).toEqual({ temp: { choice: ModelChoice.GDPS, value: 2 } })
  })

  it('should format the row correctly with a value', () => {
    const formattedItemValue = gridComponentRenderer.predictionItemValueFormatter({ value: 1.11 }, 1)
    expect(formattedItemValue).toEqual('1.1')
  })

  it('should format the row correctly without a value', () => {
    const formattedItemValue = gridComponentRenderer.predictionItemValueFormatter({ value: NOT_REPORTING }, 1)
    expect(formattedItemValue).toEqual(NOT_REPORTING)
  })

  it('should return an existent prediction item value correctly', () => {
    const itemValue = gridComponentRenderer.valueGetter(
      {
        row: { testField: { choice: ModelChoice.GDPS, value: 1.11 } },
        value: { choice: ModelChoice.GDPS, value: 1.11 }
      },
      1,
      'testField',
      'testHeader'
    )
    expect(itemValue).toEqual('1.1')
  })

  it('should return an actual field', () => {
    const actualField = gridComponentRenderer.getActualField('testForecast')
    expect(actualField).toEqual('testActual')
  })

  it('should return an actual over a prediction if it exists for grass curing', () => {
    const itemValue = gridComponentRenderer.valueGetter(
      {
        row: {
          grassCuringForecast: { choice: ModelChoice.GDPS, value: 10.0 },
          grassCuringActual: 20.0
        },
        value: { choice: ModelChoice.NULL, value: 10.0 }
      },
      1,
      'grassCuringForecast',
      GC_HEADER
    )
    expect(itemValue).toEqual('20.0')
  })
  describe('renderHeader', () => {
    const allRowsMock: MoreCast2Row[] = [
      {
        ffmcCalcActual: 0,
        dmcCalcActual: 0,
        dcCalcActual: 0,
        isiCalcActual: 0,
        buiCalcActual: 0,
        fwiCalcActual: 0,
        dgrCalcActual: 0,
        grassCuringActual: 0,
        precipActual: 0,
        rhActual: 0,
        tempActual: 0,
        windDirectionActual: 0,
        windSpeedActual: 0,
        precipGDPS: 0,
        rhGDPS: 0,
        tempGDPS: 0,
        windDirectionGDPS: 0,
        windSpeedGDPS: 0,
        precipGDPS_BIAS: 0,
        rhGDPS_BIAS: 0,
        tempGDPS_BIAS: 0,
        windDirectionGDPS_BIAS: 0,
        windSpeedGDPS_BIAS: 0,
        precipGFS: 0,
        rhGFS: 0,
        tempGFS: 0,
        windDirectionGFS: 0,
        windSpeedGFS: 0,
        precipGFS_BIAS: 0,
        rhGFS_BIAS: 0,
        tempGFS_BIAS: 0,
        windDirectionGFS_BIAS: 0,
        windSpeedGFS_BIAS: 0,
        precipHRDPS: 0,
        rhHRDPS: 0,
        tempHRDPS: 0,
        windDirectionHRDPS: 0,
        windSpeedHRDPS: 0,
        precipHRDPS_BIAS: 0,
        rhHRDPS_BIAS: 0,
        tempHRDPS_BIAS: 0,
        windDirectionHRDPS_BIAS: 0,
        windSpeedHRDPS_BIAS: 0,
        precipNAM: 0,
        rhNAM: 0,
        tempNAM: 0,
        windDirectionNAM: 0,
        windSpeedNAM: 0,
        precipNAM_BIAS: 0,
        rhNAM_BIAS: 0,
        tempNAM_BIAS: 0,
        windDirectionNAM_BIAS: 0,
        windSpeedNAM_BIAS: 0,
        precipRDPS: 0,
        rhRDPS: 0,
        tempRDPS: 0,
        windDirectionRDPS: 0,
        windSpeedRDPS: 0,
        precipRDPS_BIAS: 0,
        rhRDPS_BIAS: 0,
        tempRDPS_BIAS: 0,
        windDirectionRDPS_BIAS: 0,
        windSpeedRDPS_BIAS: 0,
        id: '',
        stationCode: 0,
        stationName: '',
        forDate: DateTime.fromISO('2016-05-25T09:08:34.123'),
        latitude: 0,
        longitude: 0,
        predictionRunTimestampRDPS: DateTime.fromISO('2016-05-25T09:08:34.123').toISO(),
        predictionRunTimestampGDPS: DateTime.fromISO('2016-05-25T09:08:34.123').toISO(),
        predictionRunTimestampHRDPS: DateTime.fromISO('2016-05-25T09:08:34.123').toISO(),
        predictionRunTimestampNAM: DateTime.fromISO('2016-05-25T09:08:34.123').toISO(),
        predictionRunTimestampGFS: DateTime.fromISO('2016-05-25T09:08:34.123').toISO()
      }
    ]
    const mockParams = {
      field: WeatherDeterminate.RDPS,
      colDef: {
        field: WeatherDeterminate.RDPS,
        headerName: WeatherDeterminate.RDPS
      }
    }
    const createMockParams = (determinate: WeatherDeterminate) => ({
      field: determinate,
      colDef: {
        field: determinate,
        headerName: determinate
      }
    })

    it('should render header with the correct headerName text', () => {
      const { getByText } = render(<div>{gridComponentRenderer.renderHeaderWith(mockParams)}</div>)
      expect(getByText(mockParams.colDef.headerName)).toBeInTheDocument()
    })

    it('should render header with model run tooltip', () => {
      const { getByText, getByTestId } = render(
        <div>{gridComponentRenderer.renderHeaderWith(mockParams, allRowsMock)}</div>
      )
      expect(getByText(mockParams.colDef.headerName)).toBeInTheDocument()
      expect(getByTestId(`${mockParams.colDef.field}-model-run-tooltip`)).toBeVisible()
    })
    describe.each(weatherModelsWithTooltips)('should render header with tooltip for determinate %s', determinate => {
      const param = createMockParams(determinate)
      it(`should render header with tooltip for ${determinate}`, () => {
        const { getByText, getByTestId } = render(
          <div>{gridComponentRenderer.renderHeaderWith(param, allRowsMock)}</div>
        )
        expect(getByText(param.colDef.headerName)).toBeInTheDocument()
        expect(getByTestId(`${param.colDef.field}-model-run-tooltip`)).toBeVisible()
      })
    })
    describe.each(WeatherDeterminateChoices.filter(determinate => !weatherModelsWithTooltips.includes(determinate)))(
      'should not render header with tooltip for bias determinate %s',
      determinate => {
        const param = createMockParams(determinate)
        it(`should not render header with tooltip for ${determinate}`, () => {
          const { queryAllByTestId } = render(<div>{gridComponentRenderer.renderHeaderWith(param, allRowsMock)}</div>)
          expect(queryAllByTestId(`${param.colDef.field}-model-run-tooltip`).length === 0)
        })
      }
    )
  })
})
