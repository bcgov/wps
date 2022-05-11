import React from 'react'
import { PDFViewer } from '@react-pdf/renderer'
import AdvisoryPDF from 'features/fba/components/AdvisoryPDF'

const AdvisoryPDFPreviewPage = () => {
  return (
    <PDFViewer>
      <AdvisoryPDF />
    </PDFViewer>
  )
}

export default React.memo(AdvisoryPDFPreviewPage)
