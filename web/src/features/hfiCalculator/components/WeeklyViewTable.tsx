import React, { useState } from 'react'

import { TableBody, TableCell, TableHead, TableRow } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireTable from 'components/FireTable'
import FireContainer from 'components/FireDisplayContainer'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import CellHeaders from 'features/hfiCalculator/components/CellHeaders'
import CalculatedPlanningAreaCells from 'features/hfiCalculator/components/CalculatedPlanningAreaCells'
import { StaticCells } from 'features/hfiCalculator/components/StaticCells'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'

export interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  weekliesByStationCode: Map<number, StationDaily[]>
  weekliesByUTC: Map<number, StationDaily[]>
  currentDay: string
  testId?: string
}

const useStyles = makeStyles({
  fireCentre: {
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#dbd9d9'
  },
  planningArea: {
    backgroundColor: 'rgba(40, 53, 147, 0.05)'
  },
  unselectedStation: {
    color: 'rgba(0,0,0,0.54)'
  },
  controls: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'baseline'
  }
})

export const WeeklyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const stationCodesList: number[] = Array.from(props.dailiesMap.keys())

  const [selected, setSelected] = useState<number[]>(stationCodesList)

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
    <FireContainer testId={props.testId}>
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
            <CellHeaders />
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.entries(props.fireCentres).map(([centreName, centre]) => {
            return (
              <React.Fragment key={`fire-centre-${centreName}`}>
                <TableRow key={`fire-centre-${centreName}`}>
                  <TableCell className={classes.fireCentre} colSpan={34}>
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
                          <TableCell className={classes.planningArea} colSpan={4}>
                            {area.name}
                          </TableCell>
                          <CalculatedPlanningAreaCells
                            area={area}
                            areaName={areaName}
                            selected={selected}
                            weekliesByStationCode={props.weekliesByStationCode}
                            weekliesByUTC={props.weekliesByUTC}
                            dailiesMap={props.dailiesMap}
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
    </FireContainer>
  )
}

export default React.memo(WeeklyViewTable)
