import React, { useState, useEffect } from 'react'
import { Button, Container, ErrorBoundary, GeneralHeader, PageTitle } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  fetchHFIDailies,
  FireStarts,
  setPrepDays,
  setSelectedPrepDate,
  setSelectedSelectedStationCodes,
  setFireStarts,
  setSelectedFireCentre
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIDailies,
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import { CircularProgress, FormControl, makeStyles, Tooltip } from '@material-ui/core'
import {
  FileCopyOutlined,
  CheckOutlined,
  InfoOutlined,
  HelpOutlineOutlined
} from '@material-ui/icons'
import { getDateRange, getPrepWeeklyDateRange, pstFormatter } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { AboutDataModal } from 'features/hfiCalculator/components/AboutDataModal'
import { HFITableCSVFormatter } from 'features/hfiCalculator/HFITableCSVFormatter'
import { PST_UTC_OFFSET } from 'utils/constants'
import PrepDaysDropdown from 'features/hfiCalculator/components/PrepDaysDropdown'
import DatePicker from 'components/DatePicker'
import { FireCentre } from 'api/hfiCalcAPI'
import { isUndefined, union } from 'lodash'
import FireCentreDropdown from 'features/hfiCalculator/components/FireCentreDropdown'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  helpIcon: {
    fill: theme.palette.primary.main
  },
  copyToClipboardInfoIcon: {
    marginLeft: '3px'
  },
  clipboardIcon: {
    marginRight: '3px'
  },
  aboutButtonText: {
    color: theme.palette.primary.main,
    textDecoration: 'underline',
    fontWeight: 'bold'
  },
  positionStyler: {
    position: 'absolute',
    right: '20px'
  },
  prepDays: {
    margin: theme.spacing(1),
    minWidth: 100
  }
}))

