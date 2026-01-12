import { PMTilesVectorSource } from 'ol-pmtiles'
import { FetchSource } from 'pmtiles'
import { API_BASE_URL } from 'utils/env'
import {
  fuelCOGColourExpression,
  getFireWeatherColourExpression,
  snowStyler
} from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { DateTime } from 'luxon'
import WebGLTile from 'ol/layer/WebGLTile'
import GeoTIFF from 'ol/source/GeoTIFF'
import { boundingExtent } from 'ol/extent'
import { fromLonLat } from 'ol/proj'
import { BC_EXTENT } from '@/utils/constants'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'

export const BASEMAP_LAYER_NAME = 'basemapLayer'
export const SNOW_LAYER_NAME = 'snowVector'
export const FWI_LAYER_NAME = 'fwiRaster'

export const getSnowPMTilesLayer = (snowDate: DateTime, token?: string) => {
  const isoDate = snowDate.toISODate() ?? ''
  const isoDateBasic = snowDate.toISODate({ format: 'basic' }) ?? ''
  const path = `psu/pmtiles/snow/${isoDate}/snowCoverage${isoDateBasic}.pmtiles`
  const url = `${API_BASE_URL}/object-store-proxy/${path}`

  // Create FetchSource with custom headers for authentication
  const customHeaders = new Headers()
  if (token) {
    customHeaders.set('Authorization', `Bearer ${token}`)
  }
  const fetchSource = new FetchSource(url, token ? customHeaders : undefined)

  const snowPMTilesSource = new PMTilesVectorSource({
    // @ts-expect-error - ol-pmtiles type definition issue: VectorTileSourceOptions already defines url as string,
    // creating an impossible intersection type (string & Source). Runtime works fine as PMTiles accepts Source.
    url: fetchSource
  })

  const snowPMTilesLayer = new VectorTileLayer({
    source: snowPMTilesSource,
    style: snowStyler,
    zIndex: 53,
    minZoom: 4,
    properties: { name: SNOW_LAYER_NAME }
  })
  return snowPMTilesLayer
}

export const getFireWeatherRasterLayer = (
  date: DateTime,
  rasterType: RasterType,
  token: string | undefined,
  layerName: string = FWI_LAYER_NAME
) => {
  const dateString = date.toISODate() ?? '' // Format: YYYY-MM-DD
  // Use API proxy to bypass CORS restrictions
  const path = `sfms/calculated/forecast/${dateString}/${rasterType}${dateString.replaceAll('-', '')}_3857_cog.tif`
  const url = `${API_BASE_URL}/object-store-proxy/${path}`

  // Prepare headers for authentication
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const source = new GeoTIFF({
    sources: [{ url, nodata: -3.4028235e38 }],
    sourceOptions: {
      headers
    },
    interpolate: false,
    normalize: false,
    projection: 'EPSG:3857'
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

export const getFuelGridCOG = (token?: string) => {
  const path = 'psu/cog/fbp2025_500m_cog.tif'
  const url = `${API_BASE_URL}/object-store-proxy/${path}`

  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return new GeoTIFF({
    sources: [
      {
        url,
        nodata: -10000 // Primary nodata value for fuel raster
      }
    ],
    sourceOptions: {
      headers
    },
    interpolate: false,
    normalize: false // important, otherwise the values will be scaled to 0-1
  })
}

export const getFuelCOGTiles = (token?: string) => {
  return new WebGLTile({
    source: getFuelGridCOG(token),
    zIndex: 51,
    opacity: 0.6,
    properties: { rasterType: 'fuel' },
    style: {
      color: fuelCOGColourExpression()
    }
  })
}

/**
 * Get the appropriate raster layer based on type
 * Handles both fire weather rasters (date-dependent) and fuel raster (static)
 */
export const getRasterLayer = (date: DateTime | null, rasterType: RasterType, token: string | undefined) => {
  if (rasterType === 'fuel') {
    return getFuelCOGTiles(token)
  }
  if (!date) {
    console.error('date is required for fire weather rasters')
    return null
  }
  return getFireWeatherRasterLayer(date, rasterType, token)
}
