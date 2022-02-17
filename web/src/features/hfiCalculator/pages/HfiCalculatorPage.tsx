import React, { useState, useEffect } from 'react'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  fetchHFIDailies,
  FireStarts,
  setPrepDays,
  setSelectedPrepDate,
  setSelectedSelectedStationCodes,
  setSelectedFireCentre,
  fetchHFIResult
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIDailies,
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import { CircularProgress, FormControl, makeStyles } from '@material-ui/core'
import { getDateRange, pstFormatter } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import LastUpdatedHeader from 'features/hfiCalculator/components/LastUpdatedHeader'
import { formControlStyles, theme } from 'app/theme'
import { PST_UTC_OFFSET } from 'utils/constants'
import PrepDaysDropdown from 'features/hfiCalculator/components/PrepDaysDropdown'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { cloneDeep, isNull, isUndefined, union } from 'lodash'
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

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { dailies, loading, error: hfiDailiesError } = useSelector(selectHFIDailies)
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const {
    numPrepDays,
    selectedStationCodes: selected,
    selectedPrepDate,
    result,
    selectedFireCentre
  } = useSelector(selectHFICalculatorState)

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
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStarts
  ) => {
    if (!isUndefined(result)) {
      const copy = cloneDeep(result.planning_area_fire_starts)
      copy[areaId][dayOffset] = { ...newFireStarts }
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: copy,
          selected_prep_date: result.selected_prep_date,
          start_date: result.start_date.toISO(),
          end_date: result.end_date.toISO()
        })
      )
    }
  }

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(
    pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  )

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

  const updateDate = (newDate: string) => {
    if (
      newDate !== dateOfInterest &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(result)
    ) {
      setDateOfInterest(newDate)
      const { start, end } = getDateRange(true, newDate)
      dispatch(setSelectedPrepDate(''))
      getDailies(start, end)
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          selected_prep_date: result.selected_prep_date,
          start_date: start.toISO(),
          end_date: end.toISO()
        })
      )
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
        fetchHFIResult({
          selected_station_code_ids: result
            ? result.selected_station_code_ids
            : Object.entries(selectedFireCentre.planning_areas).flatMap(
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                (a, _b) => a[1].stations[1].code
              ),
          selected_fire_center_id: result
            ? result.selected_fire_center_id
            : selectedFireCentre.id,
          planning_area_fire_starts: result ? result.planning_area_fire_starts : {}
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
