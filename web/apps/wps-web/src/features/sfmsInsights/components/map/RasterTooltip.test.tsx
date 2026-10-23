import { render, screen } from '@testing-library/react'
import RasterTooltip from './RasterTooltip'

describe('RasterTooltip', () => {
  it('formats numeric values with the configured decimal places', () => {
    render(<RasterTooltip label="SFC" value={7} pixelCoords={[10, 20]} decimalPlaces={1} />)

    expect(screen.getByText('SFC: 7.0')).toBeInTheDocument()
  })

  it('formats numeric values as whole numbers by default', () => {
    render(<RasterTooltip label="FMC" value={94.6} pixelCoords={[10, 20]} />)

    expect(screen.getByText('FMC: 95')).toBeInTheDocument()
  })

  it.each(['C-2', 'Non-fuel', 'Water'])('renders %s without the fuel prefix', value => {
    render(<RasterTooltip label="" value={value} pixelCoords={[10, 20]} decimalPlaces={1} />)

    expect(screen.getByText(value)).toBeInTheDocument()
  })

  it('keeps the non fuel prefix for snow', () => {
    render(<RasterTooltip label="Non-fuel" value="Snow" pixelCoords={[10, 20]} />)

    expect(screen.getByText('Non-fuel: Snow')).toBeInTheDocument()
  })

  it('does not render without a value', () => {
    const { container } = render(<RasterTooltip label="SFC" value={null} pixelCoords={[10, 20]} decimalPlaces={1} />)

    expect(container).toBeEmptyDOMElement()
  })
})
