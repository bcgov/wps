import { GridColumnHeaderParams, GridValueSetterParams } from '@mui/x-data-grid'
import { GridStateColDef } from '@mui/x-data-grid/internals'
import { render } from '@testing-library/react'
import { ModelChoice } from 'api/moreCast2API'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'

describe('GridComponentRenderer', () => {
  const gridComponentRenderer = new GridComponentRenderer()

  it('should render the header as a button with the headerName', () => {
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
    const { getByRole } = render(gridComponentRenderer.renderForecastHeaderWith(columnHeaderParams))

    const headerButton = getByRole('button')
    expect(headerButton).toBeInTheDocument()
    expect(headerButton).toBeEnabled()
    expect(headerButton).toHaveTextContent('Test ID')
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
      gridComponentRenderer.renderForecastCellWith({ row: { [field]: 1 }, formattedValue: 1 }, field)
    )
    const renderedCell = getByRole('textbox')
    expect(renderedCell).toBeInTheDocument()
    expect(renderedCell).toHaveValue('1')
    expect(renderedCell).not.toBeDisabled()
  })

  it('should render the forecast cell as uneditable with an actual', () => {
    const field = 'tempForecast'
    const actualField = `tempActual`

    const { getByRole } = render(
      gridComponentRenderer.renderForecastCellWith({ row: { [field]: 1, [actualField]: 2 }, formattedValue: 1 }, field)
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
    const formattedItemValue = gridComponentRenderer.predictionItemValueFormatter({ value: NaN }, 1)
    expect(formattedItemValue).toEqual('N/A')
  })

  it('should return an existent cell value correctly', () => {
    const cellValue = gridComponentRenderer.cellValueGetter({ value: 1.11 }, 1)
    expect(cellValue).toEqual('1.1')
  })

  it('should return an non-existent cell value correctly', () => {
    const cellValue = gridComponentRenderer.cellValueGetter({ value: NaN }, 1)
    expect(cellValue).toEqual('NaN')
  })

  it('should return an existent prediction item value correctly', () => {
    const itemValue = gridComponentRenderer.valueGetter(
      {
        row: { testField: { choice: ModelChoice.GDPS, value: 1.11 } },
        value: { choice: ModelChoice.GDPS, value: 1.11 }
      },
      1,
      'testField'
    )
    expect(itemValue).toEqual('1.1')
  })
})
