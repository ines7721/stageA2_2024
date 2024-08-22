from machine import ADC, Pin, mem32
import utime
import math
import gc


#Variables d'initialisation à modifier :

nb_resistances = 3
nb_sur_echantillons = 3
pourcentage_de_variation_max = 0.03
nb_echantillons_par_montee = 2000
duree_montee_s = 150
parametre_etalonnage = 100000
resolution_ADC = 0x3
R1 = [100000, 100000, 100000]

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def delai(attente_us):
    debut_delai = utime.ticks_us()
    while utime.ticks_diff(utime.ticks_us(), debut_delai) < attente_us:
        pass

def garbage_collect(t, frequence_garbage_collect) :
    t= t+1
    if t % frequence_garbage_collect == 0 :
        gc.collect()
    return t
        
def setup(resolution_ADC, nb_etalonnages, PIN_alim, nb_echantillons_par_montee, duree_montee_s) :
    #RESOLUTION SAADC
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution_ADC
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("Résolution SAADC -", check_resolution)
    print("0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")
    print(" ")
    
    #ALIMENTATION DU CIRCUIT AVEC VDD
    GPIO = Pin(PIN_alim, Pin.OUT)
    GPIO.value(1)
    
    #PARAMETRES DE FREQUENCE D'ECHANTILLONNAGE
    frequence_echantillonnage = nb_echantillons_par_montee/duree_montee_s
    print("Fréquence d'échantillonnage demandée :", frequence_echantillonnage, "Hz")
    periode_echantillonnage = 1/frequence_echantillonnage
    periode_min = (periode_min_3S_3R*nb_resistances*nb_sur_echantillons)/9
    if periode_echantillonnage > periode_min:
        attente_us = (periode_echantillonnage - periode_min)*1e6
        print("Fréquence d'échantillonnage ajustée")
    else :
        print("La fréquence d'échantillonnage ne peut pas dépasser 246.31 Hz pour une mesure")
        attente_us = 0
    
    #PREMIER ETALONNAGE
    nb_etalonnages = etalonnage(nb_etalonnages)
    
    return nb_etalonnages, attente_us
    
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

def tension_ref(PIN_U) :
    for j in range(0, 3) :
        tension_ref_analog = ADC(Pin(PIN_U[j], Pin.IN))
        REF.value(1)
        tension_ref = tension_ref_analog.read_u16()
        REF.value(0)
        ref.append(tension_ref * (3.3 / 65535))
    return ref

def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, pourcentage_de_variation_max) :
    z = 0
    for z in range(nb_resistances, nb_resistances+100) :
        for j in range(0, 3) :
            for i in range (0, 3) :     
                tension_U2_analog.append(ADC(Pin(PIN_U2[j], Pin.IN)))
                TST.value(1)
                tensionU2.append(tension_U2_analog[i].read_u16())
                TST.value(0)
                U2.append(tensionU2[i] * (ref[j] / 65535))
                tension_U_analog.append(ADC(Pin(PIN_U[j], Pin.IN)))
                TST.value(1)
                tensionU.append(tension_U_analog[i].read_u16())
                TST.value(0)
                U.append(tensionU[i] * (ref[j] / 65535))
            U_moy = (U[0] + U[1] + U[2])/3
            U2_moy = (U2[0] + U2[1] + U2[2])/3
            clear_calcul_resistances(tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U)
            R2i = (U2_moy * R1[j])/(U_moy - U2_moy)
            if z < nb_resistances*2 :
                R2.append(R2i)
            if z > nb_resistances*2 :
                if (R2i > R2[z-nb_resistances]*(1-pourcentage_de_variation_max)) and  (R2i < R2[z-nb_resistances]*(1+pourcentage_de_variation_max)) :
                    R2.append(R2i)
                else :
                    print("Alerte")
                    alerte = True
                    return alerte
        delai(attente_us)       
    return alerte

def clear_main(R2, ref) :
    R2.clear()
    ref.clear()
    return R2, ref

def clear_calcul_resistances(tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U):
    tension_U2_analog.clear()
    tensionU2.clear()
    U2.clear()
    tension_U_analog.clear()
    tensionU.clear()
    U.clear()

def parametres(alerte) :
    if alerte == False :
        return alerte
    if alerte == True :
        classification = True
        return classification

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Variables d'initialisation :
alerte = False
classification = False
periode_min_3S_3R = 1/246.31
nb_etalonnages = 0
frequence_garbage_collect = 50   
BASE_ADDR_ADC = 0x40007000
t=0
R2 = [0] * nb_resistances
ref = []
tension_U2_analog = []
tensionU2 = []
U2 = []
tension_U_analog = []
tensionU = []
U = []
Liste_integrales = []


#Définition des pins : 
PIN_U = (28, 3, 5)
PIN_U2 = (29, 4, 2)
PIN_alim = 43
PIN_test = 47
PIN_ref = 46





TST = Pin(PIN_test, Pin.OUT)
REF = Pin(PIN_ref, Pin.OUT)
nb_etalonnage, attente_us = setup(resolution_ADC, nb_etalonnages, PIN_alim, nb_echantillons_par_montee, duree_montee_s)
while True :
    ref = tension_ref(PIN_U)
    alerte = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, pourcentage_de_variation_max)
    t = garbpage_collect(t, frequence_garbage_collect)
    print(classification)


