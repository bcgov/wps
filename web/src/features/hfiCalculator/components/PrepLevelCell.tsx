import { makeStyles, TableCell } from '@material-ui/core'
import { fireTableStyles } from 'app/theme'
import { calculatePrepLevel } from 'features/hfiCalculator/components/prepLevel'
import React from 'react'

export interface PrepLevelCellProps {
  testid?: string
  meanIntensityGroup: number | undefined
  areaName: string
  meanPrepLevel: boolean
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
  },
  meanPrepLevel1: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.green
  },
  meanPrepLevel2: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.blue
  },
  meanPrepLevel3: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.yellow
  },
  meanPrepLevel4: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.orange
  },
  meanPrepLevel5: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.brightRed,
    color: 'white'
  },
  meanPrepLevel6: {
    ...fireTableStyles.calculatedPlanningCell,
    background: prepLevelColours.bloodRed,
    color: 'white'
  }
})

const PrepLevelCell = (props: PrepLevelCellProps) => {
  const classes = useStyles()

  const prepLevel = calculatePrepLevel(props.meanIntensityGroup)

  const formatPrepLevelByValue = () => {
    if (!props.meanPrepLevel) {
      switch (prepLevel) {
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
    } else {
      switch (prepLevel) {
        case 1:
          return classes.meanPrepLevel1
        case 2:
          return classes.meanPrepLevel2
        case 3:
          return classes.meanPrepLevel3
        case 4:
          return classes.meanPrepLevel4
        case 5:
          return classes.meanPrepLevel5
        case 6:
          return classes.meanPrepLevel6
        default:
          return classes.defaultBackground
      }
    }
  }

  return (
    <TableCell className={formatPrepLevelByValue()} data-testid={props.testid}>
      {prepLevel}
    </TableCell>
  )
}

export default React.memo(PrepLevelCell)