const clipboardCopySuccessDuration = 2000 // milliseconds

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading } = useSelector(selectHFIDailies)
  const { fireCentres } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const {
    numPrepDays,
    selectedStationCodes: selected,
    planningAreaHFIResults,
    selectedPrepDate,
    selectedFireCentre
  } = useSelector(selectHFICalculatorState)

  const [isWeeklyView, setIsWeeklyView] = useState<boolean>(selectedPrepDate == '')
  const setNumPrepDays = (numDays: number) => {
    // if the number of prep days change, we need to unset the selected prep day - it
    // could be that the selected prep day no longer falls into the prep period.
    dispatch(setSelectedPrepDate(''))
    dispatch(setPrepDays(numDays))
  }

  const setSelected = (newSelected: number[]) => {
    dispatch(setSelectedSelectedStationCodes(newSelected))
  }

  const setNewFireStarts = (
    areaName: string,
    dayOffset: number,
    newFireStarts: FireStarts
  ) => {
    dispatch(setFireStarts({ areaName, dayOffset, newFireStarts }))
  }

  const [modalOpen, setModalOpen] = useState<boolean>(false)

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )
  const [isCopied, setIsCopied] = useState(false)

  const getDailies = (start: DateTime, end: DateTime) => {
    dispatch(
      fetchHFIDailies(
        selectedFireCentre,
        getAllPlanningWeatherStationCodesFromFireCentre(selectedFireCentre),
        selected,
        start.toUTC().valueOf(),
        end.toUTC().valueOf()
      )
    )
  }

  useEffect(() => {
    setSelected(union(dailies.map(daily => daily.code)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dailies])

  useEffect(() => {
    const { start, end } = getDateRange(isWeeklyView, dateOfInterest)
    getDailies(start, end)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fireCentres])

  const updateDate = (newDate: string) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
      const { start, end } = getDateRange(true, newDate)
      dispatch(setSelectedPrepDate(''))
      getDailies(start, end)
    }
  }

  const openAboutModal = () => {
    setModalOpen(true)
  }

  const getAllPlanningWeatherStationCodesFromFireCentre = (
    centre: FireCentre | undefined
  ): number[] => {
    if (isUndefined(centre)) {
      return []
    }
    return Object.values(centre?.planning_areas).flatMap(area =>
      Object.values(area.stations).map(station => station.code)
    )
  }

  const copyTable = () => {
    if (!isUndefined(selectedFireCentre)) {
      let csvString = ''
      if (isWeeklyView) {
        const { start } = getPrepWeeklyDateRange(dateOfInterest)
        csvString += HFITableCSVFormatter.exportWeeklyRowsAsStrings(
          numPrepDays,
          start,
          selectedFireCentre,
          planningAreaHFIResults
        )
      } else {
        csvString += HFITableCSVFormatter.exportDailyRowsAsStrings(
          dateOfInterest,
          selectedFireCentre,
          planningAreaHFIResults
        )
      }
      navigator.clipboard.writeText(csvString)
      setIsCopied(true)
    } else {
      setIsCopied(false)
    }
  }

  const setSelectedFireCentreFromLocalStorage = () => {
    const findCentre = (name: string | null): FireCentre | undefined => {
      const fireCentresArray = Object.values(fireCentres)
      return fireCentresArray.find(centre => centre.name == name)
    }
    const storedFireCentre = findCentre(
      localStorage.getItem('hfiCalcPreferredFireCentre')
    )
    if (!isUndefined(storedFireCentre) && storedFireCentre !== selectedFireCentre) {
      dispatch(setSelectedFireCentre(storedFireCentre))
    }
  }

  useEffect(() => {
    /**  this logic is copied from
     https://github.com/danoc/react-use-clipboard/blob/master/src/index.tsx 
     (the react-use-clipboard package was too restrictive for our needs, but the logic for
      having a timeout on the copy success message is helpful for us)
    */
    if (isCopied) {
      const id = setTimeout(() => {
        setIsCopied(false)
      }, clipboardCopySuccessDuration)

      return () => {
        clearTimeout(id)
      }
    }
  }, [isCopied])

  useEffect(() => {
    dispatch(fetchHFIStations())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (
      selectedFireCentre &&
      selectedFireCentre?.name !== localStorage.getItem('hfiCalcPreferredFireCentre')
    ) {
      localStorage.setItem('hfiCalcPreferredFireCentre', selectedFireCentre?.name)
    }
    const { start, end } = getDateRange(true, dateOfInterest)
    if (!isUndefined(selectedFireCentre)) {
      dispatch(
        fetchHFIDailies(
          selectedFireCentre,
          getAllPlanningWeatherStationCodesFromFireCentre(selectedFireCentre),
          selected,
          start.toUTC().valueOf(),
          end.toUTC().valueOf()
        )
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireCentre])

  useEffect(() => {
    if (Object.keys(fireCentres).length > 0) {
      setSelectedFireCentreFromLocalStorage()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fireCentres])

  useEffect(() => {
    setIsWeeklyView(selectedPrepDate == '')
  }, [selectedPrepDate])

  useEffect(() => {
    setSelected(union(dailies.map(daily => daily.code)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dailies])

  const selectNewFireCentre = (newSelection: FireCentre | undefined) => {
    dispatch(setSelectedFireCentre(newSelection))
  }

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
          <FormControl className={classes.prepDays}>
            <PrepDaysDropdown days={numPrepDays} setNumPrepDays={setNumPrepDays} />
          </FormControl>
          <FormControl className={classes.formControl}>
            <FireCentreDropdown
              fireCentres={fireCentres}
              selectedValue={
                isUndefined(selectedFireCentre)
                  ? null
                  : { name: selectedFireCentre?.name }
              }
              onChange={selectNewFireCentre}
            />
          </FormControl>

          <FormControl className={classes.formControl}>
            <DatePicker date={dateOfInterest} updateDate={updateDate} />
          </FormControl>
          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles dateOfInterest={dateOfInterest} />
          </FormControl>
          <FormControl className={classes.formControl}>
            {isCopied ? (
              <Button>
                <CheckOutlined />
                Copied!
              </Button>
            ) : (
              <Button onClick={copyTable}>
                <FileCopyOutlined className={classes.clipboardIcon} />
                Copy Data to Clipboard
                <Tooltip
                  title={
                    'You can paste all table data in Excel. To format: go to the Data tab, use Text to Columns > Delimited > Comma.'
                  }
                >
                  <InfoOutlined className={classes.copyToClipboardInfoIcon} />
                </Tooltip>
              </Button>
            )}
          </FormControl>

          <FormControl className={classes.positionStyler}>
            <Button onClick={openAboutModal}>
              <HelpOutlineOutlined className={classes.helpIcon}></HelpOutlineOutlined>
              <p className={classes.aboutButtonText}>About this data</p>
            </Button>
          </FormControl>
          <AboutDataModal
            modalOpen={modalOpen}
            setModalOpen={setModalOpen}
          ></AboutDataModal>

          <ErrorBoundary>
            <ViewSwitcher
              selectedFireCentre={selectedFireCentre}
              dailies={dailies}
              dateOfInterest={dateOfInterest}
              setSelected={setSelected}
              setNewFireStarts={setNewFireStarts}
              selectedPrepDay={selectedPrepDate}
            />
          </ErrorBoundary>
        </Container>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
