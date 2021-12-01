import React, { ReactFragment, useState } from 'react'

import { TableBody, TableCell, TableHead, TableRow, Tooltip } from '@material-ui/core'
import { createTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType, isValidGrassCure } from 'features/hfiCalculator/validation'
import { calculateMeanIntensity } from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import FireTable from 'components/FireTable'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import BaseStationAttributeCells from 'features/hfiCalculator/components/BaseStationAttributeCells'
import StatusCell from 'features/hfiCalculator/components/StatusCell'
import { BACKGROUND_COLOR, fireTableStyles } from 'app/theme'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { union } from 'lodash'
import {
  getDailiesByStationCode,
  getDailiesForArea,
  getZoneFromAreaName
} from 'features/hfiCalculator/util'
import StickyCell from 'components/StickyCell'
import FireCentreCell from 'features/hfiCalculator/components/FireCentreCell'

export interface Props {
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  testId?: string
}

export const dailyTableColumnLabels = [
  'Location',
  'Elev. (m)',
  'FBP Fuel Type',
  'Status',
  'Temp (°C)',
  'RH (%)',
  'Wind Dir (°)',
  'Wind Speed (km/h)',
  'Precip (mm)',
  'Grass Cure (%)',
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

  const errorIconTheme = createTheme({
    overrides: {
      MuiSvgIcon: {
        root: {
          fill: '#D8292F'
        }
      }
    }
  })
  const toolTipSecondLine = 'Please check WFWX or contact the forecaster.'
  const createToolTipElement = (toolTipFirstLine: string): ReactFragment => {
    return (
      <div>
        {toolTipFirstLine} <br />
        {toolTipSecondLine}
      </div>
    )
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
    <FireTable
      maxHeight={700}
      ariaLabel="daily table view of HFI by planning area"
      testId="hfi-calc-daily-table"
    >
      <TableHead>
        <TableRow>
          <StickyCell left={0} zIndexOffset={12}>
            <TableCell className={classes.noBottomBorder}>
              {/* empty cell inserted for spacing purposes (aligns with checkboxes column) */}
            </TableCell>
          </StickyCell>
          <StickyCell left={50} zIndexOffset={12} className={classes.stationLocation}>
            <TableCell key="header-location" className={classes.noBottomBorder}>
              Location
            </TableCell>
          </StickyCell>
          <TableCell key="header-elevation" className={classes.nonstickyHeaderCell}>
            Elev.
            <br />
            (m)
          </TableCell>
          <StickyCell left={230} zIndexOffset={12} className={classes.rightBorder}>
            <TableCell key="header-fuel-type" className={classes.noBottomBorder}>
              FBP
              <br />
              Fuel
              <br />
              Type
            </TableCell>
          </StickyCell>
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
          <TableCell>
            Grass
            <br />
            Cure
            <br />
            (%)
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
        {Object.entries(props.fireCentres).map(([centreName, centre]) => {
          return (
            <React.Fragment key={`fire-centre-${centreName}`}>
              <TableRow key={`fire-centre-${centreName}`}>
                <FireCentreCell centre={centre}></FireCentreCell>
                <TableCell className={classes.fireCentre} colSpan={25}></TableCell>
              </TableRow>
              {Object.entries(centre.planning_areas)
                .sort((a, b) =>
                  getZoneFromAreaName(a[1].name) < getZoneFromAreaName(b[1].name) ? -1 : 1
                ) // sort by zone code
                .map(([areaName, area]) => {
                  const areaDailies = getDailiesForArea(area, props.dailies, selected)
                  const meanIntensityGroup = calculateMeanIntensity(areaDailies)
                  return (
                    <React.Fragment key={`zone-${areaName}`}>
                      <TableRow
                        className={classes.planningArea}
                        key={`zone-${areaName}`}
                        data-testid={`zone-${areaName}`}
                      >
                        <StickyCell
                          left={0}
                          zIndexOffset={10}
                          colSpan={3}
                          backgroundColor={BACKGROUND_COLOR.backgroundColor}
                        >
                          <TableCell className={classes.noBottomBorder}>
                            {area.name}
                          </TableCell>
                        </StickyCell>
                        <TableCell
                          colSpan={19}
                          className={classes.planningArea}
                        ></TableCell>
                        <MeanIntensityGroupRollup
                          area={area}
                          dailies={areaDailies}
                          selectedStations={selected}
                          meanIntensityGroup={meanIntensityGroup}
                        ></MeanIntensityGroupRollup>
                        <FireStartsCell areaName={areaName} />
                        <PrepLevelCell
                          testid={`daily-prep-level-${areaName}`}
                          meanIntensityGroup={meanIntensityGroup}
                          areaName={areaName}
                        />
                      </TableRow>
                      {Object.entries(area.stations)
                        .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                        .map(([stationCode, station]) => {
                          const daily = getDailiesByStationCode(
                            props.dailies,
                            station.code
                          )[0]
                          const grassCureError = !isValidGrassCure(
                            daily,
                            station.station_props
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
                                isDailyTable={true}
                              />
                              {daily?.observation_valid === false ? (
                                <TableCell className={classNameForRow}>
                                  <ThemeProvider theme={errorIconTheme}>
                                    <Tooltip
                                      title={createToolTipElement(
                                        daily?.observation_valid_comment
                                      )}
                                    >
                                      <ErrorOutlineIcon
                                        data-testid={`status-error`}
                                      ></ErrorOutlineIcon>
                                    </Tooltip>
                                  </ThemeProvider>
                                </TableCell>
                              ) : (
                                <StatusCell
                                  className={classNameForRow}
                                  value={daily?.status}
                                />
                              )}
                              <TableCell className={classNameForRow}>
                                {daily?.temperature}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.relative_humidity}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.wind_direction?.toFixed(0).padStart(3, '0')}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.wind_speed}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.precipitation}
                              </TableCell>
                              <GrassCureCell
                                value={daily?.grass_cure_percentage}
                                isGrassFuelType={isGrassFuelType(station.station_props)}
                                className={classNameForRow}
                                selected={isRowSelected}
                              ></GrassCureCell>
                              <TableCell className={classNameForRow}>
                                {daily?.ffmc?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.dmc?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.dc?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.isi?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.bui?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.fwi?.toFixed(DECIMAL_PLACES)}
                              </TableCell>
                              <TableCell className={classNameForRow}>
                                {daily?.danger_class}
                              </TableCell>
                              <CalculatedCell
                                testid={`${daily?.code}-ros`}
                                value={daily?.rate_of_spread?.toFixed(DECIMAL_PLACES)}
                                error={grassCureError}
                                className={classNameForRow}
                              ></CalculatedCell>
                              <CalculatedCell
                                testid={`${daily?.code}-hfi`}
                                value={daily?.hfi?.toFixed(DECIMAL_PLACES)}
                                error={grassCureError}
                                className={classNameForRow}
                              ></CalculatedCell>
                              <CalculatedCell
                                testid={`${daily?.code}-1-hr-size`}
                                value={daily?.sixty_minute_fire_size?.toFixed(
                                  DECIMAL_PLACES
                                )}
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

export default React.memo(DailyViewTable)
