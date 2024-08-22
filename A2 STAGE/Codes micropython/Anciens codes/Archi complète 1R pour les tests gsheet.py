from machine import ADC, Pin, mem32
import time

#mise en place de la résolution de l'ADC, fréquence d'échantillonnage, étalonnage de l'ADC toutes les ETLN mesures 
def setup(resolution, freq_echantillonnage, ETLN) :
    mem32[BASE_ADDR_ADC + 0x300] = 0x00000000
    inten = mem32[BASE_ADDR_ADC + 0x300]
    print(inten)
    
    mem32[BASE_ADDR_ADC + 0x304] =  0x00000000
    intenset = mem32[BASE_ADDR_ADC + 0x304]
    print(intenset)
    
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("résolution ADC =", check_resolution, "// 0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")
    
    mem32[BASE_ADDR_ADC + 0x5F8] = freq_echantillonnage
    check_freq = mem32[BASE_ADDR_ADC + 0x5F8]
    print("Fréquence d'échantillonnage =", check_freq)
    
    if ETLN == 2000 :
        mem32[BASE_ADDR_ADC + 0x00C] =  0x00000000
        #REG_etalonnage1 = mem32[BASE_ADDR_ADC + 0x00C]
        #print("REG_etalonnage1 =", REG_etalonnage1)
        check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
        #while check_ETLN < 1 :
            #check_ETLN = mem32[0x40007000 + 0x110]
        print("check_ETLN =", check_ETLN)
        if check_ETLN == 1 :
            print("Etalonnage effectué.")
        else :
            print("Etalonnage non effectué")
    
    
#faire en sorte que le PIN_alim délivre VDD au circuit
def alimentation(PIN_alim) :
    GPIO = Pin(PIN_alim, Pin.OUT)
    GPIO.value(1)
    
def tension_ref(PIN_U) :
    tension_ref_analog = ADC(Pin(PIN_U, Pin.IN))
    tension_ref = tension_ref_analog.read_u16()
    ref = tension_ref * (3.6 / 65535)
    return ref        
    
def calcul_resistance(ref, R1, PIN_U, PIN_U2) :
    tension_U2_analog = ADC(Pin(PIN_U2, Pin.IN))
    tensionU2 = tension_U2_analog.read_u16()
    U2 = tensionU2 * (3.3 / 65535)
    #print("Tension sur la broche 2: ",U2)
    tension_U_analog = ADC(Pin(PIN_U, Pin.IN))    
    tensionU = tension_U_analog.read_u16()   
    U = tensionU * (3.3 / 65535)
    #print("Tension sur la broche 29 :",U)
    U1 = U-U2
    #print("Tension aux bornes de la résistance inconnue :", U1)
    if U1!=0 :
        R2 = (U2 * R1)/U1
        #print(R2)
    else :
        print("Erreur")
        R2 = None 
        
    return R2     
  
  
  
  
i = 0
PIN_U = 29
PIN_U2 = 2
R1 = 100300.0
BASE_ADDR_ADC = 0x40007000
ETLN = 2000
#fréquence d'échantillonnage / bit 12 : 0 pour caler from machine import ADC, Pin, mem32
#sur event SAMPLE, 1 pour définir une valeur;
#bits 0-10 : valeur CC, binaire entre 80 et 2047 avec f_echantillonnage = 16MHz / CC

setup(resolution = 0x00000001, freq_echantillonnage =  0x00000000, ETLN = 2000) 
alimentation(PIN_alim = 5)

while i < 120 :
    i = i+1
    ETLN = ETLN + 1
    ref = tension_ref(PIN_U)
    R2 = calcul_resistance(ref, R1, PIN_U, PIN_U2)
    print(R2)
    time.sleep(1)
    
     


