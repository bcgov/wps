/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import moment from 'moment'
import * as d3 from 'd3'
import { PDT_UTC_OFFSET } from 'utils/constants'

export const transitionDuration = 50

/**
 * Returns a list of dates in which each date is 12am PDT within the domain
 * @param domain a pair of dates, x domain
 */
export const getTickValues = (
  domain: [Date, Date] | [undefined, undefined],
  utcOffset: number,
  includeFirst = true
) => {
  const [d1, d2] = domain

  if (!d1) {
    return []
  } else if (d1 && !d2) {
    return includeFirst ? [d1] : []
  } else {
    const result = includeFirst ? [d1] : []

    let nextDate =
      moment(d1)
        .utcOffset(utcOffset)
        .get('date') + 1
    const lastDate = moment(d2)
      .utcOffset(utcOffset)
      .get('date')

    while (lastDate >= nextDate) {
      result.push(
        moment(d1)
          .utcOffset(utcOffset)
          .set({ date: nextDate, hours: 0, minutes: 0 })
          .toDate()
      )
      nextDate++
    }

    return result
  }
}

/**
 * High order function to generate formatting functions
 * @param format format string recognized Moment
 */
const formatDate = (format: string) => (value: Date | { valueOf(): number }) => {
  if (value instanceof Date) {
    return moment(value)
      .utcOffset(PDT_UTC_OFFSET)
      .format(format)
  }

  return moment(value.valueOf())
    .utcOffset(PDT_UTC_OFFSET)
    .format(format)
}

export const formatDateInDay = formatDate('Do')
export const formatDateInMonthAndDay = formatDate('MMM D')

/**
 * Note: className should be unique
 */
export const drawDots = <T>({
  svg,
  className,
  data,
  cx,
  cy,
  radius = 1,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  data: T[]
  cx: (d: T) => number
  cy: (d: T) => number
  radius?: number
  testId?: string
}) => {
  if (data.length === 0) {
    return
  }

  const dots = svg
    .selectAll(`.${className}`)
    .data(data)
    .enter()
    .append('circle')
    .attr('class', className)
    .attr('cx', cx)
    .attr('cy', cy)
    .attr('r', radius)

  if (testId) {
    dots.attr('data-testid', testId)
  }

  const updateDots = (newCx: (d: T) => number, duration?: number) => {
    dots
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('cx', newCx)
  }

  return updateDots
}

export const drawSymbols = <T>({
  svg,
  className,
  data,
  x,
  y,
  size = 64,
  symbol = d3.symbolCircle,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  data: T[]
  x: (d: T) => number
  y: (d: T) => number
  size?: number
  symbol?: d3.SymbolType
  testId?: string
}) => {
  if (data.length === 0) {
    return
  }

  const symbolFunc = d3
    .symbol<T>()
    .type(symbol)
    .size(size)

  const path = svg
    .selectAll(`.${className}`)
    .data(data)
    .enter()
    .append('path')
    .attr('d', symbolFunc)
    .attr('transform', d => `translate(${x(d)}, ${y(d)})`)
    .attr('class', className)
  if (testId) {
    path.attr('data-testid', testId)
  }

  const update = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('transform', d => `translate(${newX(d)}, ${y(d)})`)
  }

  return update
}

export const drawPath = <T>({
  svg,
  className,
  data,
  x,
  y,
  strokeWidth = 1,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  data: T[]
  x: (d: T) => number
  y: (d: T) => number
  strokeWidth?: number
  testId?: string
}) => {
  const lineFunc = d3
    .line<T>()
    .x(x)
    .y(y)

  const path = svg
    .append('path')
    .datum(data)
    .attr('d', lineFunc)
    .attr('stroke-width', strokeWidth)
    .attr('fill', 'none')
    .attr('opacity', 0.8)
    .attr('class', className)
  if (testId) {
    path.attr('data-testid', testId)
  }

  const updatePath = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('d', lineFunc.x(newX))
  }

  return updatePath
}

