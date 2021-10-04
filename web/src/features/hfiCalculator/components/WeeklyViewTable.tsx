import React, { useState } from 'react'

import {
  Checkbox,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import FireTable from 'components/FireTable'
import FireContainer from 'components/FireDisplayContainer'
import { calculateMultipleMeanIntensityGroups } from '../multipleMeanIntensity'
import { buildWeeklyDates } from '../util'
import { calculatePrepLevel, PrepLevel } from 'features/hfiCalculator/prepLevel'
import { createCells } from 'features/hfiCalculator/cells'
import DayHeaders from 'features/hfiCalculator/components/DayHeaders'
import CellHeaders from 'features/hfiCalculator/components/CellHeaders'

export interface Props {
  title: string
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  weekliesMap: Map<number, StationDaily[]>
  weekliesMapDates: Map<Date, StationDaily[]>
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

  const stationCodesList: number[] = Array.from(props.dailiesMap.keys())

  const dates = buildWeeklyDates(props.weekliesMap)

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
  const createCalculatedCells = (
    area: PlanningArea,
    areaName: string,
    prepLevel: PrepLevel
  ) => {
    for (let i = 0; i < dates.size; i++) {
      const dailies = props.weekliesMapDates.get(new Date(String(Array.from(dates)[i])))
      return dailies?.map(daily => {
        return (
          <React.Fragment key={`${daily.date}-${daily.code}`}>
            <TableCell colSpan={3}></TableCell>
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
          </React.Fragment>
        )
      })
    }
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
            {/* Non-day specific headers */}
            <TableCell colSpan={4}></TableCell>
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
                    const meanIntensityGroup = calculateMultipleMeanIntensityGroups(
                      area,
                      props.weekliesMap,
                      selected
                    )
                    const prepLevel = calculatePrepLevel(meanIntensityGroup)

                    const calculatedCells = createCalculatedCells(
                      area,
                      areaName,
                      prepLevel
                    )

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
                          {calculatedCells}
                        </TableRow>
                        {Object.entries(area.stations)
                          .sort((a, b) => (a[1].code < b[1].code ? -1 : 1))
                          .map(([stationCode, station]) => {
                            const dailies = props.weekliesMap.get(station.code)
                            const isRowSelected = stationCodeInSelected(station.code)
                            const classNameForRow = !isRowSelected
                              ? classes.unselectedStation
                              : undefined

                            const cells = createCells(
                              dailies,
                              station,
                              classNameForRow,
                              isRowSelected
                            )
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

                                {cells}
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
