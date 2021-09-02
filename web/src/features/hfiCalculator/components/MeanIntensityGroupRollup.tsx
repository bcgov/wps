import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createMuiTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'
import { isUndefined } from 'lodash'
import { PlanningArea } from 'api/hfiCalcAPI'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { StationDaily } from 'api/hfiCalculatorAPI'
import {
  calculateMeanIntensityGroup,
  intensityGroupColours
} from 'features/hfiCalculator/components/meanIntensity'

export interface MeanIntensityGroupRollupProps {
  area: PlanningArea
  dailiesMap: Map<number, StationDaily>
}

const useStyles = makeStyles({
  intensityGroupSolid1: {
    background: intensityGroupColours.lightGreen,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid2: {
    background: intensityGroupColours.cyan,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid3: {
    background: intensityGroupColours.yellow,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid4: {
    background: intensityGroupColours.orange,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  intensityGroupSolid5: {
    background: intensityGroupColours.red,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center'
  }
})

const adjustedTheme = createMuiTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    }
  }
})

const toolTipFirstLine = 'Grass Cure % not defined in WFWX one or more stations.'
const toolTipSecondLine = 'Cannot calculate Mean FIG.'
const toolTipElement = (
  <div>
    {toolTipFirstLine} <br />
    {toolTipSecondLine}
  </div>
)

const MeanIntensityGroupRollup = (props: MeanIntensityGroupRollupProps) => {
  const classes = useStyles()

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const error = Object.entries(props.area.stations).reduce((prev, [_, currStation]) => {
    const daily = props.dailiesMap.get(currStation.code)
    if (isUndefined(daily)) {
      return true
    }
    return prev || !isValidGrassCure(daily, currStation.station_props)
  }, false)

  const meanIntensityGroup = calculateMeanIntensityGroup(props.area, props.dailiesMap)
  const formatAreaMeanIntensityGroupByValue = (
    meanIntensityGroup: number | undefined
  ) => {
    if (meanIntensityGroup === undefined) {
      return undefined
    }
    if (meanIntensityGroup < 2) {
      return classes.intensityGroupSolid1
    }
    if (meanIntensityGroup < 3) {
      return classes.intensityGroupSolid2
    }
    if (meanIntensityGroup < 4) {
      return classes.intensityGroupSolid3
    }
    if (meanIntensityGroup < 5) {
      return classes.intensityGroupSolid4
    } else {
      return classes.intensityGroupSolid5
    }
  }

  return (
    <TableCell>
      {error ? (
        <ThemeProvider theme={adjustedTheme}>
          <Tooltip
            title={toolTipElement}
            aria-label={`${toolTipFirstLine} \n ${toolTipSecondLine}`}
          >
            <ErrorOutlineIcon></ErrorOutlineIcon>
          </Tooltip>
        </ThemeProvider>
      ) : (
        <TableCell
          className={formatAreaMeanIntensityGroupByValue(meanIntensityGroup)}
          data-testid={`zone-${props.area.name}-mean-intensity`}
        >
          {meanIntensityGroup}
        </TableCell>
      )}
    </TableCell>
  )
}

export default React.memo(MeanIntensityGroupRollup)
