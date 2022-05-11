import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
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

const useStyles = makeStyles({
  ...fireTableStyles,
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

const MeanPrepLevelCell = (props: MeanPrepLevelCellProps) => {
  const classes = useStyles()

  const formatPrepLevelByValue = () => {
    switch (props.meanPrepLevel) {
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

  return (
    <TableCell
      className={prepLevelError() ? classes.defaultBackground : formatPrepLevelByValue()}
      data-testid={props.testid}
    >
      {prepLevelError() ? (
        <ErrorIconWithTooltip
          testId="prep-level-error"
          tooltipElement={prepLevelErrorTooltipElement}
          tooltipAriaText={[prepLevelTooltipText]}
        />
      ) : (
        props.meanPrepLevel
      )}
    </TableCell>
  )
}

export default React.memo(MeanPrepLevelCell)
