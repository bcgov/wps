import { isNull } from 'lodash'

export const isGrassFuelType = (fuelType: string) =>
  fuelType === 'o1a' || fuelType === 'o1b'
export const isValidFuelSetting = (
  fuelType: string,
  grassCurePercentage: number | null
) => {
  if (isGrassFuelType(fuelType)) {
    return !isNull(grassCurePercentage)
  }
  return true
}
