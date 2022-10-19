import _ from 'lodash'
import React from 'react'
import { Surface, Symbols } from 'recharts'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ToggleLegend = (props: any) => {
  const { payload, disabled, setDisabled } = props

  const handleClick = (dataKey: string) => {
    if (_.includes(disabled, dataKey)) {
      setDisabled(disabled.filter((obj: string) => obj !== dataKey))
    } else {
      setDisabled(disabled.concat(dataKey))
    }
  }

  return (
    <div className="toggle-legend">
      {payload.map((entry: { value: string; color: string }, idx: React.Key | null | undefined) => {
        const { value, color } = entry
        const active = _.includes(disabled, value)
        const style = {
          marginRight: 10,
          color: active ? '#AAA' : '#000'
        }

        return (
          <span key={idx} className="legend-item" onClick={() => handleClick(value)} style={style}>
            <Surface width={10} height={10} viewBox={{ x: 0, y: 0, width: 10, height: 10 }}>
              <Symbols cx={5} cy={5} type="circle" size={50} fill={color} />
              {active && <Symbols cx={5} cy={5} type="circle" size={25} fill={'#FFF'} />}
            </Surface>
            <span>{value}</span>
          </span>
        )
      })}
    </div>
  )
}

export default React.memo(ToggleLegend)
