import { FormControlLabel, IconButton, TextField } from '@material-ui/core'
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
import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown'
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
export interface DropDownEditProps {
  label: string
}
const DropDownEdit = (props: DropDownEditProps) => {
  return (
    <FormControlLabel
      label={props.label}
      labelPlacement="start"
      placeholder="Please select a station"
      control={
        <IconButton color="primary" aria-label="Choose station">
          <ArrowDropDownIcon />
        </IconButton>
      }
    />
  )
}

interface NumberEditProps {
  value: string
}
const NumberEdit = (props: NumberEditProps) => {
  return (
    <TextField
      id="grass-cure-percentage-number"
      type="number"
      value={props.value}
      required={true}
    />
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
    <div style={{ display: 'flex', height: 300, width: 1000 }}>
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
              renderCell: function stationDropDown(params) {
                let stationName = stationCodeMap.get(parseInt(params.value as string))
                stationName = stationName ? stationName : ''
                return (
                  <div style={{ cursor: 'pointer' }}>
                    <DropDownEdit label={`${stationName}`} />
                  </div>
                )
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
              },
              renderCell: function fuelTypeDropDown(params) {
                return (
                  <div style={{ cursor: 'pointer' }}>
                    <DropDownEdit
                      label={`${FuelTypes.lookup(params.value as string).friendlyName}`}
                    />
                  </div>
                )
              }
            },
            {
              field: 'grassCure',
              headerName: 'Grass Cure %',
              flex: 0.7,
              type: 'number',
              editable: true,
              renderCell: function numberPicker(params) {
                return <NumberEdit value={params.value as string} />
              }
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
