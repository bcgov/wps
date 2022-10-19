import { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { find } from 'lodash'

export const updateFBARow = (
  inputRows: FBATableRow[],
  updateRow: (id: number, updatedRow: FBATableRow, dispatchUpdate: boolean) => void,
  rowId: number,
  field: string,
  // eslint-disable-next-line
  value: any,
  updatedRowBuilder: (rowToUpdate: FBATableRow, field: string, value: GridMenuOption | number) => FBATableRow,
  dispatchRequest = true
): void => {
  const rowToUpdate = find(inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    updateRow(rowId, updatedRow, dispatchRequest)
  }
}

export const buildUpdatedOptionRow = (
  rowToUpdate: FBATableRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBATableRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBATableRow]: value as GridMenuOption
    }
  }
}

// eslint-disable-next-line
export const buildUpdatedNumberRow = (
  rowToUpdate: FBATableRow,
  field: string,
  // eslint-disable-next-line
  value: any
): FBATableRow => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBATableRow]: parseFloat(value)
    }
  }
}
