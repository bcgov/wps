import EsriJSON from 'ol/format/EsriJSON'
import VectorSource from 'ol/source/Vector'
import Projection from 'ol/proj/Projection'
import Geometry from 'ol/geom/Geometry'
import { VectorDataManager } from 'api/external/VectorDataManager'
import { Feature } from 'ol'

export type FireLayer = '2' | '8'
export const fireCenterLayer: FireLayer = '2'
export const fireZoneLayer: FireLayer = '8'

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
  vectorSource: VectorSource<Geometry>,
  success: ((arg0: Feature<any>[]) => void) | undefined
): Promise<void> => {
  const vectorDataManager = new VectorDataManager()
  await vectorDataManager.init()

  const data = await vectorDataManager.getOrSet(layer, extent)
  const features = new EsriJSON().readFeatures(data, {
    featureProjection: projection
  })
  if (features.length > 0) {
    vectorSource.addFeatures(features)
    if (success) {
      success(features)
    }
  }
}
