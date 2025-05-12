import axios from 'api/axios'
import { DateTime } from 'luxon'

export enum BurnStatusEnum {
  ACTIVE = "active",
  CANCELLED = "cancelled",
  COMPLETE = "complete",
  HOLD = "hold"
}

export enum FuelTypeEnum {
  C1 = "C1",
  C2 = "C2",
  C3 = "C3",
  C4 = "C4",
  C5 = "C5",
  C6 = "C6",
  C7 = "C7",
  C7B = "C7B",
  D1 = "D1",
  D2 = "D2",
  M1 = "M1",
  M2 = "M2",
  M3 = "M3",
  M4 = "M4",
  O1A = "O1A",
  O1B = "O1B",
  S1 = "S1",
  S2 = "S2",
  S3 = "S3"
}

export const fuelTypes = [
  FuelTypeEnum.C1,
  FuelTypeEnum.C2,
  FuelTypeEnum.C3,
  FuelTypeEnum.C4,
  FuelTypeEnum.C5,
  FuelTypeEnum.C6,
  FuelTypeEnum.C7,
  FuelTypeEnum.D1,
  FuelTypeEnum.D2,
  FuelTypeEnum.M1,
  FuelTypeEnum.M2,
  FuelTypeEnum.M3,
  FuelTypeEnum.M4,
  FuelTypeEnum.O1A,
  FuelTypeEnum.O1B,
  FuelTypeEnum.S1,
  FuelTypeEnum.S2,
  FuelTypeEnum.S3
]
interface FireWatchStation {
  code: number
  name: string
}

export interface FireWatch {
  burnWindowEnd: DateTime
  burnWindowStart: DateTime
  contactEmail: string[]
  fireCentre: FireWatchFireCentre | null
  geometry: number[]
  // station?: StationOption | null
  station: FireWatchStation | null
  status: BurnStatusEnum
  title: string
  // Fuel parameters
  fuelType: FuelTypeEnum
  percentConifer?: number
  percentDeadFir?: number
  percentGrassCuring?: number
  // Weather parameters
  tempMin: number
  tempPreferred: number
  tempMax: number
  rhMin: number
  rhPreferred: number
  rhMax: number
  windSpeedMin: number
  windSpeedPreferred: number
  windSpeedMax: number
  // FWI and FBP parameters
  ffmcMin: number
  ffmcPreferred: number
  ffmcMax: number
  dmcMin: number
  dmcPreferred: number
  dmcMax: number
  dcMin: number
  dcPreferred: number
  dcMax: number
  isiMin: number
  isiPreferred: number
  isiMax: number
  buiMin: number
  buiPreferred: number
  buiMax: number
  hfiMin: number
  hfiPreferred: number
  hfiMax: number
  id?: number
  createTimestamp?: DateTime
  createUser?: string
  updateTimestamp?: DateTime
  updateUser?: string
}

export interface FireWatchInput {
  burn_location: number[]
  burn_window_end: number
  burn_window_start: number
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
  temp_preferred: number
  temp_max: number
  rh_min: number
  rh_preferred: number
  rh_max: number
  wind_speed_min: number
  wind_speed_preferred: number
  wind_speed_max: number
  // FWI and FBP parameters
  ffmc_min: number
  ffmc_preferred: number
  ffmc_max: number
  dmc_min: number
  dmc_preferred: number
  dmc_max: number
  dc_min: number
  dc_preferred: number
  dc_max: number
  isi_min: number
  isi_preferred: number
  isi_max: number
  bui_min: number
  bui_preferred: number
  bui_max: number
  hfi_min: number
  hfi_preferred: number
  hfi_max: number
}

export interface FireWatchOutput extends FireWatchInput {
  id: number
  create_timestamp: number
  create_user: string 
  update_timestamp: number
  update_user: string
}

export interface FireWatchResponse {
  fire_watch: FireWatchOutput
}

export interface FireWatchListResponse {
  watch_list: FireWatchOutput[]
}

export interface FireWatchFireCentre {
  id: number
  name: string
}

export interface FireWatchFireCentresResponse {
  fire_centres: FireWatchFireCentre[]
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

export const getFireCentres = async (): Promise<FireWatchFireCentresResponse> => {
  const url = 'fire-watch/fire-centres'
  const { data } = await axios.get(url)
  return data
}

const marshalFireWatchToFireWatchInput = (fireWatch: FireWatch): FireWatchInput => {
  return {
    burn_location: fireWatch.geometry,
    burn_window_end: Math.round(fireWatch.burnWindowEnd?.toMillis()/1000),
    burn_window_start: Math.round(fireWatch.burnWindowStart?.toMillis()/1000),
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
    temp_preferred: fireWatch.tempPreferred,
    temp_max: fireWatch.tempMax,
    rh_min: fireWatch.rhMin,
    rh_preferred: fireWatch.rhPreferred,
    rh_max: fireWatch.rhMax,
    wind_speed_min: fireWatch.windSpeedMin,
    wind_speed_preferred: fireWatch.windSpeedPreferred,
    wind_speed_max: fireWatch.windSpeedMax,
    // FWI and FBP parameters
    ffmc_min: fireWatch.ffmcMin,
    ffmc_preferred: fireWatch.ffmcPreferred,
    ffmc_max: fireWatch.ffmcMax,
    dmc_min: fireWatch.dmcMin,
    dmc_preferred: fireWatch.dmcPreferred,
    dmc_max: fireWatch.dmcMax,
    dc_min: fireWatch.dcMin,
    dc_preferred: fireWatch.dcPreferred,
    dc_max: fireWatch.dcMax,
    isi_min: fireWatch.isiMin,
    isi_preferred: fireWatch.isiPreferred,
    isi_max: fireWatch.isiMax,
    bui_min: fireWatch.buiMin,
    bui_preferred: fireWatch.buiPreferred,
    bui_max: fireWatch.buiMax,
    hfi_min: fireWatch.hfiMin,
    hfi_preferred: fireWatch.hfiPreferred,
    hfi_max: fireWatch.hfiMax
  }
}


