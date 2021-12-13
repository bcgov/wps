import { isUndefined } from 'lodash'

export type PrepLevel = 1 | 2 | 3 | 4 | 5 | 6 | undefined
export const calculatePrepLevel = (
  rawMeanIntensityGroup: number | undefined,
  meanPrepLevel: boolean
): PrepLevel => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (meanPrepLevel && !isUndefined(rawMeanIntensityGroup)) {
    let meanPrepLevelNumber = Math.round(rawMeanIntensityGroup)
    switch (meanPrepLevelNumber) {
      case 1:
        return 1
      case 2:
        return 2
      case 3:
        return 3
      case 4:
        return 4
      case 5:
        return 5
      case 6:
        return 6
    }
  } else {
    let meanIntensityGroup = undefined
    if (isUndefined(rawMeanIntensityGroup)) {
      return undefined
    } else {
      meanIntensityGroup = Math.round(rawMeanIntensityGroup)
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
}
