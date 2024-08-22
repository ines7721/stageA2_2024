from machine import ADC, Pin, mem32
import utime
import math
import gc

def delai(ecart):
    debut_delai = utime.ticks_us()
    while utime.ticks_diff(utime.ticks_us(), debut_delai) < ecart:
        pass
    
def setup(resolution_ADC, resolution_timer) :
    
    #Activation de l'ADC
    mem32[BASE_ADDR_ADC + 0x500] = 1
    
    #Lancement de l'ADC
    mem32[BASE_ADDR_ADC + 0x000] = 1
    
    #Démarrage de l'horloge :
    mem32[0x40000000 + 0x000] = 1
    mem32[0x40000000 + 0x008] = 1
    
    #Lancement du timer :
    mem32[BASE_ADDR_TIMER + 0x000] = 1
    
    #Désactivation du burst mode et de l'oversample respectivement :
    mem32[BASE_ADDR_ADC + 0x5F4] = 0
    for n in range (0, 8) :
        mem32[BASE_ADDR_ADC + 0x518 + (n * 0x10)] = 0x0000000 
     
    #Réglage du buffer du SAADC (nb d'échantillons à écrire dans le buffer de sortie, nb d'échantillons à écrire dans le buffer de sortie depuis la dernière tâche START respectivement) :
    mem32[BASE_ADDR_ADC + 0x630] = 111111111111111 
    mem32[BASE_ADDR_ADC + 0x634] = 111111111111111
    
    #Configuration de la résolution de l'ADC
    mem32[BASE_ADDR_ADC + 0x5F0] = resolution_ADC
    check_resolution = mem32[BASE_ADDR_ADC + 0x5F0]
    print("Résolution SAADC -", check_resolution)
    print("0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits")    
    print(" ")
    
    #Sample rate contrôlé par tâche SAMPLE
    mem32[BASE_ADDR_ADC + 0x5F8] = 0x00000000 
      
def etalonnage(nb_etalonnages, total_sample) :
    #NE PAS OUBLIER ERRATUM CARTE DESACTIVATION ET ACTIVATION
    if total_sample % parametre_etalonnage == 0 :
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
        tension_ref = tension_ref_analog.read_u16()
        
        ref.append(tension_ref * (3.3 / 65535))
    return ref
    # -> Calcul de la tension de référence VDD à chaque nouvelle mesure
    
def sampleU (PIN_U, tension_U_analog, tensionU, ref, delai_us) :
    for j in range (0, nb_resistances) :
        for i in range(0, nb_sur_echantillons) :
            pin=ADC(Pin(PIN_U[j], Pin.IN))
            U.append(pin.read_u16() * (ref[j] / 65535))
            TST.value(1)
            TST.value(0)
    return tension_U_analog, tensionU

def sampleU2 (PIN_U2, tension_U2_analog, tensionU2, ref, delai_us) :
    for j in range (0, nb_resistances) :
        for i in range (0, nb_sur_echantillons) :
            pin=ADC(Pin(PIN_U2[j], Pin.IN))
            U2.append(pin.read_u16() * (ref[j] / 65535))
            TST.value(1)
            TST.value(0)
    return tension_U2_analog, tensionU2

def calcul_resistances (R2, tension_U2_analog, tensionU2, tension_U_analog, tensionU, total_sample) :
    tension_U2_analog.clear()
    tension_U_analog.clear()
    total_sample = total_sample + (2*nb_sur_echantillons*nb_resistances)
    for j in range (0, nb_resistances):
        U_moy = (U[0] + U[1] + U[2])/3
        U2_moy = (U2[0] + U2[1] + U2[2])/3
        U1_moy = U_moy - U2_moy
        if U1_moy != 0 :
                R2.append((U2_moy * R1[j]) / U1_moy)
        else :
            print("ERREUR : U1 = 0")
        del U[:3]
        del U2[:3]  
    U2.clear()
    U.clear()
    return R2, total_sample

def calcul_integrale (historiqueR1, historiqueR2, historiqueR3, t, debut) :
    integraleR1 = integraleR2 = integraleR3 = 0
    for i in range (0, len(historiqueR1)-1) :
        if i == 0 :
            debut_precedent = 0
        else :
            debut_precedent = debut[i-1]
        integraleR1 = integraleR1 + ((historiqueR1[i]+historiqueR1[i+1])/2*(debut[i]-debut_precedent))
        integraleR2 = integraleR2 + ((historiqueR2[i]+historiqueR1[i+1])/2*(debut[i]-debut_precedent))
        integraleR3 = integraleR3 + ((historiqueR3[i]+historiqueR1[i+1])/2*(debut[i]-debut_precedent))
    return integraleR1, integraleR2, integraleR3

