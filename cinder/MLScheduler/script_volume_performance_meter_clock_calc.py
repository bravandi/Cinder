def volume_performance_meter_clock_calc(t):
    #if(t.second > 30):
    #    t = t.replace(second=30)
    #else:
    #    t = t.replace(second=0)
    #t = t.replace(microsecond=0)
    #return t.strftime("%s")


    t = t.replace(second=0)
    t = t.replace(microsecond=0)
    return t.strftime("%s")