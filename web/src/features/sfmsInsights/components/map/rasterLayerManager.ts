import { Map } from 'ol'
import WebGLTileLayer from 'ol/layer/WebGLTile'
import { FireWeatherRasterType } from './rasterConfig'
import { getFireWeatherRasterLayer, FWI_LAYER_NAME } from './layerDefinitions'
import { DateTime } from 'luxon'

export interface RasterLayerManagerOptions {
  onLoadingChange?: (isLoading: boolean) => void
  layerName?: string
}

/**
 * Manages fire weather raster layers on an OpenLayers map
 * Handles layer switching and loading state
 */
export class RasterLayerManager {
  private map: Map | null = null
  private currentLayer: WebGLTileLayer | null = null
  private onLoadingChange?: (isLoading: boolean) => void
  private layerName: string

  constructor(options: RasterLayerManagerOptions = {}) {
    this.onLoadingChange = options.onLoadingChange
    this.layerName = options.layerName || FWI_LAYER_NAME
  }

  /**
   * Set the map instance
   */
  setMap(map: Map | null) {
    this.map = map
  }

  /**
   * Update the raster layer
   */
  updateLayer(rasterDate: DateTime, rasterType: FireWeatherRasterType, token: string | undefined) {
    if (!this.map || !token) {
      return
    }

    // Remove existing layer
    this.removeCurrentLayer()

    // Set loading state
    this.setLoadingState(true)

    // Create new layer
    const rasterLayer = getFireWeatherRasterLayer(rasterDate, rasterType, token, this.layerName)

    // Listen for when the source finishes loading
    const source = rasterLayer.getSource()
    if (source) {
      source.on('tileloadend', () => {
        this.setLoadingState(false)
      })
      source.on('tileloaderror', () => {
        this.setLoadingState(false)
      })
    }

    // Add layer to map
    this.map.addLayer(rasterLayer)
    this.currentLayer = rasterLayer
  }

  /**
   * Remove the current layer from the map
   */
  private removeCurrentLayer() {
    if (!this.map || !this.currentLayer) {
      return
    }

    this.map.removeLayer(this.currentLayer)
    this.currentLayer = null
  }

  /**
   * Set loading state and notify callback
   */
  private setLoadingState(isLoading: boolean) {
    if (this.onLoadingChange) {
      this.onLoadingChange(isLoading)
    }
  }

  /**
   * Clean up
   */
  dispose() {
    this.removeCurrentLayer()
    this.map = null
  }
}
