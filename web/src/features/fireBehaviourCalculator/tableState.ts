import {
  FBCInputGridProps,
  FBCInputRow,
  GridMenuOption
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import { find } from 'lodash'

export const updateFBCRow = (
  props: Pick<FBCInputGridProps, 'inputRows' | 'updateRow'>,
  rowId: number,
  field: string,
  // eslint-disable-next-line
  value: any,
  updatedRowBuilder: (
    rowToUpdate: FBCInputRow,
    field: string,
    value: GridMenuOption | number
  ) => FBCInputRow
): void => {
  const rowToUpdate = find(props.inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    props.updateRow(rowId, updatedRow)
  }
}

export const buildUpdatedOptionRow = (
  rowToUpdate: FBCInputRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBCInputRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: (value as GridMenuOption)?.value
    }
  }
}

// eslint-disable-next-line
export const buildUpdatedNumberRow = (
  rowToUpdate: FBCInputRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBCInputRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: parseInt(value)
    }
  }
}
