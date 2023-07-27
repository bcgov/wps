import { styled } from '@mui/material/styles'
import React, { useState, MouseEvent } from 'react'

const PREFIX = 'TableHeader'

const classes = {
  header: `${PREFIX}-header`
}

interface TableHeaderProps {
  text: string
  testId?: string
  largerMaxWidth?: boolean
}

const TableHeader = (props: TableHeaderProps) => {
  let maxWidth = '200px'
  if (!props.largerMaxWidth) {
    maxWidth = '80px'
  }

  const Root = styled('div')({
    [`&.${classes.header}`]: {
      overflow: 'hidden',
      whiteSpace: 'nowrap',
      textOverflow: 'ellipsis',
      maxWidth: maxWidth,
      '& span': {
        display: 'none'
      },
      '&:hover span': {
        display: 'block',
        backgroundColor: '#4f4f4f',
        opacity: '0.8',
        paddingLeft: '5px',
        paddingRight: '5px',
        maxWidth: '225px',
        color: '#fff',
        textAlign: 'center',
        borderRadius: '6px',
        /* Position the tooltip */
        position: 'absolute',
        left: '2px',
        top: '41px'
      }
    }
  })

  const [left, setLeft] = useState(0)

  const findParentTableContainer = (element: HTMLElement | null): HTMLElement | null => {
    // find the parent table container - if it exists.
    if (!element) {
      // failed to find the table.
      return null
    }
    if (element instanceof HTMLTableElement) {
      // return the table container.
      return element.parentElement
    }
    // keep looking for the parent table container.
    return findParentTableContainer(element.parentElement)
  }

  const hover = (e: MouseEvent<HTMLDivElement>) => {
    const fireTableContainer = findParentTableContainer(e.currentTarget)
    if (fireTableContainer) {
      const child = e.currentTarget.children[0] as HTMLSpanElement
      // clone the span, throw it into the dom, and measure the length of the text - then get rid of it.
      const clone = child.cloneNode(true) as HTMLSpanElement
      clone.style.visibility = 'hidden'
      clone.style.position = 'absolute'
      e.currentTarget.appendChild(clone)
      // NOTE: The text width is not calculated correctly from within cypress, because the hover style doesn't
      // get applied to the span from within cypress.
      const textWidth = clone.getBoundingClientRect().width
      clone.remove()
      // now we know how wide the text is, we can move it left if it exceeds the container.
      const clientWidth = fireTableContainer.getBoundingClientRect().right
      const scrollBarWidth = fireTableContainer.offsetWidth - fireTableContainer.clientWidth
      const availabeWidth = clientWidth - scrollBarWidth
      if (e.currentTarget.getBoundingClientRect().left + textWidth >= availabeWidth) {
        setLeft(availabeWidth - (e.currentTarget.getBoundingClientRect().left + textWidth))
      } else {
        setLeft(0)
      }
    }
  }

  return (
    <Root
      className={classes.header}
      onMouseOver={hover}
      {...(props.testId ? { 'data-testid': `header-${props.testId}` } : {})}
    >
      {props.text}
      <span style={{ left: left }} {...(props.testId ? { 'data-testid': `tooltip-${props.testId}` } : {})}>
        {props.text}
      </span>
    </Root>
  )
}

export default React.memo(TableHeader)
