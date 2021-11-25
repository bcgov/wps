import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'

const fireCenterLabelStyler = (label: string) => {
  return new Text({
    text: label,
    fill: new Fill({ color: 'black' }),
    font: '16px sans-serif'
  })
}

export const fireCenterStyler = (
  feature: RenderFeature | ol.Feature<Geometry>
): Style => {
  const label = feature.getProperties().mof_fire_centre_name

  return new Style({
    stroke: new Stroke({
      color: 'black',
      width: 3
    }),
    text: fireCenterLabelStyler(label)
  })
}
