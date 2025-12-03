import { BASEMAP_LAYER_NAME } from '@/features/sfmsInsights/components/map/layerDefinitions'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL, HILLSHADE_STYLE_URL, HILLSHADE_TILE_URL } from '@/utils/env'
import axios from 'axios'
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
    opacity: 0.75,
    source: basemapSource
  })
  basemapLayer.set("name", BASEMAP_LAYER_NAME);
  // Get the style json from ArcGIS Online
  const { data } = await axios.get(BASEMAP_STYLE_URL );
  applyStyle(basemapLayer, data, { updateSource: false });
  return basemapLayer;
}

const hillshadeSource = new VectorSource({
  format: new MVT({ layerName: 'mvt:layer' }),
  url: HILLSHADE_TILE_URL
})

export const createHillshadeLayer = async () => {
  const hillshadeLayer = new VectorTileLayer({
    renderMode: "vector",
    source: hillshadeSource
  })
  // Get the style json from ArcGIS Online
  const { data } = await axios.get(HILLSHADE_STYLE_URL);
  applyStyle(hillshadeLayer, data, 'hillshade', { updateSource: false });
  return hillshadeLayer;
}


