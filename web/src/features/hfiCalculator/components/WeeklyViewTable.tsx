import React from 'react'

import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'
import { FireCentre, FuelType } from 'api/hfiCalculatorAPI'
import FireTable from 'components/FireTable'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import DayIndexHeaders from 'features/hfiCalculator/components/DayIndexHeaders'
import CalculatedPlanningAreaCells from 'features/hfiCalculator/components/CalculatedPlanningAreaCells'
import { StaticCells } from 'features/hfiCalculator/components/StaticCells'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'
import { BACKGROUND_COLOR } from 'app/theme'
import { isEmpty, isUndefined, sortBy } from 'lodash'
import {
  calculateNumPrepDays,
  getDailiesByStationCode,
  stationCodeSelected,
  getSelectedFuelType
} from 'features/hfiCalculator/util'
import StickyCell from 'components/StickyCell'
import FireCentreCell from 'features/hfiCalculator/components/FireCentreCell'
import { selectAuthentication, selectHFICalculatorState, selectHFIReadyState } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { FireStartRange, PlanningAreaResult, PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { FireCentrePlanningAreaHeaderRowCell } from 'features/hfiCalculator/components/HeaderRowCell'
import { StationDataHeaderCells } from 'features/hfiCalculator/components/StationDataHeaderCells'
// import { ROLES } from 'features/auth/roles'
import PlanningAreaReadyToggle from 'features/hfiCalculator/components/PlanningAreaReadyToggle'
import { AppDispatch } from 'app/store'
import { fetchToggleReadyState } from 'features/hfiCalculator/slices/hfiReadySlice'
import {
  NoBottomBorderCell,
  PlanningAreaHeaderRowCell,
  PlanningAreaTableCellNoBottomBorder,
  PlanningAreaTableCellNonSticky,
  PlanningAreaTableRow,
  SectionSeparatorBorderTableCell,
  SpaceHeaderTableCell,
  StationPlainStylingRow,
  StickyCellNoBottomBorder,
  StickyCellRightBorderDefaultBackground,
  UnSelectedTableRow
} from 'features/hfiCalculator/components/StyledPlanningAreaComponents'

export interface Props {
  fireCentre: FireCentre | undefined
  testId?: string
  dateRange?: PrepDateRange
  setSelected: (planningAreaId: number, code: number, selected: boolean) => void
  setNewFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStartRange) => void
  setFuelType: (planningAreaId: number, code: number, fuelTypeId: number) => void
  fuelTypes: FuelType[]
}

