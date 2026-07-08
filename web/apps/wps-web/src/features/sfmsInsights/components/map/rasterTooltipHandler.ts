import type WebGLTileLayer from 'ol/layer/WebGLTile'
import { FUEL_TYPE_COLORS, RASTER_CONFIG, type RasterType } from './rasterConfig'
import { isNodataValue } from './sfmsFeatureStylers'

export type RasterValue = number | string | null
export type RasterData = Float32Array | Uint8Array | null
export type RasterTooltipData = { value: RasterValue; label: string }

export interface RasterTooltipResult {
  value: RasterValue
  label: string
  pixelCoords: [number, number]
}

const ALPHA_BAND_INDEX = 1

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
  const alphaValue = data[ALPHA_BAND_INDEX]

  // openlayers appends an alpha band when GeoTIFF nodata exists; alpha 0 means
  // the pixel is transparent even when the raster band itself reads back as 0.
  if (data.length > ALPHA_BAND_INDEX && alphaValue === 0) {
    return { value: null, label: defaultLabel }
  }

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
    const fuelType = FUEL_TYPE_COLORS.find(f => f.value === roundedValue)
    return {
      value: fuelType ? fuelType.fuelCode : null,
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
