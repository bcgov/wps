import { Checkbox } from '@material-ui/core'
import React from 'react'

interface SelectionCellProps {
  selected: number[]
  updateSelected: (newSelected: number[]) => void
  disabled: boolean
  rowId: number
}

const SelectionCell = (props: SelectionCellProps) => {
  const selectedSet = new Set(props.selected)
  return (
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
  )
}

export default React.memo(SelectionCell)
