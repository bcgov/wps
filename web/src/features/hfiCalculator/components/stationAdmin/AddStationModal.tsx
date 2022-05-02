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
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'
import {
  fetchAddStation,
  fetchAddStationOptions
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import { BasicPlanningArea, BasicWFWXStation, FuelType } from 'api/hfiCalculatorAPI'
import { isUndefined } from 'lodash'

export interface AdminStation {
  dirty: boolean
  planningArea?: BasicPlanningArea
  station?: BasicWFWXStation
  fuelType?: FuelType
}

export interface ValidAdminStation {
  planningArea: BasicPlanningArea
  station: BasicWFWXStation
  fuelType: FuelType
}
export interface AddStationModalProps {
  testId?: string
  fireCentreId: number
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

  const { changeSaved, addStationOptions } = useSelector(selectHFICalculatorState)

  const newEmptyStation: AdminStation = { dirty: false }
  const [newStation, setNewStation] = useState<AdminStation>(newEmptyStation)
  const [invalid, setInvalid] = useState<boolean>(false)

  useEffect(() => {
    dispatch(fetchAddStationOptions(props.fireCentreId))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleClose = () => {
    props.setModalOpen(false)
    setNewStation(newEmptyStation)
  }

  const handleSave = () => {
    if (
      !isUndefined(newStation.planningArea) &&
      !isUndefined(newStation.station) &&
      !isUndefined(newStation.fuelType)
    ) {
      dispatch(
        fetchAddStation(props.fireCentreId, {
          planningArea: newStation.planningArea,
          station: newStation.station,
          fuelType: newStation.fuelType
        })
      )
    }
  }

  const buildSuccessNotification = () => {
    if (changeSaved) {
      return <HFISuccessAlert message="Changes saved!" />
    }
    return <React.Fragment></React.Fragment>
  }

  return (
    <React.Fragment>
      {buildSuccessNotification()}

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
              addStationOptions={addStationOptions}
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
