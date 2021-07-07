import { uniqueId } from 'lodash'

export interface FBCFuelType {
  name: string
  friendlyName: string
  percentage_conifer: number | undefined
  percentage_dead_balsam_fir: number | undefined
  crown_base_height: number | undefined
}
export class StationConfig {
  _stationCode: number
  _fuelType: FBCFuelType | undefined
  _grassCurePercentage: number | undefined
  constructor(
    readonly id: string = uniqueId(),
    stationCode: number = 322,
    fuelType?: FBCFuelType,
    grassCurePercentage?: number
  ) {
    this._stationCode = stationCode
    this._fuelType = fuelType
    this._grassCurePercentage = grassCurePercentage
  }

  get stationCode() {
    return this._stationCode
  }
  set stationCode(value: number) {
    this._stationCode = value
  }

  get fuelType() {
    return this._fuelType
  }
  set fuelType(value: FBCFuelType | undefined) {
    this._fuelType = value
  }

  get grassCurePercentage() {
    return this._grassCurePercentage
  }
  set grassCurePercentage(value: number | undefined) {
    this._grassCurePercentage = value
  }
}
