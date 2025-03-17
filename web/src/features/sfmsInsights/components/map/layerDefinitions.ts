import { PMTilesVectorSource } from 'ol-pmtiles'
import { PMTILES_BUCKET } from 'utils/env'
import { snowStyler, styleFuelGrid } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { XYZ } from 'ol/source'
import TileLayer from 'ol/layer/Tile'
import { DateTime } from 'luxon'

export const BC_ROAD_BASE_MAP_SERVER_URL = 'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'
export const SNOW_LAYER_NAME = 'snowVector'
const FBP_ZOOM_THRESHOLD = 8

const basemapSource = new XYZ({
    url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`
  })

export const basemapLayer = new TileLayer({source: basemapSource})


const fuelGrid2000mVectorSource = new PMTilesVectorSource({
url: `${PMTILES_BUCKET}fuel/fbp2024.pmtiles`
})

// Coarse fuel grid layer visible at low zoom levels (levels 1-8).
export const fuelGrid2000mVTL = new VectorTileLayer({
  source: fuelGrid2000mVectorSource,
  style: styleFuelGrid(),
  zIndex: 51,
  opacity: 0.6,
  maxZoom: FBP_ZOOM_THRESHOLD
})

const fuelGrid500mVectorSource = new PMTilesVectorSource({
  url: `${PMTILES_BUCKET}fuel/fbp2024_500m.pmtiles`
})

// Fine fuel grid layer visible at zoom levels > 8. At zoom levels < 8 the high number of features in the 500m fuel grid tif leads to
// tiles that are too large (>500KB) and features get removed from the tile. We work around this by displaying the 2000m grid at low
// zoom levels and the 500m grid at higher zoom levels.
export const fuelGrid500mVTL = new VectorTileLayer({
  source: fuelGrid500mVectorSource,
  style: styleFuelGrid(),
  zIndex: 51,
  opacity: 0.6,
  minZoom: FBP_ZOOM_THRESHOLD
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

