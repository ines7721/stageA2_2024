from machine import ADC, Pin, mem32
import time
import math


def setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) :
    mem32[BASE_ADDR_ADC + 0x360] = 0x7FFF
    
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
    mem32[BASE_ADDR_TIMER + 0x510] = 7 #définition de la fréquence d'échantillonnage avec le prescaler
    mem32[BASE_ADDR_TIMER + 0x540] = comparaison_compteur #CC[0], comparaison déclenchée pour la valeur de compteur comparaison_compteur
    #la comparaison active entre le CC[0] et le compteur est automatique
    #2) CONFIG CANAL PPI / EEP & TEP
    mem32[BASE_ADDR_PPI + 0x500] = 1 #activation du canal 0 de périphérique PPI
    mem32[BASE_ADDR_PPI + 0x504] = 1 #activation de la lecture et écriture du canal 0 du PPI
    mem32[BASE_ADDR_PPI + 0x510] = BASE_ADDR_TIMER + 0x140 #initialisation de l'élément déclencheur du PPI : channel 0 EEP -> EVENTS_COMPARE[0] du registre timer
    mem32[BASE_ADDR_ADC + 0x5F8] = 0 #sample rate contrôlé par tâche SAMPLE uniquement
    mem32[BASE_ADDR_PPI + 0x514] = BASE_ADDR_ADC + 0x004 #initialisation de l'élément déclenché du PPI : channel 0 TEP -> TASKS_SAMPLE du registre SAADC
    mem32[BASE_ADDR_PPI + 0x910] = BASE_ADDR_TIMER + 0x00C #initialisation du second élément déclenché du channel PPI 0 : reset du compteur
    
    mem32[BASE_ADDR_ADC + 0x004] = 1
    
    
def sur_echantillonnage(oversample) :
    #Faire un compteur avec PPI pour l'échantillonnage en fonction du nombre de samples (évènement -> compare capture, tâche -> incrément) 
    oversample = 1
    return oversample
    

def etalonnage(ETLN, nb_etalonnages) :
    #rajouter condition ou ligne qui STOP le SAADC car comportement non attendu lors que le SAADC est en marche et la calibration est lancée, voir erratum de la carte
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
        start_sampling = time.ticks_us()
        tension_ref_analog = ADC(Pin(PIN_U, Pin.IN))
        tension_ref = tension_ref_analog.read_u16()
        end_sampling = time.ticks_us()
        ref = (tension_ref * (3.3 / 65535))
        
        start_times.append(start_sampling)
        end_times.append(end_sampling)
        
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
#def calcul_resistance(ref, R1, PIN_U, PIN_U2, start_times, end_times) :
            
    #start_sampling = time.ticks_us()
    #tension_U2_analog = ADC(Pin(PIN_U2, Pin.IN))
    #tensionU2 = tension_U2_analog.read_u16()
    #end_sampling = time.ticks_us()
        
    #start_times.append(start_sampling)
    #end_times.append(end_sampling)
        
    #U2 = tensionU2 * (ref / 65535)
    #tension_U_analog = ADC(Pin(PIN_U, Pin.IN))
    #tensionU = tension_U_analog.read_u16() 
    #U = tensionU * (ref/ 65535)
    #U1 = U-U2
    #if U1!=0 :
    #    R2 = ((U2 * R1)/U1)
    #else :
    #    print("Erreur")
    #    R2 = (None)
    #return R2, start_times, end_times
    #RAJOUTER UNE BOUCLE POUR CHAQUE VALEUR DE j + un calcul de moyenne ou un stockage pour calculer la moyenne à la fin de la boucle J 

def calcul_durees(nb_echantillons, start_times, end_times) :
    for i in range(nb_echantillons):
        calcul_duree_echantillonnage = time.ticks_diff(end_times[i], start_times[i])
        duree_echantillonnage.append(calcul_duree_echantillonnage)
        
        if i < nb_echantillons - 1:
            sampling_clock = time.ticks_diff(start_times[i + 1], start_times[i])
            between_duration = time.ticks_diff(start_times[i + 1], end_times[i])
            horloge_echantillonnage.append(sampling_clock)
            duree_entre_deux.append(between_duration)
        
    return duree_echantillonnage, horloge_echantillonnage, duree_entre_deux


