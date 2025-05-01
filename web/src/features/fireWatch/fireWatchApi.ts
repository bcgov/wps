import axios from 'api/axios'
import { DateTime } from 'luxon';

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

export interface FireWatch {
  burnWindowEnd: DateTime
  burnWindowStart: DateTime
  contactEmail: string[]
  fireCentre: number
  latitude: number,
  longitude: number, 
  stationCode: number
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
  fire_centre: number
  station_code: number
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

export async function getActiveFireWatches(): Promise<FireWatchListResponse> {
  const url = '/fire-watch/active'
  const { data } = await axios.get(url)
  return data
}

export async function postFireWatchInput(fireWatch: FireWatch): Promise<FireWatchResponse> {
  const fireWatchInput = marshalFireWatchToFireWatchInput(fireWatch)
  const url = '/fire-watch/watch'
  const { data } = await axios.post(url, {
    fireWatchInput
  })
  return data
}

const marshalFireWatchToFireWatchInput = (fireWatch: FireWatch) => {
  const fireWatchInput = {
    burnWindowEnd: fireWatch.burnWindowEnd?.toMillis(),
    burnWindowStart: fireWatch.burnWindowStart?.toMillis(),
    contactEmail: [fireWatch.contactEmail],
    fireCentre: fireWatch.fireCentre ,
    latitude: fireWatch.latitude ,
    longitude: fireWatch.longitude , 
    stationCode: fireWatch.stationCode ,
    status: fireWatch.status,
    title: fireWatch.title,
    // Fuel parameters
    fuelType: fireWatch.fuelType,
    percentConifer: fireWatch.percentConifer ,
    percentDeadFir: fireWatch.percentDeadFir ,
    percentGrassCuring: fireWatch.percentGrassCuring ,
    // Weather parameters
    tempMin: fireWatch.tempMin ,
    tempPreferred: fireWatch.tempPreferred ,
    tempMax: fireWatch.tempMax ,
    rhMin: fireWatch.rhMin ,
    rhPreferred: fireWatch.rhPreferred ,
    rhMax: fireWatch.rhMax ,
    windSpeedMin: fireWatch.windSpeedMin ,
    windSpeedPreferred: fireWatch.windSpeedPreferred ,
    windSpeedMax: fireWatch.windSpeedMax ,
    // FWI and FBP parameters
    ffmcMin: fireWatch.ffmcMin ,
    ffmcPreferred: fireWatch.ffmcPreferred,
    ffmcMax: fireWatch.ffmcMax,
    dmcMin: fireWatch.dmcMin,
    dmcPreferred: fireWatch.dmcPreferred,
    dmcMax: fireWatch.dmcMax,
    dcMin: fireWatch.dcMin,
    dcPreferred: fireWatch.dcPreferred,
    dcMax: fireWatch.dcMax,
    isiMin: fireWatch.isiMin,
    isiPreferred: fireWatch.isiPreferred,
    isiMax: fireWatch.isiMax,
    buiMin: fireWatch.buiMin,
    buiPreferred: fireWatch.buiPreferred,
    buiMax: fireWatch.buiMax,
    hfiMin: fireWatch.hfiMin,
    hfiPreferred: fireWatch.hfiPreferred,
    hfiMax: fireWatch.hfiMax
  }
}


