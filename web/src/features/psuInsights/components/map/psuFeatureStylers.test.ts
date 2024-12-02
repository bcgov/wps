import { setTransparency } from '@/features/psuInsights/components/map/psuFeatureStylers'

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
})
