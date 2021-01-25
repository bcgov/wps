import React, { useRef, useEffect, useState } from 'react'
import ReactDOMServer from 'react-dom/server'
import { useDispatch, useSelector } from 'react-redux'
import { Container, PageHeader, PageTitle } from 'components'
import { formatDateInPDT} from 'utils/date'
import { makeStyles } from '@material-ui/core'

const useStyles = makeStyles({

})

const PeakBurninessPage = () => {
    const classes = useStyles()
    const dispatch = useDispatch()

    return (
        <main>
            <PageHeader title="Predictive Services Unit" productName="Data Analysis" />
            <PageTitle title="Data Analysis" />
            <Container>
                <p>Insert something here</p>
            </Container>
        </main>
    )
}

export default React.memo(PeakBurninessPage)