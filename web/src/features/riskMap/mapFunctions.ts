import { Map } from 'ol'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Feature } from 'ol'
import GeoJSON, { GeoJSONFeatureCollection } from 'ol/format/GeoJSON'

export const getFeaturesFromLayer = (mapInstance: Map | null, layerName: string): Feature[] => {
  if (!mapInstance) {
    console.error('Map instance is not available.')
    return []
  }

  const layers = mapInstance.getLayers().getArray()

  const targetLayer = layers.find(layer => layer.get('name') === layerName) as VectorLayer<VectorSource>

  if (!targetLayer) {
    console.error(`Layer with name '${layerName}' not found.`)
    return []
  }

  const source = targetLayer.getSource()
  if (source instanceof VectorSource) {
    return source.getFeatures()
  }

  console.error('Target layer does not have a valid vector source.')
  return []
}

export const convertFeaturesToGeoJSON = (features: Feature[]): GeoJSONFeatureCollection => {
  const geoJSONFormat = new GeoJSON()

  return geoJSONFormat.writeFeaturesObject(features, {
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857'
  })
}
