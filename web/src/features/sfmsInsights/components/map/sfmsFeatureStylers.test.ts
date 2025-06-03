import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import {
  EMPTY_FILL,
  getColorForRasterValue,
  SNOW_FILL,
  snowStyler,
  styleFuelGrid,
  fuelCOGColourExpression,
  rasterValueToFuelTypeCode
} from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import { getColorByFuelTypeCode, colorByFuelTypeCode } from '@/features/fba/components/viz/color'

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
    const expected = getColorByFuelTypeCode('C-1')
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
  })
})

describe('fuelCOGColourExpression', () => {
  it('should return a case expression array', () => {
    const expr = fuelCOGColourExpression()
    expect(Array.isArray(expr)).toBe(true)
    expect(expr[0]).toBe('case')
  })

  it('should include all raster values and their corresponding colors', () => {
    const expr = fuelCOGColourExpression()
    const expectedLength = 1 + rasterValueToFuelTypeCode.size * 2 + 1
    expect(expr.length).toBe(expectedLength)

    for (const [rasterValue, code] of rasterValueToFuelTypeCode.entries()) {
      const idx = expr.findIndex(
        item =>
          Array.isArray(item) &&
          item[0] === '==' &&
          Array.isArray(item[1]) &&
          item[1][0] === 'band' &&
          item[2] === rasterValue
      )
      expect(idx).toBeGreaterThan(-1)
      const color = expr[idx + 1]
      const expectedColor = colorByFuelTypeCode.get(code) ?? [0, 0, 0]
      expect(color.slice(0, 3)).toEqual(expectedColor)
      expect(color[3]).toBe(1)
    }
  })

  it('should end with a transparent fallback color', () => {
    const expr = fuelCOGColourExpression()
    const fallback = expr[expr.length - 1]
    expect(fallback).toEqual([0, 0, 0, 0])
  })
})
