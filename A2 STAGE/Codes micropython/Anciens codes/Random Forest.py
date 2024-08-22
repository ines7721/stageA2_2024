import random


#Paramètrable :
seuil_delta = [0.5, 0.7]
seuil_derivee_max = [0.5, 0.7]
seuil_integrale = [0.5, 0.7]
seuil_somme = [1.5, 2.1]
nb_arbres = 10
parametres = ("delta", "integrale", "derivee_max", "somme")
nb_noeuds_min = 0
nb_noeuds_max = 5

#Initialisation :
nb_parametres = len(parametres)
vote_arbre = 0
vote_foret = 0

def type_aleatoire() :
    return random.choice(parametres)


def type_aleatoire_pondere() :
    #à implémenter manuellement
    return random.choice(parametres)
    

def donnees_aleatoires(type_noeud) :
    if type_noeud == 'delta' :
        donnee = random.choice(delta[n])
    if type_noeud == 'derivee_max' :
        donnee = random.choice(derivee_max[n])
    if type_noeud == 'integrale' :
        donnee = random.choice(integrale[n])
    if type_noeud == 'somme' :
        donnee = random.choice(somme[n])
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
    

def arbre_decisionnel() :
    vote_noeuds = 0
    nb_noeuds = random.randint(nb_noeuds_min, nb_noeuds_max)
    type_noeud = type_aleatoire()
    for i in range (0,nb_noeuds) :
        donnee = donnees_aleatoires(type_noeud)
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
        
def foret() :
    for n in range (0, nb_arbres) :
        vote_arbre = arbre_decisionnel()
        vote_foret = vote_foret + vote_arbre
    if vote_foret >= (nb_arbres/2) :
        DMMP == True
    return DMMP


    
    