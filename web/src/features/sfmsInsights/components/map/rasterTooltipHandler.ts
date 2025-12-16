import WebGLTileLayer from 'ol/layer/WebGLTile'
import { FireWeatherRasterType, RASTER_CONFIG } from './rasterConfig'
import { isNodataValue } from './sfmsFeatureStylers'

export interface RasterTooltipResult {
  value: number | null
  label: string
  pixelCoords: [number, number]
}

/**
 * Extracts raster value from layer data and determines if it should be displayed
 * This function is pure and can be tested in isolation
 */
export const getRasterTooltipData = (
  data: Float32Array | Uint8Array | null,
  rasterType: FireWeatherRasterType | undefined
): { value: number | null; label: string } => {
  const defaultLabel = rasterType ? RASTER_CONFIG[rasterType].label : 'FWI'

  // Check if we have valid data
  if (!data || data.length === 0 || data[0] === undefined) {
    return { value: null, label: defaultLabel }
  }

  const rawValue = data[0]

  // Check for NaN (can occur when undefined is coerced to number)
  if (isNaN(rawValue)) {
    return { value: null, label: defaultLabel }
  }

  // Filter out nodata values
  if (isNodataValue(rawValue)) {
    return { value: null, label: defaultLabel }
  }

  // Return valid data
  return {
    value: Math.round(rawValue),
    label: defaultLabel
  }
}

/**
 * Finds the fire weather raster layer from the map layers
 */
export const findRasterLayer = (layers: any[]): WebGLTileLayer | undefined => {
  return layers.find(l => l.getProperties()?.rasterType !== undefined) as WebGLTileLayer | undefined
}

/**
 * Extracts raster type from layer properties
 */
export const getRasterType = (layer: WebGLTileLayer): FireWeatherRasterType | undefined => {
  return layer.getProperties()?.rasterType as FireWeatherRasterType | undefined
}

/**
 * Gets raster data from layer at a specific pixel coordinate
 */
export const getRasterData = (
  layer: WebGLTileLayer,
  pixel: [number, number]
): Float32Array | Uint8Array | null => {
  return layer.getData(pixel) as Float32Array | Uint8Array | null
}

/**
 * Gets tooltip data from a raster layer at a specific pixel location
 * This orchestrates the extraction of data and tooltip information
 */
export const getDataAtPixel = (
  layer: WebGLTileLayer,
  pixel: [number, number]
): { value: number | null; label: string } => {
  const data = getRasterData(layer, pixel)
  const rasterType = getRasterType(layer)
  return getRasterTooltipData(data, rasterType)
}
