import { Map, Feature } from 'ol'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import GeoJSON, { GeoJSONFeatureCollection } from 'ol/format/GeoJSON'
import { getCenter } from 'ol/extent'

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

export const findLayerByName = (map: Map, layerName: string): VectorLayer | undefined => {
  const layers = map.getLayers().getArray()
  return layers.find(layer => layer.get('name') === layerName) as VectorLayer | undefined
}

export const zoomToFeatureWithBuffer = (map: Map, id: number, bufferKm: number) => {
  const valuesLayer = findLayerByName(map, 'uploadedValues')
  const feature = valuesLayer?.getSource()?.getFeatureById(id)

  if (feature) {
    const geometry = feature.getGeometry()

    if (geometry) {
      const extent = geometry.getExtent()
      const center = getCenter(extent)

      const buffer = bufferKm * 1000
      const bufferedExtent = [center[0] - buffer, center[1] - buffer, center[0] + buffer, center[1] + buffer]

      const view = map.getView()

      if (view) {
        view.fit(bufferedExtent, {
          duration: 500,
          padding: [50, 50, 50, 50]
        })
      }
    }
  }
}
