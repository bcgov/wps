import React, { ReactFragment, useState } from 'react'

import {
  Checkbox,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography
} from '@material-ui/core'
import { createTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { Button } from 'components'
import GrassCureCell from 'features/hfiCalculator/components/GrassCureCell'
import { isGrassFuelType, isValidGrassCure } from 'features/hfiCalculator/validation'
import { calculateMeanIntensityGroup } from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import { forEach, isUndefined } from 'lodash'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import FireTable from 'components/FireTable'
import FireContainer from 'components/FireDisplayContainer'
import { DateTime } from 'luxon/src/datetime'
import { getPrepStartAndEnd } from 'utils/date'

export interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  weekliesMap: Map<number, StationDaily[]>
  currentDay: string
  testId?: string
}

const prepLevelColours: { [description: string]: string } = {
  green: '#A0CD63',
  blue: '#4CAFEA',
  yellow: '#FFFD54',
  orange: '#F6C142',
  brightRed: '#EA3223',
  bloodRed: '#B02318'
}

const useStyles = makeStyles({
  fireCentre: {
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#dbd9d9'
  },
  planningArea: {
    backgroundColor: 'rgba(40, 53, 147, 0.05)',
    width: '100%'
  },
  fireStarts: {
    fontWeight: 'bold',
    textAlign: 'center'
  },
  unselectedStation: {
    color: 'rgba(0,0,0,0.54)'
  },
  controls: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'baseline'
  },
  prepLevel1: {
    background: prepLevelColours.green,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel2: {
    background: prepLevelColours.blue,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel3: {
    background: prepLevelColours.yellow,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel4: {
    background: prepLevelColours.orange,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel5: {
    background: prepLevelColours.brightRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  },
  prepLevel6: {
    background: prepLevelColours.bloodRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  },
  dayHeader: {
    borderLeft: '2px solid grey',
    textAlign: 'center'
  }
})

export const DailyViewTable = (props: Props): JSX.Element => {
  const classes = useStyles()

  const stationCodesList: number[] = []

  const datesList: DateTime[] = []
  // Object.entries(props.weekliesMap).forEach(station => {
  //   console.log('Station: ' + station)
  //   station.forEach(daily => {
  //     console.log('Daily: ' + daily)
  //     datesList.push(daily.date)
  //   })
  // })
  props.weekliesMap.forEach(value => {
    for (let i = 0; i < value.length; i++) {
      if (!datesList.includes(value[i].date)) {
        datesList.push(value[i].date)
      }
    }
  })

  const dates = new Set(datesList)
  console.log(datesList)

  const [selected, setSelected] = useState<number[]>(stationCodesList)

  const DECIMAL_PLACES = 1

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

  const formatPrepLevelByValue = (prepLevel: number | undefined) => {
    switch (prepLevel) {
      case 1:
        return classes.prepLevel1
      case 2:
        return classes.prepLevel2
      case 3:
        return classes.prepLevel3
      case 4:
        return classes.prepLevel4
      case 5:
        return classes.prepLevel5
      case 6:
        return classes.prepLevel6
      default:
        return
    }
  }

  const calculatePrepLevel = (meanIntensityGroup: number | undefined) => {
    // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
    if (isUndefined(meanIntensityGroup)) {
      return undefined
    }
    if (meanIntensityGroup < 3) {
      return 1
    }
    if (meanIntensityGroup < 4) {
      return 2
    }
    if (meanIntensityGroup < 5) {
      return 3
    }
    return 4
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

  const getDayName = (dateStr: string, locale: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(locale, { weekday: 'long' })
  }
  const day = getDayName(props.currentDay, 'en-CA')

  // TODO: horrible hack! do this the right way!!!!
  const startAndEnd = getPrepStartAndEnd(props.currentDay + 'T00:00:00-07:00')
  const startDate = startAndEnd.start
  console.log('startDate', startDate)
  const dayHeaders = []
  const days: Array<DateTime> = []
  for (let i = 0; i <= 5; ++i) {
    const date = startDate.plus({ days: i })
    dayHeaders.push(
      <TableCell colSpan={5} className={classes.dayHeader} key={i}>
        {date.toJSDate().toLocaleDateString('en-CA', { weekday: 'long' })}
      </TableCell>
    )
    days.push(date)
  }
  const cellHeaders = []

  for (let i = 0; i < 5; i++) {
    cellHeaders.push(
      <TableCell style={{ borderLeft: 'solid 2px grey' }}>
        ROS
        <br />
        (m/min)
      </TableCell>
    )
    cellHeaders.push(<TableCell>HFI</TableCell>)
    cellHeaders.push(
      <TableCell>
        M /
        <br />
        FIG
      </TableCell>
    )
    cellHeaders.push(
      <TableCell>
        Fire
        <br />
        Starts
      </TableCell>
    )
    cellHeaders.push(
      <TableCell>
        Prep
        <br />
        Level
      </TableCell>
    )
  }

  return (
    <FireContainer testId={props.testId}>
      <div className={classes.controls}>
        <Typography component="div" variant="subtitle2">
          {props.title}
        </Typography>
      </div>
      <FireTable
        maxHeight={700}
        ariaLabel="weekly table view of HFI by planning area"
        testId="hfi-calc-weekly-table"
      >
        <TableHead>
          <TableRow>
            <TableCell colSpan={5}></TableCell>
            {dayHeaders.map(cell => cell)}
            <TableCell colSpan={2}></TableCell>
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
            {cellHeaders}
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
                    const meanIntensityGroup = calculateMeanIntensityGroup(
                      area,
                      props.dailiesMap,
                      selected
                    )
                    const prepLevel = calculatePrepLevel(meanIntensityGroup)
                    return (
                      <React.Fragment key={`zone-${areaName}`}>
                        <TableRow
                          className={classes.planningArea}
                          key={`zone-${areaName}`}
                          data-testid={`zone-${areaName}`}
                        >
                          <TableCell className={classes.planningArea} colSpan={27}>
                            {area.name}
                          </TableCell>
                          <MeanIntensityGroupRollup
                            area={area}
                            dailiesMap={props.dailiesMap}
                            selectedStations={selected}
                          ></MeanIntensityGroupRollup>
                          <TableCell
                            className={classes.fireStarts}
                            data-testid={`weekly-fire-starts-${areaName}`}
                          >
                            {/* using a fixed value of 0-1 Fire Starts for now */}
                            0-1
                          </TableCell>
                          <TableCell
                            className={formatPrepLevelByValue(prepLevel)}
                            data-testid={`weekly-prep-level-${areaName}`}
                          >
                            {prepLevel}
                          </TableCell>
                        </TableRow>
                        {Object.entries(area.stations)
                          .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                          .map(([stationCode, station]) => {
                            const dailies = props.weekliesMap.get(station.code)
                            const isRowSelected = stationCodeInSelected(station.code)
                            const classNameForRow = !isRowSelected
                              ? classes.unselectedStation
                              : undefined
                            return (
                              <TableRow
                                className={classNameForRow}
                                key={`station-${stationCode}`}
                              >
                                <Checkbox
                                  checked={stationCodeInSelected(station.code)}
                                  onClick={() => toggleSelectedStation(station.code)}
                                  data-testid={`select-station-${station.code}`}
                                  color="primary"
                                ></Checkbox>
                                <TableCell
                                  key={`station-${station.code}-name`}
                                  className={classNameForRow}
                                >
                                  {station.station_props.name} ({station.code})
                                </TableCell>
                                <TableCell
                                  key={`station-${station.code}-elevation`}
                                  className={classNameForRow}
                                >
                                  {station.station_props.elevation}
                                </TableCell>
                                <TableCell
                                  key={`station-${station.code}-fuel-type`}
                                  className={classNameForRow}
                                >
                                  {station.station_props.fuel_type.abbrev}
                                </TableCell>

                                {dailies?.map(daily => {
                                  const grassCureError = !isValidGrassCure(
                                    daily,
                                    station.station_props
                                  )
                                  return (
                                    <div key={daily.code}>
                                      <GrassCureCell
                                        value={daily?.grass_cure_percentage}
                                        isGrassFuelType={isGrassFuelType(
                                          station.station_props
                                        )}
                                        className={classNameForRow}
                                        selected={isRowSelected}
                                      ></GrassCureCell>
                                      {Array.from(props.weekliesMap.values()).map(
                                        value => {
                                          console.log(value)
                                        }
                                      )}
                                      {days.map(day => {
                                        // the surrounding loop is wrong!
                                        return (
                                          <TableCell key={day.toMillis()} colSpan={5}>
                                            Happy stuff
                                          </TableCell>
                                        )
                                        // const aRecord = getMeMyDay(day, myListOfDatesForThisStation)
                                        // if (aRecord === null) {
                                        //   return (<TableCell key={day.toMillis()} colSpan={5}>Empy</TableCell>)
                                        // } else {
                                        //   return (
                                        //     <TableCell key={day.toMillis()} colSpan={5}>
                                        //       Happy stuff
                                        //     </TableCell>
                                        //   )
                                        // }
                                      })}
                                      {/*{props.weekliesMap.forEach((value, key) => {
                                        console.log(key + ' ' + value)
                                        for (let i = 0; i < value.length; i++) {
                                          ;<div>
                                            <CalculatedCell
                                              testid={`${value[i].code}-ros`}
                                              value={value[i].rate_of_spread?.toFixed(
                                                DECIMAL_PLACES
                                              )}
                                              error={grassCureError}
                                              className={classNameForRow}
                                            ></CalculatedCell>
                                            <CalculatedCell
                                              testid={`${value[i].code}-hfi`}
                                              value={value[i].hfi?.toFixed(
                                                DECIMAL_PLACES
                                              )}
                                              error={grassCureError}
                                              className={classNameForRow}
                                            ></CalculatedCell>
                                            <IntensityGroupCell
                                              testid={`${value[i].code}-intensity-group`}
                                              value={value[i].intensity_group}
                                              error={grassCureError}
                                              selected={isRowSelected}
                                            ></IntensityGroupCell>
                                            <TableCell colSpan={2}>
                                              
                                            </TableCell>
                                          </div>
                                        }
                                      })} */}
                                    </div>
                                  )
                                })}
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

export default React.memo(DailyViewTable)
