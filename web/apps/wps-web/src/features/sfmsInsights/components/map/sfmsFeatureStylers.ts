import type * as ol from 'ol'
import type Geometry from 'ol/geom/Geometry'
import type RenderFeature from 'ol/render/Feature'
import Fill from 'ol/style/Fill'
import Style from 'ol/style/Style'
import { type ColourBreak, FUEL_TYPE_COLOURS, RASTER_CONFIG, type SFMSNGRasterType } from './rasterConfig'

export const SNOW_FILL = 'rgba(255, 255, 255, 1)'
export const EMPTY_FILL = 'rgba(0, 0, 0, 0)'

// Nodata threshold for GeoTIFF rasters
// GeoTIFF nodata is -3.4028235e+38, use threshold for floating-point reliability
// Note: JavaScript treats number literals like 1, 1.0, and 1 as identical values.
export const NODATA_THRESHOLD = 10000000000
const RASTER_BAND = 1
const ALPHA_BAND = 2

// Helper function to check if a raster value is nodata
export const isNodataValue = (value: number): boolean => {
  return value > NODATA_THRESHOLD || value < -NODATA_THRESHOLD
}

// A styling function for the snow coverage pmtiles layer.
export const snowStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  const snow = feature.get('snow')
  const snowStyle = new Style({})
  if (snow === 1) {
    snowStyle.setFill(new Fill({ color: SNOW_FILL }))
  } else {
    snowStyle.setFill(new Fill({ color: EMPTY_FILL }))
  }
  return snowStyle
}

type ColourCaseCondition =
  | ['==', ['band', number], number]
  | ['<=', ['band', number], number]
  | ['>', ['band', number], number]
  | ['<', ['band', number], number]
  | ['>=', ['band', number], number]
type ColourCaseColour = [number, number, number, number]
type ColourCases = Array<ColourCaseCondition | ColourCaseColour>

// alpha is transparency: 0 is fully transparent, and any nonzero value is visible.
// use it as a validity flag because normalize:false may expose valid alpha as 255, not 1
const transparentWhenAlphaBandIsZero = (): ColourCases => [
  ['==', ['band', ALPHA_BAND], 0],
  [0, 0, 0, 0]
]

export const fuelCOGColourExpression = () => {
  const colourCases: ColourCases = transparentWhenAlphaBandIsZero()

  FUEL_TYPE_COLOURS.forEach(({ value, rgb }) => {
    const [r, g, b] = rgb
    colourCases.push(['==', ['band', RASTER_BAND], value], [r, g, b, 1])
  })

  // Fallback for any other values - transparent
  colourCases.push([0, 0, 0, 0])

  return ['case', ...colourCases]
}

// Generate color expression dynamically from color breaks
export const getSFMSNGRasterColourExpression = (rasterType: SFMSNGRasterType) => {
  const colourBreaks = RASTER_CONFIG[rasterType].colourBreaks
  const expression: Array<string | ColourCaseCondition | ColourCaseColour> = [
    'case',
    ...transparentWhenAlphaBandIsZero()
  ]

  // Handle nodata values - GeoTIFF nodata is -3.4028235e+38
  // Use threshold checks for floating-point reliability
  expression.push(
    ['>', ['band', RASTER_BAND], NODATA_THRESHOLD],
    [0, 0, 0, 0], // Very large positive values (nodata): transparent
    ['<', ['band', RASTER_BAND], -NODATA_THRESHOLD],
    [0, 0, 0, 0] // Very large negative values (nodata): transparent
  )

  // Dynamically build expression from color breaks
  colourBreaks.forEach((colourBreak: ColourBreak) => {
    const [r, g, b] = colourBreak.colour.match(/\d+/g)!.map(Number)

    if (colourBreak.max === null) {
      // Last break (no max) - use >= min
      expression.push(['>=', ['band', RASTER_BAND], colourBreak.min], [r, g, b, 1])
    } else {
      expression.push(['<', ['band', RASTER_BAND], colourBreak.max], [r, g, b, 1])
    }
  })

  expression.push([0, 0, 0, 0]) // Fallback: transparent
  return expression
}
