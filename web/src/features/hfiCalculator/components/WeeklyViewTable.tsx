import React, { useState } from 'react'

import { TableBody, TableCell, TableHead, TableRow } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireTable from 'components/FireTable'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import CellHeaders from 'features/hfiCalculator/components/CellHeaders'
import CalculatedPlanningAreaCells from 'features/hfiCalculator/components/CalculatedPlanningAreaCells'
import { StaticCells } from 'features/hfiCalculator/components/StaticCells'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType } from 'features/hfiCalculator/validation'
import { fireTableStyles } from 'app/theme'

export interface Props {
  fireCentres: Record<string, FireCentre>
  stationCodes: number[]
  weekliesByStationCode: Map<number, StationDaily[]>
  currentDay: string
  testId?: string
}

const useStyles = makeStyles({
  ...fireTableStyles
})

export const WeeklyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const [selected, setSelected] = useState<number[]>(props.stationCodes)

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
          <CellHeaders />
        </TableRow>
      </TableHead>
      <TableBody>
        {Object.entries(props.fireCentres).map(([centreName, centre]) => {
          return (
            <React.Fragment key={`fire-centre-${centreName}`}>
              <TableRow key={`fire-centre-${centreName}`}>
                <TableCell className={classes.fireCentre} colSpan={30}>
                  {centre.name}
                </TableCell>
              </TableRow>
              {Object.entries(centre.planning_areas)
                .sort((a, b) => (a[1].name < b[1].name ? -1 : 1))
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
                          selected={selected}
                          planningAreaClass={classes.planningArea}
                        />
                      </TableRow>
                      {Object.entries(area.stations)
                        .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                        .map(([stationCode, station]) => {
                          const dailies = props.weekliesByStationCode.get(station.code)
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
                                  dailies ? dailies[0].grass_cure_percentage : undefined
                                }
                                isGrassFuelType={isGrassFuelType(station.station_props)}
                                className={
                                  isRowSelected ? undefined : classes.unselectedStation
                                }
                                selected={isRowSelected}
                              />

                              <StaticCells
                                dailies={dailies}
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
