from machine import ADC, Pin, mem32
import time
import math
import gc
import utime

def delai(attente_us):
    debut_delai = utime.ticks_us()
    while utime.ticks_diff(utime.ticks_us(), debut_delai) < attente_us:
        pass
    
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

def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us) :
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
                if (R2i > R2[z-3]/10) and  (R2i < R2[z-3]*10) :
                    R2.append(R2i)
                else :
                    print("Alerte")
                    alerte = True
                    return R2, alerte
        delai(attente_us)       
    return R2, alerte

def clear_main(R2, ref) :
    R2.clear()
    R2 = [0]*nb_resistances
    ref.clear()
    return R2, ref

def clear_calcul_resistances(tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U):
    tension_U2_analog.clear()
    tensionU2.clear()
    U2.clear()
    tension_U_analog.clear()
    tensionU.clear()
    U.clear()



#-------------------------------------------------------------------------------------------------------------------------------------------------
#Variables d'initialisation à modifier :

alerte = False



frequence_garbage_collect = 50

pourcentage_danger = 0.99
nb_echantillons_par_montee = 2000
duree_montee_s = 150

nb_sur_echantillons = 3
nb_resistances = 3

resolution_ADC = 0x3 


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
print(type(R2))
ref = []
memoire = []
historique_resistances = []
tension_U2_analog = []
tensionU2 = []
U2 = []
tension_U_analog = []
tensionU = []
U = []
total_sample = 0
nb_etalonnages = 0
comparaison_etalonnage = parametre_etalonnage
ecart_s = 0
delta_r_test = ()
derivee_max_r_test = ()
integrale_r_test = ()
periode_min_3S_3R = 1/246.31
critere_danger_max= pourcentage_danger+1
critere_danger_min = 1-pourcentage_danger

TST = Pin(PIN_test, Pin.OUT)
REF = Pin(PIN_ref, Pin.OUT)




nb_etalonnages, attente_us = setup(resolution_ADC, nb_etalonnages, PIN_alim, nb_echantillons_par_montee, duree_montee_s) 
while i < 20000 :
    tension_ref(PIN_U)
    R2, alerte = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us)
    print("R2 :", R2[len(R2)-3], R2[len(R2)-2], R2[len(R2)-1])
    parametres = calcul_parametres(alerte, R2)
    R2, ref = clear_main(R2, ref)
    if i % frequence_garbage_collect == 0 :
        gc.collect()
    if total_sample % parametre_etalonnage == 0 :
        nb_etalonnages = etalonnage(nb_etalonnages)
    i = i+1
    total_sample = total_sample + (nb_resistances*nb_sur_echantillons)
    




