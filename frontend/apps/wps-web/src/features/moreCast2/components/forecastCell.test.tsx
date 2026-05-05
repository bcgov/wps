import { render } from '@testing-library/react'
import ForecastCell from 'features/moreCast2/components/ForecastCell'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { vi } from 'vitest'
import { initialState } from '@/features/moreCast2/slices/validInputSlice'
import { Provider } from 'react-redux'
import { buildTestStore } from '@/features/moreCast2/components/testHelper'

const defaultValue: GridRenderCellParams['formattedValue'] = '1'

type CellProps = {
  disabled?: boolean
  label?: string
  showGreaterThan?: boolean
  showLessThan?: boolean
  value?: GridRenderCellParams['formattedValue']
}

const renderCell = ({ disabled = false, label = 'foo', showGreaterThan = false, showLessThan = false, value = defaultValue }: CellProps = {}) =>
  render(
    <Provider store={buildTestStore(initialState)}>
      <ForecastCell
        disabled={disabled}
        label={label}
        showGreaterThan={showGreaterThan}
        showLessThan={showLessThan}
        value={value}
      />
    </Provider>
  )

describe('ForecastCell', () => {
  it('should have input disabled when disabled prop is true', () => {
    const { container } = renderCell({ disabled: true })
    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement).toBeDisabled()
  })

  it('should have input enabled when disabled prop is false', () => {
    const { container } = renderCell()
    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement).toBeEnabled()
  })

  it('should show less than icon when showLessThan is true', () => {
    const { queryByTestId } = renderCell({ showLessThan: true })
    expect(queryByTestId('forecast-cell-less-than-icon')).toBeInTheDocument()
  })

  it('should throw an error when showGreaterThan and showLessThan are both positive', () => {
    const consoleErrorFn = vi.spyOn(console, 'error').mockImplementation(() => vi.fn())
    expect(() => renderCell({ showGreaterThan: true, showLessThan: true }))
      .toThrow('ForecastCell cannot show both greater than and less than icons at the same time.')
    consoleErrorFn.mockRestore()
  })

  it('should not show less than icon when showLessThan is false', () => {
    const { queryByTestId } = renderCell()
    expect(queryByTestId('forecast-cell-less-than-icon')).not.toBeInTheDocument()
  })

  it('should show greater than icon when showGreaterThan is true', () => {
    const { queryByTestId } = renderCell({ showGreaterThan: true })
    expect(queryByTestId('forecast-cell-greater-than-icon')).toBeInTheDocument()
  })

  it('should not show greater than icon when showGreaterThan is false', () => {
    const { queryByTestId } = renderCell()
    expect(queryByTestId('forecast-cell-greater-than-icon')).not.toBeInTheDocument()
  })

  it('should not show less than or greater than icons when both are false', () => {
    const { queryByTestId } = renderCell()
    expect(queryByTestId('forecast-cell-greater-than-icon')).not.toBeInTheDocument()
    expect(queryByTestId('forecast-cell-less-than-icon')).not.toBeInTheDocument()
  })

  it('should not show a label when none specified', () => {
    const { container } = renderCell({ label: '' })
    expect(container.querySelector('label')).not.toBeInTheDocument()
  })

  it('should show a label when specified', () => {
    const { container } = renderCell()
    expect(container.querySelector('label')).toBeInTheDocument()
  })

  it('should display the value when provided', () => {
    const { container } = renderCell()
    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement!.value).toBe('1')
  })

  it('should not display a value when none provided', () => {
    const noValue: Pick<GridRenderCellParams, 'formattedValue'> = { formattedValue: undefined }
    const { container } = render(
      <Provider store={buildTestStore(initialState)}>
        <ForecastCell disabled={false} label="foo" showGreaterThan={false} showLessThan={false} value={noValue} />
      </Provider>
    )
    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement!.value).toBe('')
  })
})
