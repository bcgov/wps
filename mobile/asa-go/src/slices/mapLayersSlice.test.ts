import { describe, expect, it } from 'vitest'
import mapLayersSlice, { initialState, mapLayerLoadFinished, mapLayerLoadStarted } from '@/slices/mapLayersSlice'

describe('mapLayers reducer', () => {
  it('tracks concurrent layer loads', () => {
    const loadingState = mapLayersSlice(mapLayersSlice(initialState, mapLayerLoadStarted()), mapLayerLoadStarted())

    expect(loadingState.pendingLoads).toBe(2)
    expect(mapLayersSlice(loadingState, mapLayerLoadFinished()).pendingLoads).toBe(1)
  })

  it('does not let the pending load count fall below zero', () => {
    expect(mapLayersSlice(initialState, mapLayerLoadFinished()).pendingLoads).toBe(0)
  })
})
