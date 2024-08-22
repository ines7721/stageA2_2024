from machine import ADC, Pin, mem32
import time
import math
import gc
import utime

def setup(resolution_ADC, resolution_timer) :
    mem32[0x40000000 + 0x000] = 1 #Démarrage de l'horloge 
    mem32[BASE_ADDR_ADC + 0x5F4] = 0 #oversample off
    mem32[BASE_ADDR_ADC + 0x630] = 0x00000000 #qte info dans le buffer max
    mem32[BASE_ADDR_ADC + 0x634] = 0x00000000
    mem32[BASE_ADDR_ADC + 0x518 + (0 * 0x10)] = 0x0000000 #burst mode off
    mem32[BASE_ADDR_ADC + 0x518 + (1 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (2 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (3 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (4 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (5 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (6 * 0x10)] = 0x0000000
    mem32[BASE_ADDR_ADC + 0x518 + (7 * 0x10)] = 0x000000
    mem32[BASE_ADDR_ADC + 0x500] = 1 #ADC activé
    mem32[BASE_ADDR_ADC + 0x00] = 1 #lancement ADC

    mem32[0x40000000 + 0x78] = 1 #mode de latence constante
    
    #RESOLUTION
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution_ADC
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("Résolution SAADC -", check_resolution)
    print("0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")
    print(" ")
    
    
def etalonnage(nb_etalonnages) :
    nb_etalonnages = nb_etalonnages + 1
    #Activation SAADC
    mem32[BASE_ADDR_ADC + 0x500] = 1 
    ENABLE = mem32[BASE_ADDR_ADC + 0x500]
    mem32[BASE_ADDR_ADC + 0x00C] = 1
    #Démarrage de l'étalonnage
    check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
    #Vérification
    while check_ETLN < 1 : 
        check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
    if check_ETLN == 1 :
        print("Etalonnage effectué")
    return nb_etalonnages
    
def alimentation(PIN_alim, PIN_test, PIN_ref) : 
    GPIO = Pin(PIN_alim, Pin.OUT)
    TST = Pin(PIN_test, Pin.OUT)
    REF = Pin(PIN_ref, Pin.OUT)
    GPIO.value(1)
    return TST, REF
    # -> Faire en sorte que le PIN_alim délivre VDD au circuit

def tension_ref(PIN_U) :
    for j in range(0, nb_resistances) :
        tension_ref_analog = ADC(Pin(PIN_U[j], Pin.IN))
        REF.value(1)
        tension_ref = (tension_ref_analog.read_u16())
        REF.value(0)
        ref[j] = (tension_ref * (3.3 / 65535))
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
    
def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, total_sample) :
    z = 0
    for z in range(0, 50) :
        for j in range(0, 3) :
            for i in range (0, 3) :
                tension_U2_analog[i] = (ADC(Pin(PIN_U2[j], Pin.IN)))
                TST.value(1)
                tensionU2[i] = (tension_U2_analog[i].read_u16())
                TST.value(0)
                U2[i] = (tensionU2[i] * (ref[j] / 65535))
                tension_U_analog[i] = (ADC(Pin(PIN_U[j], Pin.IN)))
                TST.value(1)
                tensionU[i] = (tension_U_analog[i].read_u16())
                TST.value(0)
                U[i] = (tensionU[i] * (ref[j] / 65535))
            U_moy = (U[0] + U[1] + U[2])/3
            U2_moy = (U2[0] + U2[1] + U2[2])/3
            if ((U2_moy * R1[j])/(U_moy - U2_moy)) :
                R2[j] = ((U2_moy * R1[j])/(U_moy - U2_moy))
                print("R2 :", R2)
            else :
                end
                alerte = True
    return R2




#-------------------------------------------------------------------------------------------------------------------------------------------------
#Variables d'initialisation à modifier :



#Ecart en micro secondes entre la fin de la prise des 3 echantillons pour une résistance et le début de la prise des 3 échantillons de la résistance suivante (si 0, l'écart sera la période d'échantillonnage définie ci-dessous)
ecart_us = 0

#Nombres de mesures moyennes à faire sur les trois résistances avant de libérer de la mémoire (processus coûteux) :
frequence_garbage_collect = 50

#Nombre d'échantillons à prendre par intervalle de temps définit par temps_de_montée_minimum (en s) :
#Fréquence minimale du SAADC : 8 000 Hz, fréquence maximale : 200 000 Hz
#A vérifier : valeur minimum de fréquence : 31251 Hz / période minimum : 32us, valeur minimale pour temps_de_montee_min = 1sec ==> 3473
nb_echantillons_par_montee = 31560  
temps_de_montee_minimum = 10

#Nombre d'échantillons avec lesquels faire une moyenne pour chaque prise d'échantillon
nb_sur_echantillons = 3

#Nombres de résistances à mesurer : 
nb_resistances = 3

#Configuration de la résolution de l'ADC - 0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits
resolution_ADC = 0x3 

#Configuration de la résolution du timer - #0 : 16 bits/65536, 1 : 8 bits/256, 2 : 24 bits/16777216, 3 : 32 bits/4294967296
resolution_timer = 0x1 

#Définition des pins : 
PIN_U = (28, 3, 5)
PIN_U2 = (29, 4, 2)
PIN_alim = 43
PIN_test = 47
PIN_ref = 44

#Définition des résistances de référence :
R1 = (100000.0, 100000.0, 100000.0) #inconnues : 18k / 150k / 1M

#Définition du nombre d'échantillons à prendre avant d'effectuer un nouvel etalonnage :
parametre_etalonnage = 100000


#-----------------------------------------------------------------------------------------------------------------------------------------------------
#Constantes d'initialisation fixes :

alerte = False 
i = 0
j = 0
BASE_ADDR_ADC = 0x40007000
nb_etalonnages = 0
R2 = [0] * nb_resistances
ref = [0]*nb_resistances
tension_U2_analog = [0] * nb_sur_echantillons
tensionU2 = [0] * nb_sur_echantillons
tension_U_analog = [0] * nb_sur_echantillons
tensionU = [0] * nb_sur_echantillons
U = [0] * nb_sur_echantillons
U2 = [0] * nb_sur_echantillons
total_sample = 0
nb_etalonnages = 0
comparaison_etalonnage = parametre_etalonnage
ecart_s = 0
delta_r_test = ()
derivee_max_r_test = ()
integrale_r_test = ()




nb_etalonnages = etalonnage(nb_etalonnages)
setup(resolution_ADC, resolution_timer) 
TST, REF = alimentation(PIN_alim, PIN_test, PIN_ref)
while i < 20000 :
    tension_ref(PIN_U)
    R2 = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, total_sample)
    if i % frequence_garbage_collect == 0 :
        gc.collect()
    if total_sample % parametre_etalonnage == 0 :
        nb_etalonnages = etalonnage(nb_etalonnages)
    i = i+1
    total_sample = total_sample + (nb_resistances*nb_sur_echantillons)



