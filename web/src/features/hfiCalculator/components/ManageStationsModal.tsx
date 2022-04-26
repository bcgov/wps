import React from 'react'
import { Dialog, DialogContent, IconButton, Paper, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { Button } from '@mui/material'

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

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
  addStation: {
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
      >
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>

          <DialogContent>
            <Typography variant="h5" align="center">
              Manage Weather Stations
            </Typography>
            <Button
              variant="text"
              color="primary"
              className={classes.addStation}
              onClick={() => {
                /** no op */
              }}
              data-testid={'add-station-button'}
            >
              <AddCircleOutlineIcon />
              Add Station
            </Button>
          </DialogContent>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(ManageStationsModal)
