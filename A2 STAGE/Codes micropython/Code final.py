from machine import ADC, Pin, mem32
import time
import math
import gc
import utime
import random

#VARIABLES INITIALISATION
nb_resistances = 3
nb_sur_echantillons = 3
nb_echantillons_par_montee = 50000
duree_montee_s = 150
pourcentage_danger = 0.01 #pourcentage de déviation des valeurs de résistance au dessus duquel déclencher la classification
resolution_ADC = 0x3 #0 : 8 bits, 1 : 10 bits, 2 : 12 bits, 3 : 14 bits
parametre_etalonnage = 100000 #nombre d'échantillons à effectuer avant d'étalonnger à nouveau
R1 = (100000.0, 100000.0, 100000.0)  #inconnues : 18k / 150k / 1M

#Définition des pins : 
PIN_U = (28, 3, 5) #voir schéma intégré au rapport pour numéros des pins
PIN_U2 = (29, 4, 2)
PIN_alim = 43
PIN_test = 47
PIN_ref = 44


#HYPER-PARAMETRES RANDOM FOREST :
nb_donnees_pour_classif = 100
seuil_delta_min = 0.5
seuil_delta_max = 0.7 #intervalle dans lequel une donnée de delta doit être comprise pour indiquer qu'il n'y a pas de danger
seuil_derivee_max_min = 0.5
seuil_derivee_max_max = 0.7 #intervalle dans lequel une donnée de dérivée doit être comprise pour indiquer qu'il n'y a pas de danger
seuil_integrale_min = 0.5
seuil_integrale_max = 0.7 #intervalle dans lequel une donnée d'intégrale doit être comprise pour indiquer qu'il n'y a pas de danger
seuil_somme_min = 1.5
seuil_somme_max = 2.1 #intervalle dans lequel une donnée de somme des paramètres (integrale, derivée, delta) doit être comprise pour indiquer qu'il n'y a pas de danger
nb_arbres = 10
parametres = ("delta", "integrale", "derivee_max", "somme")
nb_noeuds_min = 0
nb_noeuds_max = 5

#VARIABLES INITIALISATION - à ne pas modifier
nb_parametres = len(parametres)
vote_arbre = 0
vote_foret = 0
alerte = False
DMMP = False
r = 0
j = 0
nb_etalonnages = 0
BASE_ADDR_ADC = 0x40007000
total_sample = 0
R2 = [0] * nb_resistances
ref = [0] * nb_resistances
tension_U2_analog = [0] * nb_sur_echantillons
tensionU2 = [0] * nb_sur_echantillons
tension_U_analog = [0] * nb_sur_echantillons
tensionU = [0] * nb_sur_echantillons
debut = [0] * nb_sur_echantillons
periode_min_3S_3R = 1/246.31
TST = Pin(PIN_test, Pin.OUT)
REF = Pin(PIN_ref, Pin.OUT)
somme = [0] * nb_resistances
integrale = [0] * nb_resistances
derivee_max = [0] * nb_resistances
delta = [0] * nb_resistances
nb_echantillons = 100

#FONCTIONS

def delai(attente_us):
    debut_delai = utime.ticks_us()
    while utime.ticks_diff(utime.ticks_us(), debut_delai) < attente_us:
        pass
#-> cette fonction sert à mettre en place un délai de attente_us micro secondes
    
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
    frequence_echantillonnage = nb_echantillons_par_montee / duree_montee_s
    print("Fréquence d'échantillonnage demandée :", frequence_echantillonnage, "Hz")
    periode_echantillonnage = 1 / frequence_echantillonnage
    periode_min = (periode_min_3S_3R * nb_resistances * nb_sur_echantillons) / 9
    if periode_echantillonnage > periode_min:
        attente_us = (periode_echantillonnage - periode_min) * 1e6
        print("Fréquence d'échantillonnage ajustée")
    else:
        print("La fréquence d'échantillonnage ne peut pas dépasser 246.31 Hz.")
        attente_us = 0
    
    #PREMIER ETALONNAGE
    nb_etalonnages = etalonnage(nb_etalonnages)
    print("Set-up terminé.")
    
    return nb_etalonnages, attente_us
    
