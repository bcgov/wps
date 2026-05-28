import { Map, MapBrowserEvent } from 'ol'
import { Coordinate } from 'ol/coordinate'
import { EventsKey } from 'ol/events'
import { unByKey } from 'ol/Observable'
import { Interaction } from 'ol/interaction'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { CurrentFireAttributes } from '@/features/currentFires/map/currentFireLayers'
import { getCurrentFireFeatureAtPixel } from '@/features/currentFires/map/currentFireFeaturePicking'

export interface CurrentFireClickData {
  attributes: CurrentFireAttributes
  coordinate: Coordinate
  pixel: number[]
}

export interface CurrentFiresClickInteractionOptions {
  currentFirePointsLayer: VectorLayer<VectorSource>
  currentFirePolygonsLayer: VectorLayer<VectorSource>
  onFireClick?: (data: CurrentFireClickData) => void
  onMapMiss?: (event: MapBrowserEvent<UIEvent>) => void
  shouldIgnoreClick?: (event: MapBrowserEvent<UIEvent>) => boolean
}

export class CurrentFiresClickInteraction extends Interaction {
  private readonly currentFirePointsLayer: VectorLayer<VectorSource>
  private readonly currentFirePolygonsLayer: VectorLayer<VectorSource>
  private listenerKey?: EventsKey
  private onFireClick?: (data: CurrentFireClickData) => void
  private onMapMiss?: (event: MapBrowserEvent<UIEvent>) => void
  private shouldIgnoreClick?: (event: MapBrowserEvent<UIEvent>) => boolean

  constructor(options: CurrentFiresClickInteractionOptions) {
    super()
    this.currentFirePointsLayer = options.currentFirePointsLayer
    this.currentFirePolygonsLayer = options.currentFirePolygonsLayer
    this.onFireClick = options.onFireClick
    this.onMapMiss = options.onMapMiss
    this.shouldIgnoreClick = options.shouldIgnoreClick
  }

  setMap(map: Map | null) {
    this.removeClickListener()
    super.setMap(map)

    if (map) {
      this.listenerKey = map.on('click', this.handleClick.bind(this))
    }
  }

  setFireClickCallback(callback: (data: CurrentFireClickData) => void) {
    this.onFireClick = callback
  }

  setMapMissCallback(callback: (event: MapBrowserEvent<UIEvent>) => void) {
    this.onMapMiss = callback
  }

  setShouldIgnoreClick(callback: (event: MapBrowserEvent<UIEvent>) => boolean) {
    this.shouldIgnoreClick = callback
  }

  dispose() {
    this.removeClickListener()
    super.dispose()
  }

  private handleClick(event: MapBrowserEvent<UIEvent>) {
    if (!this.getActive() || this.shouldIgnoreClick?.(event)) {
      return
    }

    const fireFeature = getCurrentFireFeatureAtPixel(
      event.map,
      event.pixel,
      this.currentFirePointsLayer,
      this.currentFirePolygonsLayer
    )

    if (!fireFeature) {
      this.onMapMiss?.(event)
      return
    }

    this.onFireClick?.({
      attributes: fireFeature.attributes,
      coordinate: event.coordinate,
      pixel: event.pixel
    })
  }

  private removeClickListener() {
    if (this.listenerKey) {
      unByKey(this.listenerKey)
      this.listenerKey = undefined
    }
  }
}