def delta (historiqueR1, historiqueR2, historiqueR3) :
    R_steady1 = max(historiqueR1)
    R_initial1 = min(historiqueR1)
    R_steady2 = max(historiqueR2)
    R_initial2 = min(historiqueR2)
    R_steady3 = max(historiqueR3)
    R_initial3 = min(historiqueR3)
    delta1 = (R_steady1-R_initial1)/R_initial1
    delta2 = (R_steady2-R_initial2)/R_initial2
    delta3 = (R_steady3-R_initial3)/R_initial3
    return delta1, delta2, delta3

def derivee_max(historiqueR1, historiqueR2, historiqueR3) :
    for i in range (0, len(historiqueR1)):
        if i == 0 :
            debut_precedent = 0
        else :
            debut_precedent = debut[i-1]
        derivee1.append((historiqueR1[i]-historiqueR1[i-1])/(debut[i]-debut_precedent))
        derivee2.append((historiqueR2[i]-historiqueR2[i-1])/(debut[i]-debut_precedent))
        derivee3.append((historiqueR3[i]-historiqueR3[i-1])/(debut[i]-debut_precedent))
    derivee_max1 = max(derivee1)
    derivee_max2 = max(derivee2)
    derivee_max3 = max(derivee3)
    derivee1.clear()
    derivee2.clear()
    derivee3.clear()
    return derivee_max1, derivee_max2, derivee_max3
    
def calcul_parametres(historiqueR1, historiqueR2, historiqueR3, t, debut):
    integraleR1, integraleR2, integraleR3 = calcul_integrale(historiqueR1, historiqueR2, historiqueR3, t, debut)
    delta1, delta2, delta3 = delta(historiqueR1, historiqueR2, historiqueR3)
    derivee_max1, derivee_max2, derivee_max3 = derivee_max(historiqueR1, historiqueR2, historiqueR3)
    #print("Intégrales sur les derniers 150 échantillons de R1, R2, R3 :", integraleR1, integraleR2, integraleR3)
    #print("Dérivées maximales :", derivee_max1, derivee_max2, derivee_max3)
    #print("Deltas :", delta1, delta2, delta3)
    return integraleR1, integraleR2, integraleR3, delta1, delta2  , delta3, derivee_max1, derivee_max2, derivee_max3

def sauvegarde(com, nb_resistances, R_min, R2, historiqueR1, historiqueR2, historiqueR3, historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3, pourcentage_montee_min_R1, pourcentage_montee_min_R2, pourcentage_montee_min_R3) :
    if len(historiqueR1) > 1 :
        R_min.append(historiqueR1[len(historiqueR1)-1]*pourcentage_montee_min_R1)
        R_min.append(historiqueR2[len(historiqueR2)-1]*pourcentage_montee_min_R2)
        R_min.append(historiqueR3[len(historiqueR3)-1]*pourcentage_montee_min_R3) 
        if R2[0] > R_min[0] :
            historique_integralesR1.append(integraleR1)
            historique_deltaR1.append(delta1)
            historique_deriveeR1.append(derivee_max1)
            com = True
        if R2[1] > R_min[1] :
            historique_integralesR2.append(integraleR2)
            historique_deltaR2.append(delta2)
            historique_deriveeR2.append(derivee_max2)
            com = True
        if R2[2] > R_min[2] :
            historique_integralesR3.append(integraleR3)
            historique_deltaR3.append(delta3)
            historique_deriveeR3.append(derivee_max3)
            com = True
        if com == True :
            communication(historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3)
            com = False
        R_min.clear()
    return historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3

def garbage_collect(t, frequence_garbage_collect) :
    t= t+1
    if t % frequence_garbage_collect == 0 :
        gc.collect()

def communication (historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3) :
        #protocole de classification    
        historique_integralesR1.clear()
        historique_integralesR2.clear()
        historique_integralesR3.clear()
        historique_deltaR1.clear()
        historique_deltaR2.clear()
        historique_deltaR3.clear()
        historique_deriveeR1.clear()
        historique_deriveeR2.clear()
        historique_deriveeR3.clear()
        

#-------------------------------------------------------------------------------------------------------------------------------------------------
#Variables d'initialisation à modifier :

