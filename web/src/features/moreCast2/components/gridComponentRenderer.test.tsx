import { buildTestStore } from '@/features/moreCast2/components/testHelper.test'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { GridColumnHeaderParams, GridValueSetterParams } from '@mui/x-data-grid-pro'
import { GridStateColDef } from '@mui/x-data-grid-pro/internals'
import { render } from '@testing-library/react'
import { ModelChoice } from 'api/moreCast2API'
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

describe('GridComponentRenderer', () => {
  const gridComponentRenderer = new GridComponentRenderer()
  const mockColumnClickHandlerProps: ColumnClickHandlerProps = {
    colDef: null,
    contextMenu: null,
    updateColumnWithModel: vi.fn(),
    handleClose: vi.fn()
  }

  it('should render the header with the forecast button', () => {
    const colDef: GridStateColDef = {
      field: 'testID',
      headerName: 'Test ID',
      width: 100,
      type: 'string',
      computedWidth: 100
    }
    const columnHeaderParams: GridColumnHeaderParams = {
      field: 'test',
      colDef
    }
    const { getByTestId } = render(
      gridComponentRenderer.renderForecastHeaderWith(columnHeaderParams, mockColumnClickHandlerProps)
    )

    const headerButton = getByTestId(`${colDef.field}-column-header`)
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

  it('should render the cell with the formatted value', () => {
    const { getByRole } = render(gridComponentRenderer.renderCellWith({ formattedValue: 1 }))

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
})
