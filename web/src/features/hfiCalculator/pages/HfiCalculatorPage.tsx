import React, { useState, useEffect } from 'react'
import { Button, Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  fetchHFIDailies,
  FireStarts,
  setPrepDays,
  setSelectedPrepDate,
  setSelectedSelectedStationCodes,
  setFireStarts,
  setSelectedFireCentre,
  fetchHFIResults
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
import { FileCopyOutlined, CheckOutlined, InfoOutlined } from '@material-ui/icons'
import { getDateRange, getPrepWeeklyDateRange, pstFormatter } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import LastUpdatedHeader from 'features/hfiCalculator/components/LastUpdatedHeader'
import { formControlStyles, theme } from 'app/theme'
import { HFITableCSVFormatter } from 'features/hfiCalculator/HFITableCSVFormatter'
import { PST_UTC_OFFSET } from 'utils/constants'
import PrepDaysDropdown from 'features/hfiCalculator/components/PrepDaysDropdown'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { isNull, isUndefined, union } from 'lodash'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'

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
  const { dailies, loading, error: hfiDailiesError } = useSelector(selectHFIDailies)
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
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
    if (!isUndefined(selectedFireCentre)) {
      const { start, end } = getDateRange(isWeeklyView, dateOfInterest)
      getDailies(start, end)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireCentre])

  const updateDate = (newDate: string) => {
    if (newDate !== dateOfInterest && !isUndefined(selectedFireCentre)) {
      setDateOfInterest(newDate)
      const { start, end } = getDateRange(true, newDate)
      dispatch(setSelectedPrepDate(''))
      getDailies(start, end)
    }
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
      dispatch(
        fetchHFIResults({
          num_prep_days: numPrepDays,
          selected_prep_date: selectedPrepDate,
          start_time_stamp: start.toUTC().valueOf(),
          end_time_stamp: end.toUTC().valueOf(),
          selected_station_codes: selected,
          selected_fire_center: selectedFireCentre,
          planning_area_fire_starts: {}
        })
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
        title="HFI Calculator"
        productName="HFI Calculator"
      />
      <HFIPageSubHeader
        fireCentres={fireCentres}
        dateOfInterest={dateOfInterest}
        updateDate={updateDate}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      {loading || stationDataLoading ? (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      ) : (
        <React.Fragment>
          <Container maxWidth={'xl'}>
            {(!isNull(hfiDailiesError) || !isNull(fireCentresError)) && (
              <HFIErrorAlert
                hfiDailiesError={hfiDailiesError}
                fireCentresError={fireCentresError}
              />
            )}
            <LastUpdatedHeader dailies={dailies} />
            <FormControl className={classes.prepDays}>
              <PrepDaysDropdown days={numPrepDays} setNumPrepDays={setNumPrepDays} />
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
        </React.Fragment>
      )}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
