import React from 'react'
import UpdateIcon from '@mui/icons-material/Update'
import makeStyles from '@mui/styles/makeStyles'
import { maxBy } from 'lodash'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { theme } from 'app/theme'
import { createTheme, StyledEngineProvider, ThemeProvider } from '@mui/material'

export interface LastUpdatedHeaderProps {
  dailies?: StationDaily[]
}

const useStyles = makeStyles({
  container: {
    display: 'flex',
    alignItems: 'center',
    margin: theme.spacing(1)
  },
  headerText: {
    fontSize: '14px',
    color: theme.palette.primary.main
  }
})

const lastUpdatedTheme = createTheme({
  components: {
    MuiSvgIcon: {
      styleOverrides: {
        root: {
          fill: theme.palette.primary.main
        }
      }
    }
  }
})

const findLastUpdate = (dailies?: StationDaily[]) => {
  const forecasts = dailies?.filter(daily => daily.status === 'FORECAST')
  const lastUpdatedDaily: StationDaily | undefined = maxBy(forecasts, forecast => forecast.last_updated)
  if (lastUpdatedDaily?.last_updated) {
    return DateTime.fromObject(
      {
        year: lastUpdatedDaily.last_updated.year,
        month: lastUpdatedDaily.last_updated.month,
        day: lastUpdatedDaily.last_updated.day,
        hour: lastUpdatedDaily.last_updated.hour,
        minute: lastUpdatedDaily.last_updated.minute
      },
      { zone: `UTC${PST_UTC_OFFSET}` }
    )
  }
}

const LastUpdatedHeader = (props: LastUpdatedHeaderProps) => {
  const classes = useStyles()
  const lastUpdate = findLastUpdate(props.dailies)
  if (lastUpdate) {
    const dateString = lastUpdate.toFormat('MMMM d, HH:mm') + ' PST'

    return (
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={lastUpdatedTheme}>
          <span className={classes.container}>
            <UpdateIcon></UpdateIcon>
            <p className={classes.headerText}>Forecast last updated {dateString}</p>
          </span>
        </ThemeProvider>
      </StyledEngineProvider>
    )
  } else {
    return <React.Fragment></React.Fragment>
  }
}

export default React.memo(LastUpdatedHeader)
