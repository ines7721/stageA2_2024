from machine import ADC, Pin, mem32
import time
import math



mem32[0x40007000 + 0x5F0] = 1
check_resolution = mem32[0x40007000 + 0x5F0]
if check_resolution == 1 :
    nb_b = "10 bits"
if check_resolution == 0 :
    nb_b = "8 bits"
print("Résolution SAADC -", nb_b)


test_analogique = ADC(Pin(3, Pin.IN))
test = test_analogique.read_u16()
tension_test = (3 * test) / 6553
print("tension :", tension_test)


Pin(3, Pin.IN).off()


tension_test_off = (3 * test)/ 6553
print("tension off :", tension_test_off)

