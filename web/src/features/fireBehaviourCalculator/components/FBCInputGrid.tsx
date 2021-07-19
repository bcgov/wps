import { TextField, Tooltip } from '@material-ui/core'
import {
  DataGrid,
  GridCellParams,
  GridEditCellValueParams,
  GridRowId,
  GridToolbarColumnsButton,
  GridToolbarContainer,
  GridToolbarDensitySelector,
  // GridToolbarExport,
  GridToolbarFilterButton
} from '@material-ui/data-grid'
import InfoIcon from '@material-ui/icons/Info'
import { Autocomplete } from '@material-ui/lab'
import { find, isEqual, isNull, isUndefined } from 'lodash'
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
  windSpeed: number | undefined
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
const GrassCurePercentageEdit = (props: NumberEditProps) => {
  return (
    <TextField
      id="grass-cure-percentage-number"
      type="number"
      value={props.value}
      required={true}
    />
  )
}

const WindSpeedEdit = (props: NumberEditProps) => {
  return (
    <TextField
      id="wind-speed-edit-number"
      type="number"
      value={props.value}
      required={false}
    />
  )
}

const FBCInputGrid = (props: FBCInputGridProps) => {
  const stationCodeMap = new Map(
    props.stationMenuOptions.map(station => [station.value, station.label])
  )

  const buildStationOptionFromValue = (value: number) => {
    const label = stationCodeMap.get(value)
    if (isUndefined(label)) {
      return null
    }
    const option: GridMenuOption = {
      label,
      value
    }
    return option
  }

  const buildFuelTypeMenuOption = (value: string) => {
    const fuelType = FuelTypes.lookup(value)
    if (isUndefined(fuelType)) {
      return null
    }
    const option: GridMenuOption = {
      label: fuelType.friendlyName,
      value
    }
    return option
  }

  const optionComboBox = (
    params: GridCellParams,
    optionBoxType: OptionBoxType,
    options: GridMenuOption[]
  ) => {
    const { id, api, field } = params
    const rowToUpdate = find(props.rows, ['id', params.id])
    if (!rowToUpdate) {
      return
    }

    const currentValue =
      optionBoxType.type === 'station'
        ? buildStationOptionFromValue(parseInt(rowToUpdate.weatherStation))
        : buildFuelTypeMenuOption(rowToUpdate.fuelType)

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

    return (
      <Autocomplete
        id={`combo-box-fuel-types-${Math.random()}`}
        getOptionSelected={(option, value) => isEqual(option, value)}
        options={options}
        getOptionLabel={option => option?.label}
        style={{ width: 300, height: '100%', marginTop: 20 }}
        renderInput={params => <TextField {...params} variant="outlined" />}
        onChange={handleChange}
        value={currentValue}
      />
    )
  }

  const updateCellValue = (params: GridEditCellValueParams) => {
    if (!isEqual(params.field, 'grassCure') && !isEqual(params.field, 'windSpeed')) {
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
    <div style={{ display: 'flex', height: 300, width: 1200 }}>
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
                return <GrassCurePercentageEdit value={params.value as string} />
              }
            },
            {
              field: 'windSpeed',
              // eslint-disable-next-line react/display-name
              renderHeader: () => (
                <span>
                  {'Wind Speed (km/h) (Optional)'}
                  <Tooltip title="Leave this empty to calculate forecasted/observed wind speed. Add a custom wind speed to influence the calculations">
                    <InfoIcon aria-label="info"></InfoIcon>
                  </Tooltip>
                </span>
              ),
              flex: 1.0,
              type: 'number',
              editable: true,
              renderCell: function numberPicker(params) {
                return <WindSpeedEdit value={params.value as string} />
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
