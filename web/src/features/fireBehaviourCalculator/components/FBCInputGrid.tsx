import {
  DataGrid,
  GridEditCellValueParams,
  GridRowId,
  GridToolbarColumnsButton,
  GridToolbarContainer,
  GridToolbarDensitySelector,
  GridToolbarExport,
  GridToolbarFilterButton
} from '@material-ui/data-grid'
import _ from 'lodash'
import React from 'react'
export interface FBCInputGridProps {
  testId?: string
  stationMenuOptions: GridMenuOption[]
  fuelTypeMenuOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: GridRowId, updatedRow: FBCInputRow) => void
}

export interface GridMenuOption {
  label: string
  value: string | number
}

export interface FBCInputRow {
  id: number
  weatherStation: string
  fuelType: string
  grassCure: number
}

const buildFBCGridToolbar = () => {
  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <GridToolbarDensitySelector />
      <GridToolbarExport />
      {/* TODO move add station button here */}
    </GridToolbarContainer>
  )
}

const FBCInputGrid = (props: FBCInputGridProps) => {
  const updateCellValue = (params: GridEditCellValueParams) => {
    const rowToUpdate = _.find(props.rows, ['id', params.id])
    if (rowToUpdate) {
      const updatedRow = {
        ...rowToUpdate,
        ...{
          [params.field as keyof FBCInputRow]: params.value
        }
      }
      props.updateRow(params.id, updatedRow)
    }
  }

  return (
    <div style={{ display: 'flex', height: 300, width: 800 }}>
      <div style={{ flexGrow: 1 }}>
        <DataGrid
          components={{
            Toolbar: buildFBCGridToolbar
          }}
          hideFooter={true}
          rowHeight={30}
          columns={[
            {
              field: 'weatherStation',
              headerName: 'Weather Station',
              flex: 1,
              type: 'singleSelect',
              editable: true,
              valueOptions: props.stationMenuOptions
            },
            {
              field: 'fuelType',
              flex: 1,
              headerName: 'Fuel Type',
              type: 'singleSelect',
              editable: true,
              valueOptions: props.fuelTypeMenuOptions
            },
            {
              field: 'grassCure',
              headerName: 'Grass Cure %',
              flex: 0.7,
              type: 'number',
              editable: true
            }
          ]}
          rows={props.rows}
          onCellValueChange={updateCellValue}
        />
      </div>
    </div>
  )
}

export default React.memo(FBCInputGrid)
