import React, { useState } from 'react'

import { Table, TableBody, TableCell, TableHead, TableRow } from '@material-ui/core'
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
import { BACKGROUND_COLOR, fireTableStyles } from 'app/theme'
import { isEmpty, union } from 'lodash'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { getDailiesByStationCode, getZoneFromAreaName } from 'features/hfiCalculator/util'
import StickyCell from 'components/StickyCell'
import FireCentreCell from 'features/hfiCalculator/components/FireCentreCell'

export interface Props {
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  currentDay: string
  days: number
  setDays: React.Dispatch<React.SetStateAction<number>>
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
          <DayHeaders isoDate={props.currentDay} days={props.days} />
          <TableCell colSpan={2} className={classes.spaceHeader}></TableCell>
        </TableRow>
        <TableRow>
          <StickyCell left={0} zIndexOffset={12} className={classes.noBottomBorder}>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell className={classes.noBottomBorder}>
                    {/* empty cell inserted for spacing purposes (aligns with checkboxes column) */}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </StickyCell>
          <StickyCell left={50} zIndexOffset={12}>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell key="header-location" className={classes.noBottomBorder}>
                    Location
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </StickyCell>
          <TableCell key="header-elevation" className={classes.nonstickyHeaderCell}>
            Elev.
            <br />
            (m)
          </TableCell>
          <StickyCell left={234} zIndexOffset={12}>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell key="header-fuel-type" className={classes.noBottomBorder}>
                    FBP
                    <br />
                    Fuel
                    <br />
                    Type
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </StickyCell>
          <StickyCell left={284} zIndexOffset={12} className={classes.rightBorder}>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell className={classes.noBottomBorder}>
                    Grass
                    <br />
                    Cure
                    <br />
                    (%)
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </StickyCell>
          <DayIndexHeaders days={props.days} />
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
                <FireCentreCell centre={centre}></FireCentreCell>

                <TableCell className={classes.fireCentre} colSpan={28}></TableCell>
              </TableRow>
              {Object.entries(centre.planning_areas)
                .sort((a, b) =>
                  getZoneFromAreaName(a[1].name) < getZoneFromAreaName(b[1].name) ? -1 : 1
                ) // sort by zone code
                .map(([areaName, area]) => {
                  return (
                    <React.Fragment key={`zone-${areaName}`}>
                      <TableRow>
                        <TableCell
                          colSpan={42}
                          className={classes.planningAreaBorder}
                        ></TableCell>
                      </TableRow>
                      <TableRow
                        className={classes.planningArea}
                        key={`zone-${areaName}`}
                        data-testid={`zone-${areaName}`}
                      >
                        <StickyCell
                          left={0}
                          zIndexOffset={10}
                          backgroundColor={BACKGROUND_COLOR.backgroundColor}
                          colSpan={2}
                        >
                          <Table>
                            <TableBody>
                              <TableRow>
                                <TableCell className={classes.noBottomBorder}>
                                  {area.name}
                                </TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </StickyCell>
                        <TableCell
                          className={`${classes.planningArea} ${classes.nonstickyHeaderCell}`}
                        ></TableCell>
                        <StickyCell
                          left={230}
                          zIndexOffset={10}
                          className={`${classes.rightBorder} ${classes.defaultBackground}`}
                          colSpan={2}
                        >
                          <Table>
                            <TableBody>
                              <TableRow>
                                <TableCell
                                  className={`${classes.planningArea} ${classes.noBottomBorder}`}
                                ></TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </StickyCell>
                        <CalculatedPlanningAreaCells
                          area={area}
                          areaName={areaName}
                          dailies={props.dailies}
                          selected={selected}
                          planningAreaClass={classes.planningArea}
                          days={props.days}
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
                            : classes.stationCellPlainStyling

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
                              <StickyCell
                                left={284}
                                zIndexOffset={11}
                                backgroundColor={'#ffffff'}
                                className={classes.rightBorder}
                              >
                                <Table>
                                  <TableBody>
                                    <TableRow>
                                      <GrassCureCell
                                        value={
                                          !isEmpty(dailiesForStation)
                                            ? dailiesForStation[0].grass_cure_percentage
                                            : undefined
                                        }
                                        isGrassFuelType={isGrassFuelType(
                                          station.station_props
                                        )}
                                        className={`${classes.noBottomBorder}
                                    ${
                                      isRowSelected
                                        ? classes.stationCellPlainStyling
                                        : classes.unselectedStation
                                    }
                                  `}
                                        selected={isRowSelected}
                                      />
                                    </TableRow>
                                  </TableBody>
                                </Table>
                              </StickyCell>

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
