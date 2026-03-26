import { render, fireEvent, within, act } from '@testing-library/react'
import { useDispatch } from 'react-redux'
import { GridApiContext, GridCellMode, GridTreeNodeWithRender } from '@mui/x-data-grid-pro'
import { EditInputCell } from '@/features/moreCast2/components/EditInputCell'
import { vi } from 'vitest'
import { GridApiCommunity, GridStateColDef } from '@mui/x-data-grid-pro/internals'
import { setInputValid } from '@/features/moreCast2/slices/validInputSlice'

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

// Mock the useDispatch hook
vi.mock('react-redux', () => ({
  useDispatch: vi.fn()
}))

// Mock the setInputValid action creator
vi.mock('@/features/moreCast2/slices/validInputSlice', () => ({
  setInputValid: vi.fn().mockReturnValue({ type: 'mock/setInputValid' })
}))
const mockDispatch = vi.fn()

beforeEach(() => {
  vi.clearAllMocks();
  (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch)
})

describe('EditInputCell', () => {
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

  test('should call stopCellEditMode on blur', async () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    await act(async () => {
      input.focus()
      fireEvent.blur(input)
    })
    expect(mockStopCellEditMode).toHaveBeenCalledWith({ id: 1, field: 'test' })
  })

  test('should handle Escape key press', async () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={apiMock}>
        <EditInputCell {...defaultProps} id={1} value="10" field="test" hasFocus={false} error="" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    await act(async () => {
      input.focus()
      fireEvent.keyDown(input, { key: 'Escape', code: 'Escape', charCode: 27 })
    })

    expect(mockStopCellEditMode).toHaveBeenCalledWith({ id: 1, field: 'test' })
  })

  test('should not call stopCellEditMode when Escape key is pressed and there is an error', async () => {
    const { getByTestId } = render(
      <GridApiContext.Provider value={{ current: apiMock }}>
        <EditInputCell {...defaultProps} error="Test error" />
      </GridApiContext.Provider>
    )

    const input = within(getByTestId('forecast-edit-cell')).getByRole('spinbutton') as HTMLInputElement
    await act(async () => {
      input.focus()
      // Simulate Escape key press
      fireEvent.keyDown(input, { key: 'Escape', code: 'Escape', charCode: 27 })
    })

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

  describe('Dispatch Mocking and Actions', () => {
    describe('when there is no error', () => {
      test('should call dispatch with setInputValid action on render', () => {
        render(
          <GridApiContext.Provider value={{ current: {} as any }}>
            <EditInputCell {...defaultProps} />
          </GridApiContext.Provider>
        )

        // Check that dispatch was called with the correct action
        expect(mockDispatch).toHaveBeenCalledWith(setInputValid(true))
      })
    })

    describe('when there is an error', () => {
      test('should call dispatch with setInputValid action with false when error is present', () => {
        render(
          <GridApiContext.Provider value={{ current: {} as any }}>
            <EditInputCell {...defaultProps} error="Test error" />
          </GridApiContext.Provider>
        )

        // Check that dispatch was called with the correct action
        expect(mockDispatch).toHaveBeenCalledWith(setInputValid(false))
      })
    })
  })
})
