/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import moment from 'moment'
import { Data, Shape, Legend } from 'plotly.js'

export const findMaxNumber = (arr: number[]): number => {
  if (arr.length === 0) {
    return 0
  }

  return Math.max(...arr)
}

export const findMinNumber = (arr: number[]): number => {
  if (arr.length === 0) {
    return 0
  }

  return Math.min(...arr)
}

export const layoutLegendConfig: Partial<Legend> = {
  orientation: 'h',
  yanchor: 'top',
  y: -0.35
}

export const populateNowLineData = (
  x: Date,
  y0: number,
  y1: number,
  yaxis?: string
): Data => {
  return {
    x: [x, x],
    y: [y0, y1],
    mode: 'lines',
    name: 'Now',
    line: {
      color: 'green',
      width: 2,
      dash: 'dot'
    },
    showlegend: true,
    hoverinfo: 'skip',
    yaxis
  }
}

/* -------------------------- Temp & RH -------------------------- */

interface TempRHValue {
  datetime: string
  temperature?: number | null
  relative_humidity?: number | null
  tmp_tgl_2_5th?: number
  tmp_tgl_2_90th?: number
  rh_tgl_2_5th?: number
  rh_tgl_2_90th?: number
  tmp_max?: number
  tmp_min?: number
  rh_max?: number
  rh_min?: number
  bias_adjusted_temperature?: number | null
  bias_adjusted_relative_humidity?: number | null
}