export const drawVerticalLine = ({
  svg,
  className,
  xScale,
  x,
  y1,
  y2,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  xScale: d3.ScaleTime<number, number>
  x: number
  y1: number
  y2: number
  testId?: string
}) => {
  const line = svg
    .append('line')
    .attr('x1', x)
    .attr('y1', y1)
    .attr('x2', x)
    .attr('y2', y2)
    .attr('class', className)
  if (testId) {
    line.attr('data-testid', testId)
  }

  const update = (newXScale: d3.ScaleTime<number, number>, duration?: number) => {
    // Get inverted x using the original scale
    // then calculate the new x with the new scale
    const newX = newXScale(xScale.invert(x))

    line
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('x1', newX)
      .attr('x2', newX)
  }

  return update
}

export const drawText = ({
  svg,
  className,
  xScale,
  x,
  y,
  dy,
  dx,
  text,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  xScale: d3.ScaleTime<number, number>
  x: number
  y: number
  dx: string
  dy: string
  text: string
  testId?: string
}) => {
  const textSvg = svg
    .append('text')
    .attr('y', y)
    .attr('x', x)
    .attr('dy', dy)
    .attr('dx', dx)
    .attr('class', className)
    .text(text)
  if (testId) {
    textSvg.attr('data-testid', testId)
  }

  const update = (newXScale: d3.ScaleTime<number, number>, duration?: number) => {
    // Get inverted x using the original scale
    // then calculate the new x with the new scale
    const newX = newXScale(xScale.invert(x))

    textSvg
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('x', newX)
  }

  return update
}

export const drawArea = <T>({
  svg,
  className,
  datum,
  x,
  y0,
  y1,
  curve = d3.curveNatural,
  testId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  className: string
  datum: T[]
  x: (d: T) => number // x accessor function
  y0: (d: T) => number // y0 accessor function
  y1: (d: T) => number // y1 accessor function
  curve?: d3.CurveFactory
  testId?: string
}) => {
  if (datum.length === 0) {
    return
  }

  const areaFunc = d3
    .area<T>()
    .curve(curve)
    .x(x)
    .y0(y0)
    .y1(y1)

  const path = svg
    .append('path')
    .datum(datum)
    .attr('class', className)
    .attr('d', areaFunc)
  if (testId) {
    path.attr('data-testid', testId)
  }

  const updateArea = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('d', areaFunc.x(newX))
  }

  return updateArea
}

export const addLegend = ({
  svg,
  shape = 'circle',
  text,
  fill,
  color,
  shapeX,
  shapeY,
  textX,
  textY,
  radius = 2, // circle radius
  length = 8 // rect length
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  shape?: 'circle' | 'rect' | 'diamond' | 'triangle' | 'cross'
  text: string
  color: string
  fill?: string | 'none'
  shapeX: number
  shapeY: number
  textX: number
  textY: number
  radius?: number
  length?: number
}): void => {
  if (shape === 'circle') {
    svg
      .append('circle')
      .attr('cx', shapeX)
      .attr('cy', shapeY)
      .attr('r', radius)
      .style('stroke', color)
      .style('fill', fill || color)
  } else if (shape === 'rect') {
    svg
      .append('rect')
      .attr('x', shapeX)
      .attr('y', shapeY)
      .attr('width', length)
      .attr('height', length)
      .style('stroke', color)
      .attr('fill', fill || color)
  } else if (shape === 'triangle') {
    svg
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolTriangle)
          .size(10)
      )
      .attr('transform', `translate(${shapeX},${shapeY})`)
      .style('stroke', color)
      .attr('fill', fill || color)
  } else if (shape === 'diamond') {
    svg
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolDiamond)
          .size(10)
      )
      .attr('transform', `translate(${shapeX},${shapeY})`)
      .style('stroke', color)
      .attr('fill', fill || color)
  } else if (shape === 'cross') {
    svg
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolCross)
          .size(5)
      )
      .attr('transform', `translate(${shapeX},${shapeY})`)
      .style('stroke', color)
      .attr('fill', fill || color)
  }
  svg
    .append('text')
    .attr('x', textX)
    .attr('y', textY)
    .text(text)
    .style('font-size', '9px')
    .style('fill', color)
}

const getNearestByDate = <T extends { date: Date }>(invertedDate: Date, arr: T[]): T => {
  // What is bisect: https://observablehq.com/@d3/d3-bisect
  const bisect = d3.bisector((d: T) => d.date).left
  const index = bisect(arr, invertedDate, 1)
  const a = arr[index - 1]
  const b = arr[index]
  // Get the nearest value from the user's mouse position
  const value =
    b &&
    invertedDate.valueOf() - a.date.valueOf() > b.date.valueOf() - invertedDate.valueOf()
      ? b
      : a

  return value
}