def etalonnage(nb_etalonnages) :
    nb_etalonnages += 1
    mem32[BASE_ADDR_ADC + 0x500] = 1 #activation du SAADC via le registre correspondant (obligatoire pour que l'étalonnage se fasse)
    ENABLE = mem32[BASE_ADDR_ADC + 0x500]
    mem32[BASE_ADDR_ADC + 0x00C] = 1 #envoi de la commande d'étalonnage au registre correspondannt
    check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
    #Vérification
    while check_ETLN < 1 : 
        check_ETLN = mem32[BASE_ADDR_ADC + 0x110]
    if check_ETLN == 1 :
        print("Etalonnage effectué")
    return nb_etalonnages

def tension_ref(PIN_U) :
    for j in range(nb_resistances):
        tension_ref_analog = ADC(Pin(PIN_U[j], Pin.IN)) #définition du pin
        #REF.value(1) #sert uniquement à envoyer un signal pour signaler la lecture de l'ADC (utilisé pour mesurer la fréquence d'échantillonnage à l'oscilloscope)
        tension_ref = tension_ref_analog.read_u16()
        #REF.value(0)
        ref[j] = tension_ref * (3.3 / 65535)
    return ref
#-> cette fonction sert à récupérer la valeur de tension VDD de manière préliminaire afin de l'utiliser comme référence dans la mesure des
#tensions dans la fonction calcul_referen
#On utilise la valeur maximale de VDD (3.3V) pour la mesurer, valeur qui a fourni les résultats les plus correspondants à la mesure au voltmètre.

def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, tension_U_analog, tensionU, alerte, attente_us, nb_resistances) :
    for z in range(nb_resistances, nb_resistances + nb_echantillons) : #nb_echantillons = 100 valeurs échantillonnées de résistance sont retournées par la fonction, voir rapport
        for j in range(nb_resistances): 
            U = [0] * nb_sur_echantillons #création de la liste qui contiendra les n valeurs de la tension U, avec n le nombre de sur échantillons
            U2 = [0] * nb_sur_echantillons #création de la liste qui contiendra les n valeurs de la tension U2, avec n le nombre de sur échantillons
            for i in range(nb_sur_echantillons):  #boucle de prise d'un sur échantillon   
                tension_U2_analog[i] = ADC(Pin(PIN_U2[j], Pin.IN)) #initialisation du GPIO de mesure de U2
                #TST.value(1) #utile uniquement à la mesure de la fréquence d'échantillonnage avec oscilloscope
                tensionU2[i] = tension_U2_analog[i].read_u16() #conversion analogique-numérique de l'ADC
                #TST.value(0) #utile uniquement à la mesure de la fréquence d'échantillonnage avec oscilloscope
                U2[i] = tensionU2[i] * (ref[j] / 65535) #conversion de la valeur numérique de 16 bits récupérée par l'ADC en volts
                tension_U_analog[i] = ADC(Pin(PIN_U[j], Pin.IN)) #même processus que pour U2
                #TST.value(1)
                tensionU[i] = tension_U_analog[i].read_u16()
                #TST.value(0)
                U[i] = tensionU[i] * (ref[j] / 65535)
            U_moy = sum(U) / nb_resistances #moyenne des sur-échantillons pour avoir les valeurs finales de U et U2 avec lesquelles calculer la valeur de résistance échantillonnée
            U2_moy = sum(U2) / nb_resistances
            del U #libération de RAM
            del U2
            R2i = (U2_moy * R1[j]) / (U_moy - U2_moy) #calcul intermédiaire 
            if len(R2) < nb_resistances*nb_sur_echantillons : #les n = nb_resistances*nb_echantillons echantillons premières valeurs sont automatiquement ajoutées à la liste des résistances indépendamment de leur rapport au pourcentage de variation critique, car sinon il n'y a pas assez de données pour effectuer le calul des paramètres
                R2.append(R2i)
                debut.append(utime.ticks_us()*1e-6) #prise du temps de mesure de la résistance pour obtenir les intervalles de temps nécessaires au calcul des paramètres (intégrale, dérivée)
            else:
                if (R2i > R2[len(R2)-(nb_resistances)]*(1-pourcentage_danger)) and  (R2i < R2[len(R2)-(nb_resistances)]*(1+pourcentage_danger)) : #comparaison au pourcentage de variation critique absolu une fois que les premières valeurs indispensables au calcul des paramètres ont été rajoutées à la liste des résistances mesurées
                    #print("Les échantillons respectent un écart de :", pourcentage_danger*100, "%")
                    R2.append(R2i)
                    debut.append(utime.ticks_us()*1e-6)
                else :
                    #print("Alerte")
                    alerte = True #déclenchement de l'alerte si les valeurs sortent en dehors de l'intervalle de sécurité défini par le pourcentage de danger
    if alerte:
        print("Alerte !")
    return R2, alerte, debut

