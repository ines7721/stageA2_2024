import machine 
from machine import ADC, Pin, mem32



resolution_chge = mem32[0x40007000 + 0x5F0]
print("resolution :", resolution_chge)

config = mem32[0x40007000 + 0x518 + (0x10 + 0x10)]
print("config pin 2 :", config)
 #131072

tneion_ref = mem32[0x10001000 + 0x304] 
print(tneion_ref)

mem32[0x40007000 + 0x5F8]  = 1
tt = mem32[0x40007000 + 0x5F8] 
print("tt", tt)

