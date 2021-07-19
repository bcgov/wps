import React from 'react'
import { useTable } from 'react-table'
import { isNull, isUndefined } from 'lodash'
import {
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip
} from '@material-ui/core'
import InfoIcon from '@material-ui/icons/Info'
import { FuelTypes } from '../fuelTypes'
import { buildRowCell } from '../tableRowBuilder'

export interface FBCInputGridProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  rows: FBCInputRow[]
  updateRow: (rowId: number, updatedRow: FBCInputRow) => void
  selected: number[]
  updateSelected: (selected: number[]) => void
}

export interface GridMenuOption {
  label: string
  value: string | number
}

export interface FBCInputRow {
  id: number
  weatherStation: string | undefined
  fuelType: string | undefined
  grassCure: number | undefined
  windSpeed: number | undefined
}

const FBCInputGrid = (props: FBCInputGridProps) => {
  const stationCodeMap = new Map(
    props.stationOptions.map(station => [station.value, station.label])
  )

  const buildStationOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
    const label = stationCodeMap.get(parseInt(value))

    if (isUndefined(label)) {
      return null
    }
    const option: GridMenuOption = {
      label,
      value
    }
    return option
  }

  const buildFuelTypeMenuOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
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
    weatherStation: buildStationOption(row.weatherStation),
    fuelType: buildFuelTypeMenuOption(row.fuelType),
    grassCure: row.grassCure,
    windSpeed: row.windSpeed
  }))

  const columns: any = React.useMemo(
    () => [
      {
        Header: 'Select',
        accessor: 'select'
      },
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

  const renderHeader = (column: any) => {
    if (column.id === 'windSpeed') {
      return (
        <span>
          {'Wind Speed (km/h) (Optional)'}
          <Tooltip title="Leave this empty to calculate forecasted/observed wind speed. Add a custom wind speed to influence the calculations">
            <InfoIcon aria-label="info"></InfoIcon>
          </Tooltip>
        </span>
      )
    }
    if (column.id === 'select') {
      return <Checkbox color="primary" />
    }
    return column.render('Header')
  }
  return (
    <Table {...getTableProps()}>
      <TableHead>
        {headerGroups.map(headerGroup => (
          <TableRow {...headerGroup.getHeaderGroupProps()}>
            {headerGroup.headers.map(column => (
              <TableCell {...column.getHeaderProps()}>{renderHeader(column)}</TableCell>
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
    </Table>
  )
}

export default React.memo(FBCInputGrid)
