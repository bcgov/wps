import { render, screen } from '@testing-library/react'
import GrassCureCell, { GrassCureCellProps } from 'features/fbaCalculator/components/GrassCureCell'
import { FBAFuelType, FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { isNull } from 'lodash'
import React from 'react'
describe('GrassCureCell', () => {
  const buildProps = (inputRow: FBATableRow, rowId: number, value?: number): GrassCureCellProps => ({
    inputRows: [inputRow],
    updateRow: () => {
      /** no op */
    },
    value,
    disabled: false,
    rowId: rowId
  })
  describe('grass cure failure states', () => {
    const buildInputRow = (fuelType: 'o1a' | 'o1b') => ({
      id: 0,
      weatherStation: null,
      fuelType: { label: '', value: fuelType },
      grassCure: undefined,
      windSpeed: undefined
    })
    it('should return field in error state for o1a without percentage set', () => {
      const O1ARow = buildInputRow('o1a')
      const props = buildProps(O1ARow, 0)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
    it('should return field in error state for o1b without percentage set', () => {
      const O1BRow = buildInputRow('o1b')
      const props = buildProps(O1BRow, 0)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
    it('should return field in error state when percentage is set to over 100', () => {
      const c1 = FuelTypes.lookup('c1')
      const value = c1 ? c1.name : ''
      const label = c1 ? c1.friendlyName : ''
      const inputRow = {
        id: 0,
        weatherStation: null,
        fuelType: { label, value },
        grassCure: 101,
        windSpeed: undefined
      }
      const props = buildProps(inputRow, 0)
      const { container } = render(<GrassCureCell {...props} />)
      expect(container.firstChild?.firstChild).toHaveClass('Mui-error')
    })
  })
  describe('grass cure successful states', () => {
    const buildTableRow = (fuelType: FBAFuelType | null): FBATableRow => {
      if (isNull(fuelType)) {
        fail('Got null fuel type')
      }
      return {
        id: 0,
        weatherStation: null,
        fuelType: { value: fuelType.name, label: fuelType.friendlyName },
        grassCure: 1,
        windSpeed: undefined
      }
    }
    it('should return field without error state when o1a when percentage set', () => {
      const O1ARow = buildTableRow(FuelTypes.lookup('o1a'))
      const props = buildProps(O1ARow, 0, 1)
      render(<GrassCureCell {...props} />)
      const renderedGrassCureInputField = screen.getByTestId(`grassCureInput-fba-0`).firstChild?.firstChild
      expect(renderedGrassCureInputField).toHaveValue(1)
      expect(renderedGrassCureInputField).not.toHaveClass('Mui-error')
    })
    it('should return field in error state o1b without percentage set', () => {
      const O1BRow = buildTableRow(FuelTypes.lookup('o1b'))
      const props = buildProps(O1BRow, 0, 1)
      render(<GrassCureCell {...props} />)
      const renderedGrassCureInputField = screen.getByTestId(`grassCureInput-fba-0`).firstChild?.firstChild
      expect(renderedGrassCureInputField).toHaveValue(1)
      expect(renderedGrassCureInputField).not.toHaveClass('Mui-error')
    })
  })
})
