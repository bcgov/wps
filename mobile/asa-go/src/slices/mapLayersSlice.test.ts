import { describe, expect, it } from 'vitest'
import mapLayersSlice, {
  initialState,
  mapLayerLoadFailed,
  mapLayerLoadFinished,
  mapLayerLoadStarted
} from '@/slices/mapLayersSlice'

describe('mapLayers reducer', () => {
  it('tracks concurrent layer loads', () => {
    const loadingState = mapLayersSlice(mapLayersSlice(initialState, mapLayerLoadStarted()), mapLayerLoadStarted())

    expect(loadingState.pendingLoads).toBe(2)
    expect(mapLayersSlice(loadingState, mapLayerLoadFinished()).pendingLoads).toBe(1)
  })

  it('does not let the pending load count fall below zero', () => {
    expect(mapLayersSlice(initialState, mapLayerLoadFinished()).pendingLoads).toBe(0)
  })

  it('assigns a new version to each failure occurrence', () => {
    const firstFailure = mapLayersSlice(initialState, mapLayerLoadFailed())
    const secondFailure = mapLayersSlice(firstFailure, mapLayerLoadFailed())

    expect(firstFailure.latestErrorVersion).toBe(1)
    expect(secondFailure.latestErrorVersion).toBe(2)
  })
})
