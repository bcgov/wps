import { Slider as S, withStyles } from '@material-ui/core'

const sliderBoxShadow =
  '0 3px 1px rgba(0,0,0,0.1),0 4px 8px rgba(0,0,0,0.13),0 0 0 1px rgba(0,0,0,0.02)'

const Slider = withStyles(theme => ({
  root: {
    color: theme.palette.primary.dark,
    height: 2,
    padding: '15px 0',
    width: 300,
    marginLeft: 2
  },
  thumb: {
    height: 23,
    width: 23,
    backgroundColor: '#fff',
    boxShadow: sliderBoxShadow,
    marginTop: -14,
    marginLeft: -14,
    '&:focus,&:hover,&$active': {
      boxShadow:
        '0 3px 1px rgba(0,0,0,0.1),0 4px 8px rgba(0,0,0,0.3),0 0 0 1px rgba(0,0,0,0.02)',
      // Reset on touch devices, it doesn't add specificity
      '@media (hover: none)': {
        boxShadow: sliderBoxShadow
      }
    }
  },
  active: {},
  valueLabel: {
    left: 'calc(-50% + 11px)',
    top: -22,
    '& *': {
      background: 'transparent',
      color: '#000'
    }
  },
  track: {
    height: 2
  },
  rail: {
    height: 2,
    opacity: 0.5,
    backgroundColor: theme.palette.primary.light
  },
  mark: {
    backgroundColor: theme.palette.primary.dark,
    height: 8,
    width: 1,
    marginTop: -3
  },
  markActive: {
    opacity: 1,
    backgroundColor: 'currentColor'
  }
}))(S)

export default Slider
