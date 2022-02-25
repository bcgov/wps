import React, { useState, useEffect } from 'react'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStarts,
  setSelectedFireCentre,
  fetchHFIResult,
  setSelectedPrepDate
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import { CircularProgress, FormControl, makeStyles, Tooltip } from '@material-ui/core'
import { FileCopyOutlined, CheckOutlined, InfoOutlined } from '@material-ui/icons'
import { DateRange } from 'materialui-daterange-picker'
import { getDateRange, getPrepWeeklyDateRange, pstFormatter } from 'utils/date'
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
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const { numPrepDays, selectedPrepDate, result, selectedFireCentre, loading } =
    useSelector(selectHFICalculatorState)

  const setSelected = (newSelected: number[]) => {
    if (!isUndefined(result)) {
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: newSelected,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          selected_prep_date: result.selected_prep_date.toJSDate(),
          date_range: result.date_range
        })
      )
    }
  }

  const setNewFireStarts = (
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStarts
  ) => {
    if (!isUndefined(result)) {
      const newPlanningAreaFireStarts = cloneDeep(result.planning_area_fire_starts)
      newPlanningAreaFireStarts[areaId][dayOffset] = { ...newFireStarts }
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: newPlanningAreaFireStarts,
          selected_prep_date: result.selected_prep_date.toJSDate(),
          date_range: result.date_range
        })
      )
    }
  }

  const [prepDateRange, setPrepDateRange] = useState<DateRange>()

  const updatePrepDateRange = (newDateRange: DateRange) => {
    if (
      newDateRange !== prepDateRange &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(result)
    ) {
      setPrepDateRange(newDateRange)
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          selected_prep_date: result.selected_prep_date.toJSDate(),
          date_range: newDateRange
        })
      )
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
    if (!isUndefined(selectedFireCentre)) {
      const stationCodes = selectedFireCentre.planning_areas.flatMap(area =>
        area.stations.map(station => station.code)
      )
      setSelected(union(stationCodes))

      dispatch(
        fetchHFIResult({
          date_range: result ? result.date_range : prepDateRange,
          selected_station_code_ids: stationCodes,
          selected_fire_center_id: selectedFireCentre.id,
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
        dateRange={prepDateRange}
        setDateRange={updatePrepDateRange}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      {loading || stationDataLoading || isUndefined(result) ? (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      ) : (
        <React.Fragment>
          <Container maxWidth={'xl'}>
            {!isNull(fireCentresError) && (
              <HFIErrorAlert hfiDailiesError={null} fireCentresError={fireCentresError} />
            )}
            <LastUpdatedHeader
              dailies={result?.planning_area_hfi_results.flatMap(areaResult =>
                areaResult.daily_results.flatMap(dailyResult =>
                  dailyResult.dailies.map(validatedDaily => validatedDaily.daily)
                )
              )}
            />

            <FormControl className={classes.formControl}>
              <ViewSwitcherToggles dateOfInterest={dateOfInterest} />
            </FormControl>

            <ErrorBoundary>
              <ViewSwitcher
                selectedFireCentre={selectedFireCentre}
                dateOfInterest={dateOfInterest}
                result={result}
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
