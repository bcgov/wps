import { TableCell } from '@mui/material'
import { isUndefined, isNull } from 'lodash'
import React from 'react'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { StationDaily, PlanningArea, FuelType } from 'api/hfiCalculatorAPI'
import { getSelectedFuelType } from 'features/hfiCalculator/util'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { CalculatedPlanningCell } from 'features/hfiCalculator/components/StyledPlanningAreaComponents'

export interface MeanIntensityGroupRollupProps {
  area: PlanningArea
  dailies: StationDaily[]
  meanIntensityGroup: number | undefined
  planningAreaStationInfo: { [key: number]: StationInfo[] }
  fuelTypes: FuelType[]
}

const grassCureToolTipFirstLine = 'Grass Cure % not defined in WFWX for one or more stations.'
const genericErrorToolTipFirstLine = 'Incomplete weather data in WFWX for one or more stations.'
const toolTipSecondLine = ' Cannot calculate Mean FIG.'

const grassCureErrorToolTipElement = (
  <div>
    {grassCureToolTipFirstLine}
    {toolTipSecondLine}
  </div>
)

const genericErrorToolTipElement = (
  <div>
    {genericErrorToolTipFirstLine}
    {toolTipSecondLine}
  </div>
)

const MeanIntensityGroupRollup = (props: MeanIntensityGroupRollupProps) => {
  const grassCureError = props.dailies.reduce((prev, stationDaily) => {
    const selectedFuelType = getSelectedFuelType(
      props.planningAreaStationInfo,
      props.area.id,
      stationDaily.code,
      props.fuelTypes
    )
    return prev || !isValidGrassCure(stationDaily, selectedFuelType)
  }, false)

  const genericError = props.dailies.reduce((prev, stationDaily) => {
    return prev || stationDaily.observation_valid === false
  }, false)

  if (grassCureError) {
    return (
      <TableCell>
        <ErrorIconWithTooltip
          testId={`zone-${props.area.id}-mig-error`}
          tooltipElement={grassCureErrorToolTipElement}
          tooltipAriaText={[grassCureToolTipFirstLine, toolTipSecondLine]}
        />
      </TableCell>
    )
  }
  const validatedMig =
    isUndefined(props.meanIntensityGroup) ||
    isNull(props.meanIntensityGroup) ||
    isNaN(props.meanIntensityGroup) ||
    props.meanIntensityGroup === Infinity ||
    props.meanIntensityGroup === -Infinity
      ? ''
      : props.meanIntensityGroup
  if (genericError || validatedMig === '') {
    return (
      <TableCell>
        <ErrorIconWithTooltip
          testId={`zone-${props.area.id}-mig-error`}
          tooltipElement={genericErrorToolTipElement}
          tooltipAriaText={[genericErrorToolTipFirstLine, toolTipSecondLine]}
        />
      </TableCell>
    )
  }
  return (
    <CalculatedPlanningCell data-testid={`zone-${props.area.id}-mean-intensity`}>{validatedMig}</CalculatedPlanningCell>
  )
}

export default React.memo(MeanIntensityGroupRollup)