/**
 * Attach a listener to display a tooltip in the graph, inspired by: https://observablehq.com/@d3/line-chart-with-tooltip
 * Note: .tooltip, .tooltip--hidden, and .tooltip__cursor classes need to be defined
 * The T is a generic type that captures the type of the given data
 */
export const addTooltipListener = <T extends { date: Date }>({
  svg,
  xScale,
  width,
  height,
  data,
  getTextData,
  textTestId,
  bgdTestId
}: {
  svg: d3.Selection<SVGGElement, unknown, null, undefined>
  xScale: d3.ScaleTime<number, number>
  width: number
  height: number
  data: T[]
  getTextData: (d: T) => ({ text: string; color?: string } | undefined)[]
  textTestId?: string
  bgdTestId?: string
}): void => {
  const tooltipCallout = (
    g: typeof svg,
    position: 'right' | 'left',
    textData: { text: string; color?: string }[]
  ) => {
    if (!textData) return g.attr('class', 'tooltip--hidden')

    g.attr('class', 'tooltip')

    const path = g
      .selectAll('path')
      .data([null])
      .join('path')
      .attr('fill', 'white')
      .attr('stroke', 'black')

    const text = g
      .selectAll('text')
      .data([null])
      .join('text')
      .call(txt =>
        txt
          .selectAll('tspan')
          .data(textData)
          .join('tspan')
          .attr('fill', d => d.color || 'black')
          .attr('x', 0)
          .attr('y', (_, i) => `${i * 1.5}em`)
          .text(d => d.text)
      )
    if (textTestId) {
      text.attr('data-testid', textTestId)
    }

    // Don't show the tooltip if for some reason getBBox method doesn't exist
    if (!(text.node() as SVGSVGElement).getBBox) {
      return g.attr('class', 'tooltip--hidden')
    }

    const { y: textY, width: w, height: h } = (text.node() as SVGSVGElement).getBBox()
    const padding = 8
    const startX = 13
    let translateX = startX
    let HMove = startX + padding + w
    let MPointX = startX - padding
    const MPointY = textY - 2 * padding
    // Render the tooltip on the left side
    if (position === 'left') {
      translateX = -w - startX
      HMove = -startX + padding
      MPointX = -startX - padding - w
    }
    text.attr('transform', `translate(${translateX}, ${textY})`)
    path.attr(
      'd',
      `M ${MPointX}, ${MPointY}
       H${HMove}
       v${h + 2 * padding}
       h-${w + 2 * padding}
       z
      `
    )
  }

  // Draw a rectangular that covers the whole svg space so that
  // the listener can react to user's mouseover in anywhere within the graph
  svg
    .append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('class', 'tooltip--background')
  if (bgdTestId) {
    svg.attr('data-testid', bgdTestId)
  }
  const tooltipCursor = svg
    .append('line')
    .attr('x1', 0)
    .attr('y1', 0)
    .attr('x2', 0)
    .attr('y2', height)
    .attr('class', 'tooltip__cursor')
  const tooltip = svg.append('g')
  const removeTooltip = () => {
    tooltip.call(tooltipCallout)
    tooltipCursor.style('opacity', 0)
  }
  svg.on('touchmove mousemove', function() {
    if (data.length === 0) return

    const mx = d3.mouse(this)[0]
    // if user's mouse is far away from the data range
    const extraRange = 25
    if (
      mx < xScale(data[0].date) - extraRange ||
      mx > xScale(data[data.length - 1].date) + extraRange
    ) {
      return removeTooltip()
    }

    const invertedDate = xScale.invert(mx)
    const nearest = getNearestByDate(invertedDate, data)
    if (!nearest) return // couldn't find the nearest, so don't render the tooltip

    const nearestX = xScale(nearest.date)
    const position = width / 2 > nearestX ? 'right' : 'left'
    const tooltipTextData = getTextData(nearest).filter(d => d)
    tooltip
      .attr('transform', `translate(${nearestX}, ${height / 3})`)
      .call(tooltipCallout, position, tooltipTextData)
    tooltipCursor.attr('transform', `translate(${nearestX}, 0)`).style('opacity', 1)
  })
  svg.on('touchend mouseleave', removeTooltip)
}
