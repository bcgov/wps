import { Interaction } from 'ol/interaction'
import type { MapBrowserEvent } from 'ol'
import type Map from 'ol/Map'
import type Overlay from 'ol/Overlay'
import Feature from 'ol/Feature'
import { Point } from 'ol/geom'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { toLonLat } from 'ol/proj'

export interface NewRequestClickData {
  lat: number
  lon: number
  coordinate: number[]
}

const PENDING_MARKER_STYLE = new Style({
  image: new CircleStyle({
    radius: 8,
    fill: new Fill({ color: '#fe6900' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 })
  })
})

export class NewRequestClickInteraction extends Interaction {
  private readonly overlay: Overlay
  private readonly onEmptyClick: (data: NewRequestClickData) => void
  private readonly onDismiss: () => void
  private popupOpen = false

  private readonly pendingMarkerSource = new VectorSource<Feature<Point>>()
  private readonly pendingMarkerLayer = new VectorLayer({
    source: this.pendingMarkerSource,
    style: PENDING_MARKER_STYLE,
    zIndex: 60
  })

  private readonly shouldIgnoreClick?: (event: MapBrowserEvent<UIEvent>) => boolean

  constructor(options: {
    overlay: Overlay
    onEmptyClick: (data: NewRequestClickData) => void
    onDismiss: () => void
    shouldIgnoreClick?: (event: MapBrowserEvent<UIEvent>) => boolean
  }) {
    super()
    this.overlay = options.overlay
    this.onEmptyClick = options.onEmptyClick
    this.onDismiss = options.onDismiss
    this.shouldIgnoreClick = options.shouldIgnoreClick
  }

  override setMap(map: Map | null) {
    this.getMap()?.removeLayer(this.pendingMarkerLayer)
    super.setMap(map)
    map?.addLayer(this.pendingMarkerLayer)
  }

  override handleEvent(event: MapBrowserEvent<UIEvent>): boolean {
    if (event.type !== 'click') return true

    if (this.popupOpen) {
      this.clearPopup()
      this.onDismiss()
      // let the event through if a feature was clicked so other handlers can open its popup
      return !!event.map.forEachFeatureAtPixel(event.pixel, () => true)
    }

    if (this.shouldIgnoreClick?.(event)) return true

    const [lon, lat] = toLonLat(event.coordinate)
    this.overlay.setPosition(event.coordinate)
    this.pendingMarkerSource.addFeature(new Feature({ geometry: new Point(event.coordinate) }))
    this.popupOpen = true
    this.onEmptyClick({ lat, lon, coordinate: event.coordinate })
    return false
  }

  close() {
    this.clearPopup()
  }

  private clearPopup() {
    this.overlay.setPosition(undefined)
    this.pendingMarkerSource.clear()
    this.popupOpen = false
  }

  override dispose() {
    this.getMap()?.removeLayer(this.pendingMarkerLayer)
    super.dispose()
  }
}
