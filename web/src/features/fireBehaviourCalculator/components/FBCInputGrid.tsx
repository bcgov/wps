import React from 'react'
import { useTable } from 'react-table'
import { isNull, isUndefined } from 'lodash'
import MaUTable from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableHead from '@material-ui/core/TableHead'
import TableRow from '@material-ui/core/TableRow'
import { FuelTypes } from '../fuelTypes'
import { buildRowCell } from '../tableRowBuilder'

export interface DatePickerProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: number, updatedRow: FBCInputRow) => void
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

const FBCInputGrid = (props: DatePickerProps) => {
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
    grassCure: row.grassCure,
    windSpeed: row.windSpeed
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
                return (
                  <TableCell {...cell.getCellProps()}>
                    {buildRowCell(props, cell, cell.column.id, parseInt(row.id))}
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

export default React.memo(FBCInputGrid)
