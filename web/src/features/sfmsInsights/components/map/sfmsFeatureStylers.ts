import { colorByFuelTypeCode, getColorByFuelTypeCode } from '@/features/fba/components/viz/color'
import { RASTER_COLOR_BREAKS, FireWeatherRasterType, ColorBreak, FUEL_TYPE_COLORS } from './rasterConfig'
import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import RenderFeature from 'ol/render/Feature'
import Fill from 'ol/style/Fill'
import Style from 'ol/style/Style'

export const SNOW_FILL = 'rgba(255, 255, 255, 1)'
export const EMPTY_FILL = 'rgba(0, 0, 0, 0)'

// Nodata threshold for GeoTIFF rasters
// GeoTIFF nodata is -3.4028235e+38, use threshold for floating-point reliability
export const NODATA_THRESHOLD = 10000000000.0

// Helper function to check if a raster value is nodata
export const isNodataValue = (value: number): boolean => {
  return value > NODATA_THRESHOLD || value < -NODATA_THRESHOLD
}

export const rasterValueToFuelTypeCode = new Map([
  [1, 'C-1'],
  [2, 'C-2'],
  [3, 'C-3'],
  [4, 'C-4'],
  [5, 'C-5'],
  [6, 'C-6'],
  [7, 'C-7'],
  [8, 'D-1/D-2'],
  [9, 'S-1'],
  [10, 'S-2'],
  [11, 'S-3'],
  [12, 'O-1a/O-1b'],
  [13, 'M-3'],
  [14, 'M-1/M-2']
])

export const getColorForRasterValue = (rasterValue: number): string => {
  const fuelTypeCode = rasterValueToFuelTypeCode.get(rasterValue)
  return fuelTypeCode ? getColorByFuelTypeCode(fuelTypeCode) : EMPTY_FILL
}

export const styleFuelGrid = () => {
  const style = (feature: RenderFeature | ol.Feature<Geometry>) => {
    const fuelTypeInt = feature.getProperties().fuel
    const fillColour = getColorForRasterValue(fuelTypeInt)

    return new Style({
      fill: new Fill({ color: fillColour })
    })
  }
  return style
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

type ColourCaseCondition = ['==', ['band', number], number]
type ColourCaseColour = [number, number, number, number]
type ColourCases = Array<ColourCaseCondition | ColourCaseColour>

export const fuelCOGColourExpression = () => {
  const colourCases: ColourCases = []

  FUEL_TYPE_COLORS.forEach(({ value, rgb }) => {
    const [r, g, b] = rgb
    colourCases.push(['==', ['band', 1], value], [r, g, b, 1])
  })
  colourCases.push([0, 0, 0, 0])

  return ['case', ...colourCases]
}

// Generate color expression dynamically from color breaks
export const getFireWeatherColourExpression = (rasterType: string) => {
  const colorBreaks = RASTER_COLOR_BREAKS[rasterType as FireWeatherRasterType]
  const expression: any[] = ['case']

  // Handle nodata values - GeoTIFF nodata is -3.4028235e+38
  // Use threshold checks for floating-point reliability
  expression.push(
    ['>', ['band', 1], NODATA_THRESHOLD],
    [0, 0, 0, 0], // Very large positive values (nodata): transparent
    ['<', ['band', 1], -NODATA_THRESHOLD],
    [0, 0, 0, 0] // Very large negative values (nodata): transparent
  )

  // Dynamically build expression from color breaks
  colorBreaks.forEach((colorBreak: ColorBreak) => {
    const [r, g, b] = colorBreak.color.match(/\d+/g)!.map(Number)

    if (colorBreak.max !== null) {
      expression.push(['<', ['band', 1], colorBreak.max], [r, g, b, 1])
    } else {
      // Last break (no max) - use >= min
      expression.push(['>=', ['band', 1], colorBreak.min], [r, g, b, 1])
    }
  })

  expression.push([0, 0, 0, 0]) // Fallback: transparent
  return expression
}

// Backward compatibility
export const fwiColourExpression = () => getFireWeatherColourExpression('fwi')