export const WeeklyViewTable = (props: Props): JSX.Element => {
  const dispatch: AppDispatch = useDispatch()

  const { result } = useSelector(selectHFICalculatorState)
  const { /* roles, */ isAuthenticated } = useSelector(selectAuthentication)
  const { loading, planningAreaReadyDetails } = useSelector(selectHFIReadyState)

  const toggleReady = (planningAreaId: number) => {
    if (!isUndefined(result) && !isUndefined(result.date_range)) {
      dispatch(fetchToggleReadyState(result.selected_fire_center_id, planningAreaId, result.date_range))
    }
  }

  const stationCodeInSelected = (planningAreaId: number, code: number): boolean => {
    if (isUndefined(result) || isUndefined(result?.planning_area_station_info)) {
      return false
    }
    return stationCodeSelected(result.planning_area_station_info, planningAreaId, code)
  }
  const toggleSelectedStation = (planningAreaId: number, code: number) => {
    const selected = stationCodeInSelected(planningAreaId, code)
    props.setSelected(planningAreaId, code, !selected)
  }

  const numPrepDays = calculateNumPrepDays(props.dateRange)

  if (isUndefined(result)) {
    return <React.Fragment></React.Fragment>
  }

  return (
    <FireTable ariaLabel="weekly table view of HFI by planning area" testId="hfi-calc-weekly-table">
      <TableHead>
        <TableRow>
          <DayHeaders dateRange={props.dateRange} />
          <SpaceHeaderTableCell colSpan={2}></SpaceHeaderTableCell>
        </TableRow>
        <TableRow>
          <StickyCellNoBottomBorder left={0} zIndexOffset={12}>
            <Table>
              <TableBody>
                <TableRow>
                  <NoBottomBorderCell>
                    {/* empty cell inserted for spacing purposes (aligns with checkboxes column) */}
                  </NoBottomBorderCell>
                </TableRow>
              </TableBody>
            </Table>
          </StickyCellNoBottomBorder>
          <StationDataHeaderCells />
          <DayIndexHeaders numPrepDays={numPrepDays} />
          <SectionSeparatorBorderTableCell>
            Highest
            <br />
            Daily
            <br />
            FIG
          </SectionSeparatorBorderTableCell>
          <TableCell>
            Calc.
            <br />
            Prep
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody sx={{ overflowX: 'auto', width: '100%' }}>
        {isUndefined(props.fireCentre) ? (
          <EmptyFireCentreRow colSpan={15} />
        ) : (
          <React.Fragment key={`fire-centre-${props.fireCentre.name}`}>
            <TableRow key={`fire-centre-${props.fireCentre.name}`}>
              <FireCentreCell centre={props.fireCentre}></FireCentreCell>
              <FireCentrePlanningAreaHeaderRowCell />
            </TableRow>
            {sortBy(props.fireCentre.planning_areas, planningArea => planningArea.order_of_appearance_in_list).map(
              area => {
                const areaHFIResult: PlanningAreaResult | undefined = result.planning_area_hfi_results.find(
                  planningAreaResult => planningAreaResult.planning_area_id === area.id
                )

                return (
                  areaHFIResult && (
                    <React.Fragment key={`zone-${area.name}`}>
                      <TableRow>
                        <PlanningAreaHeaderRowCell />
                      </TableRow>
                      <PlanningAreaTableRow key={`zone-${area.name}`} data-testid={`zone-${area.name}`}>
                        <StickyCell
                          left={0}
                          zIndexOffset={10}
                          backgroundColor={BACKGROUND_COLOR.backgroundColor}
                          colSpan={2}
                        >
                          <Table>
                            <TableBody>
                              <TableRow>
                                <NoBottomBorderCell>
                                  {area.name}
                                  <PlanningAreaReadyToggle
                                    enabled={/* roles.includes(ROLES.HFI.SET_READY_STATE) && */ isAuthenticated}
                                    loading={loading}
                                    readyDetails={planningAreaReadyDetails[area.id]}
                                    toggleReady={toggleReady}
                                  />
                                </NoBottomBorderCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </StickyCell>
                        <PlanningAreaTableCellNonSticky></PlanningAreaTableCellNonSticky>
                        <StickyCellRightBorderDefaultBackground left={227} zIndexOffset={10} colSpan={2}>
                          <Table>
                            <TableBody>
                              <TableRow>
                                <PlanningAreaTableCellNoBottomBorder></PlanningAreaTableCellNoBottomBorder>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </StickyCellRightBorderDefaultBackground>
                        <CalculatedPlanningAreaCells
                          area={area}
                          areaName={area.name}
                          planningAreaResult={areaHFIResult}
                          setNewFireStarts={props.setNewFireStarts}
                          numPrepDays={numPrepDays}
                          fireStartsEnabled={/* roles.includes(ROLES.HFI.SET_FIRE_STARTS) && */ isAuthenticated}
                          fireStartRanges={result.fire_start_ranges}
                          fuelTypes={props.fuelTypes}
                          planningAreaStationInfo={result.planning_area_station_info}
                        />
                      </PlanningAreaTableRow>
                      {sortBy(area.stations, station => station.order_of_appearance_in_planning_area_list).map(
                        station => {
                          const dailiesForStation = getDailiesByStationCode(result, station.code, area.id)
                          const isRowSelected = stationCodeInSelected(area.id, station.code)
                          const stationCode = station.code
                          const selectedFuelType = getSelectedFuelType(
                            result.planning_area_station_info,
                            area.id,
                            stationCode,
                            props.fuelTypes
                          )
                          if (isUndefined(selectedFuelType)) {
                            return <React.Fragment key={`weekly-undefined-fuel-type-${station.code}`}></React.Fragment>
                          }
                          const TableRowComponent = !isRowSelected ? UnSelectedTableRow : StationPlainStylingRow
                          return (
                            <TableRowComponent key={`station-${stationCode}`}>
                              <BaseStationAttributeCells
                                station={station}
                                planningAreaId={area.id}
                                selectStationEnabled={/* roles.includes(ROLES.HFI.SELECT_STATION) && */ isAuthenticated}
                                isSetFuelTypeEnabled={/* roles.includes(ROLES.HFI.SET_FUEL_TYPE) && */ isAuthenticated}
                                stationCodeInSelected={stationCodeInSelected}
                                toggleSelectedStation={toggleSelectedStation}
                                grassCurePercentage={
                                  !isEmpty(dailiesForStation) ? dailiesForStation[0].grass_cure_percentage : undefined
                                }
                                setFuelType={props.setFuelType}
                                fuelTypes={props.fuelTypes}
                                selectedFuelType={selectedFuelType}
                                isRowSelected={isRowSelected}
                              />
                              <StaticCells
                                numPrepDays={numPrepDays}
                                dailies={dailiesForStation}
                                station={station}
                                isRowSelected={isRowSelected}
                                selectedFuelType={selectedFuelType}
                              />
                            </TableRowComponent>
                          )
                        }
                      )}
                    </React.Fragment>
                  )
                )
              }
            )}
          </React.Fragment>
        )}
      </TableBody>
    </FireTable>
  )
}

export default React.memo(WeeklyViewTable)
