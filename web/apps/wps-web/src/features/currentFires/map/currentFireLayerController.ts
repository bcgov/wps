import {
  createCurrentFirePointStyle,
  createCurrentFirePointsLayer,
  createCurrentFirePolygonStyle,
  createCurrentFirePolygonsLayer
} from '@/features/currentFires/map/currentFireLayers'

export interface CurrentFireLayers {
  pointsLayer: ReturnType<typeof createCurrentFirePointsLayer>
  polygonsLayer: ReturnType<typeof createCurrentFirePolygonsLayer>
}

export class CurrentFireLayerController {
  private readonly layers: CurrentFireLayers

  constructor(layers: CurrentFireLayers) {
    this.layers = layers
  }

  setVisible(visible: boolean) {
    this.layers.pointsLayer.setVisible(visible)
    this.layers.polygonsLayer.setVisible(visible)
  }

  setStatuses(statuses: readonly string[]) {
    this.layers.pointsLayer.setStyle(createCurrentFirePointStyle(statuses))
    this.layers.polygonsLayer.setStyle(createCurrentFirePolygonStyle(statuses))
  }
}
