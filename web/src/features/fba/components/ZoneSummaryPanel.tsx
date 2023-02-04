import React from 'react'
import { Grid, Paper, Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'
import { FireZone, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import { PieChart, Pie, ResponsiveContainer, Cell } from 'recharts'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 400
  },
  zoneName: {
    fontSize: '2rem',
    textAlign: 'center',
    variant: 'h2'
  },
  centreName: {
    fontSize: '1rem',
    textAlign: 'right',
    variant: 'h6'
  },
  fuelTypesPaper: {
    padding: '20px 10px'
  },
  fuelTypesHeader: {
    fontSize: '1.3rem',
    textAlign: 'center',
    variant: 'h3'
  },
  pieChartHeader: {
    fontSize: '1rem',
    variant: 'h4'
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
          {`${fuel_type_code} (${(percent * 100).toFixed(0)}%)`}
        </text>
      )
    }

    return (
      <text x={x} y={y} fontSize={'10pt'} fill="black" textAnchor={x > cx ? 'start' : 'end'}>
        {`${fuel_type_code}: ${area.toLocaleString(undefined, { maximumFractionDigits: 0 })} ha (${(
          percent * 100
        ).toFixed(0)}%)`}
      </text>
    )
  }

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
          <Paper>
            <div className={classes.wrapper}>
              <Typography className={classes.zoneName}>{props.selectedFireZone.mof_fire_zone_name}</Typography>
              <Typography className={classes.centreName}>{props.selectedFireZone.mof_fire_centre_name}</Typography>
            </div>
            <Paper className={classes.fuelTypesPaper}>
              <Typography className={classes.fuelTypesHeader}>HFI by Fuel Type</Typography>

              <div>
                <Typography className={classes.pieChartHeader}>Advisories (HFI: 4,000-10,000 kW/m)</Typography>
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
                <Typography className={classes.pieChartHeader}>Warnings (HFI: +10,000 kW/m)</Typography>
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
            </Paper>
          </Paper>
        </Grid>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
