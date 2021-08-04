import { render } from '@testing-library/react'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
import GrassCureCell from 'features/fbaCalculator/components/GrassCureCell'
import React from 'react'
describe('GrassCureCell', () => {
  const buildProps = (inputRow: FBAInputRow) => ({
    fbaInputGridProps: {
      inputRows: [inputRow],
      updateRow: () => {},
      autoUpdateHandler: () => {}
    },
    classNameMap: { grassCure: '' },
    value: undefined,
    rowId: 0
  })
  it('should return field in error state o1a without percentage set', () => {
    const mockFFBAInputRow = {
      id: 0,
      weatherStation: undefined,
      fuelType: 'o1a',
      grassCure: undefined,
      windSpeed: undefined
    }
    const props = buildProps(mockFFBAInputRow)
    const { container } = render(<GrassCureCell {...props} />)
    expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
  })
  it('should return field in error state o1b without percentage set', () => {
    const mockFFBAInputRow = {
      id: 0,
      weatherStation: undefined,
      fuelType: 'o1b',
      grassCure: undefined,
      windSpeed: undefined
    }
    const props = buildProps(mockFFBAInputRow)
    const { container } = render(<GrassCureCell {...props} />)
    expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
  })
})
