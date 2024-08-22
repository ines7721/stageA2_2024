from machine import ADC, Pin, mem32
import time
import math
import gc


def setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) :
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
    mem32[BASE_ADDR_TIMER + 0x00] = 1 #commencement timer
    mem32[BASE_ADDR_ADC + 0x00] = 1 #lancement ADC

    mem32[0x40000000 + 0x78] = 1 #mode de latence constante
    
    #RESOLUTION
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution_ADC
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("Résolution SAADC -", check_resolution)
    print("0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")
    print(" ")
    
    #FREQUENCE D'ECHANTILLONNAGE / TIMER   
    #1) CONFIG TIMER, COUNTER ET FREQUENCE TIMER
    mem32[BASE_ADDR_TIMER + 0x504] = 0 #mise en mode Timer
    mem32[BASE_ADDR_TIMER + 0x508] = resolution_timer #nombre de bits du timer, nombre maximal atteignable par le compteur
    mem32[BASE_ADDR_TIMER + 0x510] = prescaler_binaire #définition de la fréquence d'échantillonnage
    mem32[BASE_ADDR_TIMER + 0x540] = comparaison_compteur #CC[0], comparaison déclenchée pour la valeur de compteur comparaison_compteur 
    #2) CONFIG CANAL PPI / EEP & TEP
    mem32[BASE_ADDR_PPI + 0x500] = 1 #activation du canal 0 de périphérique PPI
    mem32[BASE_ADDR_PPI + 0x510] = BASE_ADDR_TIMER + 0x140 #initialisation de l'élément déclencheur du PPI : channel 0 EEP -> EVENTS_COMPARE[0] du registre timer
    mem32[BASE_ADDR_ADC + 0x5F8] = 00000000000000 #sample rate contrôlé par tâche SAMPLE uniquement
    mem32[BASE_ADDR_PPI + 0x514] = BASE_ADDR_ADC + 0x004 #initialisation de l'élément déclenché du PPI : channel 0 TEP -> TASKS_SAMPLE du registre SAADC
    mem32[BASE_ADDR_PPI + 0x910] = BASE_ADDR_TIMER + 0x00C #initialisation du second élément déclenché du channel PPI 0 : 
    
    
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
    for j in range(0, 3) :
        tension_ref_analog = ADC(Pin(PIN_U[j], Pin.IN))
        REF.value(1)
        tension_ref = tension_ref_analog.read_u16()
        REF.value(0)
        ref.append(tension_ref * (3.3 / 65535))
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, total_sample) :
    for j in range(0, 3) :
        for i in range (0, 3) : #0 une mesure u2 et une mesure u - 1 1 de chaquec - 2 1 de chaque, à la fin de la boucle j'ai fait 3 mesures de chaque donc 6 mesures * 3 pour 3 résistances donc 18 mesures par cycle     
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
            total_sample = total_sample + 1
        time.sleep(ecart_s)
        U_moy = (U[0] + U[1] + U[2])/3
        U2_moy = (U2[0] + U2[1] + U2[2])/3
        U1_moy = U_moy-U2_moy
        if U1_moy!=0 :
            R2.append((U2_moy * R1[j])/U1_moy)
        else :
            print("Erreur")
            R2.append(None)
        tension_U2_analog.clear()
        tensionU2.clear()
        U2.clear()
        tension_U_analog.clear()
        tensionU.clear()
        U.clear()
    return R2, total_sample
    
#def calcul_parametres :
    



#-------------------------------------------------------------------------------------------------------------------------------------------------
#Variables d'initialisation à modifier :



#Ecart en micro secondes entre la fin de la prise des 3 echantillons pour une résistance et le début de la prise des 3 échantillons de la résistance suivante (si 0, l'écart sera la période d'échantillonnage définie ci-dessous)
ecart_us = 50

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

frequence_echantillonnage = (nb_echantillons_par_montee * nb_sur_echantillons * nb_resistances)/temps_de_montee_minimum
if frequence_echantillonnage in range (8000, 200001) : 
    puissance_prescaler = 16000000/frequence_echantillonnage
    prescaler = int(math.log(puissance_prescaler)/math.log(2))
    prescaler_b = bin(prescaler)[2:]
    prescaler_binaire = int(prescaler_b)
    print("Fréquence et période du timer :", frequence_echantillonnage,"Hz,", (1/frequence_echantillonnage)*1e6,"us", "Prescaler :", prescaler)

    #Nombre de tics d'horloge à laisser passer avant que le compteur ne déclenche un nouvel échantillon. Permet de baisser la fréquence d'échantillonnage 
    comparaison_compteur = 1001110001000
    comparaison_compteur_bin = bin(comparaison_compteur)[2:]
    
    print("Fréquence et période d'échantillonnage réelles :", frequence_echantillonnage/comparaison_compteur, "Hz /", (1/(frequence_echantillonnage)*comparaison_compteur)*1e6, "us")
else :
    print("Erreur, la fréquence d'échantillonnage est inférieure à 8000 Hz ou supérieure à 200 000 Hz")

#Configuration de la résolution de l'ADC - 0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits
resolution_ADC = 0x3 

#Configuration de la résolution du timer - #0 : 16 bits/65536, 1 : 8 bits/256, 2 : 24 bits/16777216, 3 : 32 bits/4294967296
resolution_timer = 0x1 

#Définition des pins : 
PIN_U = (28, 3, 5)
PIN_U2 = (29, 4, 2)
PIN_alim = 43
PIN_test = 47
PIN_ref = 46

#Définition des résistances de référence :
R1 = (100000.0, 100000.0, 100000.0) #inconnues : 18k / 150k / 1M

#Définition du nombre d'échantillons à prendre avant d'effectuer un nouvel etalonnage :
parametre_etalonnage = 10000


#-----------------------------------------------------------------------------------------------------------------------------------------------------
#Constantes d'initialisation fixes :


i = 0
j = 0
BASE_ADDR_ADC = 0x40007000
BASE_ADDR_PPI = 0x4001F000
BASE_ADDR_TIMER = 0x40009000 #TIMER1 selectionné car TIMER0 à priori non disponible
ETLN = 0
nb_etalonnages = 0
R2 = []
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
ecart_s = ecart_us* 1e-6 
delta_r_test = ()
derivee_max_r_test = ()
integrale_r_test = ()



#Séquence d'éxecution :
nb_etalonnages = etalonnage(nb_etalonnages)
setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) 
TST, REF = alimentation(PIN_alim, PIN_test, PIN_ref)

while i < 20000 :
    tension_ref(PIN_U)
    R2, total_sample = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, total_sample)
    print("Résistances inconnues des circuits 1, 2, 3 :", R2)
    historique_resistances.append(R2[:])
    R2.clear()
    ref.clear()
    if i % frequence_garbage_collect == 0 :
        gc.collect()
    if total_sample % parametre_etalonnage == 0 :
        nb_etalonnages = etalonnage(nb_etalonnages)
        i = i+1
    else :
        i = i+1
    mem_libre = gc.mem_free()
    #print(f'Mémoire libre : {mem_libre} octets; Tour : {i}')
    #print(f'L\'historique des résistances contient : {len(historique_resistances)} données')
    if i % 2048 == 0 :
        historique_resistances.clear()
    
    
print("Nombre d'étalonnages effectués :", nb_etalonnages)
print("Nombre d'échantillons pris :", total_sample)


#gc.collect modulo 100 : 1024 données récoltées
#gc.collect modulo 50 : 2048 données récoltées, pareil pour 10, pareil pour 1



