import * as ol from 'ol'
import RenderFeature from 'ol/render/Feature'
import Geometry from 'ol/geom/Geometry'
import { Fill, Stroke, Text } from 'ol/style'
import Style from 'ol/style/Style'

const fireCenterLabelStyle = new Style({
  stroke: new Stroke({
    color: 'black',
    width: 3
  }),
  text: new Text({
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
