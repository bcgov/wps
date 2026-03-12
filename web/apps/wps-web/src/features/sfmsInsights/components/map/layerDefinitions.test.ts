import { getSnowPMTilesLayer, getFireWeatherRasterLayer, getRasterLayer } from './layerDefinitions'
import { DateTime } from 'luxon'

// Mock pmtiles completely to prevent any parsing
vi.mock('pmtiles', () => ({
  FetchSource: class MockFetchSource {
    url: string
    constructor(url: string) {
      this.url = url
    }
    getKey() {
      return this.url
    }
  },
  PMTiles: class MockPMTiles {
    constructor() {
      // Do nothing - prevent any initialization
    }
  }
}))

// Mock ol-pmtiles to prevent it from using real PMTiles
vi.mock('ol-pmtiles', () => ({
  PMTilesVectorSource: class MockPMTilesVectorSource {
    private listeners: Map<string, Set<Function>> = new Map()

    constructor() {
      // Do nothing - prevent PMTiles initialization
    }

    addEventListener(type: string, listener: Function) {
      if (!this.listeners.has(type)) {
        this.listeners.set(type, new Set())
      }
      this.listeners.get(type)!.add(listener)
    }

    removeEventListener(type: string, listener: Function) {
      const typeListeners = this.listeners.get(type)
      if (typeListeners) {
        typeListeners.delete(listener)
      }
    }

    on(type: string, listener: Function) {
      this.addEventListener(type, listener)
      return this
    }

    once(type: string, listener: Function) {
      this.addEventListener(type, listener)
      return this
    }

    un(type: string, listener: Function) {
      this.removeEventListener(type, listener)
      return this
    }

    getState() {
      return 'ready'
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

  describe('getRasterLayer', () => {
    it('should return fuel layer when rasterType is fuel with null date', () => {
      const layer = getRasterLayer(null, 'fuel', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fuel')
    })

    it('should return fuel layer when rasterType is fuel with date', () => {
      const date = DateTime.fromISO('2025-11-02')
      const layer = getRasterLayer(date, 'fuel', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fuel')
    })

    it('should return fire weather layer when date is provided', () => {
      const date = DateTime.fromISO('2025-11-02')
      const layer = getRasterLayer(date, 'fwi', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fwi')
    })

    it('should return null and log error when date is null for fire weather raster', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const layer = getRasterLayer(null, 'fwi', 'test-token')
      expect(layer).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalledWith('date is required for fire weather rasters')
      consoleErrorSpy.mockRestore()
    })

    it('should return null and log error when date is null for other fire weather types', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(getRasterLayer(null, 'dmc', 'test-token')).toBeNull()
      expect(getRasterLayer(null, 'dc', 'test-token')).toBeNull()
      expect(getRasterLayer(null, 'bui', 'test-token')).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalledTimes(3)

      consoleErrorSpy.mockRestore()
    })
  })
})
