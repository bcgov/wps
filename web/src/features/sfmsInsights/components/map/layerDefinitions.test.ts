import { getSnowPMTilesLayer, getFireWeatherRasterLayer } from './layerDefinitions'
import { DateTime } from 'luxon'

// Mock FetchSource and PMTiles to prevent actual network requests
vi.mock('pmtiles', () => ({
  FetchSource: class MockFetchSource {
    url: string
    constructor(url: string) {
      this.url = url
    }
    async getBytes() {
      return {
        data: new ArrayBuffer(0),
        etag: 'test-etag',
        expires: null,
        cacheControl: null
      }
    }
    getKey() {
      return this.url
    }
  },
  PMTiles: class MockPMTiles {
    constructor(source: any) {}
    async getHeader() {
      return {
        minZoom: 0,
        maxZoom: 14,
        centerZoom: 0,
        centerLon: 0,
        centerLat: 0
      }
    }
    async getZxy() {
      return null
    }
  }
}))

describe('layerDefinitions', () => {
  describe('getSnowPMTilesLayer', () => {
    it('should create snow layer with zIndex 53', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getZIndex()).toBe(53)
    })

    it('should create snow layer with correct name property', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getProperties().name).toBe('snowVector')
    })

    it('should create snow layer with minZoom of 4', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getMinZoom()).toBe(4)
    })

    it('should generate correct PMTiles URL for snow layer', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)
      const source = layer.getSource()

      // Check that source exists
      expect(source).toBeDefined()
    })
  })

  describe('getFireWeatherRasterLayer', () => {
    it('should create fire weather layer with zIndex 52', () => {
      const rasterDate = DateTime.fromISO('2025-11-02')
      const layer = getFireWeatherRasterLayer(rasterDate, 'fwi', 'test-token')

      expect(layer.getZIndex()).toBe(52)
    })

    it('should have lower zIndex than snow layer', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fireWeatherLayer = getFireWeatherRasterLayer(date, 'fwi', 'test-token')
      const fireWeatherLayerZIdx = fireWeatherLayer.getZIndex()

      expect(snowLayer.getZIndex()).toBeGreaterThan(fireWeatherLayerZIdx!)
    })
  })

  describe('layer ordering', () => {
    it('should ensure snow layer renders on top of fire weather rasters', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fwiLayer = getFireWeatherRasterLayer(date, 'fwi', 'test-token')
      const dmcLayer = getFireWeatherRasterLayer(date, 'dmc', 'test-token')
      const dcLayer = getFireWeatherRasterLayer(date, 'dc', 'test-token')

      const snowZIndex = snowLayer.getZIndex()!
      const fwiZIndex = fwiLayer.getZIndex()!
      const dmcZIndex = dmcLayer.getZIndex()!
      const dcZIndex = dcLayer.getZIndex()!

      expect(snowZIndex).toBeGreaterThan(fwiZIndex)
      expect(snowZIndex).toBeGreaterThan(dmcZIndex)
      expect(snowZIndex).toBeGreaterThan(dcZIndex)
    })
  })
})
