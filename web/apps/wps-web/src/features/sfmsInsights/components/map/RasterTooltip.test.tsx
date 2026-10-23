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

  it.each(['C-2', 'Non-fuel', 'Water', 'Snow'])('prefixes %s with a snowflake', value => {
    render(<RasterTooltip label="" value={value} pixelCoords={[10, 20]} snowCovered />)

    expect(screen.getByText(`❄️ ${value}`)).toBeInTheDocument()
  })

  it('prefixes the full weather tooltip and preserves decimal places', () => {
    render(<RasterTooltip label="Temperature" value={4} pixelCoords={[10, 20]} decimalPlaces={1} snowCovered />)

    expect(screen.getByText('❄️ Temperature: 4.0')).toBeInTheDocument()
  })

  it('hides weather nodata under snow', () => {
    const { container } = render(<RasterTooltip label="Temperature" value={null} pixelCoords={[10, 20]} snowCovered />)

    expect(container).toBeEmptyDOMElement()
  })

  it('does not render without a value', () => {
    const { container } = render(<RasterTooltip label="SFC" value={null} pixelCoords={[10, 20]} decimalPlaces={1} />)

    expect(container).toBeEmptyDOMElement()
  })
})
