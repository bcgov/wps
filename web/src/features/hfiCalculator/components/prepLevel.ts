import { isUndefined } from 'lodash'

export const calculatePrepLevel = (
  meanIntensityGroup: number | undefined
): number | undefined => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1

  if (isUndefined(meanIntensityGroup)) {
    return undefined
  } else {
    meanIntensityGroup = Math.round(meanIntensityGroup)
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

export const calculateMeanPrepLevel = (
  rawMeanIntensityGroup: number | undefined
): number | undefined => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (isUndefined(rawMeanIntensityGroup)) {
    return undefined
  } else {
    return Math.round(rawMeanIntensityGroup)
  }
}
