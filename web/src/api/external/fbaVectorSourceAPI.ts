import EsriJSON from 'ol/format/EsriJSON'
import VectorSource from 'ol/source/Vector'
import Projection from 'ol/proj/Projection'
import Geometry from 'ol/geom/Geometry'
import { VectorDataManager } from 'api/external/VectorDataManager'

export type FireLayer = '2' | '8'
export const fireCenterLayer: FireLayer = '2'
export const fireZoneLayer: FireLayer = '8'

const vectorDataManager = new VectorDataManager()
/**
 * Retrieves fire center polygons from maps.gov.bc.ca arcserver
 * Requests are made dynamically as an openlayers vector source.
 *
 * @param extent Current extent of the view
 * @param projection Current projection
 * @param vectorSource the source to add the requested features to
 */
export const getFireCenterVectorSource = async (
  layer: FireLayer,
  extent: number[],
  projection: Projection,
  vectorSource: VectorSource<Geometry>
): Promise<void> => {
  const esriJsonFormat = new EsriJSON()
  const data = await vectorDataManager.getOrSet(layer, extent)
  const features = esriJsonFormat.readFeatures(data, {
    featureProjection: projection
  })
  if (features.length > 0) {
    vectorSource.addFeatures(features)
  }
}
