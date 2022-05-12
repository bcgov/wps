import { render, screen } from '@testing-library/react'
import WindSpeedCell, { WindSpeedCellProps } from 'features/fbaCalculator/components/WindSpeedCell'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import React from 'react'
describe('WindSpeedCell', () => {
  const buildProps = (inputRow: FBATableRow, calculatedValue?: number): WindSpeedCellProps => ({
    inputRows: [inputRow],
    updateRow: () => {
      /** no op */
    },
    inputValue: inputRow.windSpeed,
    calculatedValue,
    disabled: false,
    rowId: 0
  })
  const buildTableRow = (windSpeed: number | undefined) => ({
    id: 0,
    weatherStation: null,
    fuelType: null,
    grassCure: undefined,
    windSpeed: windSpeed
  })
  it('should set input value if no calculated value', () => {
    const row = buildTableRow(1)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild?.firstChild).toHaveValue(1)
  })
  it('should set calculated value if no input value', () => {
    const row = buildTableRow(undefined)
    const props = buildProps(row, 2)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild?.firstChild).toHaveValue(2)
  })
  it('should return field in error state when wind speed is set to over 120', () => {
    const row = buildTableRow(121)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild).toHaveClass('Mui-error')
  })
  it('should return field without error state when error is corrected', () => {
    const row = buildTableRow(121)
    const props = buildProps(row)
    const { rerender } = render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild).toHaveClass('Mui-error')

    const correctedProps = { ...props, inputValue: 120 }
    rerender(<WindSpeedCell {...correctedProps} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild?.firstChild).toHaveValue(120)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild).not.toHaveClass('Mui-error')
  })
  it('should not return field in error state when wind speed is set to float under 120', () => {
    const row = buildTableRow(119.9)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild?.firstChild).toHaveValue(119.9)
  })
  it('should return field with adjusted border color and weight when there is an input value', () => {
    const row = buildTableRow(1)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild).toHaveStyle({
      border: '2px solid #460270'
    })
  })
  it('should return field without adjusted border color and weight when there is no input value', () => {
    const row = buildTableRow(undefined)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-fba-0').firstChild).toHaveStyle({
      border: ''
    })
  })
})
