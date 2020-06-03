import React from 'react'
import { useSelector } from 'react-redux'
import { Paper, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import DailyModelsDisplay from 'features/fireWeather/components/DailyModelsDisplay'
import HourlyReadingsDisplay from 'features/fireWeather/components/HourlyReadingsDisplay'
import WxGraphByStation from 'features/fireWeather/components/WxDataGraph'
import { Station } from 'api/stationAPI'
import { selectReadings, selectModels } from 'app/rootReducer'

const useStyles = makeStyles({
  displays: {
    marginTop: 16
  },
  paper: {
    paddingLeft: 16,
    paddingRight: 16,
    marginBottom: 20
  },
  station: {
    fontSize: '1.1rem',
    paddingTop: 8,
    paddingBottom: 8
  }
})

interface Props {
  requestedStations: Station[]
}

const WxDataDisplays = ({ requestedStations }: Props) => {
  const classes = useStyles()

  const { loading: loadingReadings, readingsByStation } = useSelector(selectReadings)
  const { loading: loadingModels, noonModelsByStation, modelsByStation } = useSelector(
    selectModels
  )

  const wxDataLoading = loadingModels || loadingReadings

  return (
    <div className={classes.displays}>
      {!wxDataLoading &&
        requestedStations.map(s => {
          const readingValues = readingsByStation[s.code]
          const modelValues = modelsByStation[s.code]
          const noonModelValues = noonModelsByStation[s.code]
          const nothingToDisplay = !readingValues && !modelValues

          if (nothingToDisplay) {
            return null
          }

          return (
            <Paper key={s.code} className={classes.paper} elevation={3}>
              <Typography className={classes.station} variant="subtitle1" component="div">
                Weather station: {`${s.name} (${s.code})`}
              </Typography>
              <HourlyReadingsDisplay values={readingValues} />
              <DailyModelsDisplay values={noonModelValues} />
              <WxGraphByStation modelValues={modelValues} readingValues={readingValues} />
            </Paper>
          )
        })}
    </div>
  )
}

export default React.memo(WxDataDisplays)
