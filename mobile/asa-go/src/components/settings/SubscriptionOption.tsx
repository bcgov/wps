import { nameFormatter } from "@/utils/stringUtils";
import { ListItem, Typography, Switch } from "@mui/material";
import { useState } from "react";

interface SubscriptionOptionProps {
  fireZoneUnit: string;
}

const SubscriptionOption = ({ fireZoneUnit }: SubscriptionOptionProps) => {
  const [checked, setChecked] = useState(false);

  // Toggles when the user taps anywhere on the row (except the switch)
  const handleRowToggle = () => {
    setChecked((prev) => !prev);
  };

  // Toggles when the user taps the switch directly
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(e.target.checked);
  };

  return (
    <ListItem
      onClick={handleRowToggle}
      secondaryAction={
        <Switch
          edge="end"
          checked={checked}
          onChange={handleSwitchChange}
          // Prevent the parent ListItemButton from also toggling
          onClick={(e) => e.stopPropagation()}
          inputProps={{
            "aria-label": `Toggle subscription for ${fireZoneUnit}`,
          }}
        />
      }
      disableGutters
    >
      <Typography variant="body2" fontWeight="bold">
        {nameFormatter(fireZoneUnit, "Fire Zone", false)}
      </Typography>
    </ListItem>
  );
};

export default SubscriptionOption;
