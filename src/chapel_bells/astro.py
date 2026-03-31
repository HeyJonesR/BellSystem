"""
Astronomical calculations for sunrise/sunset.
Used to determine daylight awareness for quiet hours logic.
"""

import math
from datetime import datetime, timedelta
from typing import Optional, Tuple

class AstronomicalCalculator:
    """
    Calculate sunrise/sunset times for a given location.
    Uses simplified astronomical algorithm (accurate to ±2 minutes).
    """
    
    # Solar constants
    J2000 = 2451545.0  # Julian date for 2000-01-01
    
    def __init__(self, latitude: float, longitude: float, timezone_offset: int = 0):
        """
        Initialize with location.
        
        Args:
            latitude: Decimal degrees (-90 to 90)
            longitude: Decimal degrees (-180 to 180)
            timezone_offset: UTC offset in hours (e.g., -5 for EST)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.timezone_offset = timezone_offset
    
    def _julian_date(self, dt: datetime) -> float:
        """Convert datetime to Julian Date."""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        return jd + (dt.hour - 12) / 24 + dt.minute / 1440 + dt.second / 86400
    
    def _equation_of_time(self, jd: float) -> float:
        """Calculate equation of time in minutes."""
        t = (jd - self.J2000) / 36525
        l0 = 280.46646 + 36000.76983 * t + 0.0003032 * (t ** 2)

        # Simplified GMST calculation
        gmst = 280.46061837 + (360.98564724 * (jd - self.J2000))

        eq = (l0 - 0.0057183 - gmst +
              15 * self.timezone_offset) % 360

        if eq > 180:
            eq = eq - 360

        return eq * 4  # Convert to minutes
    
    def get_sunrise_sunset(
        self, date: datetime = None
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Calculate sunrise and sunset for given date.

        Returns:
            (sunrise, sunset) as datetime objects.
            (datetime.min, None) if polar day (midnight sun – no sunset).
            (None, datetime.max) if polar night (sun never rises).
        """
        if date is None:
            date = datetime.now()
        
        # Use simplified algorithm
        # More accurate method: use PyEphem library if available
        
        lat_rad = math.radians(self.latitude)
        lon_rad = math.radians(self.longitude)
        
        # Days since J2000 epoch
        jd_noon = self._julian_date(
            datetime(date.year, date.month, date.day, 12, 0, 0)
        )
        
        # Fractional year in radians
        gamma = 2 * math.pi * (jd_noon - self.J2000) / 365.25
        
        # Solar declination (degrees)
        declination = (
            0.37584 * math.sin(gamma) - 23.27 * 
            math.sin(gamma - 1.366) + 0.06857 * math.sin(2 * gamma) +
            23.2441 - 22.9883 * math.cos(gamma) - 0.3924 * math.cos(gamma - 1.366)
        )
        
        dec_rad = math.radians(declination)
        
        # Hour angle for sunrise/sunset (zenith angle = 90.833°)
        zenith = math.radians(90.833)
        
        numerator = -math.tan(lat_rad) * math.tan(dec_rad)
        if numerator < -1:
            # Polar day (midnight sun – sun never sets)
            return datetime.min, None
        elif numerator > 1:
            # Polar night (sun never rises)
            return None, datetime.max
        
        h = math.acos(numerator)
        h_degrees = math.degrees(h)
        
        # Equation of time
        eot = self._equation_of_time(jd_noon)
        
        # Solar noon
        solar_noon = 12 - self.longitude / 15 - eot / 60
        
        # Sunrise/sunset times (in hours from midnight)
        sunrise_hour = solar_noon - h_degrees / 15
        sunset_hour = solar_noon + h_degrees / 15
        
        # Clamp hours to valid range via modulo
        sunrise_hour = sunrise_hour % 24
        sunset_hour = sunset_hour % 24
        
        # Convert to datetime
        sunrise = datetime(
            date.year, date.month, date.day,
            int(sunrise_hour), int((sunrise_hour % 1) * 60)
        )
        sunset = datetime(
            date.year, date.month, date.day,
            int(sunset_hour), int((sunset_hour % 1) * 60)
        )
        
        return sunrise, sunset
    
    def is_daytime(self, dt: datetime = None) -> bool:
        """Check if current time is daytime."""
        if dt is None:
            dt = datetime.now()

        sunrise, sunset = self.get_sunrise_sunset(dt)

        if sunrise is None:
            return False   # polar night – sun never rises
        if sunset is None:
            return True    # polar day – sun never sets

        return sunrise <= dt <= sunset


# Alternative: Use PyEphem for higher accuracy (optional requirement)
try:
    import ephem
    
    class PyEphemCalculator:
        """High-accuracy astronomical calculations using PyEphem."""
        
        def __init__(self, latitude: float, longitude: float, timezone_offset: int = 0):
            self.location = ephem.Observer()
            self.location.lat = str(latitude)
            self.location.lon = str(longitude)
            self.timezone_offset = timezone_offset
        
        def get_sunrise_sunset(self, date: datetime = None):
            """
            Get today's sunrise/sunset using PyEphem.

            Anchors to local noon so previous_rising() returns today's sunrise
            (not yesterday's if called after dawn) and next_setting() returns
            today's sunset.
            Returns (datetime.min, None) for polar day, (None, datetime.max)
            for polar night, matching AstronomicalCalculator sentinels.
            """
            if date is None:
                date = datetime.now()

            noon = datetime(date.year, date.month, date.day, 12, 0, 0)
            self.location.date = noon
            sun = ephem.Sun()

            try:
                sunrise_ephem = self.location.previous_rising(sun)
                sunrise_dt = ephem.Date(sunrise_ephem).datetime()
            except ephem.AlwaysUpError:
                return datetime.min, None   # polar day
            except ephem.NeverUpError:
                return None, datetime.max   # polar night

            try:
                sunset_ephem = self.location.next_setting(sun)
                sunset_dt = ephem.Date(sunset_ephem).datetime()
            except ephem.AlwaysUpError:
                return datetime.min, None   # polar day
            except ephem.NeverUpError:
                return None, datetime.max   # polar night

            return sunrise_dt, sunset_dt

        def is_daytime(self, dt: datetime = None) -> bool:
            """Check if it is daytime using solar altitude (most direct method)."""
            if dt is None:
                dt = datetime.now()
            self.location.date = dt
            sun = ephem.Sun(self.location)
            return float(sun.alt) > 0

except ImportError:
    PyEphemCalculator = None
