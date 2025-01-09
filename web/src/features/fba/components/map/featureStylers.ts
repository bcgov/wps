import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import CircleStyle from 'ol/style/Circle'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'
import { range, startCase, lowerCase, isUndefined } from 'lodash'
import { FireCenter, FireShape, FireShapeArea } from 'api/fbaAPI'
import { MORECAST_MODEL_COLORS } from 'app/theme'

const GREY_FILL = 'rgba(128, 128, 128, 0.8)'
const EMPTY_FILL = 'rgba(0, 0, 0, 0.0)'
export const ADVISORY_ORANGE_FILL = 'rgba(255, 147, 38, 0.4)'
export const ADVISORY_RED_FILL = 'rgba(128, 0, 0, 0.4)'

export const ADVISORY_RED_LINE = 'rgba(238, 0, 0, 1)'
export const ADVISORY_ORANGE_LINE = 'rgba(219, 135, 1, 1)'
const ADVISORY_GREY_LINE = 'rgba(127, 127, 127, 1)'

export const HFI_ADVISORY = 'rgba(255, 128, 0, 0.4)'
export const HFI_WARNING = 'rgba(255, 0, 0, 0.4)'

enum FireShapeStatus {
  NONE = 0,
  ADVISORY = 1,
  WARNING = 2
}

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

export const fireCentreStyler = (selectedFireCenter: FireCenter | undefined) => {
  return (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fireCenterId = feature.getProperties().MOF_FIRE_CENTRE_NAME
    const isSelected = selectedFireCenter && fireCenterId == selectedFireCenter.name

    const fillColour = isSelected ? new Fill({ color: EMPTY_FILL }) : new Fill({ color: GREY_FILL })

    return new Style({
      fill: selectedFireCenter ? fillColour : undefined
    })
  }
}

export const fireCentreLineStyler = (selectedFireCenter: FireCenter | undefined) => {
  return (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fireCenterId = feature.getProperties().MOF_FIRE_CENTRE_NAME
    const isSelected = selectedFireCenter && fireCenterId == selectedFireCenter.name

    return new Style({
      stroke: new Stroke({
        color: 'black',
        width: isSelected ? 8 : 3
      })
    })
  }
}

export const fireShapeStyler = (
  fireShapeAreas: FireShapeArea[],
  advisoryThreshold: number,
  showZoneStatus: boolean
) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fire_shape_id = feature.getProperties().OBJECTID
    const fireShapes = fireShapeAreas.filter(f => f.fire_shape_id === fire_shape_id)
    const status = getFireShapeStatus(advisoryThreshold, fireShapes)

    return new Style({
      stroke: new Stroke({
        color: 'black',
        width: 1
      }),
      fill: showZoneStatus ? getAdvisoryFillColor(status) : new Fill({ color: EMPTY_FILL })
    })
  }
  return a
}

export const fireShapeLineStyler = (
  fireShapeAreas: FireShapeArea[],
  advisoryThreshold: number,
  selectedFireShape: FireShape | undefined
) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fire_shape_id = feature.getProperties().OBJECTID
    const fireShapes = fireShapeAreas.filter(f => f.fire_shape_id === fire_shape_id)
    const selected = !!(selectedFireShape?.fire_shape_id && selectedFireShape.fire_shape_id === fire_shape_id)
    const status = getFireShapeStatus(advisoryThreshold, fireShapes)

    return new Style({
      stroke: new Stroke({
        color: selected ? getFireShapeStrokeColor(status) : EMPTY_FILL,
        width: selected ? 8 : 1
      })
    })
  }
  return a
}

const getFireShapeStatus = (advisoryThreshold: number, fireShapeArea?: FireShapeArea[]) => {
  if (isUndefined(fireShapeArea) || fireShapeArea.length === 0) {
    return FireShapeStatus.NONE
  }
  const advisoryThresholdArea = fireShapeArea.find(area => area.threshold == 1)
  const warningThresholdArea = fireShapeArea.find(area => area.threshold == 2)
  const advisoryPercentage = advisoryThresholdArea?.elevated_hfi_percentage ?? 0
  const warningPercentage = warningThresholdArea?.elevated_hfi_percentage ?? 0
  let status = FireShapeStatus.NONE

  if (advisoryPercentage + warningPercentage > advisoryThreshold) {
    status = FireShapeStatus.ADVISORY
  }

  if (warningPercentage > advisoryThreshold) {
    status = FireShapeStatus.WARNING
  }

  return status
}

