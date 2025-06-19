import { DateTime } from 'luxon'

// Enums and interfaces for the front-end.

export enum BurnStatusEnum {
  ACTIVE = 'active',
  CANCELLED = 'cancelled',
  COMPLETE = 'complete',
  HOLD = 'hold'
}

export enum FuelTypeEnum {
  C1 = 'C1',
  C2 = 'C2',
  C3 = 'C3',
  C4 = 'C4',
  C5 = 'C5',
  C6 = 'C6',
  C7 = 'C7',
  C7B = 'C7B',
  D1 = 'D1',
  D2 = 'D2',
  M1 = 'M1',
  M2 = 'M2',
  M3 = 'M3',
  M4 = 'M4',
  O1A = 'O1A',
  O1B = 'O1B',
  S1 = 'S1',
  S2 = 'S2',
  S3 = 'S3'
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

export enum PrescriptionEnum {
  ALL = 'all',
  HFI = 'hfi',
  NO = 'no'
}

export interface FireWatchStation {
  code: number
  name: string
}

export interface FireWatch {
  burnWindowEnd: DateTime | null
  burnWindowStart: DateTime | null
  contactEmail: string[]
  fireCentre: FireWatchFireCentre | null
  geometry: number[]
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
  tempPreferred: number | null
  tempMax: number
  rhMin: number
  rhPreferred: number | null
  rhMax: number
  windSpeedMin: number
  windSpeedPreferred: number | null
  windSpeedMax: number
  // FWI and FBP parameters
  ffmcMin: number | null
  ffmcPreferred: number | null
  ffmcMax: number | null
  dmcMin: number | null
  dmcPreferred: number | null
  dmcMax: number | null
  dcMin: number | null
  dcPreferred: number | null
  dcMax: number | null
  isiMin: number | null
  isiPreferred: number | null
  isiMax: number | null
  buiMin: number | null
  buiPreferred: number | null
  buiMax: number | null
  hfiMin: number
  hfiPreferred: number | null
  hfiMax: number
  id: number
  createTimestamp?: DateTime
  createUser?: string
  updateTimestamp?: DateTime
  updateUser?: string
}

export interface FireWatchBurnForecast {
  fireWatch: FireWatch
  burnForecasts: BurnForecast[]
}

export interface FireWatchFireCentre {
  id: number
  name: string
}

export interface BurnForecast {
  id: number
  fireWatchId: number // The FireWatch record this BurnForecast relates to
  date: DateTime
  temp: number
  rh: number
  windSpeed: number
  ffmc: number
  dmc: number
  dc: number
  isi: number
  bui: number
  hfi: number
  inPrescription: PrescriptionEnum
}

export interface FireWatchBurnForecasts {
  fireWatch: FireWatch
  burnForecasts: BurnForecast[]
}
export interface BurnWatchRow {
  id: number
  title: string
  fireCentre: string
  station: string
  fuelType: FuelTypeEnum
  status: BurnStatusEnum
  burnWindowStart: DateTime | null
  burnWindowEnd: DateTime | null
  inPrescription: PrescriptionEnum
  fireWatch: FireWatch
  burnForecasts: BurnForecast[]
}
