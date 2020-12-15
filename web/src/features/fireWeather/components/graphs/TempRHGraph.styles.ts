import { makeStyles } from '@material-ui/core/styles'

const currLineColor = 'green'
export const observedTempColor = '#fb0058'
export const observedRHColor = '#057070'
export const forecastTempDotColor = '#a50b41'
export const forecastRHDotColor = '#17c4c4'
const forecastSummaryTempLineColor = forecastTempDotColor
const forecastSummaryRHLineColor = forecastRHDotColor
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

export const useStyles = makeStyles({
  // Give styling through classes for svg elements
  root: {
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
    '& .tooltip': {
      pointerEvents: 'none',
      font: '8.5px sans-serif',

      '&--hidden': {
        display: 'none'
      }
    },
    '& .tooltipCursor': {
      strokeWidth: 1,
      stroke: 'gray',
      strokeDasharray: '1,1',
      opacity: 0
    },
    '& .hidden': {
      visibility: 'hidden'
    },
    '& .observedTempSymbol': {
      stroke: observedTempColor,
      fill: observedTempColor
    },
    '& .observedTempPath': {
      stroke: observedTempColor
    },
    '& .observedRHSymbol': {
      stroke: observedRHColor,
      fill: observedRHColor
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
      opacity: 0.8
    },
    '& .modelTempPath': {
      stroke: modelTempColor,
      strokeDasharray: 4,
      opacity: 0.8
    },
    '& .modelRHSymbol': {
      stroke: modelRHColor,
      fill: modelRHColor,
      opacity: 0.8
    },
    '& .modelRHPath': {
      stroke: modelRHColor,
      strokeDasharray: 4,
      opacity: 0.8
    },
    '& .biasAdjModelTempSymbol': {
      stroke: biasModelTempColor,
      fill: biasModelTempColor,
      opacity: 0.8
    },
    '& .biasAdjModelTempPath': {
      stroke: biasModelTempColor,
      strokeDasharray: 5,
      opacity: 0.8
    },
    '& .biasAdjModelRHSymbol': {
      stroke: biasModelRHColor,
      fill: biasModelRHColor,
      opacity: 0.8
    },
    '& .biasAdjModelRHPath': {
      stroke: biasModelRHColor,
      strokeDasharray: 5,
      opacity: 0.8
    },
    '& .highResModelTempSymbol': {
      stroke: highResModelTempColor,
      fill: highResModelTempColor,
      opacity: 0.8
    },
    '& .highResModelTempPath': {
      stroke: highResModelTempColor,
      strokeDasharray: 2,
      opacity: 0.8
    },
    '& .highResModelRHSymbol': {
      stroke: highResModelRHColor,
      fill: highResModelRHColor,
      opacity: 0.8
    },
    '& .highResModelRHPath': {
      stroke: highResModelRHColor,
      strokeDasharray: 2,
      opacity: 0.8
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
      opacity: 0.8
    },
    '& .regionalModelTempPath': {
      stroke: regionalModelTempColor,
      strokeDasharray: 3,
      opacity: 0.8
    },
    '& .regionalModelRHSymbol': {
      stroke: regionalModelRHColor,
      fill: regionalModelRHColor,
      strokeWidth: 0.7,
      opacity: 0.8
    },
    '& .regionalModelRHPath': {
      stroke: regionalModelRHColor,
      strokeDasharray: 3,
      opacity: 0.8
    },
    '& .regionalModelSummaryTempArea': {
      stroke: regionalModelSummaryTempAreaColor,
      strokeWidth: 1,
      fill: regionalModelSummaryTempAreaColor,
      opacity: 0.3
    },
    '& .regionalModelSummaryRHArea': {
      stroke: regionalModelSummaryRHAreaColor,
      strokeWidth: 1,
      fill: regionalModelSummaryRHAreaColor,
      opacity: 0.3
    },
    '& .forecastTempDot': {
      stroke: forecastTempDotColor,
      fill: forecastTempDotColor,
      opacity: 0.8
    },
    '& .forecastRHDot': {
      stroke: forecastRHDotColor,
      fill: forecastTempDotColor,
      opacity: 0.8
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
