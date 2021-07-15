import { TextField } from '@material-ui/core'
import {
  DataGrid,
  GridCellParams,
  GridCellValue,
  GridEditCellValueParams,
  GridRowId,
  GridToolbarColumnsButton,
  GridToolbarContainer,
  GridToolbarDensitySelector,
  // GridToolbarExport,
  GridToolbarFilterButton
} from '@material-ui/data-grid'
import { Autocomplete } from '@material-ui/lab'
import { find, isEqual, isNull, isUndefined } from 'lodash'
import React from 'react'
import { FuelTypes } from '../fuelTypes'
import { GridMenuOption, theEmptyOption } from '../utils'
export interface FBCInputGridProps {
  testId?: string
  stationMenuOptions: GridMenuOption[]
  fuelTypeMenuOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: GridRowId, updatedRow: FBCInputRow) => void
  setSelected: (rowIds: number[]) => void
}
export interface FBCInputRow {
  id: number
  weatherStation: string | null | undefined
  fuelType: string | null | undefined
  grassCure: number | null | undefined
}

const buildFBCGridToolbar = () => {
  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <GridToolbarDensitySelector />
      {/* <GridToolbarExport /> */}
    </GridToolbarContainer>
  )
}
export interface DropDownEditProps {
  label: string
  options: GridMenuOption[]
}

interface OptionBoxType {
  type: 'station' | 'fuelType'
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
  const stationCodeMap: Map<string | number, string> = new Map(
    props.stationMenuOptions
      .filter(station => !isEqual(station, theEmptyOption))
      .map(station => [station.value, station.label])
  )

  const buildStationOption = (value: string | null | undefined) => {
    if (isUndefined(value) || isNull(value)) {
      return undefined
    }
    const label = stationCodeMap.get(parseInt(value))
    if (isUndefined(label)) {
      return undefined
    }
    const option: GridMenuOption = {
      label,
      value
    }
    return option
  }

  const buildFuelTypeMenuOption = (value: string | null | undefined) => {
    if (isUndefined(value) || isNull(value)) {
      return undefined
    }
    const fuelType = FuelTypes.lookup(value)
    if (isUndefined(fuelType) || isNull(fuelType)) {
      return undefined
    }
    const option: GridMenuOption = {
      label: fuelType.friendlyName,
      value
    }
    return option
  }

  const buildGridMenuOption = (
    value: GridCellValue,
    optionBoxType: OptionBoxType
  ): GridMenuOption => {
    if (isUndefined(value) || isNull(value)) {
      return theEmptyOption
    }
    const gridMenuOption =
      optionBoxType.type === 'station'
        ? buildStationOption(value as string)
        : buildFuelTypeMenuOption(value as string)

    return isUndefined(gridMenuOption) ? theEmptyOption : gridMenuOption
  }

  const optionComboBox = (
    params: GridCellParams,
    optionBoxType: OptionBoxType,
    options: GridMenuOption[]
  ) => {
    const { id, api, field, value } = params
    const rowToUpdate = find(props.rows, ['id', params.id])
    if (!rowToUpdate) {
      return
    }

    // eslint-disable-next-line
    const handleChange = (_: React.ChangeEvent<{}>, option: GridMenuOption | null) => {
      if (isNull(option)) {
        return
      }
      const editProps = { value: option }
      api.setEditCellProps({ id, field, props: editProps })
      api.commitCellChange({ id, field })
      api.setCellMode(id, field, 'view')
      const updatedRow = {
        ...rowToUpdate,
        ...{
          [params.field as keyof FBCInputRow]: option?.value
        }
      }
      props.updateRow(params.id, updatedRow)
    }

    const finalVal: GridMenuOption = buildGridMenuOption(value, optionBoxType)
    const label = isEqual(finalVal, theEmptyOption)
      ? optionBoxType.type === 'station'
        ? 'Select a station'
        : 'Select a fuel type'
      : undefined
    return (
      <Autocomplete
        id={`combo-box-fuel-types-${Math.random()}`}
        getOptionSelected={(option, value) => isEqual(option, value)}
        options={options}
        getOptionLabel={option => option?.label}
        style={{ width: 300, height: '100%', marginTop: 20 }}
        renderInput={params => <TextField {...params} label={label} variant="outlined" />}
        onChange={handleChange}
        value={finalVal}
      />
    )
  }

  const updateCellValue = (params: GridEditCellValueParams) => {
    if (!isEqual(params.field, 'grassCure')) {
      return
    }
    const rowToUpdate = find(props.rows, ['id', params.id])
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
    <div style={{ display: 'flex', height: 300, width: 1000 }}>
      <div style={{ flexGrow: 1 }}>
        <DataGrid
          components={{
            Toolbar: buildFBCGridToolbar
          }}
          checkboxSelection={true}
          onSelectionModelChange={e => props.setSelected(e.selectionModel as number[])}
          hideFooter={true}
          rowHeight={50}
          columns={[
            {
              field: 'weatherStation',
              headerName: 'Weather Station',
              flex: 1,
              type: 'singleSelect',
              editable: true,
              renderCell: (params: GridCellParams) =>
                optionComboBox(params, { type: 'station' }, props.stationMenuOptions),
              renderEditCell: (params: GridCellParams) =>
                optionComboBox(params, { type: 'station' }, props.stationMenuOptions)
            },
            {
              field: 'fuelType',
              flex: 1,
              headerName: 'Fuel Type',
              type: 'singleSelect',
              editable: true,
              renderCell: (params: GridCellParams) =>
                optionComboBox(params, { type: 'fuelType' }, props.fuelTypeMenuOptions),
              renderEditCell: (params: GridCellParams) =>
                optionComboBox(params, { type: 'fuelType' }, props.fuelTypeMenuOptions)
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
