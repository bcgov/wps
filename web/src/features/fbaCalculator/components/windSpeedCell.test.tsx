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
  const buildInputRow = (inputValues: WindSpeedInput) => ({
    id: 0,
    weatherStation: undefined,
    fuelType: '',
    grassCure: undefined,
    windSpeed: inputValues.windSpeed
  })
  it('should set input value if no calculated value', () => {
    const input = { windSpeed: 1, calculatedWindSpeed: undefined }
    const row = buildInputRow(input)
    const props = buildProps(row)
    render(<WindSpeedCell {...props} />)
    expect(screen.getByTestId('windSpeedInput-0').firstChild?.firstChild).toHaveValue(
      input.windSpeed
    )
  })
})
