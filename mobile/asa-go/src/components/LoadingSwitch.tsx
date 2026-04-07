import { Switch, SwitchProps } from "@mui/material";

interface LoadingSwitchProps {
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  "aria-label": string;
  loading?: boolean;
  disabled?: boolean;
  edge?: SwitchProps["edge"];
}

const LoadingSwitch = ({
  checked,
  onChange,
  "aria-label": ariaLabel,
  loading = false,
  disabled,
  edge,
}: LoadingSwitchProps) => (
  <Switch
    data-testid="loading-switch"
    checked={checked}
    onChange={onChange}
    disabled={disabled || loading}
    edge={edge}
    slotProps={{ input: { "aria-label": ariaLabel } }}
    sx={
      loading
        ? {
            "& .MuiSwitch-thumb": {
              animation: "thumbPulse 1.5s ease-in-out infinite",
            },
            "@keyframes thumbPulse": {
              "0%, 100%": { opacity: 1 },
              "50%": { opacity: 0.15 },
            },
          }
        : undefined
    }
  />
);

export default LoadingSwitch;
