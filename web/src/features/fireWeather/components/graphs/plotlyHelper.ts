import { DateTime } from 'luxon'
import { Data, Shape, Layout, RangeSlider, PlotData, BoxPlotData } from 'plotly.js'

import { PST_UTC_OFFSET } from 'utils/constants'
import { formatDateInPST } from 'utils/date'

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

export const rangeSliderConfig: Partial<RangeSlider> = {
  visible: true,
  bgcolor: '#dbdbdb',
  thickness: 0.1
}

export const getLayoutConfig = (title: string): Partial<Layout> => ({
  dragmode: 'pan',
  autosize: true,
  height: 600,
  margin: { pad: 10 },
  legend: { orientation: 'h', yanchor: 'top', y: -0.35, traceorder: 'reversed' }, // Locate the legend at the bottom of the graph
  title: {
    text: title,
    yanchor: 'middle'
  }
})

export const populateTimeOfInterestLineData = (
  x: string,
  y0: number,
  y1: number,
  yaxis?: string
): Data => {
  return {
    x: [x, x],
    y: [y0, y1],
    mode: 'lines',
    name: 'Time of Interest',
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
  dewpoint?: number | null
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

export interface TempRHGraphProperties {
  values: TempRHValue[]
  tempName: string
  rhName: string
  show: boolean
  symbol: string
  dash: 'solid' | 'dot' | 'dash' | 'longdash' | 'dashdot' | 'longdashdot'
  tempColor: string
  rhColor: string
  dewpointName?: string
  dewpointColor?: string
  tempPlumeColor?: string
  rhPlumeColor?: string
}

export const populateGraphDataForTempAndRH = (
  graphProps: TempRHGraphProperties
): {
  tempDots: Partial<PlotData>
  tempVerticalLines: Data[]
  biasAdjTempLine: Partial<PlotData>
  tempLine: Partial<PlotData>
  temp5thLine: Partial<PlotData>
  temp90thLine: Partial<PlotData>
  rhDots: Partial<PlotData>
  rhVerticalLines: Data[]
  biasAdjRHLine: Partial<PlotData>
  rhLine: Partial<PlotData>
  rh5thLine: Partial<PlotData>
  rh90thLine: Partial<PlotData>
  dewpointDots: Partial<PlotData>
  dewpointLine: Partial<PlotData>
  maxTempDewpoint: number
  minTempDewpoint: number
} => {
  const tempDates: string[] = []
  const rhDates: string[] = []
  const dewpointDates: string[] = []
  const tempValues: number[] = []
  const rhValues: number[] = []
  const dewpointValues: number[] = []

  const tempMinMaxDates: string[] = []
  const tempMinMaxValues: [number, number][] = []
  const rhMinMaxDates: string[] = []
  const rhMinMaxValues: [number, number][] = []

  const tempPercentileDates: string[] = []
  const temp5thValues: number[] = []
  const temp90thValues: number[] = []
  const rhPercentileDates: string[] = []
  const rh5thValues: number[] = []
  const rh90thValues: number[] = []
  const biasAdjTempDates: string[] = []
  const biasAdjRHDates: string[] = []
  const biasAdjTempValues: number[] = []
  const biasAdjRHValues: number[] = []

  graphProps.values.forEach(value => {
    const {
      datetime,
      temperature,
      relative_humidity,
      dewpoint,
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
    const date = formatDateInPST(datetime)

    if (temperature != null) {
      tempDates.push(date)
      tempValues.push(temperature)
    }
    if (relative_humidity != null) {
      rhDates.push(date)
      rhValues.push(relative_humidity)
    }
    if (dewpoint != null) {
      dewpointDates.push(date)
      dewpointValues.push(dewpoint)
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
    x: graphProps.show ? tempDates : [],
    y: graphProps.show ? tempValues : [],
    name: graphProps.tempName,
    mode: 'markers',
    type: 'scatter',
    marker: { color: graphProps.tempColor, symbol: graphProps.symbol },
    hovertemplate: `${graphProps.tempName}: %{y:.2f} (°C)<extra></extra>`
  }
  const tempVerticalLines: Data[] = tempMinMaxDates.map((date, idx) => ({
    x: graphProps.show ? [date, date] : [],
    y: graphProps.show ? tempMinMaxValues[idx] : [], // Temp min & max pair
    mode: 'lines',
    name: graphProps.tempName,
    line: {
      color: graphProps.tempColor,
      width: 3
    },
    hoverinfo: 'skip',
    showlegend: false
  }))
  const biasAdjTempLine: Data = {
    x: graphProps.show ? biasAdjTempDates : [],
    y: graphProps.show ? biasAdjTempValues : [],
    name: graphProps.tempName,
    mode: 'lines+markers',
    type: 'scatter',
    marker: { symbol: graphProps.symbol },
    line: {
      color: graphProps.tempColor,
      width: 2,
      dash: graphProps.dash
    },
    hovertemplate: `${graphProps.tempName}: %{y:.2f} (°C)<extra></extra>`
  }
  const tempLine: Data = {
    x: graphProps.show ? tempDates : [],
    y: graphProps.show ? tempValues : [],
    name: graphProps.tempName,
    mode: 'lines+markers',
    type: 'scatter',
    marker: { symbol: graphProps.symbol },
    line: {
      color: graphProps.tempColor,
      width: 2,
      dash: graphProps.dash
    },
    hovertemplate: `${graphProps.tempName}: %{y:.2f} (°C)<extra></extra>`
  }
  const temp5thLine: Data = {
    x: graphProps.show ? tempPercentileDates : [],
    y: graphProps.show ? temp5thValues : [],
    name: `${graphProps.tempName} 5th percentile`,
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    hoverinfo: 'skip',
    showlegend: false
  }
  const temp90thLine: Data = {
    x: graphProps.show ? tempPercentileDates : [],
    y: graphProps.show ? temp90thValues : [],
    name: `${graphProps.tempName} 5th - 90th percentile`,
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    fill: 'tonexty',
    fillcolor: graphProps.tempPlumeColor,
    hoverinfo: 'skip'
  }

  const dewpointDots: Data = {
    x: graphProps.show ? dewpointDates : [],
    y: graphProps.show ? dewpointValues : [],
    name: graphProps.dewpointName,
    mode: 'markers',
    type: 'scatter',
    marker: { color: graphProps.dewpointColor, symbol: graphProps.symbol },
    hovertemplate: `${graphProps.dewpointName}: %{y:.2f} (°C)<extra></extra>`
  }
  const dewpointLine: Data = {
    x: graphProps.show ? dewpointDates : [],
    y: graphProps.show ? dewpointValues : [],
    name: graphProps.dewpointName,
    mode: 'lines+markers',
    type: 'scatter',
    marker: { symbol: graphProps.symbol },
    line: {
      color: graphProps.dewpointColor,
      width: 2,
      dash: graphProps.dash
    },
    hovertemplate: `${graphProps.dewpointName}: %{y:.2f} (°C)<extra></extra>`
  }

  const rhDots: Data = {
    x: graphProps.show ? rhDates : [],
    y: graphProps.show ? rhValues : [],
    name: graphProps.rhName,
    yaxis: 'y2',
    mode: 'markers',
    type: 'scatter',
    showlegend: graphProps.show,
    marker: { color: graphProps.rhColor, symbol: graphProps.symbol },
    hovertemplate: `${graphProps.rhName}: %{y:.2f} (%)<extra></extra>`
  }
  const rhVerticalLines: Data[] = rhMinMaxDates.map((date, idx) => ({
    x: graphProps.show ? [date, date] : [],
    y: graphProps.show ? rhMinMaxValues[idx] : [], // Temp min & max pair
    mode: 'lines',
    name: graphProps.rhName,
    yaxis: 'y2',
    line: {
      color: graphProps.rhColor,
      width: 3
    },
    hoverinfo: 'skip',
    showlegend: false
  }))
  const biasAdjRHLine: Data = {
    x: graphProps.show ? biasAdjRHDates : [],
    y: graphProps.show ? biasAdjRHValues : [],
    name: graphProps.rhName,
    yaxis: 'y2',
    mode: 'lines+markers',
    type: 'scatter',
    marker: { symbol: graphProps.symbol },
    line: {
      color: graphProps.rhColor,
      width: 2,
      dash: graphProps.dash
    },
    hovertemplate: `${graphProps.rhName}: %{y:.2f} (%)<extra></extra>`
  }
  const rhLine: Data = {
    x: graphProps.show ? rhDates : [],
    y: graphProps.show ? rhValues : [],
    name: graphProps.rhName,
    yaxis: 'y2',
    mode: 'lines+markers',
    type: 'scatter',
    marker: { symbol: graphProps.symbol },
    line: {
      color: graphProps.rhColor,
      width: 2,
      dash: graphProps.dash
    },
    hovertemplate: `${graphProps.rhName}: %{y:.2f} (%)<extra></extra>`
  }
  const rh5thLine: Data = {
    x: graphProps.show ? rhPercentileDates : [],
    y: graphProps.show ? rh5thValues : [],
    name: `${graphProps.rhName} 5th percentile`,
    yaxis: 'y2',
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    hoverinfo: 'skip',
    showlegend: false
  }
  const rh90thLine: Data = {
    x: graphProps.show ? rhPercentileDates : [],
    y: graphProps.show ? rh90thValues : [],
    name: `${graphProps.rhName} 5th - 90th percentile`,
    yaxis: 'y2',
    mode: 'lines',
    type: 'scatter',
    line: { width: 0 },
    marker: { color: '444' },
    fill: 'tonexty',
    fillcolor: graphProps.rhPlumeColor,
    hoverinfo: 'skip'
  }

  const maxTempDewpoint = findMaxNumber([...tempValues, ...dewpointValues])
  const minTempDewpoint = findMinNumber([...tempValues, ...dewpointValues])

  return {
    tempDots,
    tempVerticalLines,
    biasAdjTempLine,
    tempLine,
    temp5thLine,
    temp90thLine,
    rhDots,
    rhVerticalLines,
    biasAdjRHLine,
    rhLine,
    rh5thLine,
    rh90thLine,
    dewpointDots,
    dewpointLine,
    maxTempDewpoint,
    minTempDewpoint
  }
}

/* -------------------------- Precipitation -------------------------- */

const getMidnightDate = (formattedDate: string): string => {
  return DateTime.fromISO(formattedDate)
    .setZone(`UTC${PST_UTC_OFFSET}`)
    .set({ hour: 0, minute: 0 })
    .toFormat('yyyy-MM-dd HH:mm')
}

interface PrecipValue {
  datetime: string
  precipitation?: number | null
  delta_precipitation?: number | null
  total_precipitation?: number | null
}

export const getDailyAndAccumPrecips = (
  values: PrecipValue[]
): {
  dates: string[]
  dailyPrecips: number[]
  accumPrecips: number[]
} => {
  const dates: string[] = []
  const dailyPrecips: number[] = []
  const shouldAggregate =
    values.length > 0 &&
    (values[0].precipitation !== undefined || values[0].delta_precipitation !== undefined)

  // if the type of the value is observation or one of weather models, then aggregate hourly data to daily
  if (shouldAggregate) {
    const aggregatedPrecips: { [k: string]: number } = {}
    values.forEach(({ datetime, precipitation, delta_precipitation }) => {
      const date = DateTime.fromISO(datetime)
        .setZone(`UTC${PST_UTC_OFFSET}`)
        .toFormat('yyyy-MM-dd')
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
      const midnightOfTheDay = getMidnightDate(formattedDate)
      dates.push(midnightOfTheDay)
      dailyPrecips.push(totalPrecip)
    })
  } else {
    values.forEach(({ datetime, total_precipitation }) => {
      if (total_precipitation !== undefined) {
        const midnightOfTheDay = getMidnightDate(datetime)
        dates.push(midnightOfTheDay)
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
): {
  dailyPrecipsBar: Partial<PlotData>
  accumPrecipsline: Partial<PlotData> | Partial<BoxPlotData>
  maxAccumPrecip: number
} => {
  const { dates, dailyPrecips, accumPrecips } = getDailyAndAccumPrecips(values)

  const dailyPrecipsBar: Data = {
    x: show ? dates : [],
    y: show ? dailyPrecips : [],
    name,
    type: 'bar',
    marker: {
      color: show ? color : 'transparent'
    },
    hoverinfo: show ? 'y' : 'skip',
    hovertemplate: show ? `${name}: %{y:.2f} (mm)<extra></extra>` : undefined
  }

  const accumPrecipsline: Data = {
    x: show ? dates : [],
    y: show ? accumPrecips : [],
    name: `Accumulated ${name}`,
    mode: 'lines',
    yaxis: 'y2',
    marker: {
      color
    },
    line: {
      width: 2.5
    },
    hoverinfo: 'y',
    hovertemplate: show ? `Accumulated ${name}: %{y:.2f} (mm)<extra></extra>` : undefined
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
  name: string,
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
    name,
    xref: 'x', // By setting a reference to the wind spd scale (x & y),
    yref: 'y', // we can position these arrows with wind spd values using xanchor & yanchor
    xsizemode: 'pixel', // https://plotly.com/javascript/reference/layout/shapes/#layout-shapes-items-shape-xsizemode
    ysizemode: 'pixel',
    xanchor: formatDateInPST(datetime),
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
  values: {
    datetime: string
    wind_speed: number | null | undefined
    wind_direction: number | null | undefined
  }[],
  name: string,
  show: boolean,
  lineColor: string,
  arrowColor: string
): {
  windSpdLine: Partial<PlotData>
  windDirArrows: Partial<Shape>[]
  maxWindSpd: number
  minWindSpd: number
} => {
  const dates: string[] = []
  const windSpds: number[] = []
  const windSpdsTexts: string[] = []
  const windDirArrows: Partial<Shape>[] = []

  console.log(`${name} - values: ${values.map(value => value.wind_speed)}`)

  values.forEach(({ wind_speed, wind_direction, datetime }) => {
    if (wind_speed != null) {
      dates.push(formatDateInPST(datetime))
      windSpds.push(wind_speed)
      windSpdsTexts.push(wind_direction != null ? `${Math.round(wind_direction)}` : '-')

      if (wind_direction != null && show) {
        const arrowShape = rotatePoints(arrowPoints, wind_direction)
        const path = createPath(arrowShape, name, show, datetime, wind_speed, arrowColor)
        windDirArrows.push(path)
      }
    }
  })

  const windSpdLine: Data = {
    x: show ? dates : [],
    y: show ? windSpds : [],
    name,
    mode: 'lines',
    type: 'scatter',
    line: {
      color: lineColor,
      width: 2
    },
    text: windSpdsTexts,
    hovertemplate: `${name}: %{y:.2f} km/h, %{text}°<extra></extra>`
  }

  const maxWindSpd = findMaxNumber(windSpds)
  const minWindSpd = findMinNumber(windSpds)

  return {
    windSpdLine,
    windDirArrows,
    maxWindSpd,
    minWindSpd
  }
}
