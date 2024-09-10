import { FireShapeAreaDetail } from '@/api/fbaAPI'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from '@/features/fba/components/map/featureStylers'
import { AdvisoryStatus } from '@/utils/constants'

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
