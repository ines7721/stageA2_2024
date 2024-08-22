from machine import ADC, Pin, mem32
import time
import math
import gc
import utime
import random

#VARIABLES INITIALISATION
#FONCTIONS
#FIXES
#MAIN

#LA DUREE D'EXECUTION MAXIMALE DE CE CODE AVANT QU'IL N'Y AIT PLUS DE MEMOIRE EST DE : 3 MINUTES 11 SANS CLASSIF

#VARIABLES INTITIALISATION CALCUL RESISTANCE
nb_resistances = 3
nb_sur_echantillons = 3
nb_echantillons_par_montee = 50000
duree_montee_s = 150
pourcentage_danger = 0.12
resolution_ADC = 0x3
parametre_etalonnage = 1000000000000
R1 = (100000.0, 100000.0, 100000.0) #inconnues : 18k / 150k / 1M

#Définition des pins : 
PIN_U = (28, 3, 5)
PIN_U2 = (29, 4, 2)
PIN_alim = 43
PIN_test = 47
PIN_ref = 44
PIN_LED = 13


##HYPER-PARAMETRES RANDOM FOREST :
nb_donnees_pour_classif = 100
seuil_delta = [0.5, 0.7]
seuil_derivee_max = [0.5, 0.7]
seuil_integrale = [0.5, 0.7]
seuil_somme = [1.5, 2.1]
nb_arbres = 10
parametres = ("delta", "integrale", "derivee_max", "somme")
nb_noeuds_min = 0
nb_noeuds_max = 5


#VARIABLES INITIALISATION
nb_parametres = len(parametres)
vote_arbre = 0
vote_foret = 0
alerte = False
DMMP = False
r = 0
i = 0
j = 0
frequence_garbage_collect = 50
nb_etalonnages = 0
BASE_ADDR_ADC = 0x40007000
total_sample = 0
nb_etalonnages = 0
R2 = [0] * nb_resistances
ref = []
tension_U2_analog = []
tensionU2 = []
U2 = []
tension_U_analog = []
tensionU = []
U = []
debut= []
periode_min_3S_3R = 1/246.31
TST = Pin(PIN_test, Pin.OUT)
REF = Pin(PIN_ref, Pin.OUT)
somme = []
integrale = []
derivee_max = []
delta = []



#FONCTIONS

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
        print("La fréquence d'échantillonnage ne peut pas dépasser 246.31 Hz.")
        attente_us = 0
    
    #PREMIER ETALONNAGE
    nb_etalonnages = etalonnage(nb_etalonnages)
    print("Set-up terminé.")
    
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

def calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances) :
    for z in range(nb_resistances, nb_resistances+20) :
        for j in range(0, nb_resistances) :
            for i in range (0, nb_sur_echantillons) :     
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
            if len(R2) < nb_resistances*nb_sur_echantillons :
                R2.append(R2i)
                debut.append(utime.ticks_us()*1e-6)
            else:
                if (R2i > R2[len(R2)-(nb_resistances)]*(1-pourcentage_danger)) and  (R2i < R2[len(R2)-(nb_resistances)]*(1+pourcentage_danger)) :
                    #print("Les échantillons respectent un écart de :", pourcentage_danger*100, "%")
                    R2.append(R2i)
                    debut.append(utime.ticks_us()*1e-6)
                else :
                    #print("Alerte")
                    alerte = True
        delai(attente_us)
    return R2, alerte


def clear_calcul_resistances(tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U):
    tension_U2_analog.clear()
    tensionU2.clear()
    U2.clear()
    tension_U_analog.clear()
    tensionU.clear()
    U.clear()

def slice(R2, nb_resistances):
    R_slice = [[] for _ in range(nb_resistances)]
    for i in range(nb_resistances):
        for j in range(i+nb_resistances, len(R2), nb_resistances):
            R_slice[i].append(R2[j])
    return R_slice


def calcul_integrale (nb_resistances, debut, R2, k) :
    integrales = []
    for i in range (0, nb_resistances) :
        integrales.append([0, 0])
        integrale.append([0])
    for i in range (0, len(R2)-((2*nb_resistances)-1), nb_resistances) :
        if i == 0 :
            debut_precedent = 0
        else :
            debut_precedent = debut[i-1]
        for j in range (0, nb_resistances):
            integrales[j].append((((R2[i+j]+R2[i+nb_resistances+j])/2)*(debut[i]-debut_precedent)))
            integrale[j][0] = integrale[j][0] + integrales[j][len(integrales[j])-1]
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
    
