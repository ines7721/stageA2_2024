from machine import ADC, Pin, mem32
import time


def setup(resolution, oversample, freq_echantillonnage, burst) :
    #RESOLUTION
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("Résolution SAADC : ", check_resolution)
    print("0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")
    print(" ")
    
    #FREQUENCE D'ECHANTILLONNAGE
    mem32[BASE_ADDR_ADC + 0x630] = 0x0
    mem32[BASE_ADDR_ADC + 0x5F8] = freq_echantillonnage
    check_freq = mem32[BASE_ADDR_ADC + 0x5F8]
    print("Entrée registre fréquence d'échantillonnage =", check_freq)
    print(" ")
    
    #BURST MODE, ACTIVATION DE LA MOYENNE PERIODIQUE DES ACQUISITIONS (SUR-ECHANTILLONNAGE)
    mem32[BASE_ADDR_ADC + 0x5F4] = oversample
    check_oversample = mem32[BASE_ADDR_ADC + 0x5F4] 
    print("Résolution de sur-échantillonnage :", check_oversample)
    print("0 : None, 1 : 2x, 2 : 4x, 3 : 8x, 4 : 16x ... 8 : 256x")
    print(" ")
    if check_oversample == 1 :
        OVERSAMPLE = 4
    elif check_oversample == 2 :
        OVERSAMPLE = 16
    elif check_oversample == 3 :
        OVERSAMPLE = 256
    elif check_oversample == 4 :
        OVERSAMPLE = 65635
    elif check_oversample == 5 :
        OVERSAMPLE = 4299967296
    elif check_oversample == 6 :
        OVERSAMPLE = 1.844e9
    elif check_oversample == 7 :
        OVERSAMPLE = 3.402e38
    elif check_oversample == 8 :
        OVERSAMPLE = 1.157e77
    elif check_oversample == 0 :
        OVERSAMPLE = 1       
    if burst:   
        #on modifie n = 0 et n = 3, entrées analogiques 2 et 29
        #temps acquisition 40 micro secondes, burst mode activé. 
        mem32[BASE_ADDR_ADC + 0x518]  = 0x1010000
        mem32[BASE_ADDR_ADC + 0x518 + 0x10+ 0x10+ 0x10]  = 0x1010000
        print("Mode BURST activé")
        print(" ")
    else :
        mem32[BASE_ADDR_ADC + 0x518]  = 0x0
        mem32[BASE_ADDR_ADC + 0x518 + 0x10+ 0x10+ 0x10]  = 0x0
        print("Mode BURST désactivé")
        print(" ")

    return OVERSAMPLE

def etalonnage(ETLN, nb_etalonnages) :
    if ETLN > 1000 :
        nb_etalonnages = nb_etalonnages + 1
        mem32[BASE_ADDR_ADC + 0x500] = 1 #Activation SAADC
        ENABLE = mem32[BASE_ADDR_ADC + 0x500]
        mem32[BASE_ADDR_ADC + 0x00C] = 1 #Démarrage étalonnage
        check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
        while check_ETLN < 1 : #Vérification
            check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
        if check_ETLN == 1 :
            print("Etalonnage effectué")
        ETLN = 0
        return nb_etalonnages
    
def alimentation(PIN_alim, PIN_test) : 
    GPIO = Pin(PIN_alim, Pin.OUT)
    GPIO.value(1)
    TST = Pin(PIN_test, Pin.OUT)
    return TST

    # -> Faire en sorte que le PIN_alim délivre VDD au circuit

def tension_ref(PIN_U) : 
    start_time = time.ticks_us()
    tension_ref_analog = ADC(Pin(PIN_U, Pin.IN))
    end_time = time.ticks_us()
    elapsed_time = time.ticks_diff(end_time, start_time)
    #print("période mesure Uref :", elapsed_time, "us / fréquence mesure Uref :", 1/(elapsed_time*1e-6), "Hz")
    tension_ref = tension_ref_analog.read_u16()
    ref = tension_ref * (3.3 / 65535)
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
def calcul_resistance(ref, R1, PIN_U, PIN_U2) :
    tension_U2_analog = ADC(Pin(PIN_U2, Pin.IN))
    TST.value(1)
    tensionU2 = tension_U2_analog.read_u16()
    TST.value(0)
    U2 = tensionU2 * (ref / 65535)
    #print("Tension sur la broche 2: ",U2)
    tension_U_analog = ADC(Pin(PIN_U, Pin.IN))
    TST.value(1)
    tensionU = tension_U_analog.read_u16()
    TST.value(0)
    U = tensionU * (ref / 65535)
    #print("Tension sur la broche 29 :",U)
    U1 = U-U2
    #print("Tension aux bornes de la résistance inconnue :", U1)
    if U1!=0 :
        R2 = (U2 * R1)/U1
    else :
        print("Erreur")
        R2 = None  
    return R2

  
i = 0
PIN_U = 29
PIN_U2 = 2
R1 = 10000.0
BASE_ADDR_ADC = 0x40007000
ETLN = 0
nb_etalonnages = 0   

etalonnage(ETLN, nb_etalonnages)
OVERSAMPLE = setup(resolution = 0x3, oversample = 0, freq_echantillonnage = 1111111111101, burst = False) 
TST = alimentation(PIN_alim = 5, PIN_test = 47)


while i < 100000000000000 :
    i = i+1
    ref = tension_ref(PIN_U)
    R2 = calcul_resistance(ref, R1, PIN_U, PIN_U2)
    print(R2)
    #print("ETLN =", ETLN)
    #time.sleep(1)

print("Nombre d'étalonnages effectués :", nb_etalonnages)


#1.001k ohm
#10.29k ohm 
    
     

                    