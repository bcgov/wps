import { render, screen } from '@testing-library/react'
import PrecipCell, { PrecipCellProps } from 'features/fbaCalculator/components/PrecipCell'
import { FBATableRow } from 'features/fbaCalculator/RowManager'

describe('PrecipCell', () => {
  const buildProps = (inputRow: FBATableRow, calculatedValue?: number): PrecipCellProps => ({
    inputRows: [inputRow],
    updateRow: () => {
      /** no op */
    },
    inputValue: inputRow.precipitation,
    calculatedValue,
    disabled: false,
    rowId: 0
  })
  const buildTableRow = (precip: number | undefined) => ({
    id: 0,
    weatherStation: null,
    fuelType: null,
    grassCure: undefined,
    precipitation: precip,
    windSpeed: undefined
  })
  it('should set input value if no calculated value', () => {
    const row = buildTableRow(1)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild?.firstChild).toHaveValue(1)
  })
  it('should set calculated value if no input value', () => {
    const row = buildTableRow(undefined)
    const props = buildProps(row, 2)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild?.firstChild).toHaveValue(2)
  })
  it('should return field in error state when wind speed is set to over 200', () => {
    const row = buildTableRow(201)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveClass('Mui-error')
  })
  it('should return field in error state when wind speed is set to under 0', () => {
    const row = buildTableRow(-1)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveClass('Mui-error')
  })
  it('should return field without error state when above 200 error is corrected', () => {
    const row = buildTableRow(201)
    const props = buildProps(row)
    const { rerender } = render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveClass('Mui-error')

    const correctedProps = { ...props, inputValue: 200 }
    rerender(<PrecipCell {...correctedProps} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild?.firstChild).toHaveValue(200)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).not.toHaveClass('Mui-error')
  })
  it('should return field without error state when below 0 error is corrected', () => {
    const row = buildTableRow(-1)
    const props = buildProps(row)
    const { rerender } = render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveClass('Mui-error')

    const correctedProps = { ...props, inputValue: 200 }
    rerender(<PrecipCell {...correctedProps} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild?.firstChild).toHaveValue(200)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).not.toHaveClass('Mui-error')
  })
  it('should not return field in error state when precip is set to float under 200', () => {
    const row = buildTableRow(199.9)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild?.firstChild).toHaveValue(199.9)
  })
  it('should return field with adjusted border color and weight when there is an input value', () => {
    const row = buildTableRow(1)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveStyle({
      border: '2px solid #460270'
    })
  })
  it('should return field without adjusted border color and weight when there is no input value', () => {
    const row = buildTableRow(undefined)
    const props = buildProps(row)
    render(<PrecipCell {...props} />)
    expect(screen.getByTestId('precipInput-fba-0').firstChild).toHaveStyle({
      border: ''
    })
  })
})
