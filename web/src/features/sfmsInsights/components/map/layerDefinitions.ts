import { PMTilesVectorSource } from 'ol-pmtiles'
import { PMTILES_BUCKET, PSU_BUCKET } from 'utils/env'
import { fuelCOGColourExpression, snowStyler } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { XYZ } from 'ol/source'
import TileLayer from 'ol/layer/Tile'
import { DateTime } from 'luxon'
import WebGLTile from 'ol/layer/WebGLTile'
import GeoTIFF from 'ol/source/GeoTIFF'

export const BC_ROAD_BASE_MAP_SERVER_URL = 'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'
export const SNOW_LAYER_NAME = 'snowVector'

const basemapSource = new XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`
})

export const basemapLayer = new TileLayer({ source: basemapSource })

export const getSnowPMTilesLayer = (snowDate: DateTime) => {
  const url = `${PMTILES_BUCKET}snow/${snowDate.toISODate()}/snowCoverage${snowDate.toISODate({ format: 'basic' })}.pmtiles`
  const snowPMTilesSource = new PMTilesVectorSource({
    url
  })
  const snowPMTilesLayer = new VectorTileLayer({
    source: snowPMTilesSource,
    style: snowStyler,
    zIndex: 52,
    minZoom: 4,
    properties: { name: SNOW_LAYER_NAME }
  })
  return snowPMTilesLayer
}

export const fuelGridCOG = new GeoTIFF({
  sources: [
    {
      url: `${PSU_BUCKET}cog/fbp2025_500m_cog.tif`
    }
  ],
  interpolate: false,
  normalize: false // important, otherwise the values will be scaled to 0-1
})

export const fuelCOGTiles = new WebGLTile({
  source: fuelGridCOG,
  zIndex: 51,
  opacity: 0.6,
  style: {
    color: fuelCOGColourExpression()
  }
})
