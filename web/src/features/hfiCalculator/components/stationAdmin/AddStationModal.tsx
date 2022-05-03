import React, { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  IconButton,
  Paper,
  Typography,
  Button
} from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import NewStationForm from 'features/hfiCalculator/components/stationAdmin/NewStationForm'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations, selectHFICalculatorState } from 'app/rootReducer'
import {
  fetchAddStation,
  setStationAdded
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import { FuelType } from 'api/hfiCalculatorAPI'
import { isUndefined } from 'lodash'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'

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
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'xl'
  },
  closeIcon: {
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

export const AddStationModal = (props: AddStationModalProps): JSX.Element => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  const { fuelTypes, selectedFireCentre, stationAdded } = useSelector(
    selectHFICalculatorState
  )
  const { stations: wfwxStations } = useSelector(selectFireWeatherStations)

  const newEmptyStation: AdminStation = { dirty: false }
  const [newStation, setNewStation] = useState<AdminStation>(newEmptyStation)
  const [invalid, setInvalid] = useState<boolean>(false)
  const planning_areas: BasicPlanningArea[] = selectedFireCentre
    ? selectedFireCentre.planning_areas.map(planningArea => ({
        id: planningArea.id,
        name: planningArea.name
      }))
    : []
  const stations: BasicWFWXStation[] = wfwxStations.map(station => ({
    wfwx_station_uuid: station.properties.name,
    code: station.properties.code,
    name: station.properties.name
  }))

  useEffect(() => {
    if (!isUndefined(selectedFireCentre)) {
      dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleClose = () => {
    props.setModalOpen(false)
    setNewStation(newEmptyStation)
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
      <Dialog
        fullWidth
        maxWidth="md"
        open={props.modalOpen}
        onClose={handleClose}
        data-testid="manage-stations-modal"
      >
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>

          <DialogContent>
            <Typography variant="h5" align="center">
              Add New Weather Station
            </Typography>
            <Typography variant="body1" align="center">
              New weather station will be included in the default list moving forward
            </Typography>
            <NewStationForm
              newStation={newStation}
              setNewStation={setNewStation}
              invalid={invalid}
              setInvalid={setInvalid}
              addStationOptions={{ planning_areas, stations, fuel_types: fuelTypes }}
            />
          </DialogContent>
          <SaveNewStationButton
            newStation={newStation}
            invalidNewStation={invalid}
            handleSave={handleSave}
          />
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
