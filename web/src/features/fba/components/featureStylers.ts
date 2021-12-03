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

const construct_zone_code = (fire_centre_id: number, fire_zone_id: number): string => {
  // zone_code = get_zone_code_prefix(fire_centre_id) + str(zone_alias)
  // return null
  const zone_code_prefix = get_zone_code_prefix(fire_centre_id)
  return zone_code_prefix ? `${zone_code_prefix}${fire_zone_id}` : ''
}

const get_zone_code_prefix = (fire_centre_id: number): string | null => {
  /* Returns the single-letter code corresponding to fire centre.
    Used in constructing zone codes.
    Fire centre-to-letter mappings provided by Eric Kopetski.
    */
  const fire_centre_to_zone_code_prefix: { [id: number]: string } = {
    2: 'K', // Kamloops Fire Centre
    5: 'G', // Prince George Fire Centre
    6: 'R', // Northwest Fire Centre
    3: 'C', // Cariboo Fire Centre
    1: 'N', // Southeast Fire Centre
    4: 'V' // Coastal Fire Centre
  }
  return fire_centre_id in fire_centre_to_zone_code_prefix
    ? fire_centre_to_zone_code_prefix[fire_centre_id]
    : null
}

const fireZoneTextStyler = (
  feature: RenderFeature | ol.Feature<Geometry>,
  resolution: number
): Text => {
  const text =
    resolution > 3000
      ? ''
      : construct_zone_code(
          feature.get('fire_centre_feature_id'),
          feature.get('fire_zone_feature_id')
        )
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'grey' }),
    stroke: new Stroke({ color: 'white', width: 1 }),
    font: '15px sans-serif',
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
    // image: new CircleStyle({
    //   radius: 5,
    //   fill: new Fill({
    //     color: 'black'
    //   })
    // })
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
  // NOTE: quick hack to make station styler correspond with theisian polygons
  const colorIdx = Math.floor(feature.get('code') % (hfiColors.length - 1))
  if (colorIdx < 2) {
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
  return new Style({})
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
