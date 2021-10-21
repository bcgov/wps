import React, { useState, useEffect } from 'react'

import { Button, Container, GeneralHeader, PageTitle } from 'components'

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
import { getDateRange } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { AboutDataModal } from 'features/hfiCalculator/components/AboutDataModal'
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  infoIcon: {
    fill: theme.palette.primary.main
  },
  aboutButtonText: {
    color: theme.palette.primary.main,
    textDecoration: 'underline',
    fontWeight: 'bold'
  },
  positionStyler: {
    position: 'absolute',
    right: '20px'
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const [isWeeklyView, toggleTableView] = useState(false)
  const [modalOpen, setModalOpen] = useState<boolean>(false)

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone('UTC-7').toISO()
  )
  const [previouslySelectedDateOfInterest, setPreviouslySelectedDateOfInterest] =
    useState(DateTime.now().setZone('UTC-7').toISO())

  const refreshView = () => {
    const { start, end } = getDateRange(isWeeklyView, dateOfInterest)
    dispatch(fetchHFIStations())
    dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))
  }

  const updateDate = () => {
    if (previouslySelectedDateOfInterest !== dateOfInterest) {
      refreshView()
      setPreviouslySelectedDateOfInterest(dateOfInterest)
    }
  }

  const openAboutModal = () => {
    setModalOpen(true)
  }

  useEffect(() => {
    refreshView()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    refreshView()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isWeeklyView])

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

          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles
              isWeeklyView={isWeeklyView}
              toggleTableView={toggleTableView}
            />
          </FormControl>
          <FormControl className={classes.positionStyler}>
            <Button onClick={openAboutModal}>
              <InfoOutlinedIcon className={classes.infoIcon}></InfoOutlinedIcon>
              <p className={classes.aboutButtonText}>About this data</p>
            </Button>
          </FormControl>
          <AboutDataModal
            modalOpen={modalOpen}
            setModalOpen={setModalOpen}
          ></AboutDataModal>
          <ViewSwitcher
            isWeeklyView={isWeeklyView}
            fireCentres={fireCentres}
            dailies={dailies}
            dateOfInterest={dateOfInterest}
          />
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
