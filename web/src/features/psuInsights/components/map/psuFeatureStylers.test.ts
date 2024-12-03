import { getColorForRasterValue, setTransparency } from '@/features/psuInsights/components/map/psuFeatureStylers'

describe('setTransparency', () => {
  it('should return an rgba value from rgb with correct alpha value', () => {
    const rgb = 'rgb(1, 1, 1)'
    const rgba = setTransparency(rgb, 0.5)
    expect(rgba).toBe('rgba(1, 1, 1, 0.5)')
  })

  it('should return an updated rgba value from an rgba input', () => {
    const rgb = 'rgb(1, 1, 1, 1)'
    const rgba = setTransparency(rgb, 0.5)
    expect(rgba).toBe('rgba(1, 1, 1, 0.5)')
  })

  it('should throw an error if fewer than 3 RGB values are provided', () => {
    const incompleteColor = 'rgb(1, 2)'
    expect(() => setTransparency(incompleteColor, 0.5)).toThrow(Error)
  })

  it('should return a completely transparent colour if no colour is provided as input', () => {
    const rgba = setTransparency(undefined, 0.5)
    expect(rgba).toBe('rgba(0, 0, 0, 0)')
  })
})

describe('getColorForRasterValue', () => {
  it('should get the correct colour for the specified raster value', () => {
    const rasterValue = 1
    const colour = getColorForRasterValue(rasterValue)
    expect(colour).toBe('rgb(209, 255, 115)')
  })
})
