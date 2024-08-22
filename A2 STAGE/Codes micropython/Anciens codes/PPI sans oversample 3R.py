from machine import ADC, Pin, mem32
import time
import math


def setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) :
    mem32[BASE_ADDR_ADC + 0x360] = 111111111111111
    
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
    mem32[BASE_ADDR_ADC + 0x5F8] = 0 #sample rate contrôlé par tâche SAMPLE uniquement
    mem32[BASE_ADDR_PPI + 0x514] = BASE_ADDR_ADC + 0x004 #initialisation de l'élément déclenché du PPI : channel 0 TEP -> TASKS_SAMPLE du registre SAADC
    mem32[BASE_ADDR_PPI + 0x910] = BASE_ADDR_TIMER + 0x00C #initialisation du second élément déclenché du channel PPI 0 : 
    
    
def sur_echantillonnage(oversample) :
    #Faire un compteur avec PPI pour l'échantillonnage en fonction du nombre de samples (évènement -> compare capture, tâche -> incrément) 
    oversample = 1
    return oversample
    

def etalonnage(ETLN, nb_etalonnages) :
    if ETLN > 1000 :
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
        ETLN = 0
        return nb_etalonnages
    
def alimentation(PIN_alim) : 
    GPIO = Pin(PIN_alim, Pin.OUT)
    GPIO.value(1)
    # -> Faire en sorte que le PIN_alim délivre VDD au circuit

def tension_ref(PIN_U) :
    for j in range(0, 3) :
        tension_ref_analog = ADC(Pin(PIN_U[j], Pin.IN))
        tension_ref = tension_ref_analog.read_u16()
        ref.append(tension_ref * (3.3 / 65535))
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
def calcul_resistance(ref, R1, PIN_U, PIN_U2) :
    for j in range(0, 3) :
        tension_U2_analog = ADC(Pin(PIN_U2[j], Pin.IN))
        tensionU2 = tension_U2_analog.read_u16()
        U2 = tensionU2 * (ref[j] / 65535)
        tension_U_analog = ADC(Pin(PIN_U[j], Pin.IN))
        tensionU = tension_U_analog.read_u16() 
        U = tensionU * (ref[j] / 65535)
        U1 = U-U2
        if U1!=0 :
            R2.append((U2 * R1[j])/U1)
        else :
            print("Erreur")
            R2.append(None)
    return R2
    #RAJOUTER UNE BOUCLE POUR CHAQUE VALEUR DE j + un calcul de moyenne ou un stockage pour calculer la moyenne à la fin de la boucle J 



#Constantes d'initialisation 
i = 0
j = 0
BASE_ADDR_ADC = 0x40007000
BASE_ADDR_PPI = 0x4001F000
BASE_ADDR_TIMER = 0x40009000 #TIMER1 selectionné car TIMER0 à priori non disponible
ETLN = 0
nb_etalonnages = 0
R2 = []
ref = []
historique_resistances = []
historique_refs = []

#Variables d'initialisation
nb_echantillons_par_montee = 31251 #valeur minimum : 31251 Hz / période minimum : 32us, valeur minimale pour temps_de_montee_min = 1sec ==> 3473
nb_sur_echantillons = 3
nb_resistances = 3
temps_de_montee_min = 10
frequence_echantillonnage = (nb_echantillons_par_montee * nb_sur_echantillons * nb_resistances)/temps_de_montee_min
puissance_prescaler = 16000000/frequence_echantillonnage
prescaler = int(math.log(puissance_prescaler)/math.log(2))
prescaler_b = bin(prescaler)[2:]
prescaler_binaire = int(prescaler_b)
print(prescaler_binaire)
print("Fréquence et période du timer :", frequence_echantillonnage,"Hz,", (1/frequence_echantillonnage)*1e6,"us", "Prescaler :", prescaler)
comparaison_compteur = 0xA #nombre de tics d'horloge avant la prise d'un nouvel échantillon (permet de baisser la fréquence d'horloge)
comparaison_compteur_bin = bin(comparaison_compteur)[2:]
print("Fréquence et période d'échantillonnage réelles :", frequence_echantillonnage/comparaison_compteur, "Hz /", (1/(frequence_echantillonnage)*comparaison_compteur)*1e6, "us") 

resolution_ADC = 0x3 #0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits
resolution_timer = 0x1 #0 : 16 bits/65536, 1 : 8 bits/256, 2 : 24 bits/16777216, 3 : 32 bits/4294967296


#Définition des pins : 
PIN_U = [28, 3, 5]
PIN_U2 = [29, 4, 2]
PIN_alim = 43

#Définition des résistances de référence :
R1 = [100000.0, 100000.0, 100000.0] #18k / 150k / 1M



#Séquence d'éxecution :
etalonnage(ETLN, nb_etalonnages)
setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) 
alimentation(PIN_alim)
oversample = sur_echantillonnage(oversample = 0)
while i < 20 :
    i = i+1
    ETLN = ETLN + oversample
    nb_etalonnages = etalonnage(ETLN, nb_etalonnages)
    tension_ref(PIN_U)
    calcul_resistance(ref, R1, PIN_U, PIN_U2)
    print("Résistances inconnues des circuits 1, 2, 3 :", R2)
    historique_resistances.append(R2[:])
    historique_refs.append(ref[:])
    R2.clear()
    ref.clear()
    time.sleep(1)
    

print("Nombre d'étalonnages effectués :", nb_etalonnages)

 

