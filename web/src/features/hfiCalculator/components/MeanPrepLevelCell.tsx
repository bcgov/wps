import { styled } from '@mui/material'
import { BACKGROUND_COLOR } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { CalculatedPlanningCell } from 'features/hfiCalculator/components/StyledPlanningAreaComponents'
import { isUndefined, isNull } from 'lodash'
import React from 'react'

export interface MeanPrepLevelCellProps {
  testid?: string
  areaName: string
  meanPrepLevel?: number
  emptyOrIncompleteForecast: boolean
}

const prepLevelColours: { [description: string]: string } = {
  green: '#A0CD63',
  blue: '#4CAFEA',
  yellow: '#FFFD54',
  orange: '#F6C142',
  brightRed: '#EA3223',
  bloodRed: '#B02318'
}

const MeanPrepLevelDefault = styled(CalculatedPlanningCell, { name: 'meanPrepLevelDefault' })({
  ...BACKGROUND_COLOR
})

const MeanPrepLevel1Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel1' })({
  background: prepLevelColours.green
})

const MeanPrepLevel2Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel2' })({
  background: prepLevelColours.blue
})

const MeanPrepLevel3Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel3' })({
  background: prepLevelColours.yellow
})

const MeanPrepLevel4Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel4' })({
  background: prepLevelColours.orange
})

const MeanPrepLevel5Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel5' })({
  background: prepLevelColours.brightRed,
  color: 'white'
})

const MeanPrepLevel6Cell = styled(CalculatedPlanningCell, { name: 'meanPrepLevel6' })({
  background: prepLevelColours.bloodRed,
  color: 'white'
})

const MeanPrepLevelCell = (props: MeanPrepLevelCellProps) => {
  const formatPrepLevelByValue = () => {
    switch (props.meanPrepLevel) {
      case 1:
        return MeanPrepLevel1Cell
      case 2:
        return MeanPrepLevel2Cell
      case 3:
        return MeanPrepLevel3Cell
      case 4:
        return MeanPrepLevel4Cell
      case 5:
        return MeanPrepLevel5Cell
      case 6:
        return MeanPrepLevel6Cell
      default:
        return MeanPrepLevelDefault
    }
  }

  const prepLevelError = () => {
    return (
      isUndefined(props.meanPrepLevel) ||
      isNull(props.meanPrepLevel) ||
      isNaN(props.meanPrepLevel) ||
      props.emptyOrIncompleteForecast === true
    )
  }

  const prepLevelTooltipText = 'Cannot calculate prep level. Please check the daily forecast using the tabs above.'

  const prepLevelErrorTooltipElement = <div>{prepLevelTooltipText}</div>

  const MeanPrepCellComponent = formatPrepLevelByValue()

  return (
    <MeanPrepCellComponent data-testid={props.testid}>
      {prepLevelError() ? (
        <ErrorIconWithTooltip
          testId="prep-level-error"
          tooltipElement={prepLevelErrorTooltipElement}
          tooltipAriaText={[prepLevelTooltipText]}
        />
      ) : (
        props.meanPrepLevel
      )}
    </MeanPrepCellComponent>
  )
}

export default React.memo(MeanPrepLevelCell)
