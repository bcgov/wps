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
import { boundingExtent } from 'ol/extent'
import { fromLonLat } from 'ol/proj'
import { BC_EXTENT } from '@/utils/constants'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'

export const BASEMAP_LAYER_NAME = 'basemapLayer'
export const SNOW_LAYER_NAME = 'snowVector'
export const FWI_LAYER_NAME = 'fwiRaster'

export const getSnowPMTilesLayer = (snowDate: DateTime) => {
  const url = `${PMTILES_BUCKET}snow/${snowDate.toISODate()}/snowCoverage${snowDate.toISODate({ format: 'basic' })}.pmtiles`
  const snowPMTilesSource = new PMTilesVectorSource({
    url
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
      // Pass custom headers to geotiff.js
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

export const fuelGridCOG = new GeoTIFF({
  sources: [
    {
      url: `${PSU_BUCKET}cog/fbp2025_500m_cog.tif`,
      nodata: -10000 // Primary nodata value for fuel raster
    }
  ],
  interpolate: false,
  normalize: false // important, otherwise the values will be scaled to 0-1
})

export const fuelCOGTiles = new WebGLTile({
  source: fuelGridCOG,
  zIndex: 51,
  opacity: 0.6,
  properties: { rasterType: 'fuel' },
  style: {
    color: fuelCOGColourExpression()
  }
})

/**
 * Get the appropriate raster layer based on type
 * Handles both fire weather rasters (date-dependent) and fuel raster (static)
 */
export const getRasterLayer = (date: DateTime, rasterType: RasterType, token: string | undefined) => {
  if (rasterType === 'fuel') {
    return fuelCOGTiles
  }
  return getFireWeatherRasterLayer(date, rasterType, token)
}
