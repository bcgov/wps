import * as ol from 'ol'
import Geometry from 'ol/geom/Geometry'
import { FireZoneArea } from 'api/fbaAPI'
import RenderFeature from 'ol/render/Feature'
import { Style, Stroke, Fill } from 'ol/style'
import { StyleFunction } from 'ol/style/Style'

export class FeatureStylerBuilder {
  public static createZoneStyler(
    fireZoneAreas: FireZoneArea[],
    advisoryThreshold: number,
    selectedFireZoneID: number | null
  ) {
    return function (feature: RenderFeature | ol.Feature<Geometry>) {
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
        fill: advisory ? new Fill({ color: 'rgba(128, 0, 0, 0.4)' }) : new Fill({ color: 'rgba(0, 0, 0, 0.0)' })
      })
    }
  }
}
