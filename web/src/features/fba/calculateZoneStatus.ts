import { AdvisoryMinWindStats, FireShapeAreaDetail } from '@/api/fbaAPI'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'
import { AdvisoryStatus } from '@/utils/constants'
import { isNil, isUndefined } from 'lodash'

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

export const calculateWindSpeedText = (zoneMinWindStats: AdvisoryMinWindStats[]) => {
  const advisoryThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id == 1)
  const warningThresholdMinWindSpeed = zoneMinWindStats.find(windStats => windStats.threshold.id == 2)

  if (!isNil(warningThresholdMinWindSpeed) && !isNil(advisoryThresholdMinWindSpeed)) {
    return `Minimum forecasted wind speeds of ${advisoryThresholdMinWindSpeed?.min_wind_speed?.toPrecision(1) ?? 0} km/hr and ${warningThresholdMinWindSpeed?.min_wind_speed?.toPrecision(1) ?? 0} km/hr will result in Head Fire Intensity Classes 5 and 6 respectively.`
  }

  if (isNil(warningThresholdMinWindSpeed)) {
    return `Minimum forecasted wind speed of ${advisoryThresholdMinWindSpeed?.min_wind_speed?.toPrecision(1) ?? 0} km/hr will result in Head Fire Intensity Class 5.`
  }

  if (isNil(advisoryThresholdMinWindSpeed)) {
    return `Minimum forecasted wind speed of ${warningThresholdMinWindSpeed?.min_wind_speed?.toPrecision(1) ?? 0} km/hr will result in Head Fire Intensity Class 6.`
  }
}
