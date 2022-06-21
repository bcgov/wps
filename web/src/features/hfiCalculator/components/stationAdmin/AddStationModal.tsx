import React, { useEffect, useState } from 'react'
import { Dialog, DialogContent, IconButton, Paper, Typography, Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations, selectHFICalculatorState } from 'app/rootReducer'
import {
  fetchAddStation,
  setAddedStationFailed,
  setStationAdded,
  StationInfo
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { groupBy, isNull, isUndefined } from 'lodash'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import StationListAdmin from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { StationAdminRow } from 'features/hfiCalculator/stationAdmin/admin'
import { getSelectedFuelType } from 'features/hfiCalculator/util'

export interface AdminStation {
  dirty: boolean
  planningArea?: BasicPlanningArea
  station?: BasicWFWXStation
  fuelType?: FuelType
}

export interface BasicPlanningArea {
  id: number
  name: string
}
export interface BasicWFWXStation {
  code: number
  name: string
}

export interface AddStationOptions {
  planning_areas: BasicPlanningArea[]
  stations: BasicWFWXStation[]
  fuel_types: FuelType[]
}

export interface AddStationModalProps {
  testId?: string
  planningAreas?: PlanningArea[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'xl'
  },
  closeIcon: {
    padding: 5,
    position: 'absolute',
    right: '0px'
  },
  title: {
    textAlign: 'center'
  },
  actionButton: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

export const AddStationModal = ({
  modalOpen,
  setModalOpen,
  planningAreas,
  planningAreaStationInfo
}: AddStationModalProps): JSX.Element => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  const { fuelTypes, selectedFireCentre, stationAdded, stationAddedError } = useSelector(selectHFICalculatorState)
  const { stations: wfwxStations } = useSelector(selectFireWeatherStations)

  const newEmptyStation: AdminStation = { dirty: false }
  const [newStation, setNewStation] = useState<AdminStation>(newEmptyStation)
  const [invalid] = useState<boolean>(false)
  const planning_areas: BasicPlanningArea[] = selectedFireCentre
    ? selectedFireCentre.planning_areas.map(planningArea => ({
        id: planningArea.id,
        name: planningArea.name
      }))
    : []
  const stations: BasicWFWXStation[] = wfwxStations.map(station => ({
    code: station.properties.code,
    name: station.properties.name
  }))
  const adminRows: { [key: string]: StationAdminRow[] } = groupBy(
    planningAreas
      ? planningAreas
          .map(pa =>
            pa.stations.map(station => ({
              planningAreaId: pa.id,
              station: { code: station.code, name: station.station_props.name },
              fuelType: getSelectedFuelType(planningAreaStationInfo, pa.id, station.code, fuelTypes)
            }))
          )
          .flat()
      : [],
    'planningAreaId'
  )

  const [adminRowList, setAdminRows] = useState<{ [key: string]: StationAdminRow[] }>(adminRows)

  const handleAddStation = (planningAreaId: number, row: StationAdminRow) => {
    /**
     * TODO
     */
  }

  const handleEditStation = (planningAreaId: number, rowId: number, row: StationAdminRow) => {
    /**
     * TODO
     */
  }

  useEffect(() => {
    if (!isUndefined(selectedFireCentre)) {
      dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleClose = () => {
    setModalOpen(false)
    setNewStation(newEmptyStation)
    if (!isNull(stationAddedError)) {
      dispatch(setAddedStationFailed(null))
    }
  }

  useEffect(() => {
    handleClose()
    if (stationAdded) {
      dispatch(fetchHFIStations())
      dispatch(setStationAdded(false))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stationAdded])

  const handleSave = () => {
    if (
      !isUndefined(selectedFireCentre) &&
      !isUndefined(newStation.planningArea) &&
      !isUndefined(newStation.station) &&
      !isUndefined(newStation.fuelType)
    ) {
      dispatch(
        fetchAddStation(selectedFireCentre.id, {
          planningArea: newStation.planningArea,
          station: newStation.station,
          fuelType: newStation.fuelType
        })
      )
    }
  }

  return (
    <React.Fragment>
      <Dialog fullWidth maxWidth="md" open={modalOpen} onClose={handleClose} data-testid="manage-stations-modal">
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>
          <DialogContent>
            <Typography variant="h5" align="center">
              Manage Default Weather Stations and Fuels
            </Typography>
            <Typography variant="body1" align="center">
              Change the default wx and fuelds for all future prep
            </Typography>
            {/* <NewStationForm
              newStation={newStation}
              setNewStation={setNewStation}
              invalid={invalid}
              setInvalid={setInvalid}
              handleFormChange={handleFormChange}
              addStationOptions={{ planning_areas, stations, fuel_types: fuelTypes }}
              stationAddedError={stationAddedError}
            /> */}
          </DialogContent>
          {!isUndefined(planningAreas) && !isUndefined(wfwxStations) && (
            <StationListAdmin
              planningAreas={planningAreas}
              fuelTypes={fuelTypes}
              addStationOptions={{ planning_areas, stations, fuel_types: fuelTypes }}
              planningAreaStationInfo={planningAreaStationInfo}
            />
          )}
          <SaveNewStationButton newStation={newStation} invalidNewStation={invalid} handleSave={handleSave} />
          <Button
            variant="outlined"
            color="primary"
            className={classes.actionButton}
            onClick={handleClose}
            data-testid={'cancel-new-station-button'}
          >
            Cancel
          </Button>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(AddStationModal)
