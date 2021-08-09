import { render, screen } from '@testing-library/react'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
import GrassCureCell, {
  GrassCureCellProps
} from 'features/fbaCalculator/components/GrassCureCell'
import { FBAFuelType, FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { isNull } from 'lodash'
import React from 'react'
describe('GrassCureCell', () => {
  const buildProps = (inputRow: FBAInputRow, value?: number): GrassCureCellProps => ({
    fbaInputGridProps: {
      inputRows: [inputRow],
      updateRow: () => {
        /** no op */
      }
    },
    classNameMap: { grassCure: '' },
    value,
    rowId: 0
  })
  describe('grass cure failure states', () => {
    const buildInputRow = (fuelType: 'o1a' | 'o1b') => ({
      id: 0,
      weatherStation: undefined,
      fuelType: fuelType,
      grassCure: undefined,
      windSpeed: undefined
    })
    it('should return field in error state for o1a without percentage set', () => {
      const zero1ARow = buildInputRow('o1a')
      const props = buildProps(zero1ARow)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
    it('should return field in error state for o1b without percentage set', () => {
      const zero1BRow = buildInputRow('o1b')
      const props = buildProps(zero1BRow)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
    it('should return field in error state when percentage is set to over 100', () => {
      const inputRow = {
        id: 0,
        weatherStation: undefined,
        fuelType: FuelTypes.lookup('c1')?.name,
        grassCure: 101,
        windSpeed: undefined
      }
      const props = buildProps(inputRow)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
  })
  describe('grass cure successful states', () => {
    const buildInputRow = (fuelType: FBAFuelType | null): FBAInputRow => {
      if (isNull(fuelType)) {
        fail('Got null fuel type')
      }
      return {
        id: 0,
        weatherStation: undefined,
        fuelType: fuelType.name,
        grassCure: 1,
        windSpeed: undefined
      }
    }
    it('should return field without error state when o1a when percentage set', () => {
      const zero1ARow = buildInputRow(FuelTypes.lookup('o1a'))
      const props = buildProps(zero1ARow, 1)
      render(<GrassCureCell {...props} />)
      const renderedGrassCureInputField = screen.getByTestId(`grassCureInput-0`)
        .firstChild?.firstChild
      expect(renderedGrassCureInputField).toHaveValue(1)
      expect(renderedGrassCureInputField).not.toHaveClass('Mui-error')
    })
    it('should return field in error state o1b without percentage set', () => {
      const zero1BRow = buildInputRow(FuelTypes.lookup('o1b'))
      const props = buildProps(zero1BRow, 1)
      render(<GrassCureCell {...props} />)
      const renderedGrassCureInputField = screen.getByTestId(`grassCureInput-0`)
        .firstChild?.firstChild
      expect(renderedGrassCureInputField).toHaveValue(1)
      expect(renderedGrassCureInputField).not.toHaveClass('Mui-error')
    })
  })
})
