import React, { useEffect, useState } from 'react'

import { Container, PageHeader, PageTitle } from 'components'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import { fetchHFIStations } from '../slices/stationsSlice'
import { fetchHFIDailies } from '../slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIDailies,
  selectHFIStations,
  selectHFIStationsLoading
} from 'app/rootReducer'
import { makeStyles, CircularProgress } from '@material-ui/core'
import { StationDaily } from 'api/hfiCalculatorAPI'

const HfiCalculatorPage: React.FunctionComponent = () => {
  const useStyles = makeStyles({
    container: {
      display: 'flex',
      justifyContent: 'center'
    }
  })
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const [currentDay, setCurrentDay] = useState(DateTime.now())

  useEffect(() => {
    const startTime = currentDay
      .startOf('day')
      .toUTC()
      .valueOf()
    const endTime = currentDay
      .endOf('day')
      .toUTC()
      .valueOf()
    dispatch(fetchHFIDailies(startTime, endTime))
    dispatch(fetchHFIStations())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentDay])

  const previousDay = () => {
    setCurrentDay(currentDay.minus({ days: 1 }))
  }

  const nextDay = () => {
    setCurrentDay(currentDay.plus({ days: 1 }))
  }

  const dailiesMap = new Map<number, StationDaily>()
  if (dailies !== undefined) {
    dailies.forEach(daily => {
      dailiesMap.set(daily.code, daily)
    })
  }

  return (
    <main data-testid="hfi-calculator-page">
      <PageHeader title="Predictive Services Unit" productName="HFI Calculator" />
      <PageTitle title="HFI Calculator" />
      <Container className={classes.container} maxWidth={'xl'}>
        {loading || stationDataLoading ? (
          <CircularProgress />
        ) : (
          <DailyViewTable
            title="HFI Calculator Daily View"
            testId="hfi-calc-daily-table"
            fireCentres={fireCentres}
            dailiesMap={dailiesMap}
            currentDay={currentDay.toLocaleString()}
            previousDay={previousDay}
            nextDay={nextDay}
          />
        )}
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
