import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import CircleStyle from 'ol/style/Circle'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'
import { range, startCase, lowerCase, isUndefined } from 'lodash'
import { FireZoneArea } from 'api/fbaAPI'

const fireCentreTextStyler = (feature: RenderFeature | ol.Feature<Geometry>): Text => {
  const text = feature.get('mof_fire_centre_name').replace(' Fire Centre', '\nFire Centre')
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 2 }),
    font: 'bold 16px sans-serif',
    text: text
  })
}

export const fireCentreLabelStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  return new Style({
    text: fireCentreTextStyler(feature)
  })
}

export const fireCentreStyler = (): Style => {
  return new Style({
    stroke: new Stroke({
      color: 'black',
      width: 3
    })
  })
}

export const fireZoneStyler = (
  fireZoneAreas: FireZoneArea[],
  advisoryThreshold: number,
  selectedFireZoneID: number | null
) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const mof_fire_zone_id = feature.get('mof_fire_zone_id')
    const fireZoneArea = fireZoneAreas.find(f => f.mof_fire_zone_id === mof_fire_zone_id)
    const advisory = fireZoneArea && fireZoneArea.elevated_hfi_percentage > advisoryThreshold ? true : false
    const selected = selectedFireZoneID && selectedFireZoneID === mof_fire_zone_id ? true : false
    let strokeValue = 'black'
    if (selected) {
      strokeValue = 'green'
    } else if (advisory) {
      strokeValue = 'red'
    }

    return new Style({
      stroke: new Stroke({
        color: strokeValue,
        width: selected ? 8 : 1
      }),
      fill: getAdvisoryFill(advisoryThreshold, fireZoneArea)
    })
  }
  return a
}

export const getAdvisoryFill = (advisoryThreshold: number, fireZoneArea?: FireZoneArea) => {
  if (isUndefined(fireZoneArea)) {
    return new Fill({ color: 'rgba(0, 0, 0, 0.0)' })
  }

  let fill = new Fill({ color: 'rgba(0, 0, 0, 0.0)' })
  if (fireZoneArea.threshold == 1 && fireZoneArea.elevated_hfi_percentage > advisoryThreshold) {
    // advisory color orange
    fill = new Fill({ color: 'rgba(255, 147, 38, 0.4)' })
  }

  if (fireZoneArea.threshold == 2 && fireZoneArea.elevated_hfi_percentage > advisoryThreshold) {
    // advisory color red
    fill = new Fill({ color: 'rgba(128, 0, 0, 0.4)' })
  }

  return fill
}

export const fireZoneLabelStyler = (selectedZoneID: number | null) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const text = feature.get('mof_fire_zone_name').replace(' Fire Zone', '\nFire Zone')
    const mof_fire_zone_id = feature.get('mof_fire_zone_id')
    const selected = selectedZoneID && mof_fire_zone_id === selectedZoneID ? true : false
    return new Style({
      text: new Text({
        overflow: true,
        fill: new Fill({
          color: selected ? 'green' : 'black'
        }),
        stroke: new Stroke({
          color: 'white',
          width: selected ? 4 : 2
        }),
        font: selected ? 'bold 20px sans-serif' : 'bold 15px sans-serif',
        text: text
      })
    })
  }
  return a
}

const stationTextStyler = (feature: RenderFeature | ol.Feature<Geometry>): Text => {
  const text = startCase(lowerCase(feature.get('name')))
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 2 }),
    font: '11px sans-serif',
    text: text,
    textBaseline: 'middle',
    textAlign: 'left',
    offsetX: 9,
    offsetY: 1
  })
}

export const stationStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  // NOTE: quick hack to make station styler correspond with theisian polygons - this code needs to be fixed
  // once we have the polygon implementation in place.
  const colorIdx = Math.floor(feature.get('code') % (hfiColors.length - 1))
  if (colorIdx < 2) {
    return new Style({
      image: new CircleStyle({
        radius: 5,
        fill: new Fill({
          color: 'black'
        })
      }),
      text: stationTextStyler(feature)
    })
  }
  return new Style({})
}

/**
 * Throwaway code, just for demo purposes.
 *
 * 20 times more likely not to have a HFI critical threshold color. 4000 and 10000 equally likely.
 */
const hfiColors = [new Fill({ color: 'rgba(255, 0, 0, 0.4)' }), new Fill({ color: 'rgba(255, 128, 0, 0.4)' })].concat(
  range(20).flatMap(() => new Fill({ color: 'rgba(0, 0, 0, 0)' }))
)

const hfiStyle = new Style({})

export const hfiStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  if (feature.get('hfi') === '4000 < hfi < 10000') {
    hfiStyle.setFill(new Fill({ color: 'rgba(255, 128, 0, 0.4)' }))
  } else if (feature.get('hfi') === 'hfi >= 10000') {
    hfiStyle.setFill(new Fill({ color: 'rgba(255, 0, 0, 0.4)' }))
  }
  return hfiStyle
}
