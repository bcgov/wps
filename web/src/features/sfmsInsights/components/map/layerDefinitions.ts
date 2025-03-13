import { PMTilesVectorSource } from 'ol-pmtiles'
import { PMTILES_BUCKET } from 'utils/env'
import { snowStyler, styleFuelGrid } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { XYZ } from 'ol/source'
import TileLayer from 'ol/layer/Tile'
import { DateTime } from 'luxon'

export const BC_ROAD_BASE_MAP_SERVER_URL = 'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'
export const SNOW_LAYER_NAME = 'snowVector'

const basemapSource = new XYZ({
    url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`
  })

export const basemapLayer = new TileLayer({source: basemapSource})


const fuelGridVectorSource = new PMTilesVectorSource({
url: `${PMTILES_BUCKET}fuel/fbp2024.pmtiles`
})

export const fuelGridVTL = new VectorTileLayer({
source: fuelGridVectorSource,
style: styleFuelGrid(),
zIndex: 51,
opacity: 0.6
})

export const getSnowPMTilesLayer = (snowDate: DateTime) => {
  const url = `${PMTILES_BUCKET}snow/${snowDate.toISODate()}/snowCoverage${snowDate.toISODate({format: 'basic' })}.pmtiles`
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

