
import { render } from '@testing-library/react'
import ForecastCell from 'features/moreCast2/components/ForecastCell'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'

const params: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
  row: undefined,
  formattedValue: '1'
}

describe('ForecastCell', () => {
  it('should have input disabled when disabled prop is true', () => {
    const { container } = render(
      <ForecastCell
        disabled={true}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement).toBeDisabled()
  })
  it('should have input enabled when disabled prop is false', () => {
    const { container } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement).toBeEnabled()
  })
  it('should show less than icon when showLessThan is true', () => {
    const { queryByTestId } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={true}
        value={params.formattedValue}
      />
    )

    const element = queryByTestId('forecast-cell-less-than-icon')
    expect(element).toBeInTheDocument()
  })
  it('should throw an error when showGreaterThan and showLessThan are both positive', () => {
    // Suppress the console error message for an unhandled error
    const consoleErrorFn = vi.spyOn(console, 'error').mockImplementation(() => vi.fn())
    expect(() => {
      render(
        <ForecastCell
          disabled={false}
          label="foo"
          showGreaterThan={true}
          showLessThan={true}
          value={params.formattedValue}
        />
      )
    }).toThrow('ForecastCell cannot show both greater than and less than icons at the same time.')
    consoleErrorFn.mockRestore()
  })
  it('should not show less than icon when showLessThan is false', () => {
    const { queryByTestId } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const element = queryByTestId('forecast-cell-less-than-icon')
    expect(element).not.toBeInTheDocument()
  })
  it('should show greater than icon when showGreaterThan is true', () => {
    const { queryByTestId } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={true}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const element = queryByTestId('forecast-cell-greater-than-icon')
    expect(element).toBeInTheDocument()
  })
  it('should not show less than icon when showLessThan is false', () => {
    const { queryByTestId } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const element = queryByTestId('forecast-cell-greater-than-icon')
    expect(element).not.toBeInTheDocument()
  })
  it('should not show less than or greater than icons when showLessThan and showGreater than are both false', () => {
    const { queryByTestId } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const greaterThanElement = queryByTestId('forecast-cell-greater-than-icon')
    expect(greaterThanElement).not.toBeInTheDocument()
    const lessThanElement = queryByTestId('forecast-cell-less-than-icon')
    expect(lessThanElement).not.toBeInTheDocument()
  })
  it('should not show a label when none specified', () => {
    const { container } = render(
      <ForecastCell
        disabled={false}
        label=""
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const inputElement = container.querySelector('label')
    expect(inputElement).not.toBeInTheDocument()
  })
  it('should show a label when specified', () => {
    const { container } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const inputElement = container.querySelector('label')
    expect(inputElement).toBeInTheDocument()
  })
  it('should display the value when provided', () => {
    const { container } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={params.formattedValue}
      />
    )

    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement!.value).toBe('1')
  })
  it('should not display a value when none provided', () => {
    const localParams: Pick<GridRenderCellParams, 'row' | 'formattedValue'> = {
      row: undefined,
      formattedValue: undefined
    }
    const { container } = render(
      <ForecastCell
        disabled={false}
        label="foo"
        showGreaterThan={false}
        showLessThan={false}
        value={localParams.formattedValue}
      />
    )

    const inputElement = container.querySelector('input')
    expect(inputElement).toBeInTheDocument()
    expect(inputElement!.value).toBe('')
  })
})
