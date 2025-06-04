# jalaliDate.py
# Library to convert Gregorian datetime to Jalali (Persian) datetime
# Author: SCR-IR
# Source: https://github.com/SCR-IR/jalaliDate-Python

import datetime

def gregorian_to_jalali(g_y, g_m, g_d):
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy = g_y - 1600
    gm = g_m - 1
    gd = g_d - 1

    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    for i in range(gm):
        g_day_no += g_days_in_month[i]
    if gm > 1 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        # leap year adjustment
        g_day_no += 1
    g_day_no += gd

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053  # 12053 = 33 years
    j_day_no = j_day_no % 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 366) // 365
        j_day_no = (j_day_no - 366) % 365

    for i in range(11):
        if j_day_no < j_days_in_month[i]:
            jm = i + 1
            jd = j_day_no + 1
            break
        j_day_no -= j_days_in_month[i]
    else:
        jm = 12
        jd = j_day_no + 1

    return jy, jm, jd

class JalaliDate:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __str__(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

def datetime2jalali(dt):
    """Convert a datetime.datetime object to JalaliDate."""
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return JalaliDate(jy, jm, jd)

if __name__ == "__main__":
    now = datetime.datetime.now()
    print("Gregorian:", now)
    print("Jalali:", datetime2jalali(now))