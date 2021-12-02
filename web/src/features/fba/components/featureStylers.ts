import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import CircleStyle from 'ol/style/Circle'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'
import { range, startCase, lowerCase } from 'lodash'

const fireCenterTextStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Text => {
  const text = resolution < 2300 ? '' : feature.get('mof_fire_centre_name')
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 1 }),
    font: '16px sans-serif',
    text: text
  })
}

export const fireCenterLableStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Style => {
  return new Style({
    text: fireCenterTextStyler(feature, resolution)
  })
}

export const fireCenterStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Style => {
  return new Style({
    stroke: new Stroke({
      color: 'black',
      width: 3
    })
    // text: fireCenterTextStyler(feature, resolution)
  })
}

const fireZoneTextStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Text => {
  const text = resolution > 3000 ? '' : feature.get('mof_fire_zone_name')
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 1 }),
    font: '14px sans-serif',
    text: text
  })
}

export const fireZoneStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Style => {
  return new Style({
    stroke: new Stroke({
      color: 'grey',
      width: 2
    })
  })
}

export const fireZoneLableStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Style => {
  return new Style({
    text: fireZoneTextStyler(feature, resolution)
  })
}

const stationTextStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Text => {
  // NOTE: playing with start case on fire weather stations?
  const text = resolution < 2300 ? startCase(lowerCase(feature.get('name'))) : ''
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 1 }),
    font: '10px sans-serif',
    text: text,
    textBaseline: 'center',
    textAlign: 'left',
    offsetX: 9,
    offsetY: 1
  })
}

export const stationStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Style => {
  console.log(feature)
  return new Style({
    image: new CircleStyle({
      radius: 5,
      fill: new Fill({
        color: 'black'
      })
    }),
    text: stationTextStyler(feature, resolution)
  })
}

const thessianPolygonStyle = new Style({})

/**
 * Throwaway code, just for demo purposes.
 *
 * 20 times more likely not to have a HFI critical threshold color. 4000 and 10000 equally likely.
 */
const hfiColors = [
  new Fill({ color: 'rgba(255, 0, 0, 0.4)' }),
  new Fill({ color: 'rgba(255, 128, 0, 0.4)' })
].concat(range(20).flatMap(() => new Fill({ color: 'rgba(0, 0, 0, 0)' })))

export const thessianPolygonStyler = (
  feature: RenderFeature | ol.Feature<Geometry>
): Style => {
  const colorIdx = Math.floor(feature.get('station_co') % (hfiColors.length - 1))
  thessianPolygonStyle.setFill(hfiColors[colorIdx])
  return thessianPolygonStyle
}
