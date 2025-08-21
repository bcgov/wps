import Popover from "@mui/material/Popover";
import Legend from "@/components/map/Legend";
import { LayerVisibility } from "@/components/map/layerVisibility";

interface LegendPopoverProps {
  anchorEl: HTMLButtonElement | null;
  onClose: () => void;
  layerVisibility: LayerVisibility;
  onLayerVisibilityChange: (layerName: string, visible: boolean) => void;
}

const LegendPopover = ({
  anchorEl,
  onClose,
  layerVisibility,
  onLayerVisibilityChange,
}: LegendPopoverProps) => {
  const open = Boolean(anchorEl);
  return (
    <Popover
      data-testid="asa-go-map-legend-popover"
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{
        vertical: "top",
        horizontal: "left",
      }}
      transformOrigin={{
        vertical: "bottom",
        horizontal: "left",
      }}
      slotProps={{
        paper: {
          sx: {
            borderRadius: 2,
            border: "2px solid black",
            boxShadow: 0,
            marginLeft: "-8px",
          },
        },
      }}
    >
      <Legend
        layerVisibility={layerVisibility}
        onLayerVisibilityChange={onLayerVisibilityChange}
      />
    </Popover>
  );
};

export default LegendPopover;
