import type { MapBrowserEvent } from 'ol'
import type { EventsKey } from 'ol/events'
import { Interaction } from 'ol/interaction'
import { unByKey } from 'ol/Observable'
import { SNOW_LAYER_NAME } from './layerDefinitions'
import { RASTER_CONFIG } from './rasterConfig'
import { findRasterLayer, getDataAtPixel, getRasterType, type RasterTooltipValue } from './rasterTooltipHandler'

export interface RasterTooltipData extends RasterTooltipValue {
  snowCovered?: boolean
  pixel: [number, number] | null
}

/**
 * Custom OpenLayers Interaction for raster tooltip
 *
 * Usage:
 * ```typescript
 * const tooltipInteraction = new RasterTooltipInteraction({
 *   onTooltipChange: (data) => {
 *     setRasterValue(data.value)
 *     setRasterLabel(data.label)
 *     setPixelCoords(data.pixel)
 *   }
 * })
 * map.addInteraction(tooltipInteraction)
 *
 * // Later, to disable:
 * map.removeInteraction(tooltipInteraction)
 * ```
 */
export class RasterTooltipInteraction extends Interaction {
  private onTooltipChange?: (data: RasterTooltipData) => void
  private listenerKey?: EventsKey

  constructor(options: { onTooltipChange?: (data: RasterTooltipData) => void } = {}) {
    super()
    this.onTooltipChange = options.onTooltipChange
  }

  /**
   * Called when the interaction is added to a map
   */
  setMap(map: any) {
    // Clean up previous listener if exists
    if (this.listenerKey) {
      unByKey(this.listenerKey)
    }

    // Call parent setMap
    super.setMap(map)

    // Set up new listener if map is provided
    if (map) {
      this.listenerKey = map.on('pointermove', this.handlePointerMove.bind(this))
    }
  }

  /**
   * Handle pointer move events
   */
  private handlePointerMove(event: MapBrowserEvent<PointerEvent>) {
    const map = event.map
    const pixel = map.getEventPixel(event.originalEvent) as [number, number]

    if (!this.onTooltipChange) {
      return
    }

    const rasterLayer = findRasterLayer(map.getLayers().getArray())
    if (!rasterLayer) {
      this.onTooltipChange({ value: null, label: '', pixel: null, snowCovered: false })
      return
    }

    const rasterType = getRasterType(rasterLayer)
    const snowCovered =
      map.forEachFeatureAtPixel(pixel, feature => feature.get('snow') === 1 || undefined, {
        layerFilter: layer => layer.get('name') === SNOW_LAYER_NAME
      }) === true
    const group = rasterType ? RASTER_CONFIG[rasterType].group : undefined
    if (snowCovered && (group === 'fwi' || group === 'fbp')) {
      this.onTooltipChange({ label: '', value: 'Snow', pixel, snowCovered })
      return
    }

    const { value, label } = getDataAtPixel(rasterLayer, pixel)
    if (snowCovered && group === 'fuel' && value === null) {
      this.onTooltipChange({ label: '', value: 'Snow', pixel, snowCovered })
      return
    }
    this.onTooltipChange({ value, label, pixel, snowCovered })
  }

  /**
   * Set the callback function for tooltip changes
   */
  setTooltipCallback(callback: (data: RasterTooltipData) => void) {
    this.onTooltipChange = callback
  }

  /**
   * Clean up when interaction is removed
   */
  dispose() {
    if (this.listenerKey) {
      unByKey(this.listenerKey)
    }
    super.dispose()
  }
}
