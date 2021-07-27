import { Checkbox } from '@material-ui/core'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import React from 'react'

export const buildSelectCheckboxCell = (
  props: FBCInputGridProps,
  rowId: number
): JSX.Element => {
  const selectedSet = new Set(props.selected)
  return (
    <Checkbox
      color="primary"
      checked={selectedSet.has(rowId)}
      onClick={() => {
        if (selectedSet.has(rowId)) {
          // Checked, toggle check off
          selectedSet.delete(rowId)
        } else {
          // Unchecked, toggle check on
          selectedSet.add(rowId)
        }
        props.updateSelected(Array.from(selectedSet))
      }}
    />
  )
}
