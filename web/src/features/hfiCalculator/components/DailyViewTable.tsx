import React from 'react'
import { Table, TableBody, TableCell, TableHead, TableRow, Tooltip } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { useSelector } from 'react-redux'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { FireCentre, FuelType, StationDaily } from 'api/hfiCalculatorAPI'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import FireTable from 'components/FireTable'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'
import StatusCell from 'features/hfiCalculator/components/StatusCell'
import { BACKGROUND_COLOR, fireTableStyles } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { getDailiesByStationCode, getSelectedFuelType, stationCodeSelected } from 'features/hfiCalculator/util'
import StickyCell from 'components/StickyCell'
import FireCentreCell from 'features/hfiCalculator/components/FireCentreCell'
import { selectAuthentication, selectHFICalculatorState } from 'app/rootReducer'
import { DateTime } from 'luxon'
import { isUndefined, sortBy } from 'lodash'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import { DailyResult, PlanningAreaResult, StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { RequiredDataCell } from 'features/hfiCalculator/components/RequiredDataCell'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { DailyHFICell } from 'features/hfiCalculator/components/DailyHFICell'
import { StationDataHeaderCells } from 'features/hfiCalculator/components/StationDataHeaderCells'
import { ROLES } from 'features/auth/roles'

export interface Props {
  fireCentre: FireCentre | undefined
  setSelected: (planningAreaId: number, code: number, selected: boolean) => void
  setFuelType: (planningAreaId: number, code: number, fuelTypeId: number) => void
  testId?: string
  fuelTypes: FuelType[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
}

type KeyTooltipDecimalPlacesTuple = [keyof StationDaily, string, number?]

export const dailyTableColumnLabels = [
  'Location',
  'Elev. (m)',
  'FBP Fuel Type',
  'Grass Cure (%)',
  'Status',
  'Temp (°C)',
  'RH (%)',
  'Wind Dir (°)',
  'Wind Speed (km/h)',
  'Precip (mm)',
  'FFMC',
  'DMC',
  'DC',
  'ISI',
  'BUI',
  'FWI',
  'DGR CL',
  'ROS (m/min)',
  'HFI',
  '60 min fire size (ha)',
  'Fire Type',
  'M/FIG',
  'Fire Starts',
  'Prep Level'
]

const useStyles = makeStyles({
  ...fireTableStyles
})

export const DailyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const { selectedPrepDate, result } = useSelector(selectHFICalculatorState)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)

  const getDailyForDay = (stationCode: number): StationDaily | undefined => {
    const dailiesForStation = getDailiesByStationCode(result, stationCode)
    if (selectedPrepDate != '') {
      const selectedPrepDateObject = DateTime.fromISO(selectedPrepDate)
      return dailiesForStation.filter(daily => {
        const dailyDate = daily.date
        return (
          dailyDate.year === selectedPrepDateObject.year &&
          dailyDate.month === selectedPrepDateObject.month &&
          dailyDate.day === selectedPrepDateObject.day
        )
      })[0]
    }
    return dailiesForStation[0]
  }

  const getDailyResult = (planningAreaHFIResult: PlanningAreaResult | undefined): DailyResult | undefined => {
    return planningAreaHFIResult?.daily_results.find(dailyResult => {
      const dailyResultDate = dailyResult.date
      const selectedPrepDateObject = DateTime.fromISO(selectedPrepDate)
      return (
        dailyResultDate.year === selectedPrepDateObject.year &&
        dailyResultDate.month === selectedPrepDateObject.month &&
        dailyResultDate.day === selectedPrepDateObject.day
      )
    })
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

  return (
    <FireTable maxHeight={700} ariaLabel="daily table view of HFI by planning area" testId="hfi-calc-daily-table">
      <TableHead>
        <TableRow>
          <StickyCell left={0} zIndexOffset={12}>
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
          <StationDataHeaderCells />
          <TableCell>Status</TableCell>
          <TableCell>
            Temp
            <br />
            (&deg;C)
          </TableCell>
          <TableCell>
            RH
            <br />
            (%)
          </TableCell>
          <TableCell>
            Wind
            <br />
            Dir
            <br />
            (&deg;)
          </TableCell>
          <TableCell>
            Wind
            <br />
            Speed
            <br />
            (km/h)
          </TableCell>
          <TableCell>
            Precip
            <br />
            (mm)
          </TableCell>
          <TableCell>FFMC</TableCell>
          <TableCell>DMC</TableCell>
          <TableCell>DC</TableCell>
          <TableCell>ISI</TableCell>
          <TableCell>BUI</TableCell>
          <TableCell>FWI</TableCell>
          <TableCell>
            DGR
            <br />
            CL
          </TableCell>
          <TableCell>
            ROS
            <br />
            (m/min)
          </TableCell>
          <TableCell>HFI</TableCell>
          <TableCell>
            60 min <br />
            fire size <br />
            (hectares)
          </TableCell>
          <TableCell>
            Fire
            <br />
            Type
            <Tooltip
              title={typeToolTipElement}
              aria-label={`${typeToolTipFirstLine} \n ${typeToolTipSecondLine} \n ${typeToolTipThirdLine}`}
            >
              <InfoOutlinedIcon style={{ fill: '#1A5A96' }}></InfoOutlinedIcon>
            </Tooltip>
          </TableCell>
          <TableCell>
            M /
            <br />
            FIG
          </TableCell>
          <TableCell>
            Fire
            <br />
            Starts
          </TableCell>
          <TableCell>
            Prep
            <br />
            Level
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {isUndefined(props.fireCentre) ? (
          <EmptyFireCentreRow colSpan={6} />
        ) : (
          <React.Fragment key={`fire-centre-${props.fireCentre.name}`}>
            <TableRow key={`fire-centre-${props.fireCentre.name}`}>
              <FireCentreCell centre={props.fireCentre}></FireCentreCell>
              <TableCell className={classes.fireCentre} colSpan={25}></TableCell>
            </TableRow>
            {sortBy(props.fireCentre.planning_areas, planningArea => planningArea.order_of_appearance_in_list).map(
              area => {
                const planningAreaResult = result?.planning_area_hfi_results.find(
                  areaResult => areaResult.planning_area_id === area.id
                )
                const dailyResult = getDailyResult(planningAreaResult)
                return (
                  <React.Fragment key={`zone-${area.name}`}>
                    <TableRow>
                      <TableCell colSpan={42} className={classes.planningAreaBorder}></TableCell>
                    </TableRow>
                    <TableRow
                      className={classes.planningArea}
                      key={`zone-${area.name}`}
                      data-testid={`zone-${area.name}`}
                    >
                      <StickyCell
                        left={0}
                        zIndexOffset={10}
                        colSpan={3}
                        backgroundColor={BACKGROUND_COLOR.backgroundColor}
                      >
                        <Table>
                          <TableBody>
                            <TableRow>
                              <TableCell className={classes.noBottomBorder}>{area.name}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </StickyCell>
                      <TableCell colSpan={19} className={classes.planningArea}></TableCell>
                      <MeanIntensityGroupRollup
                        area={area}
                        dailies={dailyResult ? dailyResult.dailies.map(validatedDaily => validatedDaily.daily) : []}
                        meanIntensityGroup={dailyResult?.mean_intensity_group}
                        fuelTypes={props.fuelTypes}
                        planningAreaStationInfo={props.planningAreaStationInfo}
                      ></MeanIntensityGroupRollup>
                      <FireStartsCell areaName={area.name} fireStarts={dailyResult?.fire_starts} />
                      <PrepLevelCell
                        testid={`daily-prep-level-${area.id}`}
                        toolTipText=" Incomplete data from WFWX for one or more stations. Please exclude station(s) displaying errors."
                        prepLevel={dailyResult?.prep_level}
                      />
                    </TableRow>
                    {sortBy(area.stations, station => station.order_of_appearance_in_planning_area_list).map(
                      station => {
                        if (isUndefined(result)) {
                          return <React.Fragment></React.Fragment>
                        }
                        const daily = getDailyForDay(station.code)
                        const selectedFuelType = getSelectedFuelType(
                          result.planning_area_station_info,
                          area.id,
                          station.code,
                          props.fuelTypes
                        )
                        if (isUndefined(selectedFuelType)) {
                          return <React.Fragment></React.Fragment>
                        }
                        const grassCureError = !isValidGrassCure(daily, selectedFuelType)
                        const isRowSelected = !isUndefined(area) && stationCodeInSelected(area.id, station.code)
                        const classNameForRow = !isRowSelected ? classes.unselectedStation : undefined
                        return (
                          <TableRow className={classNameForRow} key={`station-${station.code}`}>
                            <BaseStationAttributeCells
                              station={station}
                              planningAreaId={area.id}
                              className={classNameForRow}
                              selectStationEnabled={roles.includes(ROLES.HFI.SELECT_STATION) && isAuthenticated}
                              isSetFuelTypeEnabled={roles.includes(ROLES.HFI.SET_FUEL_TYPE) && isAuthenticated}
                              stationCodeInSelected={stationCodeInSelected}
                              toggleSelectedStation={toggleSelectedStation}
                              isDailyTable={true}
                              grassCurePercentage={daily?.grass_cure_percentage}
                              setFuelType={props.setFuelType}
                              fuelTypes={props.fuelTypes}
                              selectedFuelType={selectedFuelType}
                              isRowSelected={isRowSelected}
                            />

                            <StatusCell daily={daily} className={classNameForRow} isRowSelected={isRowSelected} />
                            {[
                              [
                                'temperature' as keyof StationDaily,
                                'Temperature cannot be null. Impacts DMC, BUI, ROS, HFI, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'relative_humidity' as keyof StationDaily,
                                'RH cannot be null. Impacts FFMC, ISI, ROS, HFI, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple
                            ].map(([key, tooltip, _decimalPlaces]) => {
                              return (
                                <RequiredDataCell
                                  key={key.toString()}
                                  classNameForRow={classNameForRow}
                                  dailyKey={key}
                                  daily={daily}
                                  errorToolTipText={tooltip}
                                  decimalPlaces={_decimalPlaces}
                                />
                              )
                            })}

                            <TableCell className={classNameForRow}>
                              {daily?.wind_direction?.toFixed(0).padStart(3, '0')}
                            </TableCell>

                            {[
                              [
                                'wind_speed' as keyof StationDaily,
                                'Wind speed cannot be null. Impacts FFMC, ISI, ROS, HFI, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'precipitation' as keyof StationDaily,
                                'Precipitation cannot be null. Impacts DC, BUI, ROS, HFI, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'ffmc' as keyof StationDaily,
                                'FFMC cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'dmc' as keyof StationDaily,
                                'DMC cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'dc' as keyof StationDaily,
                                'DC cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'isi' as keyof StationDaily,
                                'ISI cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'bui' as keyof StationDaily,
                                'BUI cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple,
                              [
                                'fwi' as keyof StationDaily,
                                'FWI cannot be null. Impacts ROS, HFI, Fire Type, FIG, Prep calculations.'
                              ] as KeyTooltipDecimalPlacesTuple
                            ].map(([key, tooltip, _decimalPlaces]) => {
                              return (
                                <RequiredDataCell
                                  key={key.toString()}
                                  classNameForRow={classNameForRow}
                                  dailyKey={key}
                                  daily={daily}
                                  errorToolTipText={tooltip}
                                  decimalPlaces={_decimalPlaces}
                                />
                              )
                            })}

                            <TableCell className={classNameForRow}>{daily?.danger_class}</TableCell>
                            <CalculatedCell
                              testid={`${daily?.code}-ros`}
                              value={daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
                              error={grassCureError}
                              className={classNameForRow}
                            ></CalculatedCell>
                            <DailyHFICell
                              testid={`${daily?.code}-hfi`}
                              value={daily?.hfi?.toFixed(DECIMAL_PLACES)}
                              error={grassCureError}
                              className={classNameForRow}
                            ></DailyHFICell>
                            <CalculatedCell
                              testid={`${daily?.code}-1-hr-size`}
                              value={daily?.sixty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                              error={grassCureError}
                              className={classNameForRow}
                            ></CalculatedCell>
                            <CalculatedCell
                              testid={`${daily?.code}-fire-type`}
                              value={daily?.fire_type}
                              error={grassCureError}
                              className={classNameForRow}
                            ></CalculatedCell>
                            <IntensityGroupCell
                              testid={`${daily?.code}-intensity-group`}
                              value={daily?.intensity_group}
                              error={grassCureError}
                              selected={isRowSelected}
                            ></IntensityGroupCell>
                            <TableCell colSpan={2}>
                              {/* empty cell for spacing (Fire Starts & Prev Level columns) */}
                            </TableCell>
                          </TableRow>
                        )
                      }
                    )}
                  </React.Fragment>
                )
              }
            )}
          </React.Fragment>
        )}
      </TableBody>
    </FireTable>
  )
}

export default React.memo(DailyViewTable)
