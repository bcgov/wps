import { render, screen } from '@testing-library/react'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
import WindSpeedCell, {
  WindSpeedCellProps
} from 'features/fbaCalculator/components/WindSpeedCell'
import React from 'react'
describe('WindSpeedCell', () => {
  const buildProps = (
    inputRow: FBAInputRow,
    calculatedValue?: number
  ): WindSpeedCellProps => ({
    fbaInputGridProps: {
      inputRows: [inputRow],
      stationOptions: [],
      updateRow: () => {
        /** no op */
      }
    },
    classNameMap: { windSpeed: '' },
    inputValue: inputRow.windSpeed,
    calculatedValue,
    rowId: 0
  })
  interface WindSpeedInput {
    windSpeed: number | undefined
    calculatedWindSpeed: number | undefined
  }
  const buildInputRow = (windSpeed: number | undefined) => ({
    id: 0,
    weatherStation: undefined,
    fuelType: '',
    grassCure: undefined,
    windSpeed: windSpeed
  })
  it('should set input value if no calculated value', () => {
    const row = buildInputRow(1)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-0').firstChild?.firstChild).toHaveValue(1)
  })
  it('should set calculated value if no input value', () => {
    const row = buildInputRow(undefined)
    const props = buildProps(row, 2)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-0').firstChild?.firstChild).toHaveValue(2)
  })
})
