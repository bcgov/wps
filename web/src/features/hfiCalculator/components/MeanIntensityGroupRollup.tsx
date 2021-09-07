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
  },
  alignErrorIcon: {
    marginTop: '6px',
    textAlign: 'center'
  }
})

const errorIconTheme = createMuiTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    }
  }
})

const toolTipFirstLine = 'Grass Cure % not defined in WFWX for one or more stations.'
const toolTipSecondLine = 'Cannot calculate Mean FIG.'
const toolTipElement = (
  <div>
    {toolTipFirstLine}
    {toolTipSecondLine}
  </div>
)

const MeanIntensityGroupRollup = (props: MeanIntensityGroupRollupProps) => {
  const classes = useStyles()

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const stationsWithDaily = Object.entries(props.area.stations).map(([_, station]) => ({
    station,
    daily: props.dailiesMap.get(station.code)
  }))
  const noDailyData = stationsWithDaily.every(stationDaily =>
    isUndefined(stationDaily.daily)
  )
  const error = stationsWithDaily.reduce((prev, stationDaily) => {
    return (
      prev || !isValidGrassCure(stationDaily.daily, stationDaily.station.station_props)
    )
  }, false)

  const meanIntensityGroup = calculateMeanIntensityGroup(props.area, props.dailiesMap)
  const formatAreaMeanIntensityGroupByValue = () => {
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

  return error && !noDailyData ? (
    <ThemeProvider theme={errorIconTheme}>
      <Tooltip
        title={toolTipElement}
        aria-label={`${toolTipFirstLine} \n ${toolTipSecondLine}`}
      >
        <div className={classes.alignErrorIcon}>
          <ErrorOutlineIcon></ErrorOutlineIcon>
        </div>
      </Tooltip>
    </ThemeProvider>
  ) : (
    <TableCell
      className={formatAreaMeanIntensityGroupByValue()}
      data-testid={`zone-${props.area.name}-mean-intensity`}
    >
      {meanIntensityGroup}
    </TableCell>
  )
}

export default React.memo(MeanIntensityGroupRollup)
