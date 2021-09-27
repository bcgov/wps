import React, { useState, useEffect } from 'react'

import { Container, GeneralHeader, PageTitle } from 'components'

import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import DatePicker from 'components/DatePicker'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
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
import { groupBy } from 'lodash'
import { getPrepStartAndEnd } from 'utils/date'

const useStyles = makeStyles(theme => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 210
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const [tableView, setTableView] = useState('weekly')

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  const [previouslySelectedDateOfInterest, setPreviouslySelectedDateOfInterest] =
    useState(DateTime.now().toISODate())

  const updateDate = () => {
    if (previouslySelectedDateOfInterest !== dateOfInterest) {
      if (tableView === 'daily') {
        const dailyStartTime = DateTime.fromISO(dateOfInterest)
          .startOf('day')
          .toUTC()
          .valueOf()
        const dailyEndTime = DateTime.fromISO(dateOfInterest).toUTC().valueOf()
        dispatch(fetchHFIDailies(dailyStartTime, dailyEndTime))
        dispatch(fetchHFIStations())
      } else {
        const startAndEnd = getPrepStartAndEnd(dateOfInterest)
        console.log('toutc', startAndEnd.start.toUTC().valueOf())
        dispatch(
          fetchHFIDailies(
            startAndEnd.start.toUTC().valueOf(),
            startAndEnd.end.toUTC().valueOf()
          )
        )
        dispatch(fetchHFIStations())
      }
    }
  }

  const getDayName = (dateStr: string, locale: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(locale, { weekday: 'long' })
  }
  const day = getDayName(dateOfInterest, 'en-CA')

  useEffect(() => {
    if (tableView === 'daily') {
      const dailyStartTime = DateTime.fromISO(dateOfInterest)
        .startOf('day')
        .toUTC()
        .valueOf()
      const dailyEndTime = DateTime.fromISO(dateOfInterest).toUTC().valueOf()
      dispatch(fetchHFIDailies(dailyStartTime, dailyEndTime))
      dispatch(fetchHFIStations())
    } else {
      const startAndEnd = getPrepStartAndEnd(dateOfInterest)
      console.log('toutc', startAndEnd.start.toUTC().valueOf())
      dispatch(
        fetchHFIDailies(
          startAndEnd.start.toUTC().valueOf(),
          startAndEnd.end.toUTC().valueOf()
        )
      )
      dispatch(fetchHFIStations())
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const dailiesMap = new Map<number, StationDaily>()
  if (dailies !== undefined) {
    dailies.forEach(daily => {
      dailiesMap.set(daily.code, daily)
    })
  }

  const weekliesMap = new Map<number, StationDaily[]>()
  if (dailies !== undefined) {
    const weeklies = groupBy(dailies, 'code')
    for (let i = 0; i < Object.keys(weeklies).length; i++) {
      weekliesMap.set(Number(Object.keys(weeklies)[i]), Object.values(weeklies)[i])
    }
  }

  console.log(weekliesMap)
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
          <FormControl className={classes.formControl}>
            <DatePicker
              date={dateOfInterest}
              onChange={setDateOfInterest}
              updateDate={updateDate}
            />
          </FormControl>
          <WeeklyViewTable
            title="HFI Calculator Weekly View"
            testId="hfi-calc-weekly-table"
            fireCentres={fireCentres}
            dailiesMap={dailiesMap}
            weekliesMap={weekliesMap}
            currentDay={dateOfInterest}
          />
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
