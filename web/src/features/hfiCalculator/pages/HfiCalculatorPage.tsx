import React, { useState } from 'react'

import { Container, GeneralHeader, PageTitle } from 'components'

import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import DatePicker from 'components/DatePicker'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import { fetchHFIDailies } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIDailies,
  selectHFIStations,
  selectHFIStationsLoading
} from 'app/rootReducer'
import { CircularProgress, FormControl, makeStyles } from '@material-ui/core'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { useEffect } from 'react'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    justifyContent: 'center'
  }
})

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  const updateDate = () => {
    dispatch(
      fetchHFIDailies(
        DateTime.fromISO(dateOfInterest).startOf('day').toUTC().valueOf(),
        DateTime.fromISO(dateOfInterest).endOf('day').toUTC().valueOf()
      )
    )
    dispatch(fetchHFIStations())
  }

  const dailiesMap = new Map<number, StationDaily>()
  if (dailies !== undefined) {
    dailies.forEach(daily => {
      dailiesMap.set(daily.code, daily)
    })
  }

  useEffect(() => {
    dispatch(fetchHFIStations())
    dispatch(
      fetchHFIDailies(
        DateTime.fromISO(dateOfInterest).startOf('day').toUTC().valueOf(),
        DateTime.fromISO(dateOfInterest).endOf('day').toUTC().valueOf()
      )
    )
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main data-testid="hfi-calculator-page">
      <GeneralHeader
        padding="3em"
        spacing={0.985}
        title="Predictive Services Unit"
        productName="HFI Calculator"
      />
      <PageTitle maxWidth={false} padding="1rem" title="HFI Calculator" />
      {loading || stationDataLoading ? (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      ) : (
        <Container maxWidth={'xl'}>
          <FormControl>
            <DatePicker
              date={dateOfInterest}
              onChange={setDateOfInterest}
              updateDate={updateDate}
            />
          </FormControl>
          <DailyViewTable
            testId="hfi-calc-daily-table"
            fireCentres={fireCentres}
            dailiesMap={dailiesMap}
            currentDay={dateOfInterest}
          />
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
