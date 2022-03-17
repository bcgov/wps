import React from 'react'

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
import { isEmpty, isUndefined, sortBy } from 'lodash'
import { getDailiesByStationCode } from 'features/hfiCalculator/util'
import StickyCell from 'components/StickyCell'
import FireCentreCell from 'features/hfiCalculator/components/FireCentreCell'
import { selectHFICalculatorState } from 'app/rootReducer'
import { useSelector } from 'react-redux'
import {
  FireStartRange,
  HFIResultResponse,
  PlanningAreaResult
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'

export interface Props {
  fireCentre: FireCentre | undefined
  testId?: string
  currentDay: string
  result: HFIResultResponse
  setSelected: (selected: number[]) => void
  setNewFireStarts: (
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStartRange
  ) => void
}

export const columnLabelsForEachDayInWeek: string[] = [
  'ROS (m/min)',
  'HFI',
  'M / FIG',
  'Fire Starts',
  'Prep Level'
]

export const weeklyTableColumnLabels = (numPrepDays: number): string[] => [
  'Location',
  'Elev. (m)',
  'FBP Fuel Type',
  'Grass Cure (%)',
  ...Array(numPrepDays).fill(columnLabelsForEachDayInWeek).flat(),
  'Highest Daily FIG',
  'Calc. Prep'
]

const useStyles = makeStyles({
  ...fireTableStyles
})

export const WeeklyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const { numPrepDays, result } = useSelector(selectHFICalculatorState)

  const stationCodeInSelected = (code: number) => {
    return result ? result.selected_station_code_ids.includes(code) : false
  }
  const toggleSelectedStation = (code: number) => {
    const selectedSet = new Set(result?.selected_station_code_ids)
    if (stationCodeInSelected(code)) {
      // remove station from selected
      selectedSet.delete(code)
    } else {
      // add station to selected
      selectedSet.add(code)
    }
    props.setSelected(Array.from(selectedSet))
  }

  return (
    <FireTable
      maxHeight={700}
      ariaLabel="weekly table view of HFI by planning area"
      testId="hfi-calc-weekly-table"
    >
      <TableHead>
        <TableRow>
          <DayHeaders isoDate={props.currentDay} numPrepDays={numPrepDays} />
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
          <DayIndexHeaders numPrepDays={numPrepDays} />
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
        {isUndefined(props.fireCentre) ? (
          <EmptyFireCentreRow colSpan={15} />
        ) : (
          <React.Fragment key={`fire-centre-${props.fireCentre.name}`}>
            <TableRow key={`fire-centre-${props.fireCentre.name}`}>
              <FireCentreCell centre={props.fireCentre}></FireCentreCell>

              <TableCell className={classes.fireCentre} colSpan={28}></TableCell>
            </TableRow>
            {sortBy(
              props.fireCentre.planning_areas,
              planningArea => planningArea.order_of_appearance_in_list
            ).map(area => {
              const areaHFIResult: PlanningAreaResult | undefined =
                result?.planning_area_hfi_results.find(
                  planningAreaResult => planningAreaResult.planning_area_id === area.id
                )

              return (
                areaHFIResult && (
                  <React.Fragment key={`zone-${area.name}`}>
                    <TableRow>
                      <TableCell
                        colSpan={42}
                        className={classes.planningAreaBorder}
                      ></TableCell>
                    </TableRow>
                    <TableRow
                      className={classes.planningArea}
                      key={`zone-${area.name}`}
                      data-testid={`zone-${area.name}`}
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
                        areaName={area.name}
                        planningAreaResult={areaHFIResult}
                        selectedStationCodes={
                          result ? result.selected_station_code_ids : []
                        }
                        setNewFireStarts={props.setNewFireStarts}
                        planningAreaClass={classes.planningArea}
                        numPrepDays={numPrepDays}
                        fireStartRanges={result ? result.fire_start_ranges : []}
                      />
                    </TableRow>
                    {sortBy(
                      area.stations,
                      station => station.order_of_appearance_in_planning_area_list
                    ).map(station => {
                      const dailiesForStation = getDailiesByStationCode(
                        numPrepDays,
                        props.result,
                        station.code
                      )
                      const isRowSelected = stationCodeInSelected(station.code)
                      const classNameForRow = !isRowSelected
                        ? classes.unselectedStation
                        : classes.stationCellPlainStyling
                      const stationCode = station.code
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
                            numPrepDays={numPrepDays}
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
              )
            })}
          </React.Fragment>
        )}
      </TableBody>
    </FireTable>
  )
}

export default React.memo(WeeklyViewTable)
