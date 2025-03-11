import { colorByFuelTypeCode } from '@/features/fba/components/viz/color'
import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import RenderFeature from 'ol/render/Feature'
import Fill from 'ol/style/Fill'
import Style from 'ol/style/Style'

const SNOW_FILL = 'rgba(255, 255, 255, 1)'
const EMPTY_FILL = 'rgba(0, 0, 0, 0.0)'

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

export const getColorForRasterValue = (rasterValue: number): string => {
  const fuelTypeCode = rasterValueToFuelTypeCode.get(rasterValue)
  return fuelTypeCode ? colorByFuelTypeCode.get(fuelTypeCode) : 'rgba(0, 0, 0, 0)'
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