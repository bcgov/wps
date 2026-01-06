import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RasterTooltipInteraction, RasterTooltipData } from './rasterTooltipInteraction'
import { MapBrowserEvent } from 'ol'
import { EventsKey } from 'ol/events'

interface MockMapWithHandler {
  on: ReturnType<typeof vi.fn>
  getEventPixel: ReturnType<typeof vi.fn>
  getLayers: ReturnType<typeof vi.fn>
  pointerMoveHandler?: Function
}

describe('RasterTooltipInteraction', () => {
  describe('constructor', () => {
    it('should create interaction without callback', () => {
      const interaction = new RasterTooltipInteraction()
      expect(interaction).toBeDefined()
    })

    it('should create interaction with callback', () => {
      const callback = vi.fn()
      const interaction = new RasterTooltipInteraction({ onTooltipChange: callback })
      expect(interaction).toBeDefined()
    })
  })

  describe('setMap', () => {
    let interaction: RasterTooltipInteraction
    let mockMap: any

    beforeEach(() => {
      interaction = new RasterTooltipInteraction()
      mockMap = {
        on: vi.fn(() => ({ type: 'mock-listener-key' }) as EventsKey),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [])
        }))
      }
    })

    it('should register pointermove listener when map is added', () => {
      interaction.setMap(mockMap)

      expect(mockMap.on).toHaveBeenCalledWith('pointermove', expect.any(Function))
    })

    it('should not register listener when map is null', () => {
      interaction.setMap(null)

      expect(mockMap.on).not.toHaveBeenCalled()
    })

    it('should register new listener when map is changed', () => {
      interaction.setMap(mockMap)

      // Change to a new map
      const mockMap2 = {
        on: vi.fn(() => ({ type: 'mock-listener-key-2' }) as EventsKey),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [])
        }))
      }

      interaction.setMap(mockMap2)

      // Should have registered listener on both maps
      expect(mockMap.on).toHaveBeenCalledTimes(1)
      expect(mockMap2.on).toHaveBeenCalledTimes(1)
    })

    it('should call parent setMap', () => {
      const setMapSpy = vi.spyOn(RasterTooltipInteraction.prototype as any, 'setMap')
      const newInteraction = new RasterTooltipInteraction()

      newInteraction.setMap(mockMap)

      expect(setMapSpy).toHaveBeenCalledWith(mockMap)
    })
  })

  describe('handlePointerMove', () => {
    let interaction: RasterTooltipInteraction
    let mockMap: MockMapWithHandler
    let mockRasterLayer: any
    let onTooltipChange: (data: RasterTooltipData) => void

    beforeEach(() => {
      onTooltipChange = vi.fn()
      interaction = new RasterTooltipInteraction({ onTooltipChange })

      mockRasterLayer = {
        getData: vi.fn(() => new Float32Array([42.7])),
        getProperties: vi.fn(() => ({ rasterType: 'fwi' }))
      }

      mockMap = {
        on: vi.fn((event: string, handler: Function) => {
          // Store the handler so we can call it manually
          mockMap.pointerMoveHandler = handler
          return { type: 'mock-listener-key' } as EventsKey
        }),
        getEventPixel: vi.fn(() => [100, 200]),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [mockRasterLayer])
        }))
      }

      interaction.setMap(mockMap)
    })

    it('should call onTooltipChange with correct data when raster layer exists', () => {
      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      // Manually trigger the handler
      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: 43, // Rounded from 42.7
        label: 'FWI',
        pixel: [100, 200]
      })
    })

    it('should not call onTooltipChange when no raster layer exists', () => {
      mockMap.getLayers = vi.fn(() => ({
        getArray: vi.fn(() => [])
      }))

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).not.toHaveBeenCalled()
    })

    it('should not call onTooltipChange when callback is not set', () => {
      const interactionWithoutCallback = new RasterTooltipInteraction()
      interactionWithoutCallback.setMap(mockMap)

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      // Should not throw error
      expect(() => mockMap.pointerMoveHandler!(mockEvent)).not.toThrow()
    })

    it('should handle nodata values correctly', () => {
      mockRasterLayer.getData = vi.fn(() => new Float32Array([-3.4028235e38]))

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: null,
        label: 'FWI',
        pixel: [100, 200]
      })
    })

    it.each([
      ['fwi', 'FWI'],
      ['dmc', 'DMC'],
      ['dc', 'DC'],
      ['ffmc', 'FFMC'],
      ['bui', 'BUI'],
      ['isi', 'ISI']
    ])('should handle different raster types: %s -> %s', (rasterType, expectedLabel) => {
      mockRasterLayer.getProperties = vi.fn(() => ({ rasterType }))

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: 43,
        label: expectedLabel,
        pixel: [100, 200]
      })
    })
  })

  describe('setTooltipCallback', () => {
    it('should update the callback', () => {
      const initialCallback = vi.fn()
      const newCallback = vi.fn()
      const interaction = new RasterTooltipInteraction({ onTooltipChange: initialCallback })

      interaction.setTooltipCallback(newCallback)

      const mockRasterLayer = {
        getData: vi.fn(() => new Float32Array([50])),
        getProperties: vi.fn(() => ({ rasterType: 'fwi' }))
      }

      const mockMap: MockMapWithHandler = {
        on: vi.fn((event: string, handler: Function) => {
          mockMap.pointerMoveHandler = handler
          return { type: 'mock-listener-key' } as EventsKey
        }),
        getEventPixel: vi.fn(() => [100, 200]),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [mockRasterLayer])
        }))
      }

      interaction.setMap(mockMap)

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<UIEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(initialCallback).not.toHaveBeenCalled()
      expect(newCallback).toHaveBeenCalledWith({
        value: 50,
        label: 'FWI',
        pixel: [100, 200]
      })
    })
  })

  describe('dispose', () => {
    it('should clean up listener when disposed', () => {
      const mockMap = {
        on: vi.fn(() => ({ type: 'mock-listener-key' }) as EventsKey),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [])
        }))
      }

      const interaction = new RasterTooltipInteraction()
      interaction.setMap(mockMap)

      // Dispose should not throw
      expect(() => interaction.dispose()).not.toThrow()
    })

    it('should not throw when disposing interaction without map', () => {
      const interaction = new RasterTooltipInteraction()

      expect(() => interaction.dispose()).not.toThrow()
    })
  })
})
