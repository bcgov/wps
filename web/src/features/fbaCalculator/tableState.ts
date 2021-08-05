import {
  FBAInputGridProps,
  FBAInputRow,
  GridMenuOption
} from 'features/fbaCalculator/components/FBAInputGrid'
import { find } from 'lodash'

export const updateFBARow = (
  props: Pick<FBAInputGridProps, 'inputRows' | 'updateRow'>,
  rowId: number,
  field: string,
  // eslint-disable-next-line
  value: any,
  updatedRowBuilder: (
    rowToUpdate: FBAInputRow,
    field: string,
    value: GridMenuOption | number
  ) => FBAInputRow,
  dispatchRequest = true
): void => {
  const rowToUpdate = find(props.inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    props.updateRow(rowId, updatedRow, dispatchRequest)
  }
}

export const buildUpdatedOptionRow = (
  rowToUpdate: FBAInputRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBAInputRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBAInputRow]: (value as GridMenuOption)?.value
    }
  }
}

// eslint-disable-next-line
export const buildUpdatedNumberRow = (
  rowToUpdate: FBAInputRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBAInputRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBAInputRow]: parseFloat(value)
    }
  }
}
