import WebGLTileLayer from 'ol/layer/WebGLTile'
import { RasterType, RASTER_CONFIG, FUEL_TYPE_COLORS } from './rasterConfig'
import { isNodataValue } from './sfmsFeatureStylers'

export type RasterValue = number | string | null
export type RasterData = Float32Array | Uint8Array | null
export type RasterTooltipData = { value: RasterValue; label: string }

export interface RasterTooltipResult {
  value: RasterValue
  label: string
  pixelCoords: [number, number]
}

/**
 * Extracts raster value from layer data and determines if it should be displayed
 * This function is pure and can be tested in isolation
 */
export const getRasterTooltipData = (data: RasterData, rasterType: RasterType | undefined): RasterTooltipData => {
  const defaultLabel = rasterType ? RASTER_CONFIG[rasterType].label : 'FWI'

  // Check if we have valid data
  if (!data || data.length === 0 || data[0] === undefined) {
    return { value: null, label: defaultLabel }
  }

  const rawValue = data[0]

  // Check for NaN (can occur when undefined is coerced to number)
  if (Number.isNaN(rawValue)) {
    return { value: null, label: defaultLabel }
  }

  // Filter out nodata values
  if (isNodataValue(rawValue)) {
    return { value: null, label: defaultLabel }
  }

  const roundedValue = Math.round(rawValue)

  // For fuel type, convert numeric value to fuel code
  if (rasterType === 'fuel') {
    // Filter out nodata and invalid values (99, 102, -10000)
    if (roundedValue === 99 || roundedValue === 102 || roundedValue === -10000) {
      return { value: null, label: defaultLabel }
    }

    const fuelType = FUEL_TYPE_COLORS.find(f => f.value === roundedValue)
    return {
      value: fuelType ? fuelType.fuelCode : roundedValue.toString(),
      label: defaultLabel
    }
  }

  // Return valid data for numeric rasters
  return {
    value: roundedValue,
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
export const getRasterType = (layer: WebGLTileLayer): RasterType | undefined => {
  return layer.getProperties()?.rasterType as RasterType | undefined
}

/**
 * Gets raster data from layer at a specific pixel coordinate
 */
export const getRasterData = (layer: WebGLTileLayer, pixel: [number, number]): RasterData => {
  return layer.getData(pixel) as RasterData
}

/**
 * Gets tooltip data from a raster layer at a specific pixel location
 * This orchestrates the extraction of data and tooltip information
 */
export const getDataAtPixel = (layer: WebGLTileLayer, pixel: [number, number]): RasterTooltipData => {
  const data = getRasterData(layer, pixel)
  const rasterType = getRasterType(layer)
  return getRasterTooltipData(data, rasterType)
}
