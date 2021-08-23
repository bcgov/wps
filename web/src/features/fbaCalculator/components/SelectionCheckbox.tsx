import { Checkbox } from '@material-ui/core'
import React from 'react'

interface SelectionCheckboxProps {
  selected: number[]
  updateSelected: (newSelected: number[]) => void
  rowId: number
}

const SelectionCheckbox = (props: SelectionCheckboxProps) => {
  const selectedSet = new Set(props.selected)
  return (
    <Checkbox
      data-testid={`selection-checkbox-fba`}
      color="primary"
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

export default React.memo(SelectionCheckbox)