def slice(R2, nb_resistances):
    R_slice = [[] for _ in range(nb_resistances)]
    for i in range(nb_resistances):
        for j in range(i+nb_resistances, len(R2), nb_resistances):
            R_slice[i].append(R2[j])
    return R_slice
#-> la liste R_slice est une liste contenant n listes, chacune contenant toutes les valeurs récupérées pour chaque résistance. (avec n le nombre de résistances)
#La liste originelle R2 contient n listes dans lesquelles il y a les valeurs de toutes les résistances récupérées pour chaque échantillon.


def calcul_integrale (nb_resistances, debut, R2, k) :
    integrales = [] #liste qui stocke temporairement les valeurs d'intégrales pour chaque échantillon avant de les ajouter à la somme totale des intervalles sur tous les échantillons stockés
    for i in range (0, nb_resistances) :
        integrales.append([0, 0])
        integrale.append([0])
    for i in range (0, len(R2)-((2*nb_resistances)-1), nb_resistances) : #on parcourt la liste des résistances de 0 aux avant-dernières valeurs de résistance, (toutes les n valeurs avec n le nombre de résistances = échantillon par échantillon)
        if i == 0 :
            debut_precedent = 0
        else :
            debut_precedent = debut[i-1]
        for j in range (0, nb_resistances):
            integrales[j].append((((R2[i+j]+R2[i+nb_resistances+j])/2)*(debut[i]-debut_precedent))) #calcul d'intégrale d'un échantillon avec la méthode des trapèzes
            integrale[j][0] = integrale[j][0] + integrales[j][len(integrales[j])-1] #ajout de la dernière intégrale calculée à la somme des intégrales de tous les échantillons en mémoire
    del integrales
    return integrale

def calcul_delta (R_slice, nb_resistances) :
    R_steady = []
    R_initial = []
    for i in range (0, nb_resistances) :
        R_steady.append(0)
        R_initial.append([0])
        delta.append([0])
        R_steady[i] = max(R_slice[i], key=abs)
        R_initial[i] = min(R_slice[i], key=abs)
        delta[i] = [((R_steady[i]-R_initial[i])/R_initial[i])]
    del R_steady
    del R_initial
    del R_slice
    return delta
#-> cette fonction calcule le paramètre delta selon la formule données à la p. 619 du document sur l'analyse de présence d'ammoniaque

def calcul_derivee_max (R_slice, debut, nb_resistances) :
    derivee = [[] for _ in range(nb_resistances)]
    for i in range (0,len(R_slice[0])-1):
        if i == 0 :
            debut_precedent = 0
        else :
            debut_precedent = debut[i-1]
        for j in range (0, nb_resistances) :
            derivee[j].append((R_slice[j][i]-R_slice[j][i-1])/(debut[i]-debut_precedent))
    for j in range (0, nb_resistances) :
        derivee_max.append([max(derivee[j], key=abs)])
    del derivee
    return derivee_max

    
