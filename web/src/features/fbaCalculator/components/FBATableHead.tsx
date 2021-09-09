import {
  Checkbox,
  makeStyles,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel
} from '@material-ui/core'
import FBAProgressRow from 'features/fbaCalculator/components/FBAProgressRow'
import StickyCell from 'features/fbaCalculator/components/StickyCell'
import { FBATableRow, SortByColumn } from 'features/fbaCalculator/RowManager'
import { isUndefined } from 'lodash'
import React from 'react'
import { Order } from 'utils/table'

interface FBATableHeadProps {
  toggleSorting: (selectedColumn: SortByColumn) => void
  order: Order
  rows: FBATableRow[]
  headerSelected: boolean
  setHeaderSelect: (value: React.SetStateAction<boolean>) => void
  setSelected: (value: React.SetStateAction<number[]>) => void
  loading: boolean
}

const useStyles = makeStyles({
  tableHeaderRow: {
    padding: '8px'
  },
  windSpeed: {
    width: 80
  },
  progressBar: {
    minWidth: 1900
  }
})

const FBATableHead = ({
  toggleSorting,
  order,
  rows,
  headerSelected,
  setHeaderSelect,
  setSelected,
  loading
}: FBATableHeadProps) => {
  const classes = useStyles()

  return (
    <TableHead>
      <TableRow>
        <StickyCell left={0} zIndexOffset={2}>
          <Checkbox
            data-testid="select-all"
            color="primary"
            checked={headerSelected}
            onClick={() => {
              if (headerSelected) {
                // Toggle off
                setSelected([])
                setHeaderSelect(false)
              } else {
                setSelected(rows.filter(row => !isUndefined(row)).map(row => row.id))
                setHeaderSelect(true)
              }
            }}
          />
        </StickyCell>
        <TableCell key="header-zone" sortDirection={order}>
          <TableSortLabel
            className={classes.tableHeaderRow}
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Zone)
            }}
          >
            Zone
          </TableSortLabel>
        </TableCell>
        <StickyCell left={50} zIndexOffset={2}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Station)
            }}
          >
            Weather Station
          </TableSortLabel>
        </StickyCell>
        <TableCell key="header-elevation" sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Elevation)
            }}
          >
            Elev.
            <br />
            (m)
          </TableSortLabel>
        </TableCell>
        <StickyCell left={280} zIndexOffset={2}>
          <TableSortLabel
            direction={order}
            onClick={() => toggleSorting(SortByColumn.FuelType)}
          >
            FBP Fuel Type
          </TableSortLabel>
        </StickyCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => toggleSorting(SortByColumn.GrassCure)}
          >
            Grass
            <br />
            Cure
            <br />
            (%)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Status)
            }}
          >
            Status
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Temperature)
            }}
          >
            Temp
            <br />
            (&deg;C)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.RelativeHumidity)
            }}
          >
            RH
            <br />
            (%)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.WindDirection)
            }}
          >
            Wind
            <br />
            Dir
            <br />
            (&deg;)
          </TableSortLabel>
        </TableCell>
        <TableCell className={classes.windSpeed} sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.WindSpeed)
            }}
          >
            Wind Speed (km/h)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.Precipitation)
            }}
          >
            Precip
            <br />
            (mm)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.FFMC)
            }}
          >
            FFMC
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.DMC)
            }}
          >
            DMC
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.DMC)
            }}
          >
            DC
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.ISI)
            }}
          >
            ISI
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.BUI)
            }}
          >
            BUI
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.BUI)
            }}
          >
            FWI
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.HFI)
            }}
          >
            HFI
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.CriticalHours4000)
            }}
          >
            Critical
            <br />
            Hours
            <br />
            (4000 kW/m)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.CriticalHours10000)
            }}
          >
            Critical
            <br />
            Hours
            <br />
            (10000 kW/m)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.ROS)
            }}
          >
            ROS
            <br />
            (m/min)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.FireType)
            }}
          >
            Fire Type
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.CFB)
            }}
          >
            CFB (%)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.FlameLength)
            }}
          >
            Flame <br />
            Length <br /> (m)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.ThirtyMinFireSize)
            }}
          >
            30 min <br />
            fire size <br />
            (hectares)
          </TableSortLabel>
        </TableCell>
        <TableCell sortDirection={order}>
          <TableSortLabel
            direction={order}
            onClick={() => {
              toggleSorting(SortByColumn.SixtyMinFireSize)
            }}
          >
            60 min <br />
            fire size <br />
            (hectares)
          </TableSortLabel>
        </TableCell>
      </TableRow>
      <FBAProgressRow loading={loading} />
    </TableHead>
  )
}

export default React.memo(FBATableHead)
