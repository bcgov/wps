import { AdvisoryMinWindStats, FireShapeAreaDetail } from '@/api/fbaAPI'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'
import { AdvisoryStatus } from '@/utils/constants'
import { isUndefined } from 'lodash'

export const calculateStatusColour = (
  details: FireShapeAreaDetail[],
  advisoryThreshold: number,
  defaultColour: string
) => {
  let status = defaultColour

  if (details.length === 0) {
    return status
  }

  const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
  const warningThresholdDetail = details.find(detail => detail.threshold == 2)
  const advisoryPercentage = advisoryThresholdDetail?.elevated_hfi_percentage ?? 0
  const warningPercentage = warningThresholdDetail?.elevated_hfi_percentage ?? 0

  if (advisoryPercentage + warningPercentage > advisoryThreshold) {
    status = ADVISORY_ORANGE_FILL
  }

  if (warningPercentage > advisoryThreshold) {
    status = ADVISORY_RED_FILL
  }

  return status
}

export const calculateStatusText = (
  details: FireShapeAreaDetail[],
  advisoryThreshold: number
): AdvisoryStatus | undefined => {
  if (isUndefined(details) || details.length === 0) {
    return undefined
  }

  const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
  const warningThresholdDetail = details.find(detail => detail.threshold == 2)
  const advisoryPercentage = advisoryThresholdDetail?.elevated_hfi_percentage ?? 0
  const warningPercentage = warningThresholdDetail?.elevated_hfi_percentage ?? 0

  if (warningPercentage > advisoryThreshold) {
    return AdvisoryStatus.WARNING
  }

  if (advisoryPercentage + warningPercentage > advisoryThreshold) {
    return AdvisoryStatus.ADVISORY
  }
}

export const getWindSpeedMinimum = (zoneMinWindStats: AdvisoryMinWindStats[]): number | undefined => {
  const advisoryThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id === 1)
  const warningThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id === 2)

  const advisoryWindSpeed = advisoryThresholdMinWindSpeed?.min_wind_speed ?? Infinity
  const warningWindSpeed = warningThresholdMinWindSpeed?.min_wind_speed ?? Infinity

  const validSpeeds = [advisoryWindSpeed, warningWindSpeed].filter(windSpeed => windSpeed > 0)

  const minWindSpeed = Math.min(...validSpeeds)

  return minWindSpeed !== Infinity ? minWindSpeed : undefined
}

export const calculateWindSpeedText = (zoneMinWindStats: AdvisoryMinWindStats[]): string | undefined => {
  const minWindSpeed = getWindSpeedMinimum(zoneMinWindStats)

  return minWindSpeed ? `if winds exceed ${minWindSpeed.toPrecision(1)} km/h` : undefined
}