def calcul_parametres(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, tension_U_analog, tensionU, attente_us, total_sample, nb_donnees_pour_classif, debut):
    #création des listes de stockage des paramètres
    integralef = [[] for _ in range(nb_resistances)]
    derivee_maxf = [[] for _ in range(nb_resistances)]
    deltaf = [[] for _ in range(nb_resistances)]
    sommef = [[] for _ in range(nb_resistances)]
    
    #le calcul des paramètres sera lancé n fois avec n = nb_donnees_pour_classif
    for k in range(nb_donnees_pour_classif):
        R_slice = slice(R2, nb_resistances) #création de la liste R_slice
        #calcul des paramètres :
        integrale = calcul_integrale(nb_resistances, debut, R2, k)
        derivee_max = calcul_derivee_max(R_slice, debut, nb_resistances)
        delta = calcul_delta(R_slice, nb_resistances)
        
        for i in range(nb_resistances):
            integralef[i].append(integrale[i][k]) #on ajoute la valeur d'intégrale calculée pour chaque résistance à la liste qui stockera toutes les données de paramètres
            derivee_maxf[i].append(derivee_max[i][k])
            deltaf[i].append(delta[i][k])
            sommef[i].append(integralef[i][k] + abs(deltaf[i][k]) + abs(derivee_maxf[i][k]))
        #print("Paramètres acquis pour la", k, "ième fois")
            
        #libération de l'espace mémoire :
        integrale.clear()
        delta.clear()
        derivee_max.clear()
        debut.clear()
        R_slice.clear()
        R2.clear() 
        R2, alerte, total_sample = main(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances, total_sample)

    return integralef, derivee_maxf, deltaf, sommef


def classification(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2,  tension_U_analog, tensionU, attente_us, total_sample, nb_donnees_pour_classif, debut) :
    print("Classification lancée")
    #obtention des paramètres :
    integralef, derivee_maxf, deltaf, sommef = calcul_parametres(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2,  tension_U_analog, tensionU, attente_us, total_sample, nb_donnees_pour_classif, debut)
    #print("commencement foret")
    #lancement de la fonction random_forest :
    DMMP = foret(integralef, derivee_maxf, deltaf, sommef) #DMMP est un booléen, true si la forêt le détecte, false sinon
    #print("deltaf =", deltaf)
    #print("integralef =", integralef)
    #print("derivee_maxf =", derivee_maxf)
    del deltaf
    del derivee_maxf
    del integralef
    print("Classification terminée.")
    return DMMP



def type_aleatoire() :
    #On choisit le paramètre que le noeud va évaluer au hasard avec parametres = ("delta", "integrale", "derivee_max", "somme")
    return random.choice(parametres)


def type_aleatoire_pondere() :
    #le choix du paramètre que le noeud va évaluer dépend des valeurs de précision obtenues en fonction des paramètres utilisés avec l'algorithme random forest
    #ces valeurs sont expérimentales et proviennent du tableau 3 dans le document sur l'analyse de présence d'ammoniaque p. 622
    ponderations = [0.77, 0.50, 0.77, 0.80]
    poids_total = sum(ponderations)
    rand = random.uniform(0, poids_total) #choix d'un nombre aléatoire parmis l'intervalle [0, poids total des pondérations]
    cumul = 0
    #dans la boucle suivante on additionne les poids de chaque paramètre jusqu'à ce que le cumul des poids soit supérieur au nombre aléatoire choisi
    #le paramètre qui fera dépasser le cumul est sélectionné
    for random.choice(parametre), poids in zip(parametres, ponderations):
        cumul += poids
        if rand <= cumul:
            return parametre
    

def donnees_aleatoires(type_noeud, n, integralef, derivee_maxf, deltaf, sommef) :
    #n représente la résistance choisie dans la boucle de la fonction foret
    #une valeur au hasard parmi les paramètres calculés est selectionnée, en fonction du type du noeud
    if type_noeud == 'delta' :
        donnee = random.choice(deltaf[n])
    if type_noeud == 'derivee_max' :
        donnee = random.choice(derivee_maxf[n])
    if type_noeud == 'integrale' :
        donnee = random.choice(integralef[n])
    if type_noeud == 'somme' :
        donnee = random.choice(sommef[n])
    return donnee
    
    
