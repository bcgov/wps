import type { MapBrowserEvent } from 'ol'
import type { EventsKey } from 'ol/events'
import WebGLTileLayer from 'ol/layer/WebGLTile'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NON_FUEL_LAYER_NAME, SNOW_LAYER_NAME } from './layerDefinitions'
import { type RasterTooltipData, RasterTooltipInteraction } from './rasterTooltipInteraction'

interface MockMapWithHandler {
  on: ReturnType<typeof vi.fn>
  getEventPixel: ReturnType<typeof vi.fn>
  forEachFeatureAtPixel: ReturnType<typeof vi.fn>
  getLayers: ReturnType<typeof vi.fn>
  pointerMoveHandler?: (...args: unknown[]) => void
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
        on: vi.fn(
          () =>
            ({
              type: 'mock-listener-key'
            }) as EventsKey
        ),
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
        on: vi.fn(
          () =>
            ({
              type: 'mock-listener-key-2'
            }) as EventsKey
        ),
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
        on: vi.fn((_event: string, handler: (...args: unknown[]) => void) => {
          // Store the handler so we can call it manually
          mockMap.pointerMoveHandler = handler
          return { type: 'mock-listener-key' } as EventsKey
        }),
        getEventPixel: vi.fn(() => [100, 200]),
        forEachFeatureAtPixel: vi.fn(),
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
      } as unknown as MapBrowserEvent<PointerEvent>

      // Manually trigger the handler
      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: 43,
        label: 'FWI',
        pixel: [100, 200],
        snowCovered: false
      })
    })

    it('should clear the tooltip when no raster layer exists', () => {
      mockMap.getLayers = vi.fn(() => ({
        getArray: vi.fn(() => [])
      }))

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<PointerEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({ value: null, label: '', pixel: null, snowCovered: false })
    })

    it.each([
      [99, 'Non-fuel'],
      [102, 'Water'],
      // Combustible fuel permits the numeric tooltip; unknown classification suppresses it.
      [2, '24%'],
      [255, null]
    ])('should use classification %s before reporting CFB', (fuel, expected) => {
      const classification = new WebGLTileLayer({ properties: { name: NON_FUEL_LAYER_NAME } })
      // OpenLayers returns the band value followed by alpha (255 means valid).
      vi.spyOn(classification, 'getData').mockReturnValue(new Float32Array([fuel, 255]))
      mockMap.getLayers.mockReturnValue({ getArray: () => [classification, mockRasterLayer] })
      mockRasterLayer.getProperties.mockReturnValue({ rasterType: 'cfb' })
      mockRasterLayer.getData.mockReturnValue(new Float32Array([0.24, 255]))
      mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: expected === '24%' ? 'CFB' : '',
        value: expected,
        pixel: [100, 200],
        snowCovered: false
      })
    })

    it('should suppress numeric FBP tooltips while classification is unavailable', () => {
      mockRasterLayer.getProperties.mockReturnValue({ rasterType: 'cfb' })
      mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: '',
        value: null,
        pixel: [100, 200],
        snowCovered: false
      })
      expect(mockRasterLayer.getData).not.toHaveBeenCalled()
    })

    it('should keep genuine missing data over combustible fuel missing', () => {
      const classification = new WebGLTileLayer({ properties: { name: NON_FUEL_LAYER_NAME } })
      vi.spyOn(classification, 'getData').mockReturnValue(new Float32Array([2, 255]))
      mockMap.getLayers.mockReturnValue({ getArray: () => [classification, mockRasterLayer] })
      mockRasterLayer.getProperties.mockReturnValue({ rasterType: 'cfb' })
      // Alpha 0 means missing data, not a valid CFB value of zero.
      mockRasterLayer.getData.mockReturnValue(new Float32Array([0, 0]))
      mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: 'CFB',
        value: null,
        pixel: [100, 200],
        snowCovered: false
      })
    })

    it('should not call onTooltipChange when callback is not set', () => {
      const interactionWithoutCallback = new RasterTooltipInteraction()
      interactionWithoutCallback.setMap(mockMap)

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<PointerEvent>

      // Should not throw error
      expect(() => mockMap.pointerMoveHandler!(mockEvent)).not.toThrow()
    })

    it.each([
      ['fwi', 42.7],
      ['dmc', 42.7],
      ['dc', 42.7],
      ['ffmc', 42.7],
      ['bui', 42.7],
      ['isi', 42.7],
      ['sfc', 42.7],
      ['tfc', 42.7],
      ['cfb', 42.7],
      ['hfi', 42.7],
      ['fmc', 42.7],
      ['ros', 12.3],
      ['fwi', -3.4028235e38]
    ])('should prefer snow over %s data %s', (rasterType, value) => {
      mockMap.forEachFeatureAtPixel.mockReturnValue(true)
      mockRasterLayer.getProperties.mockReturnValue({ rasterType })
      mockRasterLayer.getData.mockReturnValue(new Float32Array([value]))

      mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })

      expect(onTooltipChange).toHaveBeenCalledWith({ label: '', value: 'Snow', pixel: [100, 200], snowCovered: true })
      expect(mockRasterLayer.getData).not.toHaveBeenCalled()
    })

    it.each([
      [2, 'C-2'],
      [99, 'Non-fuel'],
      [102, 'Water']
    ])('should flag fuel value %s as snow covered without changing its value', (value, expectedValue) => {
      mockMap.forEachFeatureAtPixel.mockReturnValueOnce(true)
      mockRasterLayer.getProperties.mockReturnValue({ rasterType: 'fuel' })
      mockRasterLayer.getData.mockReturnValue(new Float32Array([value]))
      const event = { map: mockMap, originalEvent: new MouseEvent('pointermove') }

      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: '',
        value: expectedValue,
        pixel: [100, 200],
        snowCovered: true
      })

      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: '',
        value: expectedValue,
        pixel: [100, 200],
        snowCovered: expectedValue === 'Snow'
      })
    })

    it.each([new Float32Array([-3.4028235e38]), new Float32Array([101]), new Float32Array([2, 0]), null])(
      'should fall back to snow when fuel data is unavailable: %s',
      data => {
        mockMap.forEachFeatureAtPixel.mockReturnValue(true)
        mockRasterLayer.getProperties.mockReturnValue({ rasterType: 'fuel' })
        mockRasterLayer.getData.mockReturnValue(data)

        mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })
        expect(onTooltipChange).toHaveBeenCalledWith({ label: '', value: 'Snow', pixel: [100, 200], snowCovered: true })
      }
    )

    it.each([
      ['temperature', 'Temperature'],
      ['relative_humidity', 'Relative Humidity'],
      ['wind_speed', 'Wind Speed'],
      ['wind_direction', 'Wind Direction'],
      ['precipitation', 'Precipitation']
    ])('should keep %s values under snow and hide weather nodata', (rasterType, label) => {
      mockMap.forEachFeatureAtPixel.mockReturnValue(true)
      mockRasterLayer.getProperties.mockReturnValue({ rasterType })
      const event = { map: mockMap, originalEvent: new MouseEvent('pointermove') }

      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({ label, value: 43, pixel: [100, 200], snowCovered: true })

      mockRasterLayer.getData.mockReturnValue(new Float32Array([-3.4028235e38]))
      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({ label, value: null, pixel: [100, 200], snowCovered: true })
      expect(mockMap.forEachFeatureAtPixel).toHaveBeenCalledTimes(2)
    })

    it.each([
      [SNOW_LAYER_NAME, 1, 'Snow'],
      [SNOW_LAYER_NAME, 0, 43],
      [SNOW_LAYER_NAME, undefined, 43],
      ['anotherLayer', 1, 43]
    ])('should check layer %s and snow property %s', (layerName, snow, expectedValue) => {
      mockMap.forEachFeatureAtPixel.mockImplementation((_pixel, callback, options) => {
        const layer = { get: (key: string) => (key === 'name' ? layerName : undefined) }
        const feature = { get: (key: string) => (key === 'snow' ? snow : undefined) }
        return options.layerFilter(layer) ? callback(feature) : undefined
      })

      mockMap.pointerMoveHandler!({ map: mockMap, originalEvent: new MouseEvent('pointermove') })

      expect(onTooltipChange).toHaveBeenCalledWith({
        label: expectedValue === 'Snow' ? '' : 'FWI',
        value: expectedValue,
        pixel: [100, 200],
        snowCovered: expectedValue === 'Snow'
      })
    })

    it('should resume raster data and clear the tooltip after leaving snow', () => {
      const event = { map: mockMap, originalEvent: new MouseEvent('pointermove') }
      mockMap.forEachFeatureAtPixel.mockReturnValueOnce(true)
      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: '',
        value: 'Snow',
        pixel: [100, 200],
        snowCovered: true
      })

      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({
        label: 'FWI',
        value: 43,
        pixel: [100, 200],
        snowCovered: false
      })

      mockMap.forEachFeatureAtPixel.mockReturnValue(true)
      mockMap.getLayers.mockReturnValue({ getArray: () => [] })
      mockMap.pointerMoveHandler!(event)
      expect(onTooltipChange).toHaveBeenLastCalledWith({ label: '', value: null, pixel: null, snowCovered: false })
    })

    it('should handle nodata values correctly', () => {
      mockRasterLayer.getData = vi.fn(() => new Float32Array([-3.4028235e38]))

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<PointerEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: null,
        label: 'FWI',
        pixel: [100, 200],
        snowCovered: false
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
      } as unknown as MapBrowserEvent<PointerEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(onTooltipChange).toHaveBeenCalledWith({
        value: 43,
        label: expectedLabel,
        pixel: [100, 200],
        snowCovered: false
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
        on: vi.fn((_event: string, handler: (...args: unknown[]) => void) => {
          mockMap.pointerMoveHandler = handler
          return { type: 'mock-listener-key' } as EventsKey
        }),
        getEventPixel: vi.fn(() => [100, 200]),
        forEachFeatureAtPixel: vi.fn(),
        getLayers: vi.fn(() => ({
          getArray: vi.fn(() => [mockRasterLayer])
        }))
      }

      interaction.setMap(mockMap)

      const mockEvent = {
        map: mockMap,
        originalEvent: new MouseEvent('pointermove')
      } as unknown as MapBrowserEvent<PointerEvent>

      mockMap.pointerMoveHandler!(mockEvent)

      expect(initialCallback).not.toHaveBeenCalled()
      expect(newCallback).toHaveBeenCalledWith({
        value: 50,
        label: 'FWI',
        pixel: [100, 200],
        snowCovered: false
      })
    })
  })

  describe('dispose', () => {
    it('should clean up listener when disposed', () => {
      const mockMap = {
        on: vi.fn(
          () =>
            ({
              type: 'mock-listener-key'
            }) as EventsKey
        ),
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
