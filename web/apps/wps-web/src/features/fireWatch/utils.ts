import { isNil, isNull } from 'lodash'
import { BurnStatusEnum, type FireWatch, FuelTypeEnum } from '@/features/fireWatch/interfaces'

export const getBlankFireWatch = (): FireWatch => {
  return {
    id: NaN,
    burnWindowEnd: null,
    burnWindowStart: null,
    contactEmail: [],
    fireCentre: null,
    geometry: [],
    station: null,
    status: BurnStatusEnum.ACTIVE,
    title: '',
    // Fuel parameters
    fuelType: FuelTypeEnum.C1,
    percentConifer: NaN,
    percentDeadFir: NaN,
    percentGrassCuring: NaN,
    // Weather parameters
    tempMin: NaN,
    tempPreferred: NaN,
    tempMax: NaN,
    rhMin: NaN,
    rhPreferred: NaN,
    rhMax: NaN,
    windSpeedMin: NaN,
    windSpeedPreferred: NaN,
    windSpeedMax: NaN,
    // FWI and FBP parameters
    ffmcMin: NaN,
    ffmcPreferred: NaN,
    ffmcMax: NaN,
    dmcMin: NaN,
    dmcPreferred: NaN,
    dmcMax: NaN,
    dcMin: NaN,
    dcPreferred: NaN,
    dcMax: NaN,
    isiMin: NaN,
    isiPreferred: NaN,
    isiMax: NaN,
    buiMin: NaN,
    buiPreferred: NaN,
    buiMax: NaN,
    hfiMin: NaN,
    hfiPreferred: NaN,
    hfiMax: NaN
  }
}

const hasValidFuelInfo = (fireWatch: FireWatch) => {
  switch (fireWatch.fuelType) {
    case FuelTypeEnum.M1:
    case FuelTypeEnum.M2:
      return !isNil(fireWatch.percentConifer)
    case FuelTypeEnum.M3:
    case FuelTypeEnum.M4:
      return !isNil(fireWatch.percentDeadFir)
    case FuelTypeEnum.C7:
      return !isNil(fireWatch.percentGrassCuring)
  }
  return true
}

export const isValidFireWatch = (fireWatch: FireWatch) => {
  return (
    fireWatch.contactEmail.length > 0 &&
    !isNull(fireWatch.fireCentre) &&
    !isNull(fireWatch.station) &&
    fireWatch.title &&
    // Fuel parameters
    hasValidFuelInfo(fireWatch) &&
    // Weather parameters
    !Number.isNaN(fireWatch.tempMin) &&
    !Number.isNaN(fireWatch.tempMax) &&
    !Number.isNaN(fireWatch.rhMin) &&
    !Number.isNaN(fireWatch.rhMax) &&
    !Number.isNaN(fireWatch.windSpeedMin) &&
    !Number.isNaN(fireWatch.windSpeedMax) &&
    // FWI and FBP parameters
    !Number.isNaN(fireWatch.hfiMin) &&
    !Number.isNaN(fireWatch.hfiMax)
  )
}
