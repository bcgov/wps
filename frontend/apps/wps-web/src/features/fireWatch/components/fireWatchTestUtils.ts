import { BurnStatusEnum, BurnForecast, FireWatch, FuelTypeEnum, PrescriptionEnum } from '@/features/fireWatch/interfaces'
import { DateTime } from 'luxon'

export const createMockFireWatch = (overrides: Partial<FireWatch> = {}): FireWatch => {
  const now = DateTime.now()
  return {
    id: 1,
    title: 'test',
    burnWindowEnd: now,
    burnWindowStart: now,
    contactEmail: ['test@gov.bc.ca'],
    fireCentre: { id: 1, name: 'test' },
    geometry: [123, 123],
    station: { code: 1, name: 'test' },
    status: BurnStatusEnum.ACTIVE,
    fuelType: FuelTypeEnum.C1,
    tempMin: 1,
    tempPreferred: 2,
    tempMax: 3,
    rhMin: 1,
    rhPreferred: 2,
    rhMax: 3,
    windSpeedMin: 1,
    windSpeedPreferred: 2,
    windSpeedMax: 3,
    ffmcMin: 1,
    ffmcPreferred: 2,
    ffmcMax: 3,
    dmcMin: 1,
    dmcPreferred: 2,
    dmcMax: 3,
    dcMin: 1,
    dcPreferred: 2,
    dcMax: 3,
    isiMin: 1,
    isiPreferred: 2,
    isiMax: 3,
    buiMin: 1,
    buiPreferred: 2,
    buiMax: 3,
    hfiMin: 1,
    hfiPreferred: 2,
    hfiMax: 3,
    createTimestamp: now,
    createUser: 'test',
    updateTimestamp: now,
    updateUser: 'test',
    ...overrides
  }
}

export const createMockBurnForecast = (overrides: Partial<BurnForecast> = {}): BurnForecast => ({
  id: 1,
  fireWatchId: 1,
  date: DateTime.fromISO('2024-05-01'),
  temp: 18.5,
  rh: 45,
  windSpeed: 10,
  ffmc: 85,
  dmc: 12,
  dc: 200,
  isi: 3,
  bui: 40,
  hfi: 100,
  inPrescription: PrescriptionEnum.ALL,
  ...overrides
})
