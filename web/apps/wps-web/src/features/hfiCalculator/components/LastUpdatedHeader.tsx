import UpdateIcon from '@mui/icons-material/Update'
import { createTheme, ThemeProvider } from '@mui/material'
import { styled } from '@mui/material/styles'
import type { StationDaily } from '@wps/api/hfiCalculatorAPI'
import { theme } from '@wps/ui/theme'
import { formatInBCPacificTime } from '@wps/utils/date'
import { maxBy } from 'lodash'
import React from 'react'

const PREFIX = 'LastUpdatedHeader'

const Container = styled('span', { name: `${PREFIX}-container` })({
  display: 'flex',
  alignItems: 'center',
  margin: theme.spacing(1)
})

const HeaderText = styled('p', { name: `${PREFIX}-headerText` })({
  fontSize: '14px',
  color: theme.palette.primary.main
})

export interface LastUpdatedHeaderProps {
  dailies?: StationDaily[]
}

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

const LastUpdatedHeader = (props: LastUpdatedHeaderProps) => {
  const forecasts = props.dailies?.filter(daily => daily.status === 'FORECAST')
  const lastUpdate = maxBy(forecasts, forecast => forecast.last_updated)?.last_updated
  if (lastUpdate) {
    const dateString = formatInBCPacificTime(lastUpdate, 'MMMM d, HH:mm')

    return (
      <ThemeProvider theme={lastUpdatedTheme}>
        <Container>
          <UpdateIcon></UpdateIcon>
          <HeaderText>Forecast last updated {dateString}</HeaderText>
        </Container>
      </ThemeProvider>
    )
  } else {
    return <div></div>
  }
}

export default React.memo(LastUpdatedHeader)
