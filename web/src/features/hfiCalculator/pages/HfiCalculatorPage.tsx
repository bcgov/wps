import React, { useState, useEffect } from 'react'

import { Container, GeneralHeader, PageTitle } from 'components'

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
import { buildDailyMap, buildWeekliesByCode, buildWeekliesByUTC } from '../util'
import { getDateRange } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'

const useStyles = makeStyles(theme => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  formControl: {
    display: 'flex',
    flexDirection: 'row',
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
  const [isWeeklyView, toggleTableView] = useState(true)

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  const [previouslySelectedDateOfInterest, setPreviouslySelectedDateOfInterest] =
    useState(DateTime.now().toISODate())

  const updateDate = () => {
    if (previouslySelectedDateOfInterest !== dateOfInterest) {
      const { start, end } = getDateRange(isWeeklyView, dateOfInterest)
      dispatch(fetchHFIStations())
      dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))

      setPreviouslySelectedDateOfInterest(dateOfInterest)
    }
  }

  useEffect(() => {
    const { start, end } = getDateRange(isWeeklyView, dateOfInterest)
    dispatch(fetchHFIStations())
    dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))

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
            <ViewSwitcherToggles
              isWeeklyView={isWeeklyView}
              toggleTableView={toggleTableView}
            />
          </FormControl>

          <ViewSwitcher
            isWeeklyView={isWeeklyView}
            fireCentres={fireCentres}
            dailiesMap={dailiesMap}
            weekliesMap={weekliesMap}
            weekliesByUTC={weekliesByUTC}
            dateOfInterest={dateOfInterest}
          />
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
