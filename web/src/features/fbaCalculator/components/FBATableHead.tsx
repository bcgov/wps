import {
  Checkbox,
  makeStyles,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip
} from '@material-ui/core'
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined'
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
  },
  infoIcon: {
    style: {
      fill: '#1A5A96',
      textAlign: 'center'
    }
  },
  header: {
    maxWidth: '80px',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    '& span': {
      display: 'none'
    },
    '&:hover span': {
      display: 'block',
      backgroundColor: '#4f4f4f',
      opacity: '0.7',
      minWidth: '120px',
      maxWidth: '200px',
      color: '#fff',
      textAlign: 'center',
      borderRadius: '6px',
      padding: '5px 0',
      /* Position the tooltip */
      position: 'absolute',
      left: '0px',
      top: '40px',
      zIndex: '10'
    }
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

  const columnHeaderComponentsDict: { [key: string]: React.ReactFragment } = {
    Zone: (
      <TableCell key="header-zone" sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.Zone)
          }}
        >
          <div className={classes.header}>
            Zone
            <span>Zone</span>
          </div>
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
          <div className={classes.header}>
            Weather Station
            <span>Weather Station</span>
          </div>
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
          <div className={classes.header}>
            Elev. (m)
            <span>Elev. (m)</span>
          </div>
        </TableSortLabel>
      </TableCell>
    ),
    'FBP Fuel Type': (
      <StickyCell left={280} zIndexOffset={Z_INDEX_OFFSET}>
        <TableSortLabel
          direction={order}
          onClick={() => toggleSorting(SortByColumn.FuelType)}
        >
          <div className={classes.header}>
            FBP Fuel Type
            <span>FBP Fuel Type</span>
          </div>
        </TableSortLabel>
      </StickyCell>
    ),
    'Grass Cure': (
      <TableCell sortDirection={order}>
        <TableSortLabel
          direction={order}
          onClick={() => toggleSorting(SortByColumn.GrassCure)}
        >
          <div className={classes.header}>
            Grass Cure (%)
            <span>Grass Cure (%)</span>
          </div>
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
          <div className={classes.header}>
            Status
            <span>Status</span>
          </div>
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
          <div className={classes.header}>
            Temp (&deg;C)
            <span>Temp (&deg;C)</span>
          </div>
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
          <div className={classes.header}>
            RH (%)
            <span>RH (%)</span>
          </div>
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
          <div className={classes.header}>
            Wind Dir (&deg;C)
            <span>Wind Dir (&deg;C)</span>
          </div>
        </TableSortLabel>
      </TableCell>
    ),
    'Wind Speed (km/h)': (
      <TableCell className={classes.windSpeed} sortDirection={order}>
        <TableSortLabel
          className={classes.windSpeed}
          direction={order}
          onClick={() => {
            toggleSorting(SortByColumn.WindSpeed)
          }}
        >
          <div className={classes.header}>
            Wind Speed (km/h)
            <span>Wind Speed (km/h)</span>
          </div>
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
          <div className={classes.header}>
            Precip (mm)
            <span>Precip (mm)</span>
          </div>
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
          <div className={classes.header}>
            FFMC
            <span>FFMC</span>
          </div>
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
          <div className={classes.header}>
            DMC
            <span>DMC</span>
          </div>
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
          <div className={classes.header}>
            DC
            <span>DC</span>
          </div>
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
          <div className={classes.header}>
            ISI
            <span>ISI</span>
          </div>
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
          <div className={classes.header}>
            BUI
            <span>BUI</span>
          </div>
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
          <div className={classes.header}>
            FWI
            <span>FWI</span>
          </div>
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
          <div className={classes.header}>
            HFI
            <span>HFI</span>
          </div>
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
          <div className={classes.header}>
            Critical Hours (4000 kW/m)
            <span>Critical Hours (4000 kW/m)</span>
          </div>
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
          <div className={classes.header}>
            Critical Hours (10000 kW/m)
            <span>Critical Hours (10000 kW/m)</span>
          </div>
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
          <div className={classes.header}>
            ROS (m/min)
            <span>ROS (m/min)</span>
          </div>
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
          <Tooltip
            title={typeToolTipElement}
            aria-label={`${typeToolTipFirstLine} \n ${typeToolTipSecondLine} \n ${typeToolTipThirdLine}`}
          >
            <InfoOutlinedIcon className={classes.infoIcon}></InfoOutlinedIcon>
          </Tooltip>

          <div className={classes.header}>
            Fire Type
            <span>Fire Type</span>
          </div>
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
          <div className={classes.header}>
            CFB (%)
            <span>CFB (%)</span>
          </div>
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
          <div className={classes.header}>
            Flame Length (m)
            <span>Flame Length (m)</span>
          </div>
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
          <div className={classes.header}>
            30 min fire size (ha)
            <span>30 min fire size (ha)</span>
          </div>
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
          <div className={classes.header}>
            60 min fire size (ha)
            <span>60 min fire size (ha)</span>
          </div>
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
