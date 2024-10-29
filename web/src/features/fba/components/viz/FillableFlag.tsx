import React from 'react'

interface FillableFlagProps {
  maskId: string
  percent: number
}

const FillableFlag = ({ maskId, percent }: FillableFlagProps) => {
  const fillWidth = (percent / 100) * 120
  return (
    <svg width="120" height="43" viewBox="0 0 120 43" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <mask id={`mask-${maskId}`}>
          <rect x="0" y="0" width={`${fillWidth}`} height="43" fill="white" />
        </mask>
      </defs>
      <path
        d="M10.7443 41.822L0.558603 21.375L10.7443 0.928009L119.5 0.928009L119.5 41.822L10.7443 41.822Z"
        stroke="black"
        fill="black"
        mask={`url(#mask-${maskId})`}
      />
      <path
        d="M10.7443 41.822L0.558603 21.375L10.7443 0.928009L119.5 0.928009L119.5 41.822L10.7443 41.822Z"
        stroke="black"
      />
    </svg>
  )
}

export default React.memo(FillableFlag)

{
  /* <linearGradient id="grad" x1="0%" x2="100%" y1="0%" y2="0%">
<stop offset="0%" stop-color="black" />
<stop offset="50%" stop-color="white" />
</linearGradient> */
}

{
  /* <pattern id="pattern" x="0" y="0" width="2" height="43" patternUnits="userSpaceOnUse">
<rect width="2" height="43" x="0" y="0" fill="black" />
</pattern> */
}
