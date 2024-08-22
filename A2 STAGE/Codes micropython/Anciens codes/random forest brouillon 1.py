import random

nb_arbres = 5
seuils = (1, 1, 1)

class random_forest(integrales, derivee_max, delta, nb_arbres, seuil_integrales, seuil_derivee_max, seuil_delta) :
    def initialisation(nb_arbres, seuil) :
        self.nb_arbres = nb_arbres
        self.structure_foret = False
        self.seuil_integrales = seuil[0]
        self.seuil_derivee_max = seuil[1]
        self.seuil_delta = seuil[2]
        self.data = integrales, derivees_max, delta
        
    def separation(self) :
        for i in len(integrales) :
            if integrales >= seuil_integrale or abs(derivee_max) >= seuil_derivee_max or abs(delta) >= seuil_delta :
                self.branche1 = integrales[i], seuil_derivee_max[i], delta[i]
            else :
                self.branche2 = integrales[i], seuil_derivee_max[i], delta[i]
            
            
    def 