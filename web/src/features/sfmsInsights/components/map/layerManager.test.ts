import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LayerManager } from './layerManager'
import WebGLTileLayer from 'ol/layer/WebGLTile'
import VectorTileLayer from 'ol/layer/VectorTile'

describe('LayerManager', () => {
  const createMockSource = () => ({
    on: vi.fn(),
    once: vi.fn(),
    un: vi.fn(),
    getState: vi.fn(() => 'loading')
  })

  describe('constructor', () => {
    it('should create manager with default options', () => {
      const manager = new LayerManager()
      expect(manager).toBeDefined()
    })

    it('should create manager with custom options', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({
        onLoadingChange,
        trackLoading: false
      })

      expect(manager).toBeDefined()

      // Verify trackLoading: false works by checking onLoadingChange is not called
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // onLoadingChange should not be called when trackLoading is false
      expect(onLoadingChange).not.toHaveBeenCalled()
    })

    it('should use default trackLoading value of true', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange })

      const mockMap = {
        addLayer: vi.fn(),
        removeLayer: vi.fn()
      }

      const mockSource = {
        on: vi.fn(),
        once: vi.fn(),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }

      const mockLayer = {
        getSource: vi.fn(() => mockSource)
      }

      manager.setMap(mockMap as any)
      manager.updateLayer(mockLayer as any)

      // Should register loading listeners by default
      expect(mockSource.on).toHaveBeenCalledWith('tileloadend', expect.any(Function))
      expect(mockSource.once).toHaveBeenCalledWith('tileloaderror', expect.any(Function))
    })
  })

  describe('setMap', () => {
    it('should set map instance', () => {
      const manager = new LayerManager()
      const mockMap = {
        addLayer: vi.fn(),
        removeLayer: vi.fn()
      } as any

      manager.setMap(mockMap)

      // Should be able to use the map
      const mockLayer = { getSource: vi.fn(() => null) }
      manager.updateLayer(mockLayer as any)

      expect(mockMap.addLayer).toHaveBeenCalledWith(mockLayer)
    })

    it('should accept null map', () => {
      const manager = new LayerManager()
      manager.setMap(null)

      // Should not throw when calling updateLayer with null map
      expect(() => manager.updateLayer({} as any)).not.toThrow()
    })

    it('should allow changing map instance', () => {
      const manager = new LayerManager()
      const mockMap1 = { addLayer: vi.fn(), removeLayer: vi.fn() } as any
      const mockMap2 = { addLayer: vi.fn(), removeLayer: vi.fn() } as any

      manager.setMap(mockMap1)
      manager.setMap(mockMap2)

      const mockLayer = { getSource: vi.fn(() => null) }
      manager.updateLayer(mockLayer as any)

      expect(mockMap2.addLayer).toHaveBeenCalledWith(mockLayer)
      expect(mockMap1.addLayer).not.toHaveBeenCalled()
    })
  })

  describe('updateLayer', () => {
    let manager: LayerManager
    let mockMap: any

    beforeEach(() => {
      manager = new LayerManager()
      mockMap = {
        addLayer: vi.fn(),
        removeLayer: vi.fn()
      }
      manager.setMap(mockMap)
    })

    it('should add layer to map', () => {
      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      expect(mockMap.addLayer).toHaveBeenCalledWith(mockLayer)
    })

    it('should remove existing layer before adding new one', () => {
      const mockSource = createMockSource()
      const mockLayer1 = { getSource: vi.fn(() => mockSource) }
      const mockLayer2 = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer1 as any)
      manager.updateLayer(mockLayer2 as any)

      expect(mockMap.removeLayer).toHaveBeenCalledWith(mockLayer1)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(2)
    })

    it('should handle null layer', () => {
      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      manager.updateLayer(null)

      expect(mockMap.removeLayer).toHaveBeenCalledWith(mockLayer)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(1) // Only first layer
    })

    it('should not add layer when map is null', () => {
      manager.setMap(null)
      const mockLayer = { getSource: vi.fn(() => null) }

      manager.updateLayer(mockLayer as any)

      expect(mockMap.addLayer).not.toHaveBeenCalled()
    })

    it('should handle layer without source', () => {
      const mockLayer = { getSource: vi.fn(() => null) }

      expect(() => manager.updateLayer(mockLayer as any)).not.toThrow()
      expect(mockMap.addLayer).toHaveBeenCalledWith(mockLayer)
    })
  })

  describe('loading state tracking', () => {
    it('should call onLoadingChange when trackLoading is true', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Should set loading to true
      expect(onLoadingChange).toHaveBeenCalledWith(true, undefined)
    })

    it('should not call onLoadingChange when trackLoading is false', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: false })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Should not track loading
      expect(onLoadingChange).not.toHaveBeenCalled()
    })

    it('should register tileloadend listener when trackLoading is true', () => {
      const manager = new LayerManager({ trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      expect(mockSource.on).toHaveBeenCalledWith('tileloadend', expect.any(Function))
    })

    it('should register tileloaderror listener when trackLoading is true', () => {
      const manager = new LayerManager({ trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      expect(mockSource.once).toHaveBeenCalledWith('tileloaderror', expect.any(Function))
    })

    it('should not register tile listeners when trackLoading is false', () => {
      const manager = new LayerManager({ trackLoading: false })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = createMockSource()
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      expect(mockSource.on).not.toHaveBeenCalled()
    })

    it('should call onLoadingChange with false on tileloadend', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let tileloadendHandler: Function | null = null
      const mockSource = {
        on: vi.fn((event: string, handler: Function) => {
          if (event === 'tileloadend') {
            tileloadendHandler = handler
          }
        }),
        once: vi.fn(),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Clear previous calls
      onLoadingChange.mockClear()

      // Simulate tileloadend event
      tileloadendHandler!()

      expect(onLoadingChange).toHaveBeenCalledWith(false, undefined)
    })

    it('should call onLoadingChange with error on tileloaderror', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let tileloaderrorHandler: Function | null = null
      const mockSource = {
        on: vi.fn(),
        once: vi.fn((event: string, handler: Function) => {
          if (event === 'tileloaderror') {
            tileloaderrorHandler = handler
          }
        }),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Clear previous calls
      onLoadingChange.mockClear()

      // Simulate tileloaderror event
      tileloaderrorHandler!()

      expect(onLoadingChange).toHaveBeenCalledWith(
        false,
        expect.objectContaining({
          type: 'not_found'
        })
      )
    })

    it('should not throw when onLoadingChange is not provided', () => {
      const manager = new LayerManager({ trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      expect(() => manager.updateLayer(mockLayer as any)).not.toThrow()
    })
  })

  describe('dispose', () => {
    it('should remove current layer on dispose', () => {
      const manager = new LayerManager()
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      manager.dispose()

      expect(mockMap.removeLayer).toHaveBeenCalledWith(mockLayer)
    })

    it('should clear map reference on dispose', () => {
      const manager = new LayerManager()
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      manager.dispose()

      // After dispose, map is null, so updateLayer should not add layers
      mockMap.addLayer.mockClear()
      manager.updateLayer(mockLayer as any)

      expect(mockMap.addLayer).not.toHaveBeenCalled()
    })

    it('should not throw when disposing without layer', () => {
      const manager = new LayerManager()
      expect(() => manager.dispose()).not.toThrow()
    })

    it('should not throw when disposing without map', () => {
      const manager = new LayerManager()
      manager.setMap(null)
      expect(() => manager.dispose()).not.toThrow()
    })
  })

  describe('WebGLTileLayer support', () => {
    it('should work with WebGLTileLayer', () => {
      const manager = new LayerManager()
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockWebGLLayer = {
        getSource: vi.fn(() => mockSource)
      } as unknown as WebGLTileLayer

      manager.updateLayer(mockWebGLLayer)

      expect(mockMap.addLayer).toHaveBeenCalledWith(mockWebGLLayer)
    })
  })

  describe('VectorTileLayer support', () => {
    it('should work with VectorTileLayer', () => {
      const manager = new LayerManager()
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockVectorLayer = {
        getSource: vi.fn(() => mockSource)
      } as unknown as VectorTileLayer

      manager.updateLayer(mockVectorLayer)

      expect(mockMap.addLayer).toHaveBeenCalledWith(mockVectorLayer)
    })
  })

  describe('conditional layer management', () => {
    it('should support conditional layer creation', () => {
      const manager = new LayerManager()
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      // Add a layer
      manager.updateLayer(mockLayer as any)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(1)

      // Remove it by passing null
      manager.updateLayer(null)
      expect(mockMap.removeLayer).toHaveBeenCalledWith(mockLayer)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(1) // Still only 1 call

      // Add it back
      manager.updateLayer(mockLayer as any)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(2)
    })
  })

  describe('backwards compatibility', () => {
    it('should export RasterLayerManager as alias', async () => {
      const module = await import('./layerManager')
      expect(module.RasterLayerManager).toBe(module.LayerManager)
    })
  })

  describe('error handling', () => {
    it('should call onLoadingChange with error on tileloaderror', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let tileloaderrorHandler: Function | null = null
      const mockSource = {
        on: vi.fn((event: string, handler: Function) => {
          if (event === 'tileloaderror') {
            tileloaderrorHandler = handler
          }
        }),
        once: vi.fn((event: string, handler: Function) => {
          if (event === 'tileloaderror') {
            tileloaderrorHandler = handler
          }
        }),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      onLoadingChange.mockClear()

      // Simulate tileloaderror event
      tileloaderrorHandler!({ tile: {} })

      expect(onLoadingChange).toHaveBeenCalledWith(
        false,
        expect.objectContaining({
          type: 'not_found',
          message: expect.any(String)
        })
      )
    })

    it('should call onLoadingChange with error on source error event', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let errorHandler: Function | null = null
      const mockSource = {
        on: vi.fn(),
        once: vi.fn((event: string, handler: Function) => {
          if (event === 'error') {
            errorHandler = handler
          }
        }),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      onLoadingChange.mockClear()

      // Simulate error event
      errorHandler!({ error: new Error('Test error') })

      expect(onLoadingChange).toHaveBeenCalledWith(
        false,
        expect.objectContaining({
          type: 'not_found',
          message: expect.any(String)
        })
      )
    })

    it('should call onLoadingChange with error on source state change to error', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let changeHandler: Function | null = null
      const mockSource = {
        on: vi.fn((event: string, handler: Function) => {
          if (event === 'change') {
            changeHandler = handler
          }
        }),
        once: vi.fn(),
        un: vi.fn(),
        getState: vi.fn(() => 'error')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      onLoadingChange.mockClear()

      // Simulate change event with error state
      changeHandler!()

      expect(onLoadingChange).toHaveBeenCalledWith(
        false,
        expect.objectContaining({
          type: 'not_found',
          message: expect.any(String)
        })
      )
    })

    it('should trigger timeout error if no tiles load within timeout period', () => {
      vi.useFakeTimers()

      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = {
        on: vi.fn(),
        once: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      onLoadingChange.mockClear()

      // Fast-forward time by 10 seconds
      vi.advanceTimersByTime(10000)

      expect(onLoadingChange).toHaveBeenCalledWith(
        false,
        expect.objectContaining({
          type: 'not_found',
          message: expect.any(String)
        })
      )

      vi.useRealTimers()
    })

    it('should not trigger timeout error if tiles load successfully', () => {
      vi.useFakeTimers()

      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let tileloadendHandler: Function | null = null
      const mockSource = {
        on: vi.fn((event: string, handler: Function) => {
          if (event === 'tileloadend') {
            tileloadendHandler = handler
          }
        }),
        once: vi.fn(),
        getState: vi.fn(() => 'ready')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Simulate successful tile load
      tileloadendHandler!()
      onLoadingChange.mockClear()

      // Fast-forward time by 10 seconds
      vi.advanceTimersByTime(10000)

      // Should not call onLoadingChange with error
      expect(onLoadingChange).not.toHaveBeenCalled()

      vi.useRealTimers()
    })

    it('should clear timeout when removing layer', () => {
      vi.useFakeTimers()

      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      const mockSource = {
        on: vi.fn(),
        once: vi.fn(),
        un: vi.fn(),
        getState: vi.fn(() => 'loading')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)
      onLoadingChange.mockClear()

      // Remove layer
      manager.updateLayer(null)

      // Fast-forward time by 10 seconds
      vi.advanceTimersByTime(10000)

      // Should not trigger timeout error after layer removal
      expect(onLoadingChange).not.toHaveBeenCalled()

      vi.useRealTimers()
    })

    it('should not call onLoadingChange with error on change event if tiles have loaded', () => {
      const onLoadingChange = vi.fn()
      const manager = new LayerManager({ onLoadingChange, trackLoading: true })
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }
      manager.setMap(mockMap as any)

      let changeHandler: Function | null = null
      let tileloadendHandler: Function | null = null
      const mockSource = {
        on: vi.fn((event: string, handler: Function) => {
          if (event === 'change') {
            changeHandler = handler
          } else if (event === 'tileloadend') {
            tileloadendHandler = handler
          }
        }),
        once: vi.fn(),
        un: vi.fn(),
        getState: vi.fn(() => 'error')
      }
      const mockLayer = { getSource: vi.fn(() => mockSource) }

      manager.updateLayer(mockLayer as any)

      // Simulate successful tile load first
      tileloadendHandler!()
      onLoadingChange.mockClear()

      // Now simulate change event with error state
      changeHandler!()

      // Should not trigger error because tiles have already loaded
      expect(onLoadingChange).not.toHaveBeenCalledWith(false, expect.any(Object))
    })
  })

  describe('multiple manager instances', () => {
    it('should support multiple independent managers', () => {
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }

      const rasterManager = new LayerManager()
      const snowManager = new LayerManager({ trackLoading: false })

      rasterManager.setMap(mockMap as any)
      snowManager.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const rasterLayer = { getSource: vi.fn(() => mockSource) }
      const snowLayer = { getSource: vi.fn(() => mockSource) }

      rasterManager.updateLayer(rasterLayer as any)
      snowManager.updateLayer(snowLayer as any)

      expect(mockMap.addLayer).toHaveBeenCalledWith(rasterLayer)
      expect(mockMap.addLayer).toHaveBeenCalledWith(snowLayer)
      expect(mockMap.addLayer).toHaveBeenCalledTimes(2)
    })

    it('should manage layers independently across managers', () => {
      const mockMap = { addLayer: vi.fn(), removeLayer: vi.fn() }

      const manager1 = new LayerManager()
      const manager2 = new LayerManager()

      manager1.setMap(mockMap as any)
      manager2.setMap(mockMap as any)

      const mockSource = { on: vi.fn(), once: vi.fn(), un: vi.fn(), getState: vi.fn(() => 'loading') }
      const layer1 = { getSource: vi.fn(() => mockSource) }
      const layer2 = { getSource: vi.fn(() => mockSource) }

      manager1.updateLayer(layer1 as any)
      manager2.updateLayer(layer2 as any)

      // Dispose manager1
      manager1.dispose()

      expect(mockMap.removeLayer).toHaveBeenCalledWith(layer1)
      expect(mockMap.removeLayer).not.toHaveBeenCalledWith(layer2)
    })
  })
})
