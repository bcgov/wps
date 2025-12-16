import { Map } from 'ol'
import WebGLTileLayer from 'ol/layer/WebGLTile'
import VectorTileLayer from 'ol/layer/VectorTile'
import { FWI_LAYER_NAME } from './layerDefinitions'

export type ManagedLayer = WebGLTileLayer | VectorTileLayer

export interface LayerManagerOptions {
  onLoadingChange?: (isLoading: boolean) => void
  layerName?: string
  trackLoading?: boolean
}

/**
 * Generic layer manager for OpenLayers map layers
 * Supports both WebGLTileLayer (rasters) and VectorTileLayer
 * Handles layer switching and optional loading state tracking
 */
export class LayerManager {
  private map: Map | null = null
  private currentLayer: ManagedLayer | null = null
  private onLoadingChange?: (isLoading: boolean) => void
  private layerName: string
  private trackLoading: boolean

  constructor(options: LayerManagerOptions = {}) {
    this.onLoadingChange = options.onLoadingChange
    this.layerName = options.layerName || FWI_LAYER_NAME
    this.trackLoading = options.trackLoading ?? true
  }

  /**
   * Set the map instance
   */
  setMap(map: Map | null) {
    this.map = map
  }

  /**
   * Update the layer
   * @param layer The layer to add, or null to remove the current layer
   */
  updateLayer(layer: ManagedLayer | null) {
    if (!this.map) {
      return
    }

    // Remove existing layer
    this.removeCurrentLayer()

    // If layer is null, just remove the existing layer and return
    if (!layer) {
      return
    }

    // Set loading state
    if (this.trackLoading) {
      this.setLoadingState(true)
    }

    // Listen for when the source finishes loading
    if (this.trackLoading) {
      const source = layer.getSource()
      if (source) {
        source.on('tileloadend', () => {
          this.setLoadingState(false)
        })
        source.on('tileloaderror', () => {
          this.setLoadingState(false)
        })
      }
    }

    // Add layer to map
    this.map.addLayer(layer)
    this.currentLayer = layer
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

// Export legacy name for backwards compatibility
export { LayerManager as RasterLayerManager }
