import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env'
import { applyStyle } from 'ol-mapbox-style'
import MVT from 'ol/format/MVT'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/VectorTile'

const basemapSource = new VectorSource({
  format: new MVT({ layerName: 'mvt:layer' }),
  url: BASEMAP_TILE_URL
})

export const createBasemapLayer = async () => {
  const basemapLayer = new VectorTileLayer({
    source: basemapSource
  })
  basemapLayer.set('name', BASEMAP_LAYER_NAME)
  // Fetch the style json from ArcGIS Online
  const response = await fetch(BASEMAP_STYLE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  const style = await response.json()
  applyStyle(basemapLayer, style, { updateSource: false })
  return basemapLayer
}
