import { PMTilesVectorSource } from 'ol-pmtiles'
import { API_BASE_URL, PMTILES_BUCKET, PSU_BUCKET } from 'utils/env'
import {
  fuelCOGColourExpression,
  getFireWeatherColourExpression,
  snowStyler
} from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { DateTime } from 'luxon'
import WebGLTile from 'ol/layer/WebGLTile'
import GeoTIFF from 'ol/source/GeoTIFF'
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
import { boundingExtent } from 'ol/extent'
import { fromLonLat } from 'ol/proj'
import { BC_EXTENT } from '@/utils/constants'

// Register BC Lambert Conformal Conic projection
const bcLccProj = '+proj=lcc +lat_0=49 +lon_0=-125 +lat_1=49 +lat_2=77 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
proj4.defs('BC_LCC', bcLccProj)
register(proj4)

export const BASEMAP_LAYER_NAME = 'basemapLayer'
export const SNOW_LAYER_NAME = 'snowVector'
export const FWI_LAYER_NAME = 'fwiRaster'

export type FireWeatherRasterType = 'fwi' | 'dmc' | 'dc' | 'ffmc' | 'bui' | 'isi'

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

export const getFireWeatherRasterLayer = (
  date: DateTime,
  rasterType: FireWeatherRasterType,
  token: string | undefined,
  layerName: string = FWI_LAYER_NAME
) => {
  const dateString = date.toISODate() ?? '' // Format: YYYY-MM-DD
  // Use API proxy to bypass CORS restrictions
  const path = `sfms/calculated/forecast/${dateString}/${rasterType}${dateString.replace(/-/g, '')}.tif`
  const url = `${API_BASE_URL}/object-store-proxy/${path}`

  // Prepare headers for authentication
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const source = new GeoTIFF({
    sources: [{ url, nodata: -3.4028235e38 }],
    sourceOptions: {
      // Pass custom headers to geotiff.js
      headers
    },
    interpolate: false,
    normalize: false,
    projection: 'BC_LCC'
  })

  const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

  const layer = new WebGLTile({
    source: source,
    zIndex: 52,
    opacity: 0.6,
    extent: bcExtent,
    properties: { name: layerName, rasterType },
    style: {
      color: getFireWeatherColourExpression(rasterType)
    }
  })

  return layer
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