#Taux d'augmentation minimal pour considérer qu'il faut enregistrer les paramètres :
pourcentage_montee_min_R1 = 1.3
pourcentage_montee_min_R2 = 1.3
pourcentage_montee_min_R3 = 1.3


#Nombres de mesures moyennes à faire sur les trois résistances avant de libérer de la mémoire (processus coûteux) :
frequence_garbage_collect = 50

#Nombre d'échantillons avec lesquels faire une moyenne pour chaque prise d'échantillon
nb_sur_echantillons = 3

#Nombres de résistances à mesurer : 
nb_resistances = 3

#Fréquence de sur_échantillonnage souhaitée (Fréquence max = 5780 Hz, période 173 us) :
frequence_echantillonnage = 5780
delai_us = (1/frequence_echantillonnage) - 173

####rajouter calcul de la fréquence d'échantillonnage par résistance puis par tour

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

#Définition du nombre d'échantillons à prendre avant de vider la mémoire :
taille_historique_max = 900



#-----------------------------------------------------------------------------------------------------------------------------------------------------
#Constantes d'initialisation fixes :

com = False
i = 0
t = 0
j = 0
p = 0
t = 0
k = 0
integrale = 0
BASE_ADDR_ADC = 0x40007000
BASE_ADDR_PPI = 0x4001F000
BASE_ADDR_TIMER = 0x40011000 #TIMER1 selectionné car TIMER0 à priori non disponible
ETLN = 0
nb_etalonnages = 0
R2 = []
ref = []
memoire = []
historiqueR1 = []
historiqueR2 = []
historiqueR3 = []
IntegraleR = []
R_min = []
tension_U2_analog = []
tensionU2 = []
U2 = []
tension_U_analog = []
tensionU = []
U = []
total_sample = 0
nb_etalonnages = 0
comparaison_etalonnage = parametre_etalonnage
delta_r_test = ()
derivee1  = []
derivee2 = []
derivee3 = []
historique_integralesR1 = []
historique_integralesR2 = []
historique_integralesR3 = []
historique_deltaR1 = []
historique_deltaR2 = []
historique_deltaR3 = []
historique_deriveeR1 = []
historique_deriveeR2 = []
historique_deriveeR3 = []
debut = []




#-----------------------------------------------------------------------------------------------------------------------------------------------------
#Séquence d'éxecution :



setup(resolution_ADC, resolution_timer) 
TST, REF = alimentation(PIN_alim, PIN_test, PIN_ref)
print("La fréquence d'échantillonnage est :", frequence_echantillonnage, "Hz")

while True :
    debut.append((utime.ticks_us()))
    tension_ref(PIN_U)
    tension_U_analog, tensionU = sampleU(PIN_U, tension_U_analog, tensionU, ref, delai_us)
    tension_U2_analog, tensionU2 = sampleU2(PIN_U2, tension_U2_analog, tensionU2, ref,delai_us)
    R2, total_sample = calcul_resistances(R2, tension_U2_analog, tensionU2, tension_U_analog, tensionU, total_sample)
    print("Résistances inconnues des circuits 1, 2, 3 :", R2)
    historiqueR1.append(R2[0])
    historiqueR2.append(R2[1])
    historiqueR3.append(R2[2])
    integraleR1, integraleR2, integraleR3, delta1, delta2, delta3, derivee_max1, derivee_max2, derivee_max3 = calcul_parametres(historiqueR1, historiqueR2, historiqueR3, t, debut)
    historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3 = sauvegarde(com, nb_resistances, R_min, R2, historiqueR1, historiqueR2, historiqueR3, historique_integralesR1, historique_deltaR1, historique_deriveeR1, historique_integralesR2, historique_deltaR2, historique_deriveeR2, historique_integralesR3, historique_deltaR3, historique_deriveeR3, pourcentage_montee_min_R1, pourcentage_montee_min_R2, pourcentage_montee_min_R3)
    if len(historiqueR1) == 150 :
        historiqueR1.clear()
        historiqueR2.clear()
        historiqueR3.clear()
        debut.clear()
    R2.clear()
    ref.clear()
    garbage_collect(t, frequence_garbage_collect)
    nb_etalonnages = etalonnage(nb_etalonnages, total_sample)
    t = t+1

    
        
        
print("Nombre d'étalonnages effectués :", nb_etalonnages)
print("Nombre d'échantillons pris :", total_sample)


#gc.collect modulo 100 : 1024 données récoltées
#gc.collect modulo 50 : 2048 données récoltées, pareil pour 10, pareil pour 1





