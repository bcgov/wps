import React, { useState, useEffect } from 'react'

import { Button, Container, GeneralHeader, PageTitle } from 'components'

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
import { buildDailyMap, buildWeekliesByCode, buildWeekliesByUTC } from '../util'
import { getPrepDailyDateRange, getPrepWeeklyDateRange } from 'utils/date'

const useStyles = makeStyles(theme => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 210
  },
  buttonUnselected: {
    height: '56px',
    width: '210px',
    margin: '8px',
    border: '3px solid ' + theme.palette.primary.main
  },
  buttonSelected: {
    height: '56px',
    width: '210px',
    margin: '8px',
    border: '3px solid ' + theme.palette.primary.main,
    backgroundColor: theme.palette.primary.main,
    color: '#FFFFFF'
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
      const { start, end } =
        tableView === 'daily'
          ? getPrepDailyDateRange(dateOfInterest)
          : getPrepWeeklyDateRange(dateOfInterest)

      dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))
      dispatch(fetchHFIStations())

      setPreviouslySelectedDateOfInterest(dateOfInterest)
    }
  }

  const handleClickWeekly = () => {
    if (tableView === 'daily') {
      setTableView('weekly')
    }
  }

  const handleClickDaily = () => {
    if (tableView === 'weekly') {
      setTableView('daily')
    }
  }

  useEffect(() => {
    dispatch(fetchHFIStations())

    if (tableView === 'daily') {
      const dailyStartTime = DateTime.fromISO(dateOfInterest)
        .startOf('day')
        .toUTC()
        .valueOf()
      const dailyEndTime = DateTime.fromISO(dateOfInterest).toUTC().valueOf()
      dispatch(fetchHFIDailies(dailyStartTime, dailyEndTime))
      dispatch(fetchHFIStations())
    } else {
      const startAndEnd = getPrepWeeklyDateRange(dateOfInterest)
      console.log('toutc', startAndEnd.start.toUTC().valueOf())
      dispatch(
        fetchHFIDailies(
          startAndEnd.start.toUTC().valueOf(),
          startAndEnd.end.toUTC().valueOf()
        )
      )
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const dailiesMap = buildDailyMap(dailies)

  const weekliesMap = buildWeekliesByCode(dailies)

  const weekliesByUTC = buildWeekliesByUTC(dailies)

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
          <Button
            className={
              tableView === 'daily' ? classes.buttonSelected : classes.buttonUnselected
            }
            onClick={handleClickDaily}
          >
            Daily Table
          </Button>
          <Button
            className={
              tableView === 'weekly' ? classes.buttonSelected : classes.buttonUnselected
            }
            onClick={handleClickWeekly}
          >
            Weekly Table
          </Button>
          {tableView === 'daily' ? (
            <DailyViewTable
              title="HFI Calculator Daily View"
              testId="hfi-calc-daily-table"
              fireCentres={fireCentres}
              dailiesMap={dailiesMap}
            ></DailyViewTable>
          ) : (
            <WeeklyViewTable
              title="HFI Calculator Weekly View"
              testId="hfi-calc-weekly-table"
              fireCentres={fireCentres}
              dailiesMap={dailiesMap}
              weekliesByStationCode={weekliesMap}
              weekliesByUTC={weekliesByUTC}
              currentDay={dateOfInterest}
            />
          )}
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
