from machine import Pin, ADC, mem32
import time

compteur = 0
GPIO = Pin(2, Pin.IN)

#oversample :
mem32[0x40007000 + 0x5F4] = 5

#compter tâche SAMPLE:

while True :
    SAMPLE = mem32[0x40007000 + 0x004]
    if SAMPLE == 1 :
        compteur = compteur + 1
    else :
        SAMPLE = mem32[0x40007000 + 0x004]
    tension_ref_analog = ADC(GPIO)
    tension_ref = tension_ref_analog.read_u16()
    ref = tension_ref * (3.3 / 65535)
    print(ref)
    print(compteur)