def verif_noeud(type_noeud, donnee) :
    #définition de la condition de détermination de la présence de DMMP pour le noeud, en fonction de son type
    #les valeurs de seuils sont des hyper paramètres à déterminer avec l'entraînement
    #voir si il est mieux de choisir le seuil par random.choice ou de comparer la valeur aléatoire au min et max du seuil
    if type_noeud == 'delta' :
        condition = donnee > random.choice(seuil_delta_max) or donnee < random.choice(seuil_delta_min)
    if type_noeud == 'derivee_max' :
        condition = donnee > random.choice(seuil_derivee_max_max) or donnee < random.choice(seuil_derivee_max_min)
    if type_noeud == 'integrale' :
        condition = donnee > random.choice(seuil_integrale_max) or donnee < random.choice(seuil_integrale_min)
    if type_noeud == 'somme' :
        condition = donnee > random.choice(seuil_somme_max) or donnee < random.choice(seuil_somme_min)
    return condition
    

def arbre_decisionnel(n, integralef, derivee_maxf, deltaf, sommef) :
    vote_noeuds = 0 #initialisation des votes des noeuds
    vote_arbre = 0 #initialisation des vote globaux des arbres
    nb_noeuds = random.randint(nb_noeuds_min, nb_noeuds_max) #le nombre de noeud de chaque arbre est choisi de manière aléatoire
    type_noeud = type_aleatoire() #le type du premier noeud est choisi au hasard
    for i in range (0,nb_noeuds) :
        #selection du paramètres à évaluer de manière aléatoire en fonction du type du noeud :
        donnee = donnees_aleatoires(type_noeud, n, integralef, derivee_maxf, deltaf, sommef)
        #vérification du respect de la condition de présence de DMMP :
        condition = verif_noeud(type_noeud, donnee)
        if condition : #si il y a présence de DMMP :
            vote_noeuds =+ 1 #le noeud vote pour dmmp
            i =+ 1
            type_noeud = type_aleatoire_pondere() #le type du noeud suivant sera déterminé avec le choix aléatoire pondéré pour améliorer la précision 
        else :
            # "création" d'un nouveau noeud avec un type choisi de manière totalement aléatoire :
            type_noeud = type_aleatoire()
        if vote_noeuds >= (nb_noeuds/2) :
            vote_arbre =+ 1
            # -> l'arbre vote pour la présence de DMMP si plus de la moitié de ses noeuds votent ainsi
    return vote_arbre
        
def foret(integralef, derivee_maxf, deltaf, sommef) :
    vote_foret = 0
    for _ in range (0, nb_arbres) :
        for n in range(0, nb_resistances) :
            #création de n arbre pour chaque résistance avec n = le nombre d'arbre décidé en tant qu'hyper paramètre
            vote_arbre = arbre_decisionnel(n, integralef, derivee_maxf, deltaf, sommef)
            vote_foret = vote_foret + vote_arbre
    if vote_foret >= (nb_arbres/2) :V
        DMMP = True
        #-> la classification décide que le DMMP est présent si plus de la moitié des arbres votent ainsi
    return DMMP



#Set up préliminaire (résolution de l'ADC, fréquence d'échantillonnage, premier étalonnage, alimentation du circuit avec VDD) :
nb_etalonnages, attente_us = setup(resolution_ADC, nb_etalonnages, PIN_alim, nb_echantillons_par_montee, duree_montee_s)

while True:
    #calcul de la tension de référence pour améliorer la précision des calculs de résistance :
    ref = tension_ref(PIN_U)
    #calcul des n valeurs pour chaque résistance avec n le nombre d'échantillons à effectuer pour le calcul des paramètres éventuel :
    R2, alerte, debut = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, tension_U_analog, tensionU, alerte, attente_us, nb_resistances)
    #lancement de la classification si une valeur ne respectant pas le critère de danger est lue :
    if alerte == True :
        DMMP = classification(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, tension_U_analog, tensionU,attente_us, total_sample, nb_donnees_pour_classif, debut)
    R2.clear() #libération RAM
    if DMMP == True :
        print("DMMP détecté")
        break
    else :
        print("Alerte déclenchée mais DMMP non détecté")
    gc.collect() #Libération RAM
    total_sample = total_sample + (nb_resistances * nb_sur_echantillons * nb_echantillons) #mise à jour du nombre d'échantillons effectués pour l'étalonnage ci-dessous
    if total_sample % parametre_etalonnage == 0 :
        nb_etalonnages = etalonnage(nb_etalonnages)

