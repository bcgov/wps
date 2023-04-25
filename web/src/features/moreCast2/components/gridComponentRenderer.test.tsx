import { GridColumnHeaderParams, GridValueSetterParams } from '@mui/x-data-grid'
import { GridStateColDef } from '@mui/x-data-grid/internals'
import { render } from '@testing-library/react'
import { ModelChoice } from 'api/moreCast2API'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'

describe('GridComponentRenderer', () => {
  it('should render the header as a button with the headerName', () => {
    const numberRenderer = new GridComponentRenderer()
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
    const { getByRole } = render(numberRenderer.renderHeaderWith(columnHeaderParams))

    const headerButton = getByRole('button')
    expect(headerButton).toBeInTheDocument()
    expect(headerButton).toBeEnabled()
    expect(headerButton).toHaveTextContent('Test ID')
  })

  it('should set the row correctly', () => {
    const numberRenderer = new GridComponentRenderer()
    const mockValueSetterParams: GridValueSetterParams = {
      value: 2,
      row: {
        temp: {
          value: 2,
          choice: ModelChoice.GDPS
        }
      }
    }

    const updatedRow = numberRenderer.predictionItemValueSetter(mockValueSetterParams, 'temp', 1)

    expect(updatedRow).toEqual({ temp: { choice: ModelChoice.GDPS, value: 2 } })
  })
})