export const populateGraphDataForTempAndRH = (
  values: TempRHValue[],
  tempName: string,
  rhName: string,
  show: boolean,
  dash: 'solid' | 'dot' | 'dash' | 'longdash' | 'dashdot' | 'longdashdot',
  tempColor: string,
  rhColor: string,
  tempPlumeColor?: string,
  rhPlumeColor?: string
) => {
  const tempDates: Date[] = []
  const rhDates: Date[] = []
  const tempValues: number[] = []
  const rhValues: number[] = []

  const tempMinMaxDates: Date[] = []
  const tempMinMaxValues: [number, number][] = []
  const rhMinMaxDates: Date[] = []
  const rhMinMaxValues: [number, number][] = []

  const tempPercentileDates: Date[] = []
  const temp5thValues: number[] = []
  const temp90thValues: number[] = []
  const rhPercentileDates: Date[] = []
  const rh5thValues: number[] = []
  const rh90thValues: number[] = []
  const biasAdjTempDates: Date[] = []
  const biasAdjRHDates: Date[] = []
  const biasAdjTempValues: number[] = []
  const biasAdjRHValues: number[] = []

  values.forEach(value => {
    const {
      datetime,
      temperature,
      relative_humidity,
      tmp_max,
      tmp_min,
      rh_max,
      rh_min,
      tmp_tgl_2_5th,
      tmp_tgl_2_90th,
      rh_tgl_2_5th,
      rh_tgl_2_90th,
      bias_adjusted_temperature,
      bias_adjusted_relative_humidity
    } = value
    const date = new Date(datetime)

    if (temperature != null) {
      tempDates.push(date)
      tempValues.push(temperature)
    }
    if (relative_humidity != null) {
      rhDates.push(date)
      rhValues.push(relative_humidity)
    }

    // From forecast min & max
    if (tmp_min && tmp_max) {
      tempMinMaxDates.push(date)
      tempMinMaxValues.push([tmp_min, tmp_max])
    }
    if (rh_min && rh_max) {
      rhMinMaxDates.push(date)
      rhMinMaxValues.push([rh_min, rh_max])
    }

    // From model summaries
    if (tmp_tgl_2_5th && tmp_tgl_2_90th) {
      tempPercentileDates.push(date)
      temp5thValues.push(tmp_tgl_2_5th)
      temp90thValues.push(tmp_tgl_2_90th)
    }
    if (rh_tgl_2_5th && rh_tgl_2_90th) {
      rhPercentileDates.push(date)
      rh5thValues.push(rh_tgl_2_5th)
      rh90thValues.push(rh_tgl_2_90th)
    }

    // From bias adjusted models
    if (bias_adjusted_temperature != null) {
      biasAdjTempDates.push(date)
      biasAdjTempValues.push(bias_adjusted_temperature)
    }
    if (bias_adjusted_relative_humidity != null) {
      biasAdjRHDates.push(date)
      biasAdjRHValues.push(bias_adjusted_relative_humidity)
    }
  })

  const tempDots: Data = {
    x: tempDates,
    y: tempValues,
    name: tempName,
    mode: 'markers',
    type: 'scatter',
    showlegend: show,
    marker: { color: show ? tempColor : 'transparent' },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${tempName}: %{y:.2f} (°C)<extra></extra>` : undefined
  }
  const tempVerticalLines: Data[] = tempMinMaxDates.map((date, idx) => ({
    x: [date, date],
    y: tempMinMaxValues[idx], // Temp min & max pair
    mode: 'lines',
    name: tempName,
    line: {
      color: show ? tempColor : 'transparent',
      width: 3
    },
    hoverinfo: 'skip',
    showlegend: false
  }))
  const biasAdjTempLine: Data = {
    x: biasAdjTempDates,
    y: biasAdjTempValues,
    name: tempName,
    mode: 'lines+markers',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? tempColor : 'transparent',
      width: 2,
      dash
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${tempName}: %{y:.2f} (°C)<extra></extra>` : undefined
  }
  const tempLine: Data = {
    x: tempDates,
    y: tempValues,
    name: tempName,
    mode: 'lines+markers',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? tempColor : 'transparent',
      width: 2,
      dash
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${tempName}: %{y:.2f} (°C)<extra></extra>` : undefined
  }
  const temp5thLine: Data = {
    x: tempPercentileDates,
    y: temp5thValues,
    name: `${tempName} 5th percentile`,
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    hoverinfo: 'skip',
    showlegend: false
  }
  const temp90thLine: Data = {
    x: tempPercentileDates,
    y: temp90thValues,
    name: `${tempName} 5th - 90th percentile`,
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    fill: 'tonexty',
    fillcolor: show ? tempPlumeColor : 'transparent',
    hoverinfo: 'skip',
    showlegend: show
  }

  const rtDots: Data = {
    x: rhDates,
    y: rhValues,
    name: rhName,
    yaxis: 'y2',
    mode: 'markers',
    type: 'scatter',
    showlegend: show,
    marker: { color: show ? rhColor : 'transparent' },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${rhName}: %{y:.2f} (°C)<extra></extra>` : undefined
  }
  const rhVerticalLines: Data[] = rhMinMaxDates.map((date, idx) => ({
    x: [date, date],
    y: rhMinMaxValues[idx], // Temp min & max pair
    mode: 'lines',
    name: rhName,
    yaxis: 'y2',
    line: {
      color: show ? rhColor : 'transparent',
      width: 3
    },
    hoverinfo: 'skip',
    showlegend: false
  }))
  const biasAdjRHLine: Data = {
    x: biasAdjRHDates,
    y: biasAdjRHValues,
    name: rhName,
    yaxis: 'y2',
    mode: 'lines+markers',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? rhColor : 'transparent',
      width: 2,
      dash
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${rhName}: %{y:.2f} (%)<extra></extra>` : undefined
  }
  const rhLine: Data = {
    x: rhDates,
    y: rhValues,
    name: rhName,
    yaxis: 'y2',
    mode: 'lines+markers',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? rhColor : 'transparent',
      width: 2,
      dash
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${rhName}: %{y:.2f} (%)<extra></extra>` : undefined
  }
  const rh5thLine: Data = {
    x: rhPercentileDates,
    y: rh5thValues,
    name: `${rhName} 5th percentile`,
    yaxis: 'y2',
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    hoverinfo: 'skip',
    showlegend: false
  }
  const rh90thLine: Data = {
    x: rhPercentileDates,
    y: rh90thValues,
    name: `${rhName} 5th - 90th percentile`,
    yaxis: 'y2',
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    fill: 'tonexty',
    fillcolor: show ? rhPlumeColor : 'transparent',
    hoverinfo: 'skip',
    showlegend: show
  }

  const maxTemp = findMaxNumber(tempValues)
  const minTemp = findMinNumber(tempValues)

  return {
    tempDots,
    tempVerticalLines,
    biasAdjTempLine,
    tempLine,
    temp5thLine,
    temp90thLine,
    rtDots,
    rhVerticalLines,
    biasAdjRHLine,
    rhLine,
    rh5thLine,
    rh90thLine,
    maxTemp,
    minTemp
  }
}

