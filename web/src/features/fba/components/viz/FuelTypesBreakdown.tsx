import React from 'react'
import { styled } from '@mui/material/styles'
import { Typography } from '@mui/material'
import { isUndefined } from 'lodash'
import { FireShape, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import { PieChart, Pie, ResponsiveContainer, Cell } from 'recharts'
import { getColorByFuelTypeCode } from 'features/fba/components/viz/color'

const PREFIX = 'FuelTypesBreakdown'

const FuelTypesHeader = styled(Typography, {
  name: `${PREFIX}-fuelTypesHeader`
})({
  fontSize: '1.3rem',
  textAlign: 'center',
  variant: 'h3'
})

const PieChartHeader = styled(Typography, {
  name: `${PREFIX}-pieChartHeader`
})({
  fontSize: '1rem',
  textAlign: 'center',
  variant: 'h4'
})

interface Props {
  className?: string
  selectedFireZone: FireShape | undefined
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
}

interface FuelTypeDataForPieChart {
  area: number
  fuel_type_code: string
}

const RADIAN = Math.PI / 180

const FuelTypesBreakdown = (props: Props) => {
  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    outerRadius,
    percent,
    fuel_type_code
  }: {
    cx: number
    cy: number
    midAngle: number
    outerRadius: number
    percent: number
    fuel_type_code: string
  }) => {
    // Labels are positioned at the outer edge of the pie + the length of label lines (20px) +
    // an arbitrary buffer/whitespace of 5px
    const labelRadius = outerRadius + 25
    const x = cx + labelRadius * Math.cos(-midAngle * RADIAN)
    const y = cy + labelRadius * Math.sin(-midAngle * RADIAN)

    // Only label pie slices that contribute >= 2%
    if (percent * 100 < 2) {
      return
    }

    return (
      <text x={x} y={y} fontSize={'10pt'} fill="black" textAnchor={x > cx ? 'start' : 'end'}>
        {`${fuel_type_code} (${(percent * 100).toFixed(0)}%)`}
      </text>
    )
  }

  const renderLabelLine = ({
    percent,
    points,
    stroke
  }: {
    percent: number
    points: { x: number; y: number }[]
    stroke: string
  }) => {
    if (!points || points.length < 2 || percent * 100 < 2) {
      return <></>
    }

    return <path d={`M${points[0].x},${points[0].y}L${points[1].x},${points[1].y}`} stroke={stroke} strokeWidth={1.5} />
  }

  if (isUndefined(props.selectedFireZone) || isUndefined(props.fuelTypeInfo[props.selectedFireZone.fire_shape_id])) {
    return <div></div>
  } else {
    const advisories: FuelTypeDataForPieChart[] = []
    const warnings: FuelTypeDataForPieChart[] = []
    props.fuelTypeInfo[props.selectedFireZone?.fire_shape_id].forEach(record => {
      if (record.threshold.id === 1) {
        advisories.push({ area: record.area, fuel_type_code: record.fuel_type.fuel_type_code })
      } else if (record.threshold.id === 2) {
        warnings.push({ area: record.area, fuel_type_code: record.fuel_type.fuel_type_code })
      }
    })
    return (
      <div>
        <FuelTypesHeader>HFI by Fuel Type</FuelTypesHeader>
        <PieChartHeader>Advisories (HFI: 4,000-10,000 kW/m)</PieChartHeader>
        <ResponsiveContainer width={400} height={250}>
          <PieChart>
            <Pie
              data={advisories}
              dataKey={'area'}
              nameKey={'fuel_type_code'}
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
              labelLine={renderLabelLine}
              label={renderCustomizedLabel}
            >
              {advisories.map(entry => (
                <Cell key={`cell-${entry.fuel_type_code}`} fill={getColorByFuelTypeCode(entry.fuel_type_code)} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <PieChartHeader>Warnings (HFI: +10,000 kW/m)</PieChartHeader>
        <ResponsiveContainer width={400} height={250}>
          <PieChart>
            <Pie
              data={warnings}
              dataKey={'area'}
              nameKey={'fuel_type_code'}
              cx="50%"
              cy="50%"
              outerRadius={80}
              labelLine={renderLabelLine}
              label={renderCustomizedLabel}
            >
              {warnings.map(entry => (
                <Cell key={`cell-${entry.fuel_type_code}`} fill={getColorByFuelTypeCode(entry.fuel_type_code)} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }
}

export default React.memo(FuelTypesBreakdown)
