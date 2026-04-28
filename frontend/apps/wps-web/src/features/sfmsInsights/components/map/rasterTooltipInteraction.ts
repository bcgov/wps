import { Interaction } from 'ol/interaction'
import { MapBrowserEvent } from 'ol'
import { EventsKey } from 'ol/events'
import { unByKey } from 'ol/Observable'
import { findRasterLayer, getDataAtPixel } from './rasterTooltipHandler'

export interface RasterTooltipData {
  value: number | string | null
  label: string
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
  private handlePointerMove(event: MapBrowserEvent<UIEvent>) {
    const map = event.map
    const pixel = map.getEventPixel(event.originalEvent) as [number, number]

    // Find the fire weather raster layer
    const rasterLayer = findRasterLayer(map.getLayers().getArray())

    if (rasterLayer && this.onTooltipChange) {
      // Get tooltip data from the raster layer at the pixel location
      const { value, label } = getDataAtPixel(rasterLayer, pixel)

      // Emit the tooltip data
      this.onTooltipChange({
        value,
        label,
        pixel
      })
    }
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
