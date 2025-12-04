import axios from 'axios'
import { applyStyle } from 'ol-mapbox-style'
import MVT from 'ol/format/MVT'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/VectorTile'

export const getStyleJson = async (url: string) => {
  try {
    const { data } = await axios.get(url)
    return data
  } catch {
    console.error('Unable to fetch style JSON.')
    return {}
  }
}

export const createVectorTileLayer = async (
  tileUrl: string,
  glstyle: any,
  opacity: number,
  name: string
): Promise<VectorTileLayer> => {
  const source = new VectorSource({
    format: new MVT({ layerName: 'mvt:layer' }),
    url: tileUrl
  })
  const basemapLayer = new VectorTileLayer({
    opacity,
    source
  })
  basemapLayer.set('name', name)
  applyStyle(basemapLayer, glstyle, { updateSource: false })
  return basemapLayer
}

export const createHillshadeVectorTileLayer = async (
  tileUrl: string,
  glstyle: any,
  opacity: number,
  name: string
): Promise<VectorTileLayer> => {
  return await createVectorTileLayer(tileUrl, glstyle, opacity, name)
}
