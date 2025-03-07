import { getColorForRasterValue } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'

describe('getColorForRasterValue', () => {
  it('should get the correct colour for the specified raster value', () => {
    const rasterValue = 1
    const colour = getColorForRasterValue(rasterValue)
    expect(colour).toBe('rgb(209, 255, 115)')
  })
  it('should return a transparent colour if no colour is found', () => {
    const rasterValue = 1000
    const colour = getColorForRasterValue(rasterValue)
    expect(colour).toBe('rgba(0, 0, 0, 0)')
  })
})
