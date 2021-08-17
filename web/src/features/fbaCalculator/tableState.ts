import { GridRowId } from '@material-ui/data-grid'
import {
  FBAInputRow,
  GridMenuOption
} from 'features/fbaCalculator/components/FBAInputGrid'
import { find } from 'lodash'

export const updateFBARow = (
  inputRows: FBAInputRow[],
  updateRow: (id: GridRowId, updatedRow: FBAInputRow, dispatchUpdate: boolean) => void,
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
  const rowToUpdate = find(inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    updateRow(rowId, updatedRow, dispatchRequest)
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
