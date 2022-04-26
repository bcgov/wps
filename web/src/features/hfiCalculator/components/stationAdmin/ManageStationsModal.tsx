import React from 'react'
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
import AddStationButton from 'features/hfiCalculator/components/stationAdmin/AddStationButton'
import StationsList from 'features/hfiCalculator/components/stationAdmin/StationsList'

export interface ModalProps {
  testId?: string
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'lg'
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

export const ManageStationsModal = (props: ModalProps): JSX.Element => {
  const classes = useStyles()

  const handleClose = () => {
    props.setModalOpen(false)
  }

  return (
    <React.Fragment>
      <Dialog
        fullWidth
        className={classes.modalWindow}
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
              Manage Weather Stations
            </Typography>
            <AddStationButton />
            <StationsList />
          </DialogContent>
          <Button
            variant="contained"
            color="primary"
            className={classes.actionButton}
            onClick={() => {
              /** no op */
            }}
            data-testid={'cancel-hfi-admin-button'}
          >
            Save
          </Button>
          <Button
            variant="outlined"
            color="primary"
            className={classes.actionButton}
            onClick={handleClose}
            data-testid={'cancel-hfi-admin-button'}
          >
            Cancel
          </Button>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(ManageStationsModal)
