// Demo only: answers the API calls the Insights page makes, with real station locations from the
// BCWS data mart and made-up climatology. Nothing here reaches a server.
import type { ClimatologyDay, ClimatologyObservation, ClimatologySeries } from '@wps/api/climatologyAPI'
import axios from '@wps/api/axios'
import type { InternalAxiosRequestConfig } from 'axios'
import stations from './stations.json'

type Station = (typeof stations)[number]
const byCode = new Map(stations.map(station => [station.properties.code, station]))

const hash = (...parts: number[]) => {
  let h = 2166136261
  for (const part of parts) {
    h = Math.imul(h ^ Math.floor(part), 16777619)
  }
  return ((h >>> 0) % 100000) / 100000
}
const noise = (...parts: number[]) => hash(...parts) + hash(...parts, 7) + hash(...parts, 13) - 1.5

/** A made-up noon value for a station on a day: a seasonal curve, cooler up high and north. */
const valueOn = (station: Station, variable: string, year: number, dayOfYear: number) => {
  const [lon, lat] = station.geometry.coordinates
  const season = Math.sin(((dayOfYear - 105) / 365) * 2 * Math.PI)
  const code = station.properties.code
  // Some years run warm or dry throughout, as real years do.
  const yearAnomaly = noise(year, 1) * 1.5
  const spell = noise(year, Math.floor(dayOfYear / 9), 2) * 3
  switch (variable) {
    case 'relative_humidity':
      return Math.min(100, Math.max(8, 55 - 22 * season + noise(code, year, dayOfYear) * 18 - spell * 3))
    case 'wind_speed':
      return Math.max(0, 9 + (lon + 125) * 0.3 + noise(code, year, dayOfYear, 3) * 9)
    case 'precipitation': {
      const wet = hash(code, year, dayOfYear, 4) < 0.25 - 0.1 * season
      return wet ? hash(code, year, dayOfYear, 5) ** 2 * 18 : 0
    }
    default:
      return (
        13 + 12 * season - station.properties.elevation * 0.0065 - (lat - 49) * 0.7 + yearAnomaly + spell + noise(code, year, dayOfYear) * 4
      )
  }
}

const FIRST_YEAR = 1990
const DAY = 24 * 60 * 60 * 1000

const percentile = (sorted: number[], p: number) => {
  const index = (sorted.length - 1) * p
  const low = Math.floor(index)
  return sorted[low] + (sorted[Math.min(low + 1, sorted.length - 1)] - sorted[low]) * (index - low)
}

const mean = (values: number[]) => values.reduce((sum, value) => sum + value, 0) / values.length

// Each station has history from the year it opened, so a group's membership changes over time.
const firstYear = (station: Station) => FIRST_YEAR + Math.floor(hash(station.properties.code, 9) * 20)

const series = (codes: number[], variable: string, year: number, pooled: boolean): ClimatologySeries => {
  const group = codes.map(code => byCode.get(code)).filter((station): station is Station => !!station)
  const today = new Date()
  const days: ClimatologyDay[] = []
  const observations: ClimatologyObservation[] = []
  for (let dayOfYear = 0; dayOfYear < 365; dayOfYear++) {
    const date = new Date(Date.UTC(2025, 0, 1) + dayOfYear * DAY)
    const values: number[] = []
    const contributing = new Set<number>()
    for (let past = FIRST_YEAR; past <= today.getFullYear(); past++) {
      if (past === year) continue
      const reporting = group.filter(station => past >= firstYear(station))
      if (reporting.length === 0) continue
      const stationValues = reporting.map(station => valueOn(station, variable, past, dayOfYear))
      reporting.forEach(station => contributing.add(station.properties.code))
      if (pooled) values.push(...stationValues)
      else values.push(mean(stationValues))
    }
    if (values.length > 0) {
      values.sort((a, b) => a - b)
      days.push({
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
        count: values.length,
        station_count: contributing.size,
        minimum: values[0],
        p25: percentile(values, 0.25),
        median: percentile(values, 0.5),
        p75: percentile(values, 0.75),
        p90: percentile(values, 0.9),
        maximum: values[values.length - 1]
      })
    }
    const observed = new Date(Date.UTC(year, date.getUTCMonth(), date.getUTCDate()))
    if (observed <= today && group.length > 0) {
      observations.push({
        date: observed.toISOString().slice(0, 10),
        value: mean(group.map(station => valueOn(station, variable, year, dayOfYear))),
        station_count: group.length
      })
    }
  }
  return {
    station_codes: codes,
    first_reference_year: FIRST_YEAR,
    last_reference_year: today.getFullYear() - (year === today.getFullYear() ? 1 : 0),
    days,
    observations
  }
}

const respond = (config: InternalAxiosRequestConfig, data: unknown, status = 200) =>
  Promise.resolve({ data, status, statusText: 'OK', headers: {}, config })

axios.defaults.adapter = async config => {
  const url = config.url ?? ''
  // A little latency, as the real API has.
  await new Promise(resolve => setTimeout(resolve, 250))
  if (url.startsWith('/stations')) {
    return respond(config, { type: 'FeatureCollection', features: stations })
  }
  if (url === '/climatology/daily') {
    const { station_codes, variable, year, method } = config.params
    const codes: number[] = ([] as number[]).concat(station_codes).map(Number)
    const all =
      method === 'each'
        ? codes.map(code => series([code], variable, Number(year), false))
        : [series(codes, variable, Number(year), method === 'pooled')]
    return respond(config, { variable, year: Number(year), method, series: all })
  }
  // The fire weather map tab's calls are not part of this demo.
  return Promise.reject(Object.assign(new Error(`Not in the demo: ${url}`), { config, response: { status: 404 } }))
}
