import { colorByFuelTypeCode } from '@/features/fba/components/viz/color'
import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import RenderFeature from 'ol/render/Feature'
import Fill from 'ol/style/Fill'
import Style from 'ol/style/Style'

const rasterValueToFuelTypeCode = new Map([
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

const getColorForRasterValue = (rasterValue: number): string => {
  const fuelTypeCode = rasterValueToFuelTypeCode.get(rasterValue)
  return fuelTypeCode ? colorByFuelTypeCode.get(fuelTypeCode) : null
}

/**
 * Takes rgb or rgba values as input, sets or updates the alpha value, and returns a new rgba value
 * @param color rgb or rgba colour string ex. rgb(1, 2, 3) or rgba(1, 2, 3, 0.2)
 * @param alpha number value between 0 and 1
 * @returns rgba value with alpha set ex. rgba(1, 2, 3, 0.5)
 */
export const setTransparency = (color: string, alpha: number): string => {
  if (!color) return 'rgba(0, 0, 0, 0)'
  const rgbMatch = color.match(/\d+/g)
  if (!rgbMatch || rgbMatch.length < 3) {
    throw new Error(`Invalid color format: ${color}`)
  }
  const [r, g, b] = rgbMatch.map(Number)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export const styleFuelGrid = () => {
  const style = (feature: RenderFeature | ol.Feature<Geometry>) => {
    const fuelTypeInt = feature.getProperties().fuel
    const fillColour = getColorForRasterValue(fuelTypeInt)
    const fillRGBA = setTransparency(fillColour, 0.6)

    return new Style({
      fill: new Fill({ color: fillRGBA })
    })
  }
  return style
}