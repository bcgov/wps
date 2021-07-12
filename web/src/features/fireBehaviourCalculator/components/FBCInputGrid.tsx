import {
  DataGrid,
  GridCellParams,
  GridEditCellValueParams,
  GridRowId,
  GridToolbarColumnsButton,
  GridToolbarContainer,
  GridToolbarDensitySelector,
  // GridToolbarExport,
  GridToolbarFilterButton,
  GridValueFormatterParams
} from '@material-ui/data-grid'
import _ from 'lodash'
import React from 'react'
import { FuelTypes } from '../fuelTypes'
export interface FBCInputGridProps {
  testId?: string
  stationMenuOptions: GridMenuOption[]
  fuelTypeMenuOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: GridRowId, updatedRow: FBCInputRow) => void
  setSelected: (rowIds: number[]) => void
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
      {/* <GridToolbarExport /> */}
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

  const stationCodeMap = new Map(
    props.stationMenuOptions.map(station => [station.value, station.label])
  )

  return (
    <div style={{ display: 'flex', height: 300, width: 800 }}>
      <div style={{ flexGrow: 1 }}>
        <DataGrid
          components={{
            Toolbar: buildFBCGridToolbar
          }}
          checkboxSelection={true}
          onSelectionModelChange={e => props.setSelected(e.selectionModel as number[])}
          onCellClick={(params: GridCellParams) =>
            params.api.setCellMode(params.id, params.field, 'edit')
          }
          hideFooter={true}
          rowHeight={30}
          columns={[
            {
              field: 'weatherStation',
              headerName: 'Weather Station',
              flex: 1,
              type: 'singleSelect',
              editable: true,
              valueOptions: props.stationMenuOptions,
              valueFormatter: (params: GridValueFormatterParams) => {
                if (!(_.isNull(params.value) || _.isUndefined(params.value))) {
                  return stationCodeMap.get(parseInt(params.value as string))
                }
                return params
              }
            },
            {
              field: 'fuelType',
              flex: 1,
              headerName: 'Fuel Type',
              type: 'singleSelect',
              editable: true,
              valueOptions: props.fuelTypeMenuOptions,
              valueFormatter: (params: GridValueFormatterParams) => {
                return FuelTypes.lookup(params.value as string).friendlyName
              }
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
