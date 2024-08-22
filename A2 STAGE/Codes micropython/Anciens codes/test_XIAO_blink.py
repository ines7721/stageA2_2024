from machine import Pin
from timeit import timer
 
led = Pin(18, Pin.OUT)
Counter = 0
Fun_Num = 0
 
def fun(tim):
    global Counter
    Counter = Counter + 1 
    print(Counter)
    led.value(Counter%2)
 
tim = Timer(-1)
tim.init(period=500, mode=Timer.PERIODIC, callback=fun)