import { Checkbox, makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

interface SelectionCellProps {
  selected: number[]
  updateSelected: (newSelected: number[]) => void
  disabled: boolean
  rowId: number
}

const useStyles = makeStyles(theme => ({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px',
    left: 0,
    position: 'sticky',
    zIndex: theme.zIndex.appBar + 1,
    backgroundColor: '#FFFFFF'
  }
}))

const SelectionCell = (props: SelectionCellProps) => {
  const classes = useStyles()

  const selectedSet = new Set(props.selected)
  return (
    <TableCell className={classes.dataRow}>
      <Checkbox
        data-testid={`selection-checkbox-fba`}
        color="primary"
        disabled={props.disabled}
        checked={selectedSet.has(props.rowId)}
        onClick={() => {
          if (selectedSet.has(props.rowId)) {
            // Checked, toggle check off
            selectedSet.delete(props.rowId)
          } else {
            // Unchecked, toggle check on
            selectedSet.add(props.rowId)
          }
          props.updateSelected(Array.from(selectedSet))
        }}
      />
    </TableCell>
  )
}

export default React.memo(SelectionCell)
