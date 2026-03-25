import { FireZoneUnit } from "@/api/fbaAPI";
import { selectSettings } from "@/store";
import { fireZoneUnitNameFormatter } from "@/utils/stringUtils";
import {
  ListItem,
  ListItemButton,
  ListItemText,
  Switch,
  Typography,
} from "@mui/material";
import { useSelector } from "react-redux";

interface SubscriptionOptionProps {
  fireZoneUnit: FireZoneUnit;
  onToggle: (fireZoneUnitId: number) => void;
}

const SubscriptionOption = ({ fireZoneUnit, onToggle }: SubscriptionOptionProps) => {
  const { subscriptions } = useSelector(selectSettings);

  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onToggle(fireZoneUnit.id);
  };

  const handleSubscriptionUpdate = () => {
    onToggle(fireZoneUnit.id);
  };

  return (
    <ListItem disableGutters disablePadding>
      <ListItemButton disableRipple onClick={handleSubscriptionUpdate}>
        <ListItemText>
          <Typography
            variant="body2"
            fontWeight="bold"
            sx={{ whiteSpace: "pre-line" }}
          >
            {fireZoneUnitNameFormatter(fireZoneUnit.name)}
          </Typography>
        </ListItemText>
        <Switch
          edge="end"
          checked={subscriptions.includes(fireZoneUnit.id)}
          onChange={handleSwitchChange}
          slotProps={{
            input: {
              "aria-label": `Toggle subscription for ${fireZoneUnit.name}`,
            },
          }}
        />
      </ListItemButton>
    </ListItem>
  );
};

export default SubscriptionOption;
