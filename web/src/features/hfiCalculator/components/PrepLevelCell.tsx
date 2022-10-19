import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
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

const useStyles = makeStyles({
  ...fireTableStyles,
  prepLevel1: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.green,
    background: DAILY_BACKGROUND_COLOR
  },
  prepLevel2: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.blue,
    background: DAILY_BACKGROUND_COLOR
  },
  prepLevel3: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.yellow,
    background: DAILY_BACKGROUND_COLOR
  },
  prepLevel4: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.orange,
    background: DAILY_BACKGROUND_COLOR
  },
  prepLevel5: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.brightRed,
    background: DAILY_BACKGROUND_COLOR
  },
  prepLevel6: {
    ...fireTableStyles.calculatedPlanningCell,
    border: '2px solid ' + prepLevelColours.bloodRed,
    background: DAILY_BACKGROUND_COLOR
  }
})

const PrepLevelCell = (props: PrepLevelCellProps) => {
  const classes = useStyles()

  const formatPrepLevelByValue = () => {
    switch (props.prepLevel) {
      case 1:
        return classes.prepLevel1
      case 2:
        return classes.prepLevel2
      case 3:
        return classes.prepLevel3
      case 4:
        return classes.prepLevel4
      case 5:
        return classes.prepLevel5
      case 6:
        return classes.prepLevel6
      default:
        return classes.defaultBackground
    }
  }

  const prepLevelErrorTooltipElement = (toolTipText: string) => <div>{toolTipText}</div>

  return (
    <TableCell className={formatPrepLevelByValue()} data-testid={props.testid}>
      {isNull(props.prepLevel) || isUndefined(props.prepLevel) ? (
        <ErrorIconWithTooltip
          testId="prep-level-error"
          tooltipElement={prepLevelErrorTooltipElement(props.toolTipText)}
          tooltipAriaText={[props.toolTipText]}
        />
      ) : (
        props.prepLevel
      )}
    </TableCell>
  )
}

export default React.memo(PrepLevelCell)
