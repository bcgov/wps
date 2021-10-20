import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'
import { PlanningArea } from 'api/hfiCalcAPI'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import {
  calculateMeanIntensity,
  intensityGroupColours
} from 'features/hfiCalculator/components/meanIntensity'
import { fireTableStyles } from 'app/theme'
import { StationDaily } from 'api/hfiCalculatorAPI'

export interface MeanIntensityGroupRollupProps {
  area: PlanningArea
  dailies: StationDaily[]
  selectedStations: number[]
  meanIntensityGroupOverride?: number
}

const useStyles = makeStyles({
  ...fireTableStyles,
  intensityGroupSolid1: {
    ...fireTableStyles.calculatedPlanningCell,
    background: intensityGroupColours.lightGreen
  },
  intensityGroupSolid2: {
    ...fireTableStyles.calculatedPlanningCell,
    background: intensityGroupColours.cyan
  },
  intensityGroupSolid3: {
    ...fireTableStyles.calculatedPlanningCell,
    background: intensityGroupColours.yellow
  },
  intensityGroupSolid4: {
    ...fireTableStyles.calculatedPlanningCell,
    background: intensityGroupColours.orange
  },
  intensityGroupSolid5: {
    ...fireTableStyles.calculatedPlanningCell,
    background: intensityGroupColours.red,
    color: 'white'
  },
  alignErrorIcon: {
    ...fireTableStyles.planningArea,
    paddingTop: '10px',
    textAlign: 'center'
  }
})

const errorIconTheme = createTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    }
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

  const meanIntensityGroup = calculateMeanIntensity(props.dailies)

  if (grassCureError) {
    return (
      <ThemeProvider theme={errorIconTheme}>
        <Tooltip
          title={grassCureErrorToolTipElement}
          aria-label={`${grassCureToolTipFirstLine} \n ${toolTipSecondLine}`}
        >
          <div className={classes.alignErrorIcon}>
            <ErrorOutlineIcon
              data-testid={`zone-${props.area.id}-mig-error`}
            ></ErrorOutlineIcon>
          </div>
        </Tooltip>
      </ThemeProvider>
    )
  }
  if (genericError) {
    return (
      <ThemeProvider theme={errorIconTheme}>
        <Tooltip
          title={genericErrorToolTipElement}
          aria-label={`${genericErrorToolTipFirstLine} ${toolTipSecondLine}`}
        >
          <div className={classes.alignErrorIcon}>
            <ErrorOutlineIcon
              data-testid={`zone-${props.area.id}-mig-error`}
            ></ErrorOutlineIcon>
          </div>
        </Tooltip>
      </ThemeProvider>
    )
  } else {
    const formatAreaMeanIntensityGroupByValue = () => {
      if (meanIntensityGroup === undefined) {
        return classes.defaultBackground
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
      <TableCell
        className={formatAreaMeanIntensityGroupByValue()}
        data-testid={`zone-${props.area.id}-mean-intensity`}
      >
        {meanIntensityGroup}
      </TableCell>
    )
  }
}

export default React.memo(MeanIntensityGroupRollup)