/* -------------------------- Precipitation -------------------------- */

interface PrecipValue {
  datetime: string
  precipitation?: number | null
  delta_precipitation?: number | null
  total_precipitation?: number | null
}

export const getDailyAndAccumPrecips = (values: PrecipValue[]) => {
  const dates: Date[] = []
  const dailyPrecips: number[] = []
  const shouldAggregate =
    values.length > 0 &&
    (values[0].precipitation !== undefined || values[0].delta_precipitation !== undefined)

  // if the type of the value is observation or one of weather models, then aggregate hourly data to daily
  if (shouldAggregate) {
    const aggregatedPrecips: { [k: string]: number } = {}
    values.forEach(({ datetime, precipitation, delta_precipitation }) => {
      const date = moment(datetime).format('YYYY-MM-DD')
      let precip = 0
      if (precipitation != null) {
        precip = precipitation
      } else if (delta_precipitation != null) {
        precip = delta_precipitation
      }

      if (!aggregatedPrecips[date]) {
        aggregatedPrecips[date] = precip
      } else {
        aggregatedPrecips[date] = aggregatedPrecips[date] + precip
      }
    })

    Object.entries(aggregatedPrecips).forEach(([formattedDate, totalPrecip]) => {
      const midNightOfTheDay = moment(formattedDate)
        .set({ hour: 0 })
        .toDate()
      dates.push(midNightOfTheDay)
      dailyPrecips.push(totalPrecip)
    })
  } else {
    values.forEach(({ datetime, total_precipitation }) => {
      if (total_precipitation !== undefined) {
        const midNightOfTheDay = moment(datetime)
          .set({ hour: 0 })
          .toDate()
        dates.push(midNightOfTheDay)
        dailyPrecips.push(Number(total_precipitation))
      }
    })
  }

  // Create a list of accumulated precips for each day in time
  const accumPrecips: number[] = []
  dailyPrecips.forEach((daily, idx) => {
    if (idx === 0) {
      return accumPrecips.push(daily)
    }

    const prevAccum = accumPrecips[accumPrecips.length - 1]
    accumPrecips.push(prevAccum + daily)
  })

  return { dates, dailyPrecips, accumPrecips }
}

export const populateGraphDataForPrecip = (
  values: PrecipValue[],
  name: string,
  color: string,
  show: boolean
) => {
  const { dates, dailyPrecips, accumPrecips } = getDailyAndAccumPrecips(values)

  const dailyPrecipsBar: Data = {
    x: dates,
    y: dailyPrecips,
    name,
    type: 'bar',
    showlegend: show,
    marker: {
      color: show ? color : 'transparent'
    },
    hoverinfo: show ? 'y' : 'skip',
    hovertemplate: show ? `${name}: %{y:.2f} (mm/cm)<extra></extra>` : undefined
  }

  const accumPrecipsline: Data = {
    x: dates,
    y: accumPrecips,
    name: `Accumulated ${name}`,
    mode: 'lines',
    yaxis: 'y2',
    showlegend: show,
    marker: {
      color: show ? color : 'transparent'
    },
    hoverinfo: show ? 'y' : 'skip',
    hovertemplate: show
      ? `Accumulated ${name}: %{y:.2f} (mm/cm)<extra></extra>`
      : undefined
  }

  const maxAccumPrecip = findMaxNumber(accumPrecips)

  return {
    dailyPrecipsBar,
    accumPrecipsline,
    maxAccumPrecip
  }
}

