import { styled } from '@mui/material'
import { BACKGROUND_COLOR } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { CalculatedPlanningCell } from 'features/hfiCalculator/components/StyledPlanningArea'
import { isNull, isUndefined } from 'lodash'
import React from 'react'

export interface PrepLevelCellProps {
  testid?: string
  toolTipText: string
  prepLevel: number | undefined
}

const prepLevelColours: { [description: string]: string } = {
  green: '#A0CD63',
  blue: '#4CAFEA',
  yellow: '#FFFD54',
  orange: '#F6C142',
  brightRed: '#EA3223',
  bloodRed: '#B02318'
}

const DAILY_BACKGROUND_COLOR = 'white'

const PrepLevelDefault = styled(CalculatedPlanningCell, { name: 'prepLevelDefault' })({
  ...BACKGROUND_COLOR
})

const PrepLevel1Cell = styled(CalculatedPlanningCell, { name: 'prepLevel1' })({
  border: '2px solid ' + prepLevelColours.green,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevel2Cell = styled(CalculatedPlanningCell, { name: 'prepLevel2' })({
  border: '2px solid ' + prepLevelColours.blue,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevel3Cell = styled(CalculatedPlanningCell, { name: 'prepLevel3' })({
  border: '2px solid ' + prepLevelColours.yellow,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevel4Cell = styled(CalculatedPlanningCell, { name: 'prepLevel4' })({
  border: '2px solid ' + prepLevelColours.orange,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevel5Cell = styled(CalculatedPlanningCell, { name: 'prepLevel5' })({
  border: '2px solid ' + prepLevelColours.brightRed,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevel6Cell = styled(CalculatedPlanningCell, { name: 'prepLevel6' })({
  border: '2px solid ' + prepLevelColours.bloodRed,
  background: DAILY_BACKGROUND_COLOR
})

const PrepLevelCell = (props: PrepLevelCellProps) => {
  const formatPrepLevelByValue = () => {
    switch (props.prepLevel) {
      case 1:
        return PrepLevel1Cell
      case 2:
        return PrepLevel2Cell
      case 3:
        return PrepLevel3Cell
      case 4:
        return PrepLevel4Cell
      case 5:
        return PrepLevel5Cell
      case 6:
        return PrepLevel6Cell
      default:
        return PrepLevelDefault
    }
  }

  const prepLevelErrorTooltipElement = (toolTipText: string) => <div>{toolTipText}</div>

  const PrepLevelCellComponent = formatPrepLevelByValue()

  return (
    <PrepLevelCellComponent data-testid={props.testid}>
      {isNull(props.prepLevel) || isUndefined(props.prepLevel) ? (
        <ErrorIconWithTooltip
          testId="prep-level-error"
          tooltipElement={prepLevelErrorTooltipElement(props.toolTipText)}
          tooltipAriaText={[props.toolTipText]}
        />
      ) : (
        props.prepLevel
      )}
    </PrepLevelCellComponent>
  )
}

export default React.memo(PrepLevelCell)
