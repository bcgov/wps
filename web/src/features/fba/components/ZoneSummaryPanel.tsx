import React from 'react'
import { Grid, TextField } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'
import { FireZone, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import { PieChart, Pie, ResponsiveContainer, Label, Cell } from 'recharts'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 300
  },
  zoneName: {
    fontSize: '2rem'
  },
  centreName: {
    fontSize: '1.2rem'
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
}

interface FuelTypeDataForPieChart {
  area: number
  fuel_type_code: string
}

const RADIAN = Math.PI / 180
const COLOURS = [
  '#2191FB',
  '#FCB1A6',
  '#B33951',
  '#CCF5AC',
  '#8CDEDC',
  '#9DACFF',
  '#4F7CAC',
  '#FFA62B',
  '#C09BD8',
  '#EBC3DB',
  '#D19C1D',
  '#FFC0BE',
  '#ED7D3A'
]

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    fuel_type_code,
    area,
    index
  }) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if (percent * 100 < 2) {
      return
    }
    if (percent * 100 < 5) {
      return (
        <text x={x} y={y} fontSize={'10pt'} fill="black">
          {`${fuel_type_code} - (${(percent * 100).toFixed(0)}%)`}
        </text>
      )
    }

    return (
      <text x={x} y={y} fontSize={'10pt'} fill="black" textAnchor={x > cx ? 'start' : 'end'}>
        {`${fuel_type_code} - ${area.toFixed(0)} ha (${(percent * 100).toFixed(0)}%)`}
      </text>
    )
  }

  // const renderCustomizedLabel = entry => {
  //   return `${entry.name} - ${entry.value.toFixed(0)}`
  // }

  if (isUndefined(props.selectedFireZone) || isUndefined(props.fuelTypeInfo[props.selectedFireZone.mof_fire_zone_id])) {
    return <div></div>
  } else {
    const advisories: FuelTypeDataForPieChart[] = []
    const warnings: FuelTypeDataForPieChart[] = []
    props.fuelTypeInfo[props.selectedFireZone?.mof_fire_zone_id].forEach(thing => {
      if (thing.threshold.id === 1) {
        advisories.push({ area: thing.area, fuel_type_code: thing.fuel_type.fuel_type_code })
      } else if (thing.threshold.id === 2) {
        warnings.push({ area: thing.area, fuel_type_code: thing.fuel_type.fuel_type_code })
      }
    })
    return (
      <div className={props.className}>
        <Grid item>
          <div className={classes.wrapper}>
            <TextField className={classes.zoneName} value={props.selectedFireZone.mof_fire_zone_name} />
            <TextField className={classes.centreName} value={props.selectedFireZone.mof_fire_centre_name} />
          </div>
          <div>
            <Label>Advisories</Label>
            <ResponsiveContainer width="100%" aspect={2}>
              <PieChart>
                <Pie
                  data={advisories}
                  dataKey={'area'}
                  nameKey={'fuel_type_code'}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  labelLine={false}
                  label={renderCustomizedLabel}
                >
                  {advisories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLOURS[index % COLOURS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div>
            <Label>Warnings</Label>
            <ResponsiveContainer width="100%" aspect={2}>
              <PieChart>
                <Pie
                  data={warnings}
                  dataKey={'area'}
                  nameKey={'fuel_type_code'}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  labelLine={false}
                  label={renderCustomizedLabel}
                >
                  {warnings.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLOURS[index % COLOURS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Grid>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
