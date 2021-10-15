import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  IconButton,
  Paper,
  makeStyles,
  Fab,
  Checkbox
} from '@material-ui/core'
import { Clear } from '@material-ui/icons'

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  columns: string[]
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  parentCallback: (selectedColumnsLabels: string[]) => void
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'md'
  },
  closeIcon: {
    position: 'absolute',
    right: '0px'
  },
  selectionBox: {
    height: '20px',
    boxSizing: 'border-box'
  }
}))

export const FilterColumnsModal = (props: ModalProps) => {
  const classes = useStyles()

  // set all columns as selected by default
  const [selected, setSelected] = useState(
    new Set(Array.from(Array(props.columns.length).keys()))
  )

  const handleClose = () => {
    props.setModalOpen(false)
  }

  const handleApplyAndClose = () => {
    const selectedColumnLabels = Array.from(selected)
      .sort((a, b) => a - b)
      .map(index => {
        return props.columns[index]
      })
    props.parentCallback(selectedColumnLabels)
    props.setModalOpen(false)
  }

  const toggleSelectedIndex = (index: number) => {
    if (!selected.has(index)) {
      // toggle index ON
      selected.add(index)
    } else if (selected.has(index)) {
      // toggle index OFF
      selected.delete(index)
    }
    setSelected(new Set(selected))
  }

  return (
    <Dialog
      fullWidth
      className={classes.modalWindow}
      open={props.modalOpen}
      onClose={handleClose}
    >
      <Paper>
        <DialogTitle>
          Show Columns
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <Clear />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {props.columns.map((column, index) => {
            return (
              <div key={column}>
                <Checkbox
                  checked={selected.has(index)}
                  color="primary"
                  onClick={() => {
                    toggleSelectedIndex(index)
                  }}
                  size="small"
                  data-testid={`filter-${column.replaceAll(' ', '-')}`}
                  // below is some jiggery-pokery to get checkboxes to squish closer together vertically
                  // https://stackoverflow.com/questions/64261614/how-to-decrease-vetical-distance-between-two-checkboxes-with-label
                  classes={{ root: classes.selectionBox }}
                />
                <a>{column}</a>
              </div>
            )
          })}
        </DialogContent>
        <DialogActions>
          <Fab
            color="primary"
            aria-label="apply"
            onClick={handleApplyAndClose}
            variant="extended"
            data-testId="apply-btn"
          >
            Apply
          </Fab>
          <Fab
            color="secondary"
            aria-label="cancel"
            onClick={handleClose}
            variant="extended"
          >
            Cancel
          </Fab>
        </DialogActions>
      </Paper>
    </Dialog>
  )
}

export default React.memo(FilterColumnsModal)
