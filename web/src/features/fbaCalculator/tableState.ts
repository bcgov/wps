import { GridMenuOption } from 'features/fbaCalculator/components/FBAInputGrid'
import { FBCTableRow } from 'features/fbaCalculator/RowManager'
import { find } from 'lodash'

export const updateFBARow = (
  inputRows: FBCTableRow[],
  updateRow: (id: number, updatedRow: FBCTableRow, dispatchUpdate: boolean) => void,
  rowId: number,
  field: string,
  // eslint-disable-next-line
  value: any,
  updatedRowBuilder: (
    rowToUpdate: FBCTableRow,
    field: string,
    value: GridMenuOption | number
  ) => FBCTableRow,
  dispatchRequest = true
): void => {
  const rowToUpdate = find(inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    updateRow(rowId, updatedRow, dispatchRequest)
  }
}

export const buildUpdatedOptionRow = (
  rowToUpdate: FBCTableRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBCTableRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCTableRow]: value as GridMenuOption
    }
  }
}

// eslint-disable-next-line
export const buildUpdatedNumberRow = (
  rowToUpdate: FBCTableRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBCTableRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCTableRow]: parseFloat(value)
    }
  }
}
