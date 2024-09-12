import { render, fireEvent, within } from '@testing-library/react'
import { GridApiContext, GridCellMode, GridTreeNodeWithRender } from '@mui/x-data-grid-pro'
import { EditInputCell } from '@/features/moreCast2/components/EditInputCell'
import { vi } from 'vitest'
import { GridApiCommunity, GridStateColDef } from '@mui/x-data-grid-pro/internals'

const mockSetEditCellValue = vi.fn()
const mockStopCellEditMode = vi.fn()

// Mock API context
const apiMock = {
  current: {
    setEditCellValue: mockSetEditCellValue,
    stopCellEditMode: mockStopCellEditMode
  }
} as unknown as GridApiCommunity

// Mock GridRenderEditCellParams
const defaultProps = {
  id: 1,
  api: apiMock,
  row: undefined,
  rowNode: undefined as unknown as GridTreeNodeWithRender,
  colDef: undefined as unknown as GridStateColDef,
  cellMode: 'edit' as GridCellMode,
  tabIndex: 0 as 0 | -1,
  value: '10',
  field: 'test',
  hasFocus: false,
  error: ''
}

describe('EditInputCell Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('should focus input when hasFocus is true', () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} hasFocus={true} />
      </GridApiContext.Provider>
    )
    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    expect(input).toHaveFocus()
  })

  test('should call setEditCellValue on value change', () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    expect(input.value).toBe('10')
    // Change the value and fire the event
    fireEvent.change(input, { target: { value: '20' } })
    expect(mockSetEditCellValue).toHaveBeenCalledWith({ id: 1, field: 'test', value: '20' })
  })

  test('should call stopCellEditMode on blur', () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    input.focus()
    fireEvent.blur(input)

    expect(mockStopCellEditMode).toHaveBeenCalledWith({ id: 1, field: 'test' })
  })

  test('should handle Escape key press', () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    input.focus()
    fireEvent.keyDown(input, { key: 'Escape', code: 'Escape', charCode: 27 })

    expect(mockStopCellEditMode).toHaveBeenCalledWith({ id: 1, field: 'test' })
  })

  test('should not call stopCellEditMode when Escape key is pressed and there is an error', () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={{ current: apiMock }}>
        <EditInputCell {...defaultProps} error="Test error" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    input.focus()
    // Simulate Escape key press
    fireEvent.keyDown(input, { key: 'Escape', code: 'Escape', charCode: 27 })

    // Verify that stopCellEditMode was not called
    expect(mockStopCellEditMode).not.toHaveBeenCalled()
  })

  test('should show tooltip with error and style correctly', () => {
    const { getByRole } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="Test error" />
      </GridApiContext.Provider>
    )

    const tooltip = getByRole('tooltip')
    expect(tooltip).toBeVisible()
    expect(tooltip).toHaveTextContent('Test error')
  })
})
