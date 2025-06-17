import {
  BurnForecast,
  BurnStatusEnum,
  FireWatch,
  FireWatchBurnForecast,
  FireWatchFireCentre,
  FireWatchStation,
  FuelTypeEnum,
  PrescriptionEnum
} from '@/features/fireWatch/interfaces'
import axios from 'api/axios'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'

// Interfaces for data transfer objects and functions for fetching data.

export interface FireWatchInput {
  burn_location: number[]
  burn_window_end: string | null
  burn_window_start: string | null
  contact_email: string[]
  fire_centre: FireWatchFireCentre | null
  station: FireWatchStation | null
  status: BurnStatusEnum
  title: string
  // Fuel parameters
  fuel_type: FuelTypeEnum
  percent_conifer?: number
  percent_dead_fir?: number
  percent_grass_curing?: number
  // Weather parameters
  temp_min: number
  temp_preferred: number | null
  temp_max: number
  rh_min: number
  rh_preferred: number | null
  rh_max: number
  wind_speed_min: number
  wind_speed_preferred: number | null
  wind_speed_max: number
  // FWI and FBP parameters
  ffmc_min: number | null
  ffmc_preferred: number | null
  ffmc_max: number | null
  dmc_min: number | null
  dmc_preferred: number | null
  dmc_max: number | null
  dc_min: number | null
  dc_preferred: number | null
  dc_max: number | null
  isi_min: number | null
  isi_preferred: number | null
  isi_max: number | null
  bui_min: number | null
  bui_preferred: number | null
  bui_max: number | null
  hfi_min: number
  hfi_preferred: number | null
  hfi_max: number
}

export interface FireWatchOutput extends FireWatchInput {
  id: number
  create_timestamp: string
  create_user: string
  update_timestamp: string
  update_user: string
}

export interface FireWatchResponse {
  fire_watch: FireWatchOutput
}

export interface FireWatchListResponse {
  watch_list: FireWatchOutput[]
}

export interface FireWatchFireCentresResponse {
  fire_centres: FireWatchFireCentre[]
}

// API data transfer object
export interface BurnForecastOutput {
  id: number
  fire_watch_id: number // The FireWatch record this BurnForecast relates to
  date: string
  temp: number
  rh: number
  wind_speed: number
  ffmc: number
  dmc: number
  dc: number
  isi: number
  bui: number
  hfi: number
  in_prescription: string
}

// API data transfer object
export interface FireWatchOutputBurnForecast {
  fire_watch: FireWatchOutput
  burn_forecasts: BurnForecastOutput[]
}

// API response data transfer object
export interface FireWatchBurnForecastsResponse {
  fire_watch_burn_forecasts: FireWatchOutputBurnForecast[]
}

export const getActiveFireWatches = async (): Promise<FireWatchListResponse> => {
  const url = '/fire-watch/active'
  const { data } = await axios.get(url)
  return data
}

export const postFireWatchInput = async (fireWatch: FireWatch): Promise<FireWatchResponse> => {
  const fireWatchInput = marshalFireWatchToFireWatchInput(fireWatch)
  const url = '/fire-watch/watch'
  const { data } = await axios.post(url, {
    fire_watch: fireWatchInput
  })
  return data
}

export const patchFireWatchUpdate = async (fireWatch: FireWatch): Promise<FireWatchBurnForecast> => {
  const fireWatchInput = marshalFireWatchToFireWatchInput(fireWatch)
  const url = `/fire-watch/watch/${fireWatch.id}`
  const { data } = await axios.patch(url, {
    fire_watch: fireWatchInput
  })
  const updatedFireWatchBurnForecasts = marshalBurnForecasts(data.fire_watch_burn_forecasts)
  return updatedFireWatchBurnForecasts[0]
}

export const getFireCentres = async (): Promise<FireWatchFireCentresResponse> => {
  const url = 'fire-watch/fire-centres'
  const { data } = await axios.get(url)
  return data
}

export async function getBurnForecasts(): Promise<FireWatchBurnForecast[]> {
  const url = '/fire-watch/burn-forecasts'
  const { data } = await axios.get(url)
  const burnForecasts = marshalBurnForecasts(data.fire_watch_burn_forecasts)
  return burnForecasts
}

const marshalFireWatchToFireWatchInput = (fireWatch: FireWatch): FireWatchInput => {
  return {
    burn_location: fireWatch.geometry,
    burn_window_end: fireWatch.burnWindowEnd?.toISO() ?? null,
    burn_window_start: fireWatch.burnWindowStart?.toISO() ?? null,
    contact_email: fireWatch.contactEmail,
    fire_centre: fireWatch.fireCentre ?? null,
    station: fireWatch.station ?? null,
    status: fireWatch.status,
    title: fireWatch.title,
    // Fuel parameters
    fuel_type: fireWatch.fuelType,
    percent_conifer: fireWatch.percentConifer,
    percent_dead_fir: fireWatch.percentDeadFir,
    percent_grass_curing: fireWatch.percentGrassCuring,
    // Weather parameters
    temp_min: fireWatch.tempMin,
    temp_preferred: fireWatch.tempPreferred ?? null,
    temp_max: fireWatch.tempMax,
    rh_min: fireWatch.rhMin,
    rh_preferred: fireWatch.rhPreferred ?? null,
    rh_max: fireWatch.rhMax,
    wind_speed_min: fireWatch.windSpeedMin,
    wind_speed_preferred: fireWatch.windSpeedPreferred ?? null,
    wind_speed_max: fireWatch.windSpeedMax,
    // FWI and FBP parameters
    ffmc_min: fireWatch.ffmcMin ?? null,
    ffmc_preferred: fireWatch.ffmcPreferred ?? null,
    ffmc_max: fireWatch.ffmcMax ?? null,
    dmc_min: fireWatch.dmcMin ?? null,
    dmc_preferred: fireWatch.dmcPreferred ?? null,
    dmc_max: fireWatch.dmcMax ?? null,
    dc_min: fireWatch.dcMin ?? null,
    dc_preferred: fireWatch.dcPreferred ?? null,
    dc_max: fireWatch.dcMax ?? null,
    isi_min: fireWatch.isiMin ?? null,
    isi_preferred: fireWatch.isiPreferred ?? null,
    isi_max: fireWatch.isiMax ?? null,
    bui_min: fireWatch.buiMin ?? null,
    bui_preferred: fireWatch.buiPreferred ?? null,
    bui_max: fireWatch.buiMax ?? null,
    hfi_min: fireWatch.hfiMin,
    hfi_preferred: fireWatch.hfiPreferred ?? null,
    hfi_max: fireWatch.hfiMax
  }
}

