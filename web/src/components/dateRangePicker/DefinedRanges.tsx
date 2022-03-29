import React from 'react'
import { List, ListItem, ListItemText } from '@material-ui/core'
import { DefinedRange, DateRange } from 'components/dateRangePicker/types'
import { isSameRange } from 'components/dateRangePicker/utils'

type DefinedRangesProps = {
  setRange: (range: DateRange) => void
  selectedRange: DateRange
  ranges: DefinedRange[]
}

const DefinedRanges: React.FunctionComponent<DefinedRangesProps> = ({
  ranges,
  setRange,
  selectedRange
}: DefinedRangesProps) => (
  <List>
    {ranges.map((range, idx) => (
      <ListItem button key={idx} onClick={() => setRange(range)}>
        <ListItemText
          primaryTypographyProps={{
            variant: 'body2',
            style: {
              fontWeight: isSameRange(range, selectedRange) ? 'bold' : 'normal'
            }
          }}
        >
          {range.label}
        </ListItemText>
      </ListItem>
    ))}
  </List>
)

export default DefinedRanges
