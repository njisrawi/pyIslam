# -*- coding: utf-8 -*-

from math import pi, atan, sqrt, tan, floor
from datetime import time
from pyIslam.hijri import HijriDate
from pyIslam.baselib import dcos, dsin, gregorianToJulianDay


class PrayerConf:
    def __init__(self, longitude, latitude, timezone, zenith_ref=3,
                 asr_madhab=1, enable_summer_time=False):
        '''Initialize the PrayerConf object
        @param longitude: geographical longitude of the given location
        @param latitude: geographical latitude of the given location
        @param timezone: the time zone GMT(+/-timezone)
        @param zenith_ref: integer value for the Fajr and
        Ishaa zenith angle reference
        1 = University of Islamic Sciences, Karachi
        2 = Muslim World League
        3 = Egyptian General Authority of Survey (default)
        4 = Umm al-Qura University, Makkah
        5 = Islamic Society of North America
        @param asr_madhab: integer value
        1 = Shafii (default)
        2 = Hanafi
        @param: enable_summer_time: True if summer time is used in the place,
        False (default) if not'''

        self.longitude = longitude
        self.latitude = latitude
        self.timezone = timezone
        self.sherookZenith = 90.83333  # Constants
        self.maghrebZenith = 90.83333

        if asr_madhab == 2:
            self.asrMadhab = asr_madhab  # 1 = Shafii, 2 = Hanafi
        else:
            self.asrMadhab = 1

        self.middleLongitude = self.timezone * 15
        self.longitudeDifference = (self.middleLongitude - self.longitude) / 15

        self.summerTime = enable_summer_time

        zeniths = {1: (108.0, 108.0), # 1 = University of Islamic Sciences, Karachi
                   2: (108.0, 107.0), # 2 = Muslim World League
                   3: (109.5, 107.5), # 3 = Egyptian General Authority of Survey
                   4: (108.5, None),  # 4 = Umm al-Qura University, Makkah
                   5: (105.0, 105.0)} # 5 = Islamic Society of North America

        # Pythonista way to write switch-case instruction
        (self.fajrZenith, self.ishaaZenith) = zeniths.get(zenith_ref, zeniths[3])


class Prayer:
    '''Prayer times and qiblah calculating class'''
    def __init__(self, conf, dat, correction_val=0):
        self.__conf = conf
        self.__date = dat

        if not (correction_val in range(-2, 3)):
            raise Exception('Correction value exception')
        else:
            self.__correction_val = correction_val

    def __equationOfTime(self):
        '''Get equation of time'''
        n = gregorianToJulianDay(self.__date) - 2451544.5
        g = 357.528 + 0.9856003 * n
        c = 1.9148 * dsin(g) + 0.02 * dsin(2 * g) + 0.0003 * dsin(3 * g)
        lamda = 280.47 + 0.9856003 * n + c
        r = (-2.468 * dsin(2 * lamda)
             + 0.053 * dsin(4 * lamda)
             + 0.0014 * dsin(6 * lamda))
        return (c + r) * 4

    def __asrZenith(self):
        '''Get the zenith angle for asr (according to choosed asr fiqh)'''
        delta = self.__sunDeclination()
        x = (dsin(self.__conf.latitude) * dsin(delta)
             + dcos(self.__conf.latitude) * dcos(delta))
        a = atan(x / sqrt(-x * x + 1))
        x = self.__conf.asrMadhab + (1 / tan(a))
        return 90 - (180 / pi) * (atan(x) + 2 * atan(1))

    def __sunDeclination(self):
        '''Get sun declination'''
        n = gregorianToJulianDay(self.__date) - 2451544.5
        epsilon = 23.44 - 0.0000004 * n
        l = 280.466 + 0.9856474 * n
        g = 357.528 + 0.9856003 * n
        lamda = l + 1.915 * dsin(g) + 0.02 * dsin(2 * g)
        x = dsin(epsilon) * dsin(lamda)
        return (180 / (4 * atan(1))) * atan(x / sqrt(-x * x + 1))

    def __dohrTime(self):
        '''# Dohr time for internal use, return number of hours,
        not time object'''
        ld = self.__conf.longitudeDifference
        time_eq = self.__equationOfTime()
        duhr_t = 12 + ld + time_eq / 60
        return duhr_t

    def __prayerTime(self, zenith):
        '''Get Times for "Fajr, Sherook, Asr, Maghreb, ishaa"'''
        delta = self.__sunDeclination()
        s = ((dcos(zenith)
              - dsin(self.__conf.latitude) * dsin(delta))
             / (dcos(self.__conf.latitude) * dcos(delta)))
        return (180 / pi * (atan(-s / sqrt(-s * s + 1)) + pi / 2)) / 15

    def __hoursToTime(val, shift, summer_time):
        '''Convert a decimal value (in hours) to time object'''
        if not (isinstance(shift, float) or isinstance(shift, int)):
            raise Exception("'shift' value must be an 'int' or 'float'")

        if summer_time:
            st = 1
        else:
            st = 0

        hours = val + shift/3600
        minutes = (hours - floor(hours)) * 60
        seconds = (minutes - floor(minutes)) * 60
        return time((floor(hours) + st), floor(minutes), floor(seconds))

    def fajrTime(self, shift=0.0):
        '''Get the Fajr time'''
        return (Prayer._Prayer__hoursToTime
                (self.__dohrTime() - self.__prayerTime(self.__conf.fajrZenith),
                 shift, self.__conf.summerTime))

    def sherookTime(self, shift=0.0):
        '''Get the Sunrise (Sherook) time'''
        return (Prayer._Prayer__hoursToTime
                (self.__dohrTime()
                 - self.__prayerTime(self.__conf.sherookZenith),
                 shift, self.__conf.summerTime))

    def dohrTime(self, shift=0.0):
        return Prayer._Prayer__hoursToTime(self.__dohrTime(),
                                           shift, self.__conf.summerTime)

    def asrTime(self, shift=0.0):
        '''Get the Asr time'''
        return (Prayer._Prayer__hoursToTime
                (self.__dohrTime() + self.__prayerTime(self.__asrZenith()),
                 shift, self.__conf.summerTime))

    def maghrebTime(self, shift=0.0):
        '''Get the Maghreb time'''
        return (Prayer._Prayer__hoursToTime
                (self.__dohrTime() + self.__prayerTime
                 (self.__conf.maghrebZenith), shift, self.__conf.summerTime))

    def ishaaTime(self, shift=0.0):
        '''Get the Ishaa time'''
        if (self.__conf.ishaaZenith is None):
            # ishaaZenith==None <=> method == Umm al-Qura University, Makkah
            if HijriDate.getHijri(self.__date,
                                  self.__correction_val).month == 9:
                ishaa_t = self.__dohrTime()
                + self.__prayerTime(self.__conf.maghrebZenith) + 2.0
            else:
                ishaa_t = self.__dohrTime()
                + self.__prayerTime(self.__conf.maghrebZenith) + 1.5
        else:
            ishaa_t = self.__prayerTime(self.__conf.ishaaZenith)
            ishaa_t = self.__dohrTime() + ishaa_t
        return Prayer._Prayer__hoursToTime(ishaa_t, shift,
                                           self.__conf.summerTime)