const marshalFireWatchOutputToFireWatch = (fireWatchOutput: FireWatchOutput): FireWatch => {
  return {
    id: fireWatchOutput.id,
    createTimestamp: DateTime.fromISO(fireWatchOutput.create_timestamp),
    createUser: fireWatchOutput.create_user,
    updateTimestamp: DateTime.fromISO(fireWatchOutput.update_timestamp),
    updateUser: fireWatchOutput.update_user,
    geometry: fireWatchOutput.burn_location,
    burnWindowEnd: isNull(fireWatchOutput.burn_window_end)
      ? null
      : DateTime.fromISO(fireWatchOutput.burn_window_end),
    burnWindowStart: isNull(fireWatchOutput.burn_window_start)
      ? null
      : DateTime.fromISO(fireWatchOutput.burn_window_start),
    contactEmail: fireWatchOutput.contact_email,
    fireCentre: fireWatchOutput.fire_centre,
    station: fireWatchOutput.station,
    status: fireWatchOutput.status,
    title: fireWatchOutput.title,
    fuelType: fireWatchOutput.fuel_type,
    percentConifer: fireWatchOutput.percent_conifer,
    percentDeadFir: fireWatchOutput.percent_dead_fir,
    percentGrassCuring: fireWatchOutput.percent_grass_curing,
    tempMin: fireWatchOutput.temp_min,
    tempPreferred: fireWatchOutput.temp_preferred,
    tempMax: fireWatchOutput.temp_max,
    rhMin: fireWatchOutput.rh_min,
    rhPreferred: fireWatchOutput.rh_preferred,
    rhMax: fireWatchOutput.rh_max,
    windSpeedMin: fireWatchOutput.wind_speed_min,
    windSpeedPreferred: fireWatchOutput.wind_speed_preferred,
    windSpeedMax: fireWatchOutput.wind_speed_max,
    ffmcMin: fireWatchOutput.ffmc_min,
    ffmcPreferred: fireWatchOutput.ffmc_preferred,
    ffmcMax: fireWatchOutput.ffmc_max,
    dmcMin: fireWatchOutput.dmc_min,
    dmcPreferred: fireWatchOutput.dmc_preferred,
    dmcMax: fireWatchOutput.dmc_max,
    dcMin: fireWatchOutput.dc_min,
    dcPreferred: fireWatchOutput.dc_preferred,
    dcMax: fireWatchOutput.dc_max,
    isiMin: fireWatchOutput.isi_min,
    isiPreferred: fireWatchOutput.isi_preferred,
    isiMax: fireWatchOutput.isi_max,
    buiMin: fireWatchOutput.bui_min,
    buiPreferred: fireWatchOutput.bui_preferred,
    buiMax: fireWatchOutput.bui_max,
    hfiMin: fireWatchOutput.hfi_min,
    hfiPreferred: fireWatchOutput.hfi_preferred,
    hfiMax: fireWatchOutput.hfi_max
  }
}

const marshalBurnForecastOutputToBurnForecast = (burnForecastOutput: BurnForecastOutput): BurnForecast => {
  return {
    id: burnForecastOutput.id,
    fireWatchId: burnForecastOutput.fire_watch_id,
    date: DateTime.fromISO(burnForecastOutput.date),
    temp: burnForecastOutput.temp,
    rh: burnForecastOutput.rh,
    windSpeed: burnForecastOutput.wind_speed,
    ffmc: burnForecastOutput.ffmc,
    dmc: burnForecastOutput.dmc,
    dc: burnForecastOutput.dc,
    isi: burnForecastOutput.isi,
    bui: burnForecastOutput.bui,
    hfi: burnForecastOutput.hfi,
    inPrescription: burnForecastOutput.in_prescription as PrescriptionEnum
  }
}

// Convert fire watch burn forecasts from the API shape to frontend shape.
const marshalBurnForecasts = (values: FireWatchOutputBurnForecast[]) => {
  const fireWatchBurnForecasts: FireWatchBurnForecast[] = values.map((value: FireWatchOutputBurnForecast) => {
    const fireWatch = marshalFireWatchOutputToFireWatch(value.fire_watch)
    const burnForecasts: BurnForecast[] = []
    for (const burnForecastOutput of value.burn_forecasts) {
      const burnForecast = marshalBurnForecastOutputToBurnForecast(burnForecastOutput)
      burnForecasts.push(burnForecast)
    }
    const fireWatchBurnForecast = {
      fireWatch,
      burnForecasts: burnForecasts
    }
    return fireWatchBurnForecast
  })
  return fireWatchBurnForecasts
}
