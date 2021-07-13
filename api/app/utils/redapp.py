""" Call Java REDapp code.
"""
from datetime import datetime
# import jnius
# from jnius import autoclass


def FBPCalculateStatisticsCOM(elevation: float,  # pylint: disable=invalid-name
                              latitude: float,
                              longitude: float,
                              time_of_interest: datetime,
                              ffmc: float,
                              dmc: float,
                              dc: float,
                              bui: float,
                              wind_speed: float,
                              wind_direction: float):
    """ ca.cwfgm.fbp.FBPCalculations::FBPCalculateStatisticsCOM
    """
    from jnius import autoclass  # pylint: disable=import-outside-toplevel
    Calendar = autoclass('java.util.Calendar')  # pylint: disable=invalid-name
    TimeZone = autoclass('java.util.TimeZone')  # pylint: disable=invalid-name
    FBPCalculations = autoclass('ca.cwfgm.fbp.FBPCalculations')  # pylint: disable=invalid-name

    fbp = FBPCalculations()
    fbp.elevation = elevation
    fbp.latitude = latitude
    fbp.longitude = longitude
    fbp.ffmc = ffmc
    fbp.dmc = dmc
    fbp.dc = dc
    fbp.bui = bui
    fbp.windSpeed = wind_speed
    fbp.windDirection = wind_direction

    gmt = Calendar.getInstance(TimeZone.getTimeZone("GMT"))
    gmt.set(time_of_interest.year, time_of_interest.month, time_of_interest.day,
            time_of_interest.hour, time_of_interest.minute, time_of_interest.second)
    fbp.m_date = gmt

    fbp.FBPCalculateStatisticsCOM()

    return fbp


def get_class_FBPCalculations():
    """
    public class FBPCalculations {
        public double ros_t;
        public double ros_eq;
        public double fros;
        public double bros;
        public double rso;
        public double hfi;
        public double ffi;
        public double bfi;
        public double area;
        public double perimeter;
        public double distanceHead;
        public double distanceFlank;
        public double distanceBack;
        public double lb;
        public double csi;
        public double cfb;
        public double sfc;
        public double tfc;
        public double cfc;
        public double isi;
        public double fmc;
        public double wsv;
        public double raz;
        public double conifMixedWood;
        public double deadBalsam;
        public double grassCuring;
        public double grassFuelLoad;
        public double crownBase;
        public double elapsedTime;
        public double ffmc;
        public double windSpeed;
        public double windDirection;
        public double bui;
        public double dmc;
        public double dc;
        public double slopeValue;
        public double aspect;
        public double latitude;
        public double longitude;
        public double elevation;
        public boolean acceleration;
        public boolean useCrownBaseHeight;
        public boolean useBui;
        public boolean useBuildup;
        public boolean useSlope;
        public boolean useGreenup;
        public int fuelType;
        public String fireDescription;
        public String headFireDescription;
        public String flankFireDescription;
        public String backFireDescription;

        public Calendar m_date;

        public boolean cfbPossible = true;

        public FBPCalculations() {
        initializeInputValues();
        initializeOutputValues();
        }
        public void FBPCalculateStatisticsCOM()
    }
    """
    # We get a segmentation fault if we import jnius at the top of the file, so we do it here
    # instead.
    from jnius import autoclass
    return autoclass('ca.cwfgm.fbp.FBPCalculations')


def get_class_FWICalculations():
    """
    public class FWICalculations {

        public double ystrdyFFMC;
        public double ystrdyDMC;
        public double ystrdyDC;
        public double noonTemp;
        public double noonRH;
        public double noonPrecip;
        public double noonWindSpeed;
        public double hrlyTemp;
        public double hrlyRH;
        public double hrlyPrecip;
        public double hrlyWindSpeed;
        public double dlyFFMC;
        public double dlyDMC;
        public double dlyDC;
        public double dlyISI;
        public double dlyBUI;
        public double dlyFWI;
        public double dlyDSR;
        public double hlyHFFMC;
        public double hlyHISI;
        public double hlyHFWI;
        public double prvhlyFFMC;
        public boolean calcHourly;
        public boolean useVanWagner;
        public boolean useLawsonPreviousHour = false;
        private WorldLocation wl;
        public Calendar m_date;
        public String m_init_timezone_code;

        public double getLatitude();
        public void setLatitude(double value);
        public double getLongitude();
        public void setLongitude(double value);

        public void setTimezone(WTimeSpan span);
        public void setDST(WTimeSpan span);

        public void FWICalculateDailyStatisticsCOM();
    """
    # return None
    import jnius
    return jnius.autoclass('ca.cwfgm.fwi.FWICalculations')
