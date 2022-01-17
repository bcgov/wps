import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'
import { PlanningArea } from 'api/hfiCalcAPI'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { fireTableStyles } from 'app/theme'
import { StationDaily } from 'api/hfiCalculatorAPI'

export interface MeanIntensityGroupRollupProps {
  area: PlanningArea
  dailies: StationDaily[]
  selectedStations: number[]
  meanIntensityGroup: number | undefined
}

const useStyles = makeStyles({
  intensityGroup: {
    ...fireTableStyles.calculatedPlanningCell
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

  if (grassCureError) {
    return (
      <TableCell>
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
      </TableCell>
    )
  }
  if (genericError) {
    return (
      <TableCell>
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
      </TableCell>
    )
  }
  return (
    <TableCell
      className={classes.intensityGroup}
      data-testid={`zone-${props.area.id}-mean-intensity`}
    >
      {props.meanIntensityGroup}
    </TableCell>
  )
}

export default React.memo(MeanIntensityGroupRollup)
