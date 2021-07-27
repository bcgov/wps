import { Checkbox } from '@material-ui/core'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import React from 'react'

interface SelectionCheckboxProps {
  fbcInputGridProps: Pick<FBCInputGridProps, 'selected' | 'updateSelected'>
  rowId: number
}

const SelectionCheckbox = (props: SelectionCheckboxProps) => {
  const selectedSet = new Set(props.fbcInputGridProps.selected)
  return (
    <Checkbox
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
        props.fbcInputGridProps.updateSelected(Array.from(selectedSet))
      }}
    />
  )
}

export default React.memo(SelectionCheckbox)
