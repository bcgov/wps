import React from "react";
import {
  Grid,
  Typography,
  Checkbox,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Icon,
  FormControlLabel,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import {
  ADVISORY_ORANGE_FILL,
  ADVISORY_RED_FILL,
  HFI_ADVISORY,
  HFI_WARNING,
} from "@/featureStylers";
import { HFI_LAYER_NAME, ZONE_STATUS_LAYER_NAME } from "@/layerDefinitions";

const LegendGrid = styled(Grid)({
  display: "flex",
  flexDirection: "column",
  width: "fit-content",
  backgroundColor: "#fffafa",
  marginBottom: "0.5rem",
  alignItems: "flex-start",
});

const LegendSymbol = styled(Icon)({
  width: "2.5rem",
  height: "1rem",
});

const LegendTitle = styled(Typography)({
  fontVariant: "h1",
  fontSize: "1.2rem",
  fontWeight: "bold",
  margin: "0.6rem 0.2rem",
  textAlign: "left",
});

interface SubItem {
  label: string;
  symbol: string;
}

interface LegendItemProps {
  label: string;
  checked: boolean;
  onChange: (
    event: React.ChangeEvent<HTMLInputElement>,
    checked: boolean
  ) => void;
  subItems?: SubItem[];
  description?: string | null;
  renderEmptyDescription?: boolean;
}

const LegendItem = ({
  label,
  checked,
  onChange,
  subItems,
  description,
  renderEmptyDescription = false,
}: LegendItemProps) => (
  <div>
    <Grid>
      <Grid container alignItems="center">
        <FormControlLabel
          control={
            <Checkbox
              data-testid={`${label.toLowerCase().split(" ")[0]}-checkbox`}
              checked={checked}
              onChange={onChange}
            />
          }
          label={
            <Typography
              variant="h2"
              sx={{ fontSize: "1rem", fontWeight: "bold", cursor: "pointer" }}
            >
              {label}
            </Typography>
          }
          sx={{ paddingLeft: 2 }}
        />
      </Grid>
      <Grid container alignItems={"center"}>
        <Grid item sx={{ transform: "translate(50%, -50%)" }}>
          <Typography variant="body1" sx={{ fontSize: "0.75rem" }}>
            {description ?? (renderEmptyDescription && <span>&nbsp;</span>)}
          </Typography>
        </Grid>
      </Grid>
      {subItems && (
        <List dense sx={{ marginLeft: "2.5rem", marginTop: "-1rem" }}>
          {subItems.map((subItem) => (
            <ListItem disablePadding key={subItem.label}>
              <ListItemIcon>
                <LegendSymbol sx={{ backgroundColor: subItem.symbol }} />
              </ListItemIcon>
              <ListItemText>{subItem.label}</ListItemText>
            </ListItem>
          ))}
        </List>
      )}
    </Grid>
  </div>
);

interface LayerVisibility {
  [layerName: string]: boolean;
}

interface LegendProps {
  layerVisibility: LayerVisibility;
  onLayerVisibilityChange: (layerName: string, visible: boolean) => void;
}

const Legend = ({ layerVisibility, onLayerVisibilityChange }: LegendProps) => {
  const zoneStatusSubItems: SubItem[] = [
    { label: "Advisory", symbol: ADVISORY_ORANGE_FILL },
    { label: "Warning", symbol: ADVISORY_RED_FILL },
  ];
  const hfiSubItems: SubItem[] = [
    { label: "4,000 to 9,999", symbol: HFI_ADVISORY },
    { label: "≥10,000", symbol: HFI_WARNING },
  ];

  return (
    <LegendGrid padding={"0 0.5rem"} data-testid={`asa-go-map-legend`}>
      <LegendTitle align="center" gutterBottom>
        Layers
      </LegendTitle>
      <LegendItem
        label="Zone Unit Status"
        checked={layerVisibility[ZONE_STATUS_LAYER_NAME] ?? true}
        onChange={(_, checked) =>
          onLayerVisibilityChange(ZONE_STATUS_LAYER_NAME, checked)
        }
        subItems={zoneStatusSubItems}
      />
      <LegendItem
        label="HFI Potential (kW/m)"
        checked={layerVisibility[HFI_LAYER_NAME] ?? false}
        onChange={(_, checked) =>
          onLayerVisibilityChange(HFI_LAYER_NAME, checked)
        }
        subItems={hfiSubItems}
      />
    </LegendGrid>
  );
};

export default Legend;
