import type { FireCentre } from '@wps/types/fireCentre'
import type * as ol from 'ol'
import type Geometry from 'ol/geom/Geometry'
import type RenderFeature from 'ol/render/Feature'
import { Fill, Stroke } from 'ol/style'
import Style from 'ol/style/Style'

const GREY_FILL = 'rgba(128, 128, 128, 0.8)'
const EMPTY_FILL = 'rgba(0, 0, 0, 0.0)'

export const fireCentreStyler = (selectedFireCentre: FireCentre | undefined) => {
  return (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fireCentreId = feature.getProperties().MOF_FIRE_CENTRE_NAME
    const isSelected = selectedFireCentre && fireCentreId === selectedFireCentre.name

    const fillColour = isSelected ? new Fill({ color: EMPTY_FILL }) : new Fill({ color: GREY_FILL })

    return new Style({
      fill: selectedFireCentre ? fillColour : undefined
    })
  }
}

export const fireCentreLineStyler = (selectedFireCentre: FireCentre | undefined) => {
  return (feature: RenderFeature | ol.Feature<Geometry>): Style => {
    const fireCentreId = feature.getProperties().MOF_FIRE_CENTRE_NAME
    const isSelected = selectedFireCentre && fireCentreId === selectedFireCentre.name

    return new Style({
      stroke: new Stroke({
        color: 'black',
        width: isSelected ? 8 : 3
      })
    })
  }
}
