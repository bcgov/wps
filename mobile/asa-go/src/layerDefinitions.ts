import type { DateTime } from 'luxon'
import MVT from 'ol/format/MVT'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/VectorTile'
import { applyStyle } from 'ol-mapbox-style'
import type { RunType } from '@/api/fbaAPI'
import { localBasemapStyle } from '@/components/map/localBasemapStyle'
import { hfiStyler } from '@/featureStylers'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from '@/utils/env'
import { pmtilesCache } from '@/utils/pmtilesCache'
import { type PMTilesFileVectorOptions, PMTilesFileVectorSource } from '@/utils/pmtilesVectorSource'

export const BASEMAP_LAYER_NAME = 'basemapLayer'
export const LOCAL_BASEMAP_LAYER_NAME = 'localBasemapLayer'
export const HFI_LAYER_NAME = 'hfiVectorLayer'
export const ZONE_STATUS_LAYER_NAME = 'fireShapeVector'

type HFILayerOptions = PMTilesFileVectorOptions & {
  for_date: DateTime
  run_type: RunType
  run_date: DateTime
}

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

export const createLocalBasemapVectorLayer = async () => {
  const filename = 'bc_20250326_z6.pmtiles'
  const localBasemapSource = await PMTilesFileVectorSource.create({ filename }, () =>
    pmtilesCache.loadPMTiles(filename)
  )
  const localBasemapLayer = new VectorTileLayer({
    source: localBasemapSource,
    zIndex: 10
  })
  localBasemapLayer.set('name', LOCAL_BASEMAP_LAYER_NAME)
  applyStyle(localBasemapLayer, localBasemapStyle, { updateSource: false })
  return localBasemapLayer
}

export const createHFILayer = async (options: HFILayerOptions, visible: boolean = true): Promise<VectorTileLayer> => {
  const hfiVectorSource = await PMTilesFileVectorSource.create({ filename: options.filename }, () =>
    pmtilesCache.loadHFIPMTiles(options.for_date, options.run_type, options.run_date, options.filename)
  )
  return new VectorTileLayer({
    source: hfiVectorSource,
    style: hfiStyler,
    zIndex: 51,
    properties: { name: HFI_LAYER_NAME },
    visible: visible
  })
}
