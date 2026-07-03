import {
  FIRE_CENTRE_LAYER_NAME,
  FIRE_CENTRE_LINE_LAYER_NAME,
  getFireCentreLinePMTilesLayer,
  getFireCentrePMTilesLayers
} from '@/features/map/fireCentreLayer'

// mock ol-pmtiles to prevent it from using real PMTiles
vi.mock('ol-pmtiles', () => ({
  PMTilesVectorSource: class MockPMTilesVectorSource {
    constructor(public options: { url: string }) {}

    addEventListener() {}

    removeEventListener() {}

    on() {
      return this
    }

    once() {
      return this
    }

    un() {
      return this
    }

    getState() {
      return 'ready'
    }
  }
}))

describe('fireCentreLayerDefinitions', () => {
  describe('getFireCentreLinePMTilesLayer', () => {
    it('should create only a fire centre line layer', () => {
      const layer = getFireCentreLinePMTilesLayer({ zIndex: 54 })

      expect(layer.getProperties().name).toBe(FIRE_CENTRE_LINE_LAYER_NAME)
      expect(layer.getZIndex()).toBe(54)
    })
  })

  describe('getFireCentrePMTilesLayers', () => {
    it('should create only fire centre fill and line layers', () => {
      const layers = getFireCentrePMTilesLayers()

      expect(Object.keys(layers)).toEqual(['fireCentreLayer', 'fireCentreLineLayer'])
      expect(layers.fireCentreLayer.getProperties().name).toBe(FIRE_CENTRE_LAYER_NAME)
      expect(layers.fireCentreLineLayer.getProperties().name).toBe(FIRE_CENTRE_LINE_LAYER_NAME)
    })

    it('should share a single PMTiles source between fire centre layers', () => {
      const { fireCentreLayer, fireCentreLineLayer } = getFireCentrePMTilesLayers()

      expect(fireCentreLayer.getSource()).toBe(fireCentreLineLayer.getSource())
    })

    it('should use the default FBA z-indexes', () => {
      const { fireCentreLayer, fireCentreLineLayer } = getFireCentrePMTilesLayers()

      expect(fireCentreLayer.getZIndex()).toBe(51)
      expect(fireCentreLineLayer.getZIndex()).toBe(52)
    })

    it('should allow SFMS to place fire centre boundaries above raster layers', () => {
      const { fireCentreLayer, fireCentreLineLayer } = getFireCentrePMTilesLayers({ zIndex: 54 })

      expect(fireCentreLayer.getZIndex()).toBe(54)
      expect(fireCentreLineLayer.getZIndex()).toBe(55)
    })
  })
})
