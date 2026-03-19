import { FireZoneUnit } from "@/api/fbaAPI";
import { toggleSubscription } from "@/slices/settingsSlice";
import { AppDispatch, selectSettings } from "@/store";
import { nameFormatter } from "@/utils/stringUtils";
import {
  ListItem,
  ListItemButton,
  ListItemText,
  Switch,
  Typography,
} from "@mui/material";
import { useDispatch, useSelector } from "react-redux";

interface SubscriptionOptionProps {
  fireZoneUnit: FireZoneUnit;
}

const SubscriptionOption = ({ fireZoneUnit }: SubscriptionOptionProps) => {
  const dispatch: AppDispatch = useDispatch();
  const { subscriptions } = useSelector(selectSettings);

  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    handleSubscriptionUpdate();
  };

  const handleSubscriptionUpdate = () => {
    dispatch(toggleSubscription(fireZoneUnit.id));
  };

  return (
    <ListItem disableGutters disablePadding>
      <ListItemButton disableRipple onClick={handleSubscriptionUpdate}>
        <ListItemText>
          <Typography variant="body2" fontWeight="bold">
            {nameFormatter(fireZoneUnit.name, "Fire Zone", false)}
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
