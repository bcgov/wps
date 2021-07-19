import React from 'react'
import { useTable } from 'react-table'
import { find, isEqual, isNull, isUndefined } from 'lodash'
import MaUTable from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableHead from '@material-ui/core/TableHead'
import TableRow from '@material-ui/core/TableRow'
import { FBCInputRow, GridMenuOption } from './FBCInputGrid'
import { Autocomplete } from '@material-ui/lab'
import { TextField } from '@material-ui/core'
import { FuelTypes } from '../fuelTypes'

interface DatePickerProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: number, updatedRow: FBCInputRow) => void
}

const TestComponent = (props: DatePickerProps) => {
  const stationCodeMap = new Map(
    props.stationOptions.map(station => [station.value, station.label])
  )

  const buildStationOption = (value: number) => {
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
    if (isUndefined(fuelType) || isNull(fuelType)) {
      return null
    }
    const option: GridMenuOption = {
      label: fuelType.friendlyName,
      value
    }
    return option
  }

  const data = props.rows.map(row => ({
    weatherStation: buildStationOption(parseInt(row.weatherStation)),
    fuelType: buildFuelTypeMenuOption(row.fuelType),
    grassCure: 0,
    windSpeed: 0
  }))

  const columns: any = React.useMemo(
    () => [
      {
        Header: 'Station',
        accessor: 'weatherStation'
      },
      {
        Header: 'FuelType',
        accessor: 'fuelType'
      },
      {
        Header: 'Grass Cure %',
        accessor: 'grassCure'
      },
      {
        Header: 'Wind Speed (km/hr) (Optional)',
        accessor: 'windSpeed'
      }
    ],
    []
  )

  const tableInstance = useTable({ columns, data })

  const { getTableProps, headerGroups, rows, prepareRow } = tableInstance

  const buildCell = (
    cell: { column: { id: string }; value: GridMenuOption },
    field: string,
    rowId: number
  ) => {
    const changeHandler = (event: React.ChangeEvent<{}>, value: any) => {
      console.log(field)

      const rowToUpdate = find(props.rows, ['id', rowId])
      if (rowToUpdate) {
        const updatedRow = {
          ...rowToUpdate,
          ...{
            [field as keyof FBCInputRow]: (value as GridMenuOption).value
          }
        }
        props.updateRow(rowId, updatedRow)
      }
    }

    if (cell.column.id === 'weatherStation') {
      return (
        <Autocomplete
          options={props.stationOptions}
          getOptionSelected={(option, value) => isEqual(option, value)}
          getOptionLabel={option => option?.label}
          id={`combo-box-fuel-types-${Math.random()}`}
          style={{ width: 300 }}
          renderInput={params => <TextField {...params} label="Select a station" />}
          onChange={changeHandler}
          value={cell.value}
        />
      )
    }
    if (cell.column.id === 'fuelType') {
      return (
        <Autocomplete
          options={props.fuelTypeOptions}
          getOptionSelected={(option, value) => isEqual(option, value)}
          getOptionLabel={option => option?.label}
          id={`combo-box-fuel-types-${Math.random()}`}
          style={{ width: 300 }}
          renderInput={params => <TextField {...params} label="Select a fuel type" />}
          onChange={changeHandler}
          value={cell.value}
        />
      )
    }
    return <TextField type="number" />
  }

  return (
    <MaUTable {...getTableProps()}>
      <TableHead>
        {headerGroups.map(headerGroup => (
          <TableRow {...headerGroup.getHeaderGroupProps()}>
            {headerGroup.headers.map(column => (
              <TableCell {...column.getHeaderProps()}>
                {column.render('Header')}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableHead>
      <TableBody>
        {rows.map((row, i) => {
          prepareRow(row)
          return (
            <TableRow {...row.getRowProps()}>
              {row.cells.map(cell => {
                console.log(cell.column.id)
                return (
                  <TableCell {...cell.getCellProps()}>
                    {buildCell(cell, cell.column.id, parseInt(row.id))}
                  </TableCell>
                )
              })}
            </TableRow>
          )
        })}
      </TableBody>
    </MaUTable>
  )
}

export default React.memo(TestComponent)
