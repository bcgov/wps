
import { render } from '@testing-library/react'
import FuelDistribution from 'features/fba/components/viz/FuelDistribution'

describe('FuelDistribution', () => {
  it('should have width relative to parent', () => {
    const rendered = render(
      <div style={{ width: '100px' }}>
        <FuelDistribution code={'C-2'} percent={50} />
      </div>
    )

    const element = rendered.getByTestId('fuel-distribution-box')
    expect(element).toBeInTheDocument()
    expect(element).toHaveStyle('width: 50%')
  })
  it('should have the correct background color', () => {
    const rendered = render(
      <div style={{ width: '100px' }}>
        <FuelDistribution code={'C-2'} percent={50} />
      </div>
    )

    const element = rendered.getByTestId('fuel-distribution-box')
    expect(element).toBeInTheDocument()
    expect(element).toHaveStyle('background: #226633')
  })
})
