import * as ol from 'ol'
import type Geometry from 'ol/geom/Geometry'
import {
  CFB_COLOUR_BREAKS,
  FMC_COLOUR_BREAKS,
  FUEL_COLOUR_BREAKS,
  FUEL_TYPE_COLOURS,
  HFI_COLOUR_BREAKS,
  SFC_COLOUR_BREAKS,
  TFC_COLOUR_BREAKS
} from '@/features/sfmsInsights/components/map/rasterConfig'
import {
  EMPTY_FILL,
  fuelCOGColourExpression,
  getSFMSNGRasterColourExpression,
  isNodataValue,
  NODATA_THRESHOLD,
  SNOW_FILL,
  snowStyler
} from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'

describe('snowStyler', () => {
  it('should render correct fill color for snow', () => {
    const feature = new ol.Feature<Geometry>({ snow: 1 })
    const snowStyle = snowStyler(feature)
    expect(snowStyle.getFill()?.getColor()).toBe(SNOW_FILL)
  })
  it('should render the correct fill color for no snow', () => {
    const feature = new ol.Feature<Geometry>({ snow: 0 })
    const snowStyle = snowStyler(feature)
    expect(snowStyle.getFill()?.getColor()).toBe(EMPTY_FILL)
  })
})

describe('fuelCOGColourExpression', () => {
  it.each([
    [99, 'Non-fuel', [130, 130, 130]],
    [102, 'Water', [115, 223, 255]]
  ] as const)('should display %s as %s in the map and legend', (value, label, rgb) => {
    const expr = fuelCOGColourExpression()
    const index = expr.findIndex(item => JSON.stringify(item) === JSON.stringify(['==', ['band', 1], value]))
    expect(index).toBeGreaterThan(-1)
    expect(expr[index + 1]).toEqual([...rgb, 1])
    expect(FUEL_COLOUR_BREAKS.find(item => item.min === value)).toEqual({
      min: value,
      max: value,
      colour: `rgb(${rgb.join(', ')})`,
      label
    })
  })

  it('should return a case expression array', () => {
    const expr = fuelCOGColourExpression()
    expect(Array.isArray(expr)).toBe(true)
    expect(expr[0]).toBe('case')
  })

  it('should make pixels with a zero alpha band transparent', () => {
    const expr = fuelCOGColourExpression()

    expect(expr[1]).toEqual(['==', ['band', 2], 0])
    expect(expr[2]).toEqual([0, 0, 0, 0])
  })

  it('should include all raster values and their corresponding colors', () => {
    const expr = fuelCOGColourExpression()
    const expectedLength = 1 + 2 + FUEL_TYPE_COLOURS.length * 2 + 1
    expect(expr.length).toBe(expectedLength)

    // Check valid fuel type values
    for (const { value: rasterValue, rgb: expectedColor } of FUEL_TYPE_COLOURS) {
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

describe('getSFMSNGRasterColourExpression', () => {
  it('should use the normalized shared palettes for SFC and FMC', () => {
    expect(SFC_COLOUR_BREAKS.map(colourBreak => colourBreak.colour)).toEqual([
      'rgb(0, 0, 255)',
      'rgb(102, 153, 204)',
      'rgb(0, 170, 0)',
      'rgb(128, 255, 0)',
      'rgb(255, 255, 0)',
      'rgb(255, 170, 0)',
      'rgb(255, 0, 0)'
    ])
    expect(FMC_COLOUR_BREAKS.map(colourBreak => colourBreak.colour)).toEqual([
      'rgb(255, 170, 0)',
      'rgb(255, 255, 0)',
      'rgb(128, 255, 0)',
      'rgb(0, 170, 0)',
      'rgb(102, 153, 204)',
      'rgb(0, 0, 255)'
    ])
  })

  it('should make pixels with a zero alpha band transparent before applying color breaks', () => {
    const expr = getSFMSNGRasterColourExpression('fwi')

    expect(expr[0]).toBe('case')
    expect(expr[1]).toEqual(['==', ['band', 2], 0])
    expect(expr[2]).toEqual([0, 0, 0, 0])
  })

  it('should still handle large nodata sentinels explicitly', () => {
    const expr = getSFMSNGRasterColourExpression('fwi')

    expect(expr).toContainEqual(['>', ['band', 1], NODATA_THRESHOLD])
    expect(expr).toContainEqual(['<', ['band', 1], -NODATA_THRESHOLD])
  })

  it.each([
    ['sfc', SFC_COLOUR_BREAKS],
    ['fmc', FMC_COLOUR_BREAKS],
    ['tfc', TFC_COLOUR_BREAKS],
    ['cfb', CFB_COLOUR_BREAKS],
    ['hfi', HFI_COLOUR_BREAKS]
  ] as const)('should include every %s colour break', (rasterType, colourBreaks) => {
    const expr = getSFMSNGRasterColourExpression(rasterType)

    for (const colourBreak of colourBreaks) {
      const [red, green, blue] = colourBreak.colour.match(/\d+/g)!.map(Number)
      expect(expr).toContainEqual([red, green, blue, 1])
    }
  })

  it('should label CFB breaks as percentages while using fraction thresholds', () => {
    expect(CFB_COLOUR_BREAKS.map(({ label }) => label)).toEqual([
      '0-10%',
      '10-30%',
      '30-50%',
      '50-60%',
      '60-80%',
      '80-90%',
      '90-100%'
    ])
    expect(CFB_COLOUR_BREAKS[0].min).toBe(0)
    expect(CFB_COLOUR_BREAKS.at(-1)?.max).toBeNull()
  })
})

describe('NODATA_THRESHOLD', () => {
  it('should be defined as 10 billion', () => {
    expect(NODATA_THRESHOLD).toBe(10000000000)
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
