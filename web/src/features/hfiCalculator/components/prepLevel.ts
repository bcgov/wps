import { isUndefined } from 'lodash'

export type PrepLevel = 1 | 2 | 3 | 4 | 5 | 6 | undefined
export const calculatePrepLevel = (meanIntensityGroup: number | undefined): PrepLevel => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (isUndefined(meanIntensityGroup)) {
    return undefined
  }
  if (meanIntensityGroup < 3) {
    return 1
  }
  if (meanIntensityGroup < 4) {
    return 2
  }
  if (meanIntensityGroup < 5) {
    return 3
  }
  return 4
}
