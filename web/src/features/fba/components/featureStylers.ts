import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'

const createTextStyle = (feature: RenderFeature | ol.Feature<Geometry>) => {
  return new Text({
    text: feature.getProperties().mof_fire_centre_name,
    fill: new Fill({ color: 'black' }),
    stroke: new Stroke({ color: 'black', width: 1 })
  })
}

export const fireCenterStyler = (
  feature: RenderFeature | ol.Feature<Geometry>
): Style => {
  return new Style({
    stroke: new Stroke({
      color: 'black',
      width: 3
    }),
    text: createTextStyle(feature)
  })
}
