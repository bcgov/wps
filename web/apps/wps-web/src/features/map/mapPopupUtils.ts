import Map from 'ol/Map'

export const panMapToFitElement = (map: Map, element: HTMLElement | null, margin = 16) => {
  requestAnimationFrame(() => {
    if (!element) {
      return
    }

    const mapElement = map.getTargetElement()
    const mapRect = mapElement.getBoundingClientRect()
    const elementRect = element.getBoundingClientRect()

    if (elementRect.width === 0 || elementRect.height === 0) {
      return
    }

    let deltaX = 0
    let deltaY = 0

    if (elementRect.left < mapRect.left + margin) {
      deltaX = elementRect.left - (mapRect.left + margin)
    } else if (elementRect.right > mapRect.right - margin) {
      deltaX = elementRect.right - (mapRect.right - margin)
    }

    if (elementRect.top < mapRect.top + margin) {
      deltaY = elementRect.top - (mapRect.top + margin)
    } else if (elementRect.bottom > mapRect.bottom - margin) {
      deltaY = elementRect.bottom - (mapRect.bottom - margin)
    }

    if (deltaX === 0 && deltaY === 0) {
      return
    }

    const view = map.getView()
    const center = view.getCenter()
    if (!center) {
      return
    }

    const centerPixel = map.getPixelFromCoordinate(center)
    const newCenter = map.getCoordinateFromPixel([centerPixel[0] + deltaX, centerPixel[1] + deltaY])
    view.animate({ center: newCenter, duration: 150 })
  })
}