def calcul_parametres(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, attente_us, total_sample, nb_donnees_pour_classif, debut):
    integralef = [[] for _ in range(nb_resistances)]
    derivee_maxf = [[] for _ in range(nb_resistances)]
    deltaf = [[] for _ in range(nb_resistances)]
    sommef = [[] for _ in range(nb_resistances)]
    
    for k in range(nb_donnees_pour_classif):
        R_slice = slice(R2, nb_resistances)
        integrale = calcul_integrale(nb_resistances, debut, R2, k)
        derivee_max = calcul_derivee_max(R_slice, debut, nb_resistances)
        delta = calcul_delta(R_slice, nb_resistances)
        
        for i in range(nb_resistances):
            integralef[i].append(integrale[i][0])
            derivee_maxf[i].append(derivee_max[i][0])
            deltaf[i].append(delta[i][0])
            sommef[i].append(integralef[i][k] + abs(deltaf[i][k]) + abs(derivee_maxf[i][k]))
        #print("Paramètres acquis pour la", k, "ième fois")
        integrale.clear()
        delta.clear()
        derivee_max.clear()
        debut.clear()
        R_slice.clear()
        R2.clear() 
        R2, alerte, total_sample = main(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances, total_sample)

    return integralef, derivee_maxf, deltaf, sommef
        
def classification(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, attente_us, total_sample, nb_donnees_pour_classif, debut) :
    print("Classification lancée")
    integralef, derivee_maxf, deltaf, sommef = calcul_parametres(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, attente_us, total_sample, nb_donnees_pour_classif, debut)
    print("commencement foret")
    DMMP = foret(integralef, derivee_maxf, deltaf, sommef)
    print("deltaf =", deltaf)
    print("integralef =", integralef)
    print("derivee_maxf =", derivee_maxf)
    del deltaf
    del derivee_maxf
    del integralef
    print("Classification terminée.")
    return DMMP

def main(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances, total_sample) :
    ref = tension_ref(PIN_U)
    R2, alerte = calcul_resistance(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances)
    ref.clear()
    total_sample = total_sample + (nb_resistances*nb_sur_echantillons)
    return R2, alerte, total_sample

def type_aleatoire() :
    return random.choice(parametres)


def type_aleatoire_pondere() :
    #à implémenter manuellement
    return random.choice(parametres)
    

def donnees_aleatoires(type_noeud, n, integralef, derivee_maxf, deltaf, sommef) :
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
    if type_noeud == 'delta' :
        condition = donnee > random.choice(seuil_delta)
    if type_noeud == 'derivee_max' :
        condition = donnee > random.choice(seuil_derivee_max)
    if type_noeud == 'integrale' :
        condition = donnee > random.choice(seuil_integrale)
    if type_noeud == 'somme' :
        condition = donnee > random.choice(seuil_somme)
    return condition
    

def arbre_decisionnel(n, integralef, derivee_maxf, deltaf, sommef) :
    vote_noeuds = 0
    vote_arbre = 0
    nb_noeuds = random.randint(nb_noeuds_min, nb_noeuds_max)
    type_noeud = type_aleatoire()
    for i in range (0,nb_noeuds) :
        donnee = donnees_aleatoires(type_noeud, n, integralef, derivee_maxf, deltaf, sommef)
        condition = verif_noeud(type_noeud, donnee)
        if condition :
            vote_noeuds =+ 1
            i =+ 1
            type_noeud = type_aleatoire_pondere()
        else :
            type_noeud = type_aleatoire()
        if vote_noeuds >= (nb_noeuds/2) :
            vote_arbre =+ 1
    return vote_arbre
        
def foret(integralef, derivee_maxf, deltaf, sommef) :
    vote_foret = 0
    for _ in range (0, nb_arbres) :
        for n in range(0, nb_resistances) :
            vote_arbre = arbre_decisionnel(n, integralef, derivee_maxf, deltaf, sommef)
            vote_foret = vote_foret + vote_arbre
    if vote_foret >= (nb_arbres/2) :
        DMMP = True
    return DMMP



nb_etalonnages, attente_us = setup(resolution_ADC, nb_etalonnages, PIN_alim, nb_echantillons_par_montee, duree_montee_s) 
while True :
    debout_boucle = gc.mem_free()
    #print("debut_boucle")
    R2, alerte, total_sample = main(ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, alerte, attente_us, nb_resistances, total_sample)
    if alerte == True :
        DMMP = classification(R2, alerte, nb_resistances, ref, R1, PIN_U, PIN_U2, tension_U2_analog, tensionU2, U2, tension_U_analog, tensionU, U, attente_us, total_sample, nb_donnees_pour_classif, debut)
    R2.clear()
    if DMMP == True :
        print("DMMP détecté")
        break
        LED = Pin(PIN_LED, Pin.OUT)
        LED.value(1)
    else :
        gc.collect()
        print("DMMP non détecté")
    gc.collect()
    if total_sample % parametre_etalonnage == 0 :
        nb_etalonnages = etalonnage(nb_etalonnages)
    fin_boucle = gc.mem_free()
    #print("fin_boucle")


     


    

    








