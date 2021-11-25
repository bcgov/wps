import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'
import { range } from 'lodash'

const fireCenterLabelStyle = new Style({
  stroke: new Stroke({
    color: 'black',
    width: 3
  }),
  text: new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'black' }),
    font: '16px sans-serif'
  })
})

export const fireCenterStyler = (
  feature: RenderFeature | ol.Feature<Geometry>
): Style => {
  fireCenterLabelStyle.getText().setText(feature.get('mof_fire_centre_name'))
  return fireCenterLabelStyle
}

const fireZoneLabelStyle = new Style({
  stroke: new Stroke({
    color: 'black',
    width: 2
  }),
  text: new Text({
    overflow: true,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'black' }),
    font: '12px sans-serif'
  })
})
export const fireZoneStyler = (feature: RenderFeature | ol.Feature<Geometry>): Style => {
  fireZoneLabelStyle.getText().setText(feature.get('mof_fire_zone_name'))
  return fireZoneLabelStyle
}

const thessianPolygonStyle = new Style({
  stroke: new Stroke({
    color: 'green',
    width: 1
  })
})

/**
 * Throwaway code, just for demo purposes.
 *
 * 10 times more likely not to have a HFI critical threshold color. 4000 and 10000 equally likely.
 */
const hfiColors = [
  new Fill({ color: 'rgba(255, 0, 0, 0.4)' }),
  new Fill({ color: 'rgba(255, 128, 0, 0.4)' })
].concat(range(10).flatMap(() => new Fill({ color: 'rgba(0, 0, 0, 0)' })))

export const thessianPolygonStyler = (): Style => {
  const colorIdx = Math.floor(Math.random() * hfiColors.length - 1)
  thessianPolygonStyle.setFill(hfiColors[colorIdx])
  return thessianPolygonStyle
}
