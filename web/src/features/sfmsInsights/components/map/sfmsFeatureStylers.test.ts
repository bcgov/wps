import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import {
  EMPTY_FILL,
  getColorForRasterValue,
  SNOW_FILL,
  snowStyler,
  styleFuelGrid,
  fuelCOGColourExpression,
  NODATA_THRESHOLD,
  isNodataValue
} from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import { getColorByFuelTypeCode } from '@/features/fba/components/viz/color'
import { FUEL_TYPE_COLORS } from '@/features/sfmsInsights/components/map/rasterConfig'

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
    // Expected: 'case' + (3 nodata cases * 2) + (14 fuel types * 2) + fallback = 1 + 6 + 28 + 1 = 36
    const expectedLength = 1 + 3 * 2 + FUEL_TYPE_COLORS.length * 2 + 1
    expect(expr.length).toBe(expectedLength)

    // Check nodata values are transparent (99, 102, -10000)
    const nodataValues = [99, 102, -10000]
    for (const nodataValue of nodataValues) {
      const idx = expr.findIndex(
        item =>
          Array.isArray(item) &&
          item[0] === '==' &&
          Array.isArray(item[1]) &&
          item[1][0] === 'band' &&
          item[2] === nodataValue
      )
      expect(idx).toBeGreaterThan(-1)
      const color = expr[idx + 1]
      expect(color).toEqual([0, 0, 0, 0]) // Transparent
    }

    // Check valid fuel type values
    for (const { value: rasterValue, rgb: expectedColor } of FUEL_TYPE_COLORS) {
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

describe('NODATA_THRESHOLD', () => {
  it('should be defined as 10 billion', () => {
    expect(NODATA_THRESHOLD).toBe(10000000000.0)
  })
})

describe('isNodataValue', () => {
  describe('should return true for nodata values', () => {
    it.each([
      ['very large positive value just beyond threshold', NODATA_THRESHOLD + 1],
      ['very large positive value', 10000000001],
      ['typical GeoTIFF nodata positive', 3.4028235e38],
      ['maximum positive value', Number.MAX_VALUE],
      ['positive infinity', Infinity],
      ['very large negative value just beyond threshold', -NODATA_THRESHOLD - 1],
      ['very large negative value', -10000000001],
      ['typical GeoTIFF nodata negative', -3.4028235e38],
      ['maximum negative value', -Number.MAX_VALUE],
      ['negative infinity', -Infinity]
    ])('%s: %f', (_description, value) => {
      expect(isNodataValue(value)).toBe(true)
    })
  })

  describe('should return false for valid values', () => {
    it.each([
      ['zero', 0],
      ['typical FWI minimum', 1],
      ['typical FWI value', 50],
      ['typical FWI maximum', 100],
      ['high FWI value', 150],
      ['small negative value', -1],
      ['moderate negative value', -100],
      ['large negative value', -1000],
      ['positive threshold boundary', NODATA_THRESHOLD],
      ['negative threshold boundary', -NODATA_THRESHOLD]
    ])('%s: %f', (_description, value) => {
      expect(isNodataValue(value)).toBe(false)
    })
  })
})
