import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import CircleStyle from 'ol/style/Circle'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'
import { range, startCase, lowerCase, isUndefined } from 'lodash'
import { FireZone, FireZoneArea } from 'api/fbaAPI'

const EMPTY_FILL = 'rgba(0, 0, 0, 0.0)'
const ADVISORY_ORANGE_FILL = 'rgba(255, 147, 38, 0.4)'
const ADVISORY_RED_FILL = 'rgba(128, 0, 0, 0.4)'

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
  selectedFireZone: FireZone | undefined
) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const mof_fire_zone_id = feature.get('MOF_FIRE_ZONE_ID')
    const fireZoneAreaByThreshold = fireZoneAreas.filter(f => f.mof_fire_zone_id === mof_fire_zone_id)
    const selected =
      selectedFireZone?.mof_fire_zone_id && selectedFireZone.mof_fire_zone_id === mof_fire_zone_id ? true : false
    let strokeValue = 'black'
    if (selected) {
      strokeValue = 'green'
    }

    return new Style({
      stroke: new Stroke({
        color: strokeValue,
        width: selected ? 8 : 1
      }),
      fill: getAdvisoryColors(advisoryThreshold, fireZoneAreaByThreshold)
    })
  }
  return a
}

export const getAdvisoryColors = (advisoryThreshold: number, fireZoneArea?: FireZoneArea[]) => {
  let fill = new Fill({ color: EMPTY_FILL })
  if (isUndefined(fireZoneArea) || fireZoneArea.length === 0) {
    return fill
  }

  const advisoryThresholdArea = fireZoneArea.find(area => area.threshold == 1)
  const warningThresholdArea = fireZoneArea.find(area => area.threshold == 2)
  const advisoryPercentage = advisoryThresholdArea?.elevated_hfi_percentage ?? 0
  const warningPercentage = warningThresholdArea?.elevated_hfi_percentage ?? 0

  if (advisoryPercentage + warningPercentage > advisoryThreshold) {
    // advisory color orange
    fill = new Fill({ color: ADVISORY_ORANGE_FILL })
  }

  if (warningPercentage > advisoryThreshold) {
    // advisory color red
    fill = new Fill({ color: ADVISORY_RED_FILL })
  }

  return fill
}

export const fireZoneLabelStyler = (selectedFireZone: FireZone | undefined) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const text = feature.get('mof_fire_zone_name').replace(' Fire Zone', '\nFire Zone')
    const feature_mof_fire_zone_id = feature.get('mof_fire_zone_id')
    const selected =
      !isUndefined(selectedFireZone) && feature_mof_fire_zone_id === selectedFireZone.mof_fire_zone_id ? true : false
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
  const hfi = feature.get('hfi')
  if (hfi === 1) {
    hfiStyle.setFill(new Fill({ color: 'rgba(255, 128, 0, 0.4)' }))
  } else if (hfi === 2) {
    hfiStyle.setFill(new Fill({ color: 'rgba(255, 0, 0, 0.4)' }))
  } else {
    hfiStyle.setFill(new Fill({ color: 'rgba(0, 0, 0, 0)' }))
  }
  return hfiStyle
}
