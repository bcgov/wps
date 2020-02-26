import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { makeStyles } from '@material-ui/core/styles'

import { Station } from 'api/stationAPI'
import { selectPercentilesReducer } from 'app/rootReducer'
import { PageTitle } from 'components/PageTitle'
import { Container } from 'components/Container'
import { fetchStations } from 'features/fwiCalculator/slices/stationsSlice'
import { WeatherStationsDropdown } from 'features/fwiCalculator/components/StationsDropdown'
import { ActionButtons } from 'features/fwiCalculator/components/ActionButtons'
import { TimeRangeTextfield } from 'features/fwiCalculator/components/TimeRangeTextfield'
import { PercentileTextfield } from 'features/fwiCalculator/components/PercentileTextfield'
import {
  fetchPercentiles,
  resetPercentilesResult
} from 'features/fwiCalculator/slices/percentilesSlice'
import { PercentileResultTable } from 'features/fwiCalculator/components/PercentileResultTable'

const useStyles = makeStyles({
  resultTables: {
    display: 'flex'
  }
})

export const FWICalculatorPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const [stations, setStations] = useState<Station[]>([])
  const { result } = useSelector(selectPercentilesReducer)

  useEffect(() => {
    dispatch(fetchStations())
  }, [dispatch])

  const onStationsChange = (s: Station[]) => {
    if (s.length > 3) {
      return
    }
    setStations(s)
  }

  const onCalculateClick = () => {
    const stationCodes = stations.map(s => s.code)
    const percentile = 90
    const yearRange = { start: 2010, end: 2019 }
    dispatch(fetchPercentiles(stationCodes, percentile, yearRange))
  }

  const onResetClick = () => {
    setStations([])
    dispatch(resetPercentilesResult())
  }

  return (
    <>
      <PageTitle title="FWI Calculator" />
      <Container>
        <WeatherStationsDropdown
          stations={stations}
          onStationsChange={onStationsChange}
        />

        <TimeRangeTextfield />

        <PercentileTextfield />

        <ActionButtons
          stations={stations}
          onCalculateClick={onCalculateClick}
          onResetClick={onResetClick}
        />

        <div className={classes.resultTables}>
          {stations.map(station => {
            const stationResult = result?.stations[station.code]
            if (!stationResult) return null

            return (
              <PercentileResultTable
                key={station.code}
                station={station}
                stationResponse={stationResult}
              />
            )
          })}
        </div>
      </Container>
    </>
  )
}
