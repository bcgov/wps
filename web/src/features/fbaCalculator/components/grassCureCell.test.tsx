import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/extend-expect'
import GrassCureCell, {
  GrassCureCellProps
} from 'features/fbaCalculator/components/GrassCureCell'
import React from 'react'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
describe('GrassCureCell', () => {
  it('should return field in error state when number not input', () => {
    const mockFFBAInputRow: FBAInputRow = {
      id: 0,
      weatherStation: undefined,
      fuelType: undefined,
      grassCure: undefined,
      windSpeed: undefined
    }

    const mockFBAInputGridProps: GrassCureCellProps = {
      fbaInputGridProps: {
        inputRows: [mockFFBAInputRow],
        updateRow: () => {},
        autoUpdateHandler: () => {}
      },
      classNameMap: { grassCure: '' },
      value: undefined,
      rowId: 0
    }
    render(<GrassCureCell {...mockFBAInputGridProps} />)
    expect(screen.getByRole('textbox')).toBeDefined()
  })
})
