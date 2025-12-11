import { colorByFuelTypeCode, getColorByFuelTypeCode } from '@/features/fba/components/viz/color'
import { RASTER_COLOR_BREAKS } from './rasterColorBreaks'
import { FireWeatherRasterType } from './layerDefinitions'
import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import RenderFeature from 'ol/render/Feature'
import Fill from 'ol/style/Fill'
import Style from 'ol/style/Style'

export const SNOW_FILL = 'rgba(255, 255, 255, 1)'
export const EMPTY_FILL = 'rgba(0, 0, 0, 0)'

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

  rasterValueToFuelTypeCode.forEach((code, value) => {
    const [r, g, b] = colorByFuelTypeCode.get(code) ?? [0, 0, 0]
    colourCases.push(['==', ['band', 1], value], [r, g, b, 1])
  })
  colourCases.push([0, 0, 0, 0])

  return ['case', ...colourCases]
}

// Generate color expression dynamically from color breaks
export const getFireWeatherColourExpression = (rasterType: string) => {
  const colorBreaks = RASTER_COLOR_BREAKS[rasterType as FireWeatherRasterType]
  const expression: any[] = ['case']

  // Dynamically build expression from color breaks
  colorBreaks.forEach(colorBreak => {
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
