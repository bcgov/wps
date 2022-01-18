import { isUndefined, range } from 'lodash'
import { NUM_WEEK_DAYS } from '../constants'

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
  rawMeanIntensityGroups: (number | undefined)[]
): number | undefined => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (isUndefined(rawMeanIntensityGroups)) {
    return undefined
  } else {
    const existingDailies: number[] = []
    rawMeanIntensityGroups.forEach(daily => {
      if (!isUndefined(daily)) {
        existingDailies.push(Math.round(daily))
      }
    })
    return Math.round(
      existingDailies?.reduce((a, b) => a + b, 0) / existingDailies.length
    )
  }
}

export const calculateDailyPrepLevels = (
  dailyMeanIntensityGroups: (number | undefined)[]
): (number | undefined)[] => {
  const prepLevels: (number | undefined)[] = []
  range(NUM_WEEK_DAYS).map(day => {
    const meanIntensityGroup = dailyMeanIntensityGroups[day]
    prepLevels.push(calculatePrepLevel(meanIntensityGroup))
  })
  return prepLevels
}