#Constantes d'initialisation 
i = 0
BASE_ADDR_ADC = 0x40007000
BASE_ADDR_PPI = 0x4001F000
BASE_ADDR_TIMER = 0x4000A000 #TIMER2 selectionné car TIMER0 à priori non disponible
ETLN = 0
nb_etalonnages = 0
start_times = []
end_times = []
duree_echantillonnage = []
horloge_echantillonnage = []
duree_entre_deux = []



#Variables d'initialisation
nb_echantillons_par_montee = 1000000 #valeur minimum : 31251 Hz / période minimum : 32us, valeur minimale pour temps_de_montee_min = 1sec ==> 3473
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

resolution_ADC = 0x1 #0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits
resolution_timer = 0x1 #0 : 16 bits/65536, 1 : 8 bits/256, 2 : 24 bits/16777216, 3 : 32 bits/4294967296
comparaison_compteur = 50000 #max : résolution timer; nombre de tics d'horloge avant la prise d'un nouvel échantillon (permet de baisser la fréquence d'horloge)
comparaison_compteur_bin = bin(comparaison_compteur)[2:]
nb_echantillons = 7

print("Fréquence et période d'échantillonnage de l'ADC :", frequence_echantillonnage/comparaison_compteur, "Hz /", (1/(frequence_echantillonnage)*comparaison_compteur)*1e6, "us") 


#Définition des pins : 
PIN_U = 5
#PIN_U2 = 2
PIN_alim = 43

#Définition des résistances de référence :
R1 = 100000.0



#Séquence d'éxecution :
etalonnage(ETLN, nb_etalonnages)
setup(resolution_ADC, resolution_timer, prescaler_binaire, comparaison_compteur) 
alimentation(PIN_alim)

while i < nb_echantillons :
    ref = tension_ref(PIN_U)
    #R2, start_times, end_times = calcul_resistance(ref, R1, PIN_U, PIN_U2, start_times, end_times)
    print("Tension ref :", ref)
    i = i+1

i=0
for i in range(nb_echantillons):
    calcul_duree_echantillonnage = time.ticks_diff(end_times[i], start_times[i])
    duree_echantillonnage.append(calcul_duree_echantillonnage)
        
    if i < nb_echantillons - 1:
        sampling_clock = time.ticks_diff(start_times[i + 1], start_times[i])
        between_duration = time.ticks_diff(start_times[i + 1], end_times[i])
        horloge_echantillonnage.append(sampling_clock)
        duree_entre_deux.append(between_duration)
    
    
 
    



#print("durée échantillonnage :", duree_echantillonnage, "horloge echantillonnage", horloge_echantillonnage, "duree entre deux echantillons :", duree_entre_deux)

print("")
print("Durée d'échantillonnage : temps que prend l'ADC entre le début d'un échantillon et la fin de l'échantillon :")
for i, duration in enumerate(duree_echantillonnage):
    frequency = 1 / (duration * 1e-6) if duration > 0 else 0
    print(f"Échantillon {i+1}: {duration} us, Fréquence : {frequency:.2f} Hz")

print("\nHorloge d'échantillonnage : temps que prend l'ADC entre la micro-seconde de début de l'échantillonnage d'un échantillon et la micro-seconde de début du prochain échantillon")
for i, clock in enumerate(horloge_echantillonnage):
    frequency = 1 / (clock * 1e-6) if clock > 0 else 0
    print(f"Échantillon {i+1}: {clock} us, Fréquence: {frequency:.2f} Hz")

print("\nDurée entre deux échantillons : temps qui s'écoule entre la fin d'un échantillon et le début du prochain")
for i, duration in enumerate(duree_entre_deux):
    frequency = 1 / (duration * 1e-6) if duration > 0 else 0
    print(f"Échantillon {i+1}: {duration} us, Fréquence: {frequency:.2f} Hz")

 


