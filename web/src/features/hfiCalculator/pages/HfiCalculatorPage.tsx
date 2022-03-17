import React, { useState, useEffect } from 'react'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStarts,
  setSelectedFireCentre,
  fetchHFIResult,
  setSaved,
  fetchPDFDownload,
  PrepDateRange
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
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
import { pstFormatter } from 'utils/date'
import { DateRange } from 'materialui-daterange-picker'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import SaveButton from 'features/hfiCalculator/components/SaveButton'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { PST_UTC_OFFSET } from 'utils/constants'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { cloneDeep, isNull, isUndefined } from 'lodash'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import { DateTime } from 'luxon'
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
  const { selectedPrepDate, result, selectedFireCentre, loading, saved } = useSelector(
    selectHFICalculatorState
  )

  const setSelected = (newSelected: number[]) => {
    if (!isUndefined(result)) {
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: newSelected,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
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
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: newPlanningAreaFireStarts,
          date_range: result.date_range
        })
      )
    }
  }

  const getBrowserCurrentDate = () => {
    return pstFormatter(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  }
  const [prepDateRange, setPrepDateRange] = useState<PrepDateRange>()

  const updatePrepDateRange = (newDateRange: DateRange) => {
    if (
      // newDateRange !== prepDateRange &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(result)
    ) {
      setPrepDateRange({
        // This is so annoying that I have to do this to make the network call work
        start_date: newDateRange.startDate?.toISOString().split('T')[0],
        end_date: newDateRange.endDate?.toISOString().split('T')[0]
      })
      dispatch(setSaved(false))
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: result.planning_area_fire_starts,
          date_range: prepDateRange
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
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: stationCodes,
          selected_fire_center_id: selectedFireCentre.id,
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
    if (!isUndefined(result)) {
      setPrepDateRange(result.date_range)
    }
  }, [result, result?.date_range])

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
          date_range: result.date_range,
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
          date_range: result.date_range
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

          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles
              dateRange={prepDateRange}
              selectedPrepDate={selectedPrepDate}
            />
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
              result={result}
              dateRange={prepDateRange}
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
        dateRange={prepDateRange}
        setDateRange={updatePrepDateRange}
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