/* -------------------------- Wind -------------------------- */

/**
 *   Basic arrow shape (before any transformations)
 *
 *              "front"
 *                 ^
 *                / \
 *   "leftEnd"   / | \   "rightEnd"
 *                 |
 *                 |
 *                 |
 *               "back"
 *
 */
type Point = [number, number]
const front: Point = [0, 8]
const back: Point = [0, -10]
const leftEnd: Point = [5, 0]
const rightEnd: Point = [-5, 0]
const arrowPoints = [front, back, leftEnd, rightEnd]

const buildArrowShapePath = (arrowShape: Point[]): string => {
  return `M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[2][0]} ${arrowShape[2][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[3][0]} ${arrowShape[3][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[1][0]} ${arrowShape[1][1]}`
}

const rotatePoints = (points: Point[], angle: number, cw = true): Point[] => {
  /**
   * https://academo.org/demos/rotation-about-point/
   * To rotate points around the origin,
   * to coordinates of the new point would be located at (x',y')
   *
   * x' = xcos(theta) - ysin(theta)
   * y' = ycos(theta) + xsin(theta)
   *
   * Where theta is the angle of rotation
   */

  // We need to rotate the arrow by 180 degrees (the degrees indiciate the origin of the wind,
  // not the direction)
  let theta = (Math.PI / 180) * ((angle + 180) % 360) // Turn the angle(number) into degree

  if (cw) {
    theta = -theta
  }

  return points.map(point => [
    point[0] * Math.cos(theta) - point[1] * Math.sin(theta),
    point[1] * Math.cos(theta) + point[0] * Math.sin(theta)
  ])
}

const createPath = (
  arrowShape: Point[],
  show: boolean,
  datetime: string,
  wind_speed: number,
  colour: string
): Partial<Shape> => {
  return {
    type: 'path',
    path: buildArrowShapePath(arrowShape),
    visible: show,
    layer: 'above',
    xref: 'x', // By setting a reference to the wind spd scale (x & y),
    yref: 'y', // we can position these arrows with wind spd values using xanchor & yanchor
    xsizemode: 'pixel', // https://plotly.com/javascript/reference/layout/shapes/#layout-shapes-items-shape-xsizemode
    ysizemode: 'pixel',
    xanchor: new Date(datetime).valueOf(),
    yanchor: wind_speed,
    line: {
      color: show ? colour : 'transparent'
    }
  }
}

interface WindValue {
  datetime: string
  wind_direction?: number | null
  wind_speed?: number | null
}

export const populateGraphDataForWind = (
  values: WindValue[],
  name: string,
  show: boolean,
  lineColor: string,
  arrowColor: string
) => {
  const dates: Date[] = []
  const windSpds: number[] = []
  const windSpdsTexts: string[] = []
  const windDirArrows: Partial<Shape>[] = []

  values.forEach(({ wind_direction, wind_speed, datetime }) => {
    if (wind_speed != null) {
      dates.push(new Date(datetime))
      windSpds.push(wind_speed)
      windSpdsTexts.push(wind_direction != null ? `${Math.round(wind_direction)}` : '-')

      if (wind_direction != null) {
        const arrowShape = rotatePoints(arrowPoints, wind_direction)
        const path = createPath(arrowShape, show, datetime, wind_speed, arrowColor)
        windDirArrows.push(path)
      }
    }
  })

  const windSpdLine: Data = {
    x: dates,
    y: windSpds,
    name,
    mode: 'lines',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? lineColor : 'transparent',
      width: 2
    },
    text: windSpdsTexts,
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${name}: %{y:.2f} km/h, %{text}°<extra></extra>` : ''
  }

  const maxWindSpd = findMaxNumber(windSpds)
  const minWindSpd = findMinNumber(windSpds)

  return { windSpdLine, windDirArrows, maxWindSpd, minWindSpd }
}
