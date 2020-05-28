import React from 'react'
import { useSelector } from 'react-redux'
import { Paper, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import DailyModelsDisplay from 'features/fireWeather/components/DailyModelsDisplay'
import HourlyReadingsDisplay from 'features/fireWeather/components/HourlyReadingsDisplay'
import WxGraphByStation from 'features/fireWeather/components/WxGraphByStation'
import { Station } from 'api/stationAPI'
import { selectReadings, selectModels } from 'app/rootReducer'
import { ErrorMessage } from 'components'

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
  stations: Station[]
}

const WxDisplaysByStations = ({ stations }: Props) => {
  const classes = useStyles()
  const { error: errorFetchingReadings, readingsByStation } = useSelector(selectReadings)
  const {
    error: errorFetchingModels,
    noonModelsByStation,
    modelsByStation
  } = useSelector(selectModels)

  return (
    <>
      {errorFetchingModels && (
        <ErrorMessage
          error={errorFetchingModels}
          context="while fetching global model data"
          marginTop={5}
        />
      )}

      {errorFetchingReadings && (
        <ErrorMessage
          error={errorFetchingReadings}
          context="while fetching hourly readings"
          marginTop={5}
        />
      )}

      <div className={classes.displays}>
        {stations.map(s => {
          const ReadingValues = readingsByStation[s.code]
          const ModelValues = modelsByStation[s.code]
          const noonModelValues = noonModelsByStation[s.code]
          const nothingToDisplay = !ReadingValues && !ModelValues

          if (nothingToDisplay) {
            return null
          }

          return (
            <Paper key={s.code} className={classes.paper} elevation={3}>
              <Typography className={classes.station} variant="subtitle1" component="div">
                Weather station: {`${s.name} (${s.code})`}
              </Typography>
              <HourlyReadingsDisplay values={ReadingValues} />
              <DailyModelsDisplay values={noonModelValues} />
              <WxGraphByStation values={ModelValues} />
            </Paper>
          )
        })}
      </div>
    </>
  )
}

export default React.memo(WxDisplaysByStations)
