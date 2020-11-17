import { makeStyles } from '@material-ui/core/styles'

const currLineColor = 'green'
export const observedTempColor = '#a50b41'
export const observedRHColor = '#17c4c4'
export const modelTempColor = '#f56c9c'
export const modelRHColor = '#32e7e7'
export const biasModelTempColor = '#e604d0'
export const biasModelRHColor = '#176bc4'
export const modelSummaryTempAreaColor = '#ff96aa'
export const modelSummaryRHAreaColor = '#94ffeb'
export const highResModelTempColor = '#a017c2'
export const highResModelRHColor = '#3ac417'
export const highResModelSummaryTempAreaColor = '#cba9d6'
export const highResModelSummaryRHAreaColor = '#b5f0a5'
export const regionalModelTempColor = '#ea6d0e'
export const regionalModelRHColor = '#026200'
export const regionalModelSummaryTempAreaColor = '#f48f41'
export const regionalModelSummaryRHAreaColor = '#2a8989'
export const forecastTempDotColor = '#fb0058'
export const forecastRHDotColor = '#057070'
const forecastSummaryTempLineColor = forecastTempDotColor
const forecastSummaryRHLineColor = forecastRHDotColor

export const useStyles = makeStyles({
  // Give styling through classes for svg elements
  root: {
    paddingBottom: 15,
    '& .xAxisLabel': {
      textAnchor: 'start',
      font: '9px sans-serif'
    },
    '& .yAxisLabel': {
      textAnchor: 'middle',
      font: '9px sans-serif'
    },
    '& .currLine': {
      strokeWidth: 1,
      stroke: currLineColor,
      strokeDasharray: '4,4'
    },
    '& .currLabel': {
      font: '9px sans-serif',
      fill: currLineColor
    },
    '& .tooltipCursor': {
      strokeWidth: 1,
      stroke: 'gray',
      strokeDasharray: '1,1',
      opacity: 0
    },
    '& .tooltip': {
      pointerEvents: 'none',
      font: '8.5px sans-serif',

      '&--hidden': {
        display: 'none'
      }
    },
    '& .observedTempSymbol': {
      stroke: observedTempColor,
      fill: observedTempColor,
      cursor: 'pointer'
    },
    '& .observedTempPath': {
      stroke: observedTempColor
    },
    '& .observedRHSymbol': {
      stroke: observedRHColor,
      fill: observedRHColor,
      cursor: 'pointer'
    },
    '& .observedRHPath': {
      stroke: observedRHColor
    },
    '& .modelSummaryTempArea': {
      stroke: modelSummaryTempAreaColor,
      strokeWidth: 1,
      fill: modelSummaryTempAreaColor,
      opacity: 0.5
    },
    '& .modelSummaryRHArea': {
      stroke: modelSummaryRHAreaColor,
      strokeWidth: 1,
      fill: modelSummaryRHAreaColor,
      opacity: 0.5
    },
    '& .modelTempSymbol': {
      stroke: modelTempColor,
      fill: modelTempColor,
      cursor: 'pointer'
    },
    '& .modelTempPath': {
      stroke: modelTempColor
    },
    '& .modelRHSymbol': {
      stroke: modelRHColor,
      fill: modelRHColor,
      cursor: 'pointer'
    },
    '& .modelRHPath': {
      stroke: modelRHColor
    },
    '& .biasAdjModelTempSymbol': {
      stroke: biasModelTempColor,
      fill: biasModelTempColor,
      cursor: 'pointer'
    },
    '& .biasAdjModelTempPath': {
      stroke: biasModelTempColor
    },
    '& .biasAdjModelRHSymbol': {
      stroke: biasModelRHColor,
      fill: biasModelRHColor,
      cursor: 'pointer'
    },
    '& .biasAdjModelRHPath': {
      stroke: biasModelRHColor
    },
    '& .highResModelTempSymbol': {
      stroke: highResModelTempColor,
      fill: highResModelTempColor,
      cursor: 'pointer'
    },
    '& .highResModelTempPath': {
      stroke: highResModelTempColor
    },
    '& .highResModelRHSymbol': {
      stroke: highResModelRHColor,
      fill: highResModelRHColor,
      cursor: 'pointer'
    },
    '& .highResModelRHPath': {
      stroke: highResModelRHColor
    },
    '& .highResModelSummaryTempArea': {
      stroke: highResModelSummaryTempAreaColor,
      strokeWidth: 1,
      fill: highResModelSummaryTempAreaColor,
      opacity: 0.5
    },
    '& .highResModelSummaryRHArea': {
      stroke: highResModelSummaryRHAreaColor,
      strokeWidth: 1,
      fill: highResModelSummaryRHAreaColor,
      opacity: 0.5
    },
    '& .regionalModelTempSymbol': {
      stroke: regionalModelTempColor,
      fill: regionalModelTempColor,
      cursor: 'pointer'
    },
    '& .regionalModelTempPath': {
      stroke: regionalModelTempColor
    },
    '& .regionalModelRHSymbol': {
      stroke: regionalModelRHColor,
      fill: regionalModelRHColor,
      strokeWidth: 0.7,
      cursor: 'pointer'
    },
    '& .regionalModelRHPath': {
      stroke: regionalModelRHColor
    },
    '& .regionalModelSummaryTempArea': {
      stroke: regionalModelSummaryTempAreaColor,
      strokeWidth: 1,
      fill: regionalModelSummaryTempAreaColor,
      opacity: 0.2
    },
    '& .regionalModelSummaryRHArea': {
      stroke: regionalModelSummaryRHAreaColor,
      strokeWidth: 1,
      fill: regionalModelSummaryRHAreaColor,
      opacity: 0.2
    },
    '& .forecastTempDot': {
      stroke: forecastTempDotColor,
      fill: 'none',
      cursor: 'pointer'
    },
    '& .forecastRHDot': {
      stroke: forecastRHDotColor,
      fill: 'none',
      cursor: 'pointer'
    },
    '& .forecastSummaryTempLine': {
      stroke: forecastSummaryTempLineColor,
      strokeWidth: 1.5,
      opacity: 0.8
    },
    '& .forecastSummaryRHLine': {
      stroke: forecastSummaryRHLineColor,
      strokeWidth: 1.5,
      opacity: 0.8
    }
  }
})
