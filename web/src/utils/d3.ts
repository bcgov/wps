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
): Date[] => {
  const [d1, d2] = domain

  if (!d1) {
    return []
  }

  const result = includeFirst ? [d1] : []

  const next = moment(d1)
    .utcOffset(utcOffset)
    .add(1, 'days')
    .set({
      hours: 0,
      minute: 0
    })
  const last = moment(d2).utcOffset(utcOffset)

  while (last >= next) {
    result.push(moment(next).toDate())
    next.add(1, 'days')
  }

  return result
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

  const redraw = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('transform', d => `translate(${newX(d)}, ${y(d)})`)
  }

  return redraw
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

  const redraw = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('d', lineFunc.x(newX))
  }

  return redraw
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

  const redraw = (newXScale: d3.ScaleTime<number, number>, duration?: number) => {
    // Get the corresponding value from the domain using the original scale
    // then calculate new x with the updated x scale
    const newX = newXScale(xScale.invert(x))

    line
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('x1', newX)
      .attr('x2', newX)
  }

  return redraw
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

  const redraw = (newXScale: d3.ScaleTime<number, number>, duration?: number) => {
    // Get inverted x using the original scale
    // then calculate the new x with the new scale
    const newX = newXScale(xScale.invert(x))

    textSvg
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('x', newX)
  }

  return redraw
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

  const redraw = (newX: (d: T) => number, duration?: number) => {
    path
      .transition(d3.event.transform)
      .duration(duration || transitionDuration)
      .attr('d', areaFunc.x(newX))
  }

  return redraw
}

const createIcon = (
  item: d3.Selection<SVGGElement, unknown, null, undefined>,
  d: Legend
):
  | d3.Selection<SVGRectElement, unknown, null, undefined>
  | d3.Selection<SVGPathElement, unknown, null, undefined>
  | d3.Selection<SVGCircleElement, unknown, null, undefined> => {
  if (d.shape === 'rect') {
    return item
      .append(d.shape)
      .attr('width', 4)
      .attr('height', 4)
      .style('stroke', d.color)
      .style('fill', d.fill || d.color)
  } else if (d.shape === 'diamond') {
    return item
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolDiamond)
          .size(10)
      )
      .style('stroke', d.color)
      .attr('fill', d.fill || d.color)
  } else if (d.shape === 'triangle') {
    return item
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolTriangle)
          .size(7)
      )
      .style('stroke', d.color)
      .attr('fill', d.fill || d.color)
  } else if (d.shape === 'cross') {
    return item
      .append('path')
      .attr(
        'd',
        d3
          .symbol()
          .type(d3.symbolCross)
          .size(7)
      )
      .style('stroke', d.color)
      .attr('fill', d.fill || d.color)
  }
  return item
    .append(d.shape)
    .attr('r', 2)
    .style('stroke', d.color)
    .style('fill', d.fill || d.color)
}

const translateIcon = (
  shape: 'circle' | 'rect' | 'diamond' | 'cross' | 'triangle',
  xOffset: number,
  yOffset: number,
  icon:
    | d3.Selection<SVGRectElement, unknown, null, undefined>
    | d3.Selection<SVGPathElement, unknown, null, undefined>
    | d3.Selection<SVGCircleElement, unknown, null, undefined>
): string => {
  if (shape === 'triangle') {
    // rather frustrated - having to add magic number (+1) to render triangle correctly.
    return `translate(${xOffset + (icon.node()?.getBBox().width ?? 0) / 2}, ${yOffset +
      1})`
  } else if (shape === 'rect') {
    return `translate(${xOffset}, ${yOffset - (icon.node()?.getBBox().height ?? 0) / 2})`
  }
  // diamond, circle, cross
  return `translate(${xOffset + (icon.node()?.getBBox().width ?? 0) / 2}, ${yOffset})`
}

export interface Legend {
  text: string
  shape: 'rect' | 'circle' | 'cross' | 'diamond' | 'triangle'
  color: string
  fill: null | string
}

export const addLegend = (
  svg: d3.Selection<SVGGElement, unknown, null, undefined>,
  legendWidth: number,
  data: Legend[]
): number => {
  const numColumns = 3 // number of columns
  const columnWidth = legendWidth / numColumns // how wide is each column
  const iconTextPadding = 5 // amount of padding between icon and text
  const lineHeight = 15 // height of line of text

  const legend = svg.selectAll('.legend')

  legend
    .data(data)
    .enter()
    .append('g')
    .attr('transform', 'translate(0, 0)')
    .each(function(legendData: Legend, i) {
      const legendItem = d3.select(this)

      const text = legendItem
        .append('text')
        .attr('text-anchor', 'left')
        .style('alignment-baseline', 'central')
        .style('fill', legendData.color)
        .style('font-size', '9px')
        .text(legendData.text)

      const icon = createIcon(legendItem, legendData)
      // Calculte x offset using the remainder.
      const xOffset = (i % numColumns) * columnWidth
      // Calculate y offset using the quotient.
      const yOffset = ((i / numColumns) | 0) * lineHeight

      // Move icon and text to the correct location.
      icon.attr('transform', translateIcon(legendData.shape, xOffset, yOffset, icon))
      const iconWidth = icon.node()?.getBBox().width ?? 0
      text.attr(
        'transform',
        'translate(' + (xOffset + iconTextPadding + iconWidth) + ', ' + yOffset + ')'
      )
    })
  return ((data.length / 4) | 0) * lineHeight + lineHeight
}

export const getNearestByDate = <T extends { date: Date }>(
  invertedDate: Date,
  arr: T[]
): T => {
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
