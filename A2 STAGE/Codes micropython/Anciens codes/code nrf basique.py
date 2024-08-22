import time
import machine
from machine import ADC
from machine import Pin


analog_in_U = ADC(Pin(29, Pin.IN))
tensionU = analog_in_U.read_u16()   
#print("analog_in_u ", analog_in_U)
analog_in_U2 = ADC(Pin(2, Pin.IN))
tensionU2 = analog_in_U2.read_u16()
R1 = 100300
#in_U = machine.ADC(29)




while True:
    U = (tensionU * 3.3) / 65536
    #print("Tension U: ")
    
    U2 = (tensionU2 * 3.3) / 65536
    #print("Tension U2: ", U2)
    
    U1 = U - U2
    #print("Tension U1: ", U1)
    
    if U1 != 0:
        R2 = (U2 * R1) / (U - U2)
        print("Résistance calculée: ", R2)
    else:
        print("Erreur")
    
    time.sleep(1)