import React, { useState } from 'react'
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  IconButton,
  Paper,
  Typography
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core'
import { Clear } from '@material-ui/icons'
import SelectionCell from 'features/fbaCalculator/components/SelectionCell'

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  columns: string[]
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxHeight: '800px',
    maxWidth: '600px'
  }
}))

export const FilterColumnsModal = (props: ModalProps) => {
  const classes = useStyles()

  // set all columns as selected by default
  const [selected, setSelected] = useState<number[]>(
    Array.from(Array(props.columns.length).keys())
  )

  const handleOpen = () => {
    props.setModalOpen(true)
  }

  const handleClose = () => {
    props.setModalOpen(false)
  }

  return (
    <Dialog className={classes.modalWindow} open={props.modalOpen} onClose={handleClose}>
      <Paper>
        <div>
          <Typography variant="h5" component="h5">
            Filter Table by Columns
          </Typography>
          <IconButton onClick={handleClose}>
            <Clear />
          </IconButton>
        </div>
        <DialogContent>
          {props.columns.map((column, index) => {
            return (
              <div key={column}>
                <SelectionCell
                  selected={selected}
                  updateSelected={(newSelected: number[]) => setSelected(newSelected)}
                  disabled={false}
                  rowId={index}
                />
                <p>{column}</p>
              </div>
            )
          })}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary" variant="contained">
            Save changes
          </Button>
          <Button onClick={handleClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Paper>
    </Dialog>
  )
}

export default React.memo(FilterColumnsModal)
