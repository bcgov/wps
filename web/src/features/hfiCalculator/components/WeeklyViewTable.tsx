import React, { useState } from 'react'

import { TableBody, TableCell, TableHead, TableRow } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre } from 'api/hfiCalcAPI'
import FireTable from 'components/FireTable'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import DayIndexHeaders from 'features/hfiCalculator/components/DayIndexHeaders'
import CalculatedPlanningAreaCells from 'features/hfiCalculator/components/CalculatedPlanningAreaCells'
import { StaticCells } from 'features/hfiCalculator/components/StaticCells'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType } from 'features/hfiCalculator/validation'
import { fireTableStyles } from 'app/theme'
import { isEmpty, union } from 'lodash'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { getDailiesByStationCode, getZoneFromAreaName } from 'features/hfiCalculator/util'

export interface Props {
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  currentDay: string
  testId?: string
}

export const columnLabelsForEachDayInWeek: string[] = [
  'ROS (m/min)',
  'HFI',
  'M / FIG',
  'Fire Starts',
  'Prep Level'
]

export const weeklyTableColumnLabels: string[] = [
  'Location',
  'Elev. (m)',
  'FBP Fuel Type',
  'Grass Cure (%)',
  ...Array(5).fill(columnLabelsForEachDayInWeek).flat(),
  'Highest Daily FIG',
  'Calc. Prep'
]

const useStyles = makeStyles({
  ...fireTableStyles
})

export const WeeklyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const [selected, setSelected] = useState<number[]>(
    union(props.dailies.map(daily => daily.code))
  )

  const stationCodeInSelected = (code: number) => {
    return selected.includes(code)
  }
  const toggleSelectedStation = (code: number) => {
    const selectedSet = new Set(selected)
    if (stationCodeInSelected(code)) {
      // remove station from selected
      selectedSet.delete(code)
    } else {
      // add station to selected
      selectedSet.add(code)
    }
    setSelected(Array.from(selectedSet))
  }

  return (
    <FireTable
      maxHeight={700}
      ariaLabel="weekly table view of HFI by planning area"
      testId="hfi-calc-weekly-table"
    >
      <TableHead>
        <TableRow>
          <DayHeaders isoDate={props.currentDay} />
          <TableCell colSpan={2} className={classes.spaceHeader}></TableCell>
        </TableRow>
        <TableRow>
          <TableCell>
            {/* empty cell inserted for spacing purposes (aligns with checkboxes column) */}
          </TableCell>
          <TableCell key="header-location">Location</TableCell>
          <TableCell key="header-elevation">
            Elev.
            <br />
            (m)
          </TableCell>
          <TableCell key="header-fuel-type">
            FBP
            <br />
            Fuel
            <br />
            Type
          </TableCell>
          <TableCell>
            Grass
            <br />
            Cure
            <br />
            (%)
          </TableCell>
          <DayIndexHeaders />
          <TableCell className={classes.sectionSeparatorBorder}>
            Highest
            <br />
            Daily
            <br />
            FIG
          </TableCell>
          <TableCell>
            Calc.
            <br />
            Prep
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {Object.entries(props.fireCentres).map(([centreName, centre]) => {
          return (
            <React.Fragment key={`fire-centre-${centreName}`}>
              <TableRow key={`fire-centre-${centreName}`}>
                <TableCell className={classes.fireCentre} colSpan={32}>
                  {centre.name}
                </TableCell>
              </TableRow>
              {Object.entries(centre.planning_areas)
                .sort((a, b) =>
                  getZoneFromAreaName(a[1].name) < getZoneFromAreaName(b[1].name) ? -1 : 1
                ) // sort by zone code
                .map(([areaName, area]) => {
                  return (
                    <React.Fragment key={`zone-${areaName}`}>
                      <TableRow
                        className={classes.planningArea}
                        key={`zone-${areaName}`}
                        data-testid={`zone-${areaName}`}
                      >
                        <TableCell className={classes.planningArea} colSpan={5}>
                          {area.name}
                        </TableCell>
                        <CalculatedPlanningAreaCells
                          area={area}
                          areaName={areaName}
                          dailies={props.dailies}
                          selected={selected}
                          planningAreaClass={classes.planningArea}
                        />
                      </TableRow>
                      {Object.entries(area.stations)
                        .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                        .map(([stationCode, station]) => {
                          const dailiesForStation = getDailiesByStationCode(
                            props.dailies,
                            station.code
                          )
                          const isRowSelected = stationCodeInSelected(station.code)
                          const classNameForRow = !isRowSelected
                            ? classes.unselectedStation
                            : undefined

                          return (
                            <TableRow
                              className={classNameForRow}
                              key={`station-${stationCode}`}
                            >
                              <BaseStationAttributeCells
                                station={station}
                                className={classNameForRow}
                                stationCodeInSelected={stationCodeInSelected}
                                toggleSelectedStation={toggleSelectedStation}
                              />
                              <GrassCureCell
                                value={
                                  !isEmpty(dailiesForStation)
                                    ? dailiesForStation[0].grass_cure_percentage
                                    : undefined
                                }
                                isGrassFuelType={isGrassFuelType(station.station_props)}
                                className={
                                  isRowSelected ? undefined : classes.unselectedStation
                                }
                                selected={isRowSelected}
                              />

                              <StaticCells
                                dailies={dailiesForStation}
                                station={station}
                                classNameForRow={classNameForRow}
                                isRowSelected={isRowSelected}
                              />
                            </TableRow>
                          )
                        })}
                    </React.Fragment>
                  )
                })}
            </React.Fragment>
          )
        })}
      </TableBody>
    </FireTable>
  )
}

export default React.memo(WeeklyViewTable)
