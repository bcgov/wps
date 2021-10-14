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
  visibleColumns: string[]
}

const useStyles = makeStyles({
  windSpeed: {
    width: 80
  },
  progressBar: {
    minWidth: 1900
  }
})

const Z_INDEX_OFFSET = 2

const FBATableHead = ({
  toggleSorting,
  order,
  rows,
  headerSelected,
  setHeaderSelect,
  setSelected,
  loading,
  visibleColumns
}: FBATableHeadProps) => {
  const classes = useStyles()

  const columnHeaderComponentsDict: { [key: string]: React.ReactFragment } = {
    Zone: (
      <TableCell key="header-zone" sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Zone)
          }}
        >
          Zone
        </TableSortLabel>
      </TableCell>
    ),
    'Weather Station': (
      <StickyCell left={57} zIndexOffset={Z_INDEX_OFFSET}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Station)
          }}
        >
          Weather Station
        </TableSortLabel>
      </StickyCell>
    ),
    Elevation: (
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
    ),
    'FBP Fuel Type': (
      <StickyCell left={280} zIndexOffset={Z_INDEX_OFFSET}>
        <TableSortLabel
          direction={order}
          onClick={() => toggleSorting(SortByColumn.FuelType)}
        >
          FBP Fuel Type
        </TableSortLabel>
      </StickyCell>
    ),
    'Grass Cure': (
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
    ),
    Status: (
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
    ),
    Temp: (
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
    ),
    RH: (
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
    ),
    'Wind Dir': (
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
    ),
    'Wind Speed (km/h)': (
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
    ),
    'Precip (mm)': (
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
    ),
    FFMC: (
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
    ),
    DMC: (
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
    ),
    DC: (
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
    ),
    ISI: (
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
    ),
    BUI: (
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
    ),
    FWI: (
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
    ),
    HFI: (
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
    ),
    'Critical Hours (4000 kW/m)': (
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
    ),
    'Critical Hours (10000 kW/m)': (
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
    ),
    'ROS (m/min)': (
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
    ),
    'Fire Type': (
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
    ),
    'CFB (%)': (
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
    ),
    'Flame Length (m)': (
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
    ),
    '30 min fire size (ha)': (
      <TableCell sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.ThirtyMinFireSize)
          }}
        >
          30 min <br />
          fire size <br />
          (ha)
        </TableSortLabel>
      </TableCell>
    ),
    '60 min fire size (ha)': (
      <TableCell sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.SixtyMinFireSize)
          }}
        >
          60 min <br />
          fire size <br />
          (ha)
        </TableSortLabel>
      </TableCell>
    )
  }

  return (
    <TableHead>
      <TableRow>
        <StickyCell left={0} zIndexOffset={Z_INDEX_OFFSET}>
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
        {visibleColumns.map(colName => {
          return columnHeaderComponentsDict[colName]
        })}
      </TableRow>
      <FBAProgressRow loading={loading} zIndexOffset={Z_INDEX_OFFSET} />
    </TableHead>
  )
}

export default React.memo(FBATableHead)
