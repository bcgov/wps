import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import * as colorModule from '@/components/profile/color'
import FuelDistribution from './FuelDistribution'

// Mock getColorByFuelTypeCode
vi.mock('@/components/profile/color', () => ({
  getColorByFuelTypeCode: vi.fn()
}))

describe('FuelDistribution', () => {
  const mockColor = '#123456'

  beforeEach(() => {
    vi.mocked(colorModule.getColorByFuelTypeCode).mockReturnValue(mockColor)
  })

  it('renders the fuel distribution box with correct width and background color', () => {
    render(<FuelDistribution code="ABC" percent={42} />)

    const percent = screen.getByText('42%')
    const box = screen.getByTestId('fuel-distribution-box')

    expect(percent).toBeInTheDocument()
    expect(percent).toHaveStyle({ textAlign: 'right' })

    expect(box).toBeInTheDocument()
    expect(box).toHaveStyle({
      width: '42%',
      background: mockColor,
      height: '100%'
    })
    expect(colorModule.getColorByFuelTypeCode).toHaveBeenCalledWith('ABC')
  })
})