const getFireShapeStrokeColor = (fireShapeStatus: FireShapeStatus) => {
  switch (fireShapeStatus) {
    case FireShapeStatus.ADVISORY:
      return ADVISORY_ORANGE_LINE
    case FireShapeStatus.WARNING:
      return ADVISORY_RED_LINE
    default:
      return ADVISORY_GREY_LINE
  }
}

export const getAdvisoryFillColor = (fireShapeStatus: FireShapeStatus) => {
  switch (fireShapeStatus) {
    case FireShapeStatus.ADVISORY:
      return new Fill({ color: ADVISORY_ORANGE_FILL })
    case FireShapeStatus.WARNING:
      return new Fill({ color: ADVISORY_RED_FILL })
    default:
      return new Fill({ color: EMPTY_FILL })
  }
}

/**
 * Given an OpenLayers feature from the fire zone unit label layer, return a label to display on the map.
 * @param feature The feature of interest from the fire zone unit layer.
 * @returns A string to be used as a label on the map.
 */
const getFireZoneUnitLabel = (feature: RenderFeature | ol.Feature<Geometry>) => {
  const fireZoneId = feature.getProperties().FIRE_ZONE_
  let fireZoneUnit = feature.getProperties().FIRE_ZON_1
  // Fire zone unit labels sometimes include a geographic place name as a reference. eg. Skeena Zone (Kalum).
  // If present, we want to display the geographic location on the second line of the label.
  if (fireZoneUnit && fireZoneUnit.indexOf('(') > 0) {
    const index = fireZoneUnit.indexOf('(')
    const prefix = fireZoneUnit.substring(0, index).trim()
    const suffix = fireZoneUnit.substring(index)
    fireZoneUnit = `${prefix}\n${suffix}`
  }

  return `${fireZoneId}-${fireZoneUnit}`
}

export const fireShapeLabelStyler = (selectedFireShape: FireShape | undefined) => {
  const a = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const text = getFireZoneUnitLabel(feature)
    const feature_fire_shape_id = feature.getProperties().OBJECTID
    const selected =
      !isUndefined(selectedFireShape) && feature_fire_shape_id === selectedFireShape.fire_shape_id ? true : false
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

const selectedStationTextStyler = (feature: RenderFeature | ol.Feature<Geometry>): Text => {
  const text = startCase(lowerCase(feature.get('displayLabel')))
  return new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'white', width: 2 }),
    font: '14px sans-serif',
    text: text,
    textBaseline: 'middle',
    textAlign: 'left',
    offsetX: 20,
    offsetY: 0
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

const getCircleStyleByModel = (model: string | undefined) => {
  let fillColor = '#64646470'
  let strokeColor = '#00000070'
  const modelArray = ['hrdps', 'rdps', 'gdps', 'nam', 'gfs']
  const randomModel = modelArray[Math.floor(Math.random() * modelArray.length)]

  if (model) {
    fillColor = MORECAST_MODEL_COLORS[randomModel].mapbg
    strokeColor = MORECAST_MODEL_COLORS[randomModel].border
  }
  return new CircleStyle({
    radius: 15,
    fill: new Fill({
      color: fillColor
    }),
    stroke: new Stroke({
      color: strokeColor,
      width: 2
    })
  })
}

export const selectedStationStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  return new Style({
    image: getCircleStyleByModel(feature.get('model')),
    text: selectedStationTextStyler(feature)
  })
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
    hfiStyle.setFill(new Fill({ color: HFI_ADVISORY }))
  } else if (hfi === 2) {
    hfiStyle.setFill(new Fill({ color: HFI_WARNING }))
  } else {
    hfiStyle.setFill(new Fill({ color: EMPTY_FILL }))
  }
  return hfiStyle
}
