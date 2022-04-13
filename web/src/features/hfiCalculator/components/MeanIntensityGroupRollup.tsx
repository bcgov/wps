import { TableCell } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { isUndefined } from 'lodash'
import React from 'react'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { fireTableStyles } from 'app/theme'
import { StationDaily, PlanningArea } from 'api/hfiCalculatorAPI'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'

export interface MeanIntensityGroupRollupProps {
  area: PlanningArea
  dailies: StationDaily[]
  meanIntensityGroup: number | undefined
}

const useStyles = makeStyles({
  intensityGroup: {
    ...fireTableStyles.calculatedPlanningCell
  }
})

const grassCureToolTipFirstLine =
  'Grass Cure % not defined in WFWX for one or more stations.'
const genericErrorToolTipFirstLine =
  'Incomplete weather data in WFWX for one or more stations.'
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
  const classes = useStyles()
  const stationMap = new Map(
    Object.entries(props.area.stations).map(([, station]) => [station.code, station])
  )

  const grassCureError = props.dailies.reduce((prev, stationDaily) => {
    return (
      prev ||
      !isValidGrassCure(stationDaily, stationMap.get(stationDaily.code)?.station_props)
    )
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
  if (genericError) {
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
  const validatedMig =
    isUndefined(props.meanIntensityGroup) ||
    isNaN(props.meanIntensityGroup) ||
    props.meanIntensityGroup === Infinity ||
    props.meanIntensityGroup === -Infinity
      ? ''
      : props.meanIntensityGroup
  return (
    <TableCell
      className={classes.intensityGroup}
      data-testid={`zone-${props.area.id}-mean-intensity`}
    >
      {validatedMig}
    </TableCell>
  )
}

export default React.memo(MeanIntensityGroupRollup)
