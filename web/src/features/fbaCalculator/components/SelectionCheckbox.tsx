import { Checkbox } from '@material-ui/core'
import { FBAInputGridProps } from 'features/fbaCalculator/components/FBATable'
import React from 'react'

interface SelectionCheckboxProps {
  fbaInputGridProps: Pick<FBAInputGridProps, 'selected' | 'updateSelected'>
  rowId: number
}

const SelectionCheckbox = (props: SelectionCheckboxProps) => {
  const selectedSet = new Set(props.fbaInputGridProps.selected)
  return (
    <Checkbox
      data-testid={`selection-checkbox-${props.rowId}`}
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
        props.fbaInputGridProps.updateSelected(Array.from(selectedSet))
      }}
    />
  )
}

export default React.memo(SelectionCheckbox)
