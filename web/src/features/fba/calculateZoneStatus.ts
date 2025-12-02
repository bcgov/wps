import { AdvisoryMinWindStats, FireShapeAreaDetail } from '@/api/fbaAPI'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'
import { AdvisoryStatus } from '@/utils/constants'
import { isNil } from 'lodash'

export const calculateStatusColour = (details: FireShapeAreaDetail | undefined, defaultColour: string) => {
  switch (details?.status) {
    case AdvisoryStatus.ADVISORY:
      return ADVISORY_ORANGE_FILL
    case AdvisoryStatus.WARNING:
      return ADVISORY_RED_FILL
    default:
      return defaultColour
  }
}

export const getWindSpeedMinimum = (zoneMinWindStats: AdvisoryMinWindStats[]): number | undefined => {
  const advisoryThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id === 1)
  const warningThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id === 2)

  const advisoryWindSpeed = advisoryThresholdMinWindSpeed?.min_wind_speed ?? -1
  const warningWindSpeed = warningThresholdMinWindSpeed?.min_wind_speed ?? -1

  const validSpeeds = [advisoryWindSpeed, warningWindSpeed].filter(windSpeed => windSpeed >= 0)

  const minWindSpeed = Math.min(...validSpeeds)

  return minWindSpeed !== Infinity ? minWindSpeed : undefined
}

export const calculateWindSpeedText = (zoneMinWindStats: AdvisoryMinWindStats[]): string | undefined => {
  const minWindSpeed = getWindSpeedMinimum(zoneMinWindStats)

  // 0 is falsy, so we need to perform a null/undefined check for this to consider 0 valid
  return !isNil(minWindSpeed) ? `if winds exceed ${minWindSpeed.toFixed(0)} km/h` : undefined
}
