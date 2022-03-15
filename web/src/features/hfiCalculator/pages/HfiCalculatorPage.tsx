import React, { useState, useEffect } from 'react'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStarts,
  setSelectedFireCentre,
  fetchHFIResult,
  fetchLoadHFIResult,
  setSelectedPrepDate,
  setSaved,
  fetchPDFDownload
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import { DateTime } from 'luxon'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import {
  CircularProgress,
  FormControl,
  makeStyles,
  Table,
  TableBody
} from '@material-ui/core'
import { getDateRange, pstFormatter } from 'utils/date'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import SaveButton from 'features/hfiCalculator/components/SaveButton'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { PST_UTC_OFFSET, PST_ISO_TIMEZONE } from 'utils/constants'
import PrepDaysDropdown from 'features/hfiCalculator/components/PrepDaysDropdown'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { cloneDeep, isNull, isUndefined } from 'lodash'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'

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
  },
  saveButton: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const { numPrepDays, selectedPrepDate, result, selectedFireCentre, loading, saved } =
    useSelector(selectHFICalculatorState)

  const setNumPrepDays = (numDays: number) => {
    // if the number of prep days change, we need to unset the selected prep day - it
    // could be that the selected prep day no longer falls into the prep period.
    if (!isUndefined(result)) {
      dispatch(setSaved(false))
      const newEndDate = DateTime.fromISO(result.start_date + PST_ISO_TIMEZONE).plus({
        days: numDays
      })

      const prepDateObj = DateTime.fromISO(selectedPrepDate)
      const startDate = DateTime.fromISO(result.start_date + PST_ISO_TIMEZONE)
      if (prepDateObj < startDate || prepDateObj > newEndDate) {
        // we only need to change the selected prep date, the change in prep days would result in the
        // selected date being invalid.
        dispatch(setSelectedPrepDate(''))
      }

      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          start_date: result.start_date,
          end_date: newEndDate.toISO().split('T')[0]
        })
      )
    }
  }

  const setSelected = (newSelected: number[]) => {
    if (!isUndefined(result)) {
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: newSelected,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          start_date: result.start_date,
          end_date: result.end_date
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
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: newPlanningAreaFireStarts,
          start_date: result.start_date,
          end_date: result.end_date
        })
      )
    }
  }

  const getBrowserCurrentDate = () => {
    return pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  }

  // the DatePicker component requires dateOfInterest to be in string format
  const [dateOfInterest, setDateOfInterest] = useState(getBrowserCurrentDate())

  const updateDate = (newDate: string) => {
    if (
      newDate !== dateOfInterest &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(result)
    ) {
      setDateOfInterest(newDate)
      const { start, end } = getDateRange(true, newDate)
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          start_date: start.toISODate(),
          end_date: end.toISODate()
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
      dispatch(fetchLoadHFIResult({ selected_fire_center_id: selectedFireCentre.id }))
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
    if (!isUndefined(result)) {
      // TODO: Ooooh no! HACK! If you be doing string stuff like this, things will break!
      setDateOfInterest(result.start_date + 'T00:00:00.000-08:00')
    }
  }, [result, result?.start_date])

  const selectNewFireCentre = (newSelection: FireCentre | undefined) => {
    dispatch(setSelectedFireCentre(newSelection))
  }

  const handleSaveClicked = () => {
    if (!isUndefined(result)) {
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          start_date: result.start_date,
          end_date: result.end_date,
          persist_request: true
        })
      )
    }
  }

  const handleDownloadClicked = () => {
    if (!isUndefined(result)) {
      dispatch(
        fetchPDFDownload({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          start_date: result.start_date,
          end_date: result.end_date
        })
      )
    }
  }

  const buildHFIContent = () => {
    if (isUndefined(selectedFireCentre)) {
      return (
        <Table>
          <TableBody>
            <EmptyFireCentreRow />
          </TableBody>
        </Table>
      )
    } else if (loading || stationDataLoading || isUndefined(result)) {
      return (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      )
    }
    return (
      <React.Fragment>
        <Container maxWidth={'xl'}>
          {!isNull(fireCentresError) && (
            <HFIErrorAlert hfiDailiesError={null} fireCentresError={fireCentresError} />
          )}
          <FormControl className={classes.prepDays}>
            <PrepDaysDropdown days={numPrepDays} setNumPrepDays={setNumPrepDays} />
          </FormControl>

          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles dateOfInterest={dateOfInterest} />
          </FormControl>

          <FormControl className={classes.saveButton}>
            <DownloadPDFButton onClick={handleDownloadClicked} />
          </FormControl>

          <FormControl className={classes.saveButton}>
            <SaveButton saved={saved} onClick={handleSaveClicked} />
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
    )
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
        result={result}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      {buildHFIContent()}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
