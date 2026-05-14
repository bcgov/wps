export const getUpdatedSubscriptions = (
  subscriptions: number[],
  fireZoneUnitId: number,
): number[] => {
  if (subscriptions.includes(fireZoneUnitId)) {
    return subscriptions.filter((sub) => sub !== fireZoneUnitId);
  }

  return [...subscriptions, fireZoneUnitId];
};
