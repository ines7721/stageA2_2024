import machine
from machine import ADC
from machine import Pin



pin = Pin(2, Pin.IN)
U_analogue = ADC(pin)
print("U_analogue :", U_analogue)
print("adc.value() :", U_analogue.value())
U_board = U_analogue.value()

U = (U_board * 3.3) / 255
print("Tension calculée :", U)