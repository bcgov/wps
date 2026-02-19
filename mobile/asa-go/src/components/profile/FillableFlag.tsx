import React from "react";

interface FillableFlagProps {
  maskId: string;
  percent: number;
  testId?: string;
  showPercent?: boolean;
}

const FillableFlag = ({
  maskId,
  percent,
  testId,
  showPercent = true,
}: FillableFlagProps) => {
  const fillWidth = (percent / 100) * 120;
  return (
    <svg
      width="100"
      height="43"
      viewBox="0 0 120 43"
      preserveAspectRatio="none"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
    >
      <defs>
        <mask id={`mask-${maskId}`}>
          <rect x="0" y="0" width={`${fillWidth}`} height="43" fill="white" />
        </mask>
        <filter id={`shadow-${maskId}`}>
          <feDropShadow
            dx="-2"
            dy="2"
            stdDeviation="4"
            floodColor="white"
            floodOpacity="1"
          />
          <feDropShadow
            dx="2"
            dy="2"
            stdDeviation="4"
            floodColor="white"
            floodOpacity="1"
          />
          <feDropShadow
            dx="2"
            dy="-2"
            stdDeviation="4"
            floodColor="white"
            floodOpacity="1"
          />
          <feDropShadow
            dx="-2"
            dy="-2"
            stdDeviation="4"
            floodColor="white"
            floodOpacity="1"
          />
        </filter>
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
      {showPercent && (
        <text
          x="60"
          y="21.5"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="16"
          fontWeight="bold"
          fill="black"
          filter={`url(#shadow-${maskId})`}
          data-testid={testId}
        >
          {percent}%
        </text>
      )}
    </svg>
  );
};

export default React.memo(FillableFlag);
