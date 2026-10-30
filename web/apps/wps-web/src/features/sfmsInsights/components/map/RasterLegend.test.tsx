import { render, screen } from '@testing-library/react'
import RasterLegend from './RasterLegend'
import { RASTER_CONFIG, type RasterType } from './rasterConfig'

describe('RasterLegend', () => {
  it.each((Object.keys(RASTER_CONFIG) as RasterType[]).filter(type => RASTER_CONFIG[type].group === 'fbp'))(
    'should include separate Non-fuel and Water entries for %s',
    rasterType => {
      render(<RasterLegend rasterType={rasterType} />)
      expect(screen.getByText('Non-fuel')).toBeInTheDocument()
      expect(screen.getByText('Water')).toBeInTheDocument()
      expect(screen.getByText(RASTER_CONFIG[rasterType].label)).toBeInTheDocument()
    }
  )

  it.each(['temperature', 'fwi'] as const)('should not add Non-fuel to %s', rasterType => {
    render(<RasterLegend rasterType={rasterType} />)
    expect(screen.queryByText('Non-fuel')).not.toBeInTheDocument()
    expect(screen.queryByText('Water')).not.toBeInTheDocument()
  })
})
