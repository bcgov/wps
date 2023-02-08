import { Checkbox, TableCell, TableRow, TableSortLabel, Tooltip, TableHead } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import FBAProgressRow from 'features/fbaCalculator/components/FBAProgressRow'
import TableHeader from 'features/fbaCalculator/components/TableHeader'
import StickyCell from 'components/StickyCell'
import { FBATableRow, SortByColumn } from 'features/fbaCalculator/RowManager'
import { isUndefined } from 'lodash'
import React from 'react'
import { Order } from 'utils/table'
import { ColumnLabel } from 'features/fbaCalculator/components/FBATable'

interface FBATableHeadProps {
  toggleSorting: (selectedColumn: SortByColumn) => void
  order: Order
  rows: FBATableRow[]
  headerSelected: boolean
  setHeaderSelect: (value: React.SetStateAction<boolean>) => void
  setSelected: (value: React.SetStateAction<number[]>) => void
  loading: boolean
  visibleColumns: ColumnLabel[]
}

const useStyles = makeStyles({
  windSpeed: {
    width: 80
  },
  progressBar: {
    minWidth: 1900
  },
  infoIcon: {
    style: {
      fill: '#1A5A96',
      textAlign: 'center'
    }
  },
  headerCell: {
    zIndex: 1103
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

  const typeToolTipFirstLine = 'SUR = Surface Type'
  const typeToolTipSecondLine = 'IC = Intermittent Crown Type'
  const typeToolTipThirdLine = 'CC = Continuous Crown Type'
  const typeToolTipElement = (
    <div>
      {typeToolTipFirstLine} <br />
      {typeToolTipSecondLine} <br />
      {typeToolTipThirdLine}
    </div>
  )

  const columnHeaderComponentsDict = {
    Zone: (
      <TableCell className={classes.headerCell} key="header-zone" sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Zone)
          }}
        >
          <TableHeader text={'Zone'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Weather Station': (
      <StickyCell left={57} zIndexOffset={Z_INDEX_OFFSET + 3} key="weather-station">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Station)
          }}
        >
          <TableHeader largerMaxWidth={true} text={'Weather Station'}></TableHeader>
        </TableSortLabel>
      </StickyCell>
    ),
    Elevation: (
      <TableCell className={classes.headerCell} key="header-elevation" sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Elevation)
          }}
        >
          <TableHeader text={'Elev. (m)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'FBP Fuel Type': (
      <StickyCell left={280} zIndexOffset={Z_INDEX_OFFSET} key="fbp-fuel-type">
        <TableSortLabel direction={order} onClick={() => toggleSorting(SortByColumn.FuelType)}>
          <TableHeader largerMaxWidth={true} text={'FBP Fuel Type'}></TableHeader>
        </TableSortLabel>
      </StickyCell>
    ),
    'Grass Cure': (
      <TableCell sortDirection={order} key="grass-cure">
        <TableSortLabel direction={order} onClick={() => toggleSorting(SortByColumn.GrassCure)}>
          <TableHeader text={'Grass Cure (%)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    Status: (
      <TableCell sortDirection={order} key="status">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Status)
          }}
        >
          <TableHeader text={'Status'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    Temp: (
      <TableCell sortDirection={order} key="temp">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Temperature)
          }}
        >
          <TableHeader text={'Temp (°C)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    RH: (
      <TableCell sortDirection={order} key="rh">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.RelativeHumidity)
          }}
        >
          <TableHeader text={'RH (%)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Wind Dir': (
      <TableCell sortDirection={order} key="wind-dir">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.WindDirection)
          }}
        >
          <TableHeader text={'Wind Dir (°C)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Wind Speed (km/h)': (
      <TableCell className={classes.windSpeed} sortDirection={order} key="wind-speed">
        <TableSortLabel
          className={classes.windSpeed}
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.WindSpeed)
          }}
        >
          <TableHeader text={'Wind Speed (km/h)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Precip (mm)': (
      <TableCell sortDirection={order} key="precip">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Precipitation)
          }}
        >
          <TableHeader text={'Precip (mm)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    FFMC: (
      <TableCell sortDirection={order} key="ffmc">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.FFMC)
          }}
        >
          <TableHeader text={'FFMC'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    DMC: (
      <TableCell sortDirection={order} key="dmc">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.DMC)
          }}
        >
          <TableHeader text={'DMC'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    DC: (
      <TableCell sortDirection={order} key="dc">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.DMC)
          }}
        >
          <TableHeader text={'DC'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    ISI: (
      <TableCell sortDirection={order} key="isi">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.ISI)
          }}
        >
          <TableHeader text={'ISI'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    BUI: (
      <TableCell sortDirection={order} key="bui">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.BUI)
          }}
        >
          <TableHeader text={'BUI'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    FWI: (
      <TableCell sortDirection={order} key="fwi">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.BUI)
          }}
        >
          <TableHeader text={'FWI'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    HFI: (
      <TableCell sortDirection={order} key="hfi">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.HFI)
          }}
        >
          <TableHeader text={'HFI'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Critical Hours (4000 kW/m)': (
      <TableCell sortDirection={order} key="critical-hours-4000">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.CriticalHours4000)
          }}
        >
          <TableHeader text={'Critical Hours (4000 kW/m)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Critical Hours (10000 kW/m)': (
      <TableCell sortDirection={order} key="critical-hours-10000">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.CriticalHours10000)
          }}
        >
          <TableHeader text={'Critical Hours (10000 kW/m)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'ROS (m/min)': (
      <TableCell sortDirection={order} key="ros">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.ROS)
          }}
        >
          <TableHeader text={'ROS m/min'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Fire Type': (
      <TableCell sortDirection={order} key="fire-type">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.FireType)
          }}
        >
          <Tooltip
            title={typeToolTipElement}
            aria-label={`${typeToolTipFirstLine} \n ${typeToolTipSecondLine} \n ${typeToolTipThirdLine}`}
          >
            <InfoOutlinedIcon className={classes.infoIcon}></InfoOutlinedIcon>
          </Tooltip>

          <TableHeader text={'Fire Type'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'CFB (%)': (
      <TableCell className={classes.headerCell} sortDirection={order} key="cfb">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.CFB)
          }}
        >
          <TableHeader text={'CFB (%)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    'Flame Length (m)': (
      <TableCell className={classes.headerCell} sortDirection={order} key="flame-length">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.FlameLength)
          }}
        >
          <TableHeader text={'Flame Length (m)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    '30 min fire size (ha)': (
      <TableCell className={classes.headerCell} sortDirection={order} key="30-min-fire">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.ThirtyMinFireSize)
          }}
        >
          <TableHeader text={'30 min fire size (ha)'}></TableHeader>
        </TableSortLabel>
      </TableCell>
    ),
    '60 min fire size (ha)': (
      <TableCell className={classes.headerCell} sortDirection={order} key="60-min-fire">
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.SixtyMinFireSize)
          }}
        >
          <TableHeader text={'60 min fire size (ha)'} testId="fire-size"></TableHeader>
        </TableSortLabel>
      </TableCell>
    )
  }

  return (
    <TableHead>
      <TableRow>
        <StickyCell left={0} zIndexOffset={Z_INDEX_OFFSET + 100}>
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
