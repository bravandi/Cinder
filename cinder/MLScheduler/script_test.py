from script_volume_clock_calc import *
from script_volume_performance_meter_clock_calc import *
from datetime import datetime
import pdb

if __name__ == '__main__':
    n1 = datetime.now()
    n2 = datetime.now()

    print ("n1 time: " + str(n1) + "\n")
    print ("n2 time: " + str(n2) + "\n")

    print ("volume_performance_meter_clock_calc:\n")
    print (volume_performance_meter_clock_calc(n1))
    print (datetime.fromtimestamp(float(volume_performance_meter_clock_calc(n1))))

    print ("volume_clock_calc:\n")
    print (volume_clock_calc(n2))
    print (datetime.fromtimestamp(float(volume_clock_calc(n2))))