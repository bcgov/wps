import { Map } from 'ol'
import WebGLTileLayer from 'ol/layer/WebGLTile'
import VectorTileLayer from 'ol/layer/VectorTile'
import { FWI_LAYER_NAME } from './layerDefinitions'

export type ManagedLayer = WebGLTileLayer | VectorTileLayer

export interface RasterError {
  type: 'not_found' | 'forbidden' | 'network' | 'unknown'
  message: string
  statusCode?: number
}

export interface LayerManagerOptions {
  onLoadingChange?: (isLoading: boolean, error?: RasterError) => void
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
  private onLoadingChange?: (isLoading: boolean, error?: RasterError) => void
  private layerName: string
  private trackLoading: boolean
  private timeoutId?: number

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
        let hasLoaded = false

        // Listen for successful tile loads
        source.on('tileloadend', () => {
          hasLoaded = true
          this.setLoadingState(false)
        })

        // Listen for tile loading errors (once to avoid duplicate notifications)
        source.once('tileloaderror', (event: any) => {
          const error = this.extractErrorFromEvent(event)
          this.setLoadingState(false, error)
        })

        // Listen for source-level errors (e.g., GeoTIFF initialization failures)
        source.once('error', (event: any) => {
          const error = this.extractErrorFromEvent(event)
          this.setLoadingState(false, error)
        })

        // Monitor source state changes to catch initialization errors (check only once)
        const checkSourceError = () => {
          const state = source.getState()
          if (state === 'error' && !hasLoaded) {
            const error = this.extractErrorFromEvent({})
            this.setLoadingState(false, error)
            source.un('change', checkSourceError)
          }
        }
        source.on('change', checkSourceError)

        // Safety timeout: if nothing loads after 10 seconds, show error
        this.timeoutId = window.setTimeout(() => {
          const state = source.getState()
          if (!hasLoaded && state !== 'ready') {
            const error = this.extractErrorFromEvent({})
            this.setLoadingState(false, error)
          }
        }, 10000)
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

    // Clear timeout if it exists
    if (this.timeoutId) {
      clearTimeout(this.timeoutId)
      this.timeoutId = undefined
    }

    // Remove event listeners from source
    const source = this.currentLayer.getSource()
    if (source) {
      source.un('tileloadend', () => {})
      source.un('tileloaderror', () => {})
      source.un('error', () => {})
      source.un('change', () => {})
    }

    this.map.removeLayer(this.currentLayer)
    this.currentLayer = null
  }

  /**
   * Set loading state and notify callback
   */
  private setLoadingState(isLoading: boolean, error?: RasterError) {
    if (this.onLoadingChange) {
      this.onLoadingChange(isLoading, error)
    }
  }

  /**
   * Extract error information from tile load error event
   * Since OpenLayers doesn't expose HTTP status codes, we use 'not_found' as the default
   * error type since the most common case is that data doesn't exist for the requested date
   */
  private extractErrorFromEvent(event: any): RasterError {
    // Default to 'not_found' which is the most common scenario
    // This will display as a warning (orange) rather than an error (red)
    const errorType: RasterError['type'] = 'not_found'
    const message = 'Raster data not available for this date'

    return {
      type: errorType,
      message
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
