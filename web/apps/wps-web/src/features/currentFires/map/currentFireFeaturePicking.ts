import Map from 'ol/Map'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import {
  CurrentFireAttributes,
  getCurrentFirePointAttributes,
  getCurrentFirePolygonAttributes
} from '@/features/currentFires/map/currentFireLayers'

export interface CurrentFireFeaturePick {
  attributes: CurrentFireAttributes
}

export const getCurrentFireFeatureAtPixel = (
  map: Map,
  pixel: number[],
  currentFirePointsLayer: VectorLayer<VectorSource>,
  currentFirePolygonsLayer: VectorLayer<VectorSource>
): CurrentFireFeaturePick | null => {
  const pointFeature = map.forEachFeatureAtPixel(pixel, (feature, layer) =>
    layer === currentFirePointsLayer ? feature : undefined
  )
  if (pointFeature) {
    return { attributes: getCurrentFirePointAttributes(pointFeature) }
  }

  const polygonFeature = map.forEachFeatureAtPixel(pixel, (feature, layer) =>
    layer === currentFirePolygonsLayer ? feature : undefined
  )
  return polygonFeature ? { attributes: getCurrentFirePolygonAttributes(polygonFeature) } : null
}
