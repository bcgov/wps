import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import { EMPTY_FILL, getColorForRasterValue, SNOW_FILL, snowStyler, styleFuelGrid } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import { colorByFuelTypeCode } from '@/features/fba/components/viz/color'

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

describe('styleFuelGrid', () => {
  it('should render correct fill color for invalid fuel type code', () => {
    const feature = new ol.Feature<Geometry>({ fuel: -1 })
    const styler = styleFuelGrid()
    const fuelStyle = styler(feature)
    expect(fuelStyle.getFill()?.getColor()).toBe(EMPTY_FILL)
  })
  it('should render correct fill color for valid fuel type code', () => {
    const feature = new ol.Feature<Geometry>({ fuel: 1 })
    const styler = styleFuelGrid()
    const fuelStyle = styler(feature)
    const expected = colorByFuelTypeCode.get('C-1')
    expect(fuelStyle.getFill()?.getColor()).toBe(expected)
  })
})

describe('snowStyler', () => {
  it('should render correct fill color for snow', () => {
    const feature = new ol.Feature<Geometry>({ snow: 1 })
    const snowStyle = snowStyler(feature)
    expect(snowStyle.getFill()?.getColor()).toBe(SNOW_FILL)
  })
  it('should render the correct fill color for no snow', () => {
    describe('snowStyler', () => {
      const feature = new ol.Feature<Geometry>({ snow: 0 })
      const snowStyle = snowStyler(feature)
      expect(snowStyle.getFill()?.getColor()).toBe(EMPTY_FILL)
    })
  } )
})




