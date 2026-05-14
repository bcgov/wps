import { modelRegistry, ModelRunHour, ModelType } from '@/features/weatherToolkit/weatherToolkitTypes'
import { getWxChart } from '@wps/api/weatherToolkitAPI'
import { DateTime } from 'luxon'
import { useEffect, useRef, useState } from 'react'

// The number of charts to pre-fetch to improve the user perception of performance.
const PREFETCH_AHEAD = 5

export const buildChartKey = (
  model: ModelType,
  modelRunDate: DateTime,
  modelRunHour: ModelRunHour,
  hour: number
): string => {
  const { ecccPath, resolution } = modelRegistry[model]
  const dateStr = modelRunDate.toFormat('yyyyMMdd')
  const hourStr = hour.toString().padStart(3, '0')
  return `wx_4panel_charts/${dateStr}/${ecccPath}/${resolution}/${modelRunHour}/${hourStr}/${model}_${dateStr}T${modelRunHour}Z_F${hourStr}_4panel.png`
}

export interface WxChartCacheResult {
  cache: Map<string, string>
  failed: Set<string>
}

export function useWxChartCache(
  model: ModelType,
  modelRunDate: DateTime,
  modelRunHour: ModelRunHour,
  currentHour: number
): WxChartCacheResult {
  const [cache, setCache] = useState<Map<string, string>>(new Map())
  const [failed, setFailed] = useState<Set<string>>(new Set())
  const stateRef = useRef({
    cache: new Map<string, string>(),
    failed: new Set<string>(),
    fetching: new Set<string>(),
    generation: 0
  })

  // Reset when model params change
  useEffect(() => {
    const state = stateRef.current
    state.generation++
    state.cache.forEach(url => URL.revokeObjectURL(url))
    state.cache = new Map()
    state.failed = new Set()
    state.fetching = new Set()
    setCache(new Map())
    setFailed(new Set())
  }, [model, modelRunDate, modelRunHour])

  // Prefetch rolling window of PREFETCH_AHEAD frames ahead of currentHour
  useEffect(() => {
    const state = stateRef.current
    const gen = state.generation
    const { interval, maxHour } = modelRegistry[model]
    const targetHour = Math.min(currentHour + PREFETCH_AHEAD * interval, maxHour)

    for (let hour = currentHour; hour <= targetHour; hour += interval) {
      const key = buildChartKey(model, modelRunDate, modelRunHour, hour)
      if (state.cache.has(key) || state.fetching.has(key)) continue

      state.fetching.add(key)
      getWxChart(key)
        .then(blob => {
          if (stateRef.current.generation !== gen) return
          const url = URL.createObjectURL(blob)
          state.fetching.delete(key)
          state.cache.set(key, url)
          const wasInFailed = state.failed.delete(key)
          setCache(new Map(state.cache))
          if (wasInFailed) setFailed(new Set(state.failed))
        })
        .catch(() => {
          if (stateRef.current.generation !== gen) return
          state.fetching.delete(key)
          state.failed.add(key)
          setFailed(new Set(state.failed))
        })
    }
  }, [currentHour, model, modelRunDate, modelRunHour])

  // Revoke all URLs on unmount
  useEffect(() => {
    return () => {
      stateRef.current.cache.forEach(url => URL.revokeObjectURL(url))
    }
  }, [])

  return { cache, failed }
}
