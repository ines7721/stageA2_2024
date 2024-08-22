import random

def classification(R_slice, integrales, delta, derivee_max):
    nb_arbres = 5
    arbres = [arbre_decisionnel() for _ in range(nb_arbres)]
    
    for arbre in arbres:
        arbre.entrainement(integrales, delta, derivee_max)
    
    votes = [arbre.prediction(integrales, delta, derivee_max) for arbre in arbres]
    preediction_finale = max(set(votes), key=votes.count)
    
    print("Classification lancée, résultat final :", prediction_finale)
    return prediction_finale

class arbre_decisionnel:
    def intialisation(self):
        self.modele = None
    
    def entrainement(self, integrales, delta, derivee_max):
        self.modele = random.choice([0, 1])  
    
    def prediction(self, integrales, delta, derivee_max):
        return self.modele