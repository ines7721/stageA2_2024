import ulab

Liste_integrales = []


nb_resistances = 3


for i in range (0, nb_resistances+1):
    Liste_integrales.append([0])
print("lite integreales", Liste_integrales)

for j in range (1, nb_resistances+1) :
    Liste_integrales[j].append(1)
    print(Liste_integrales[j])

print("Liste_integrales[1]:")
print(Liste_integrales[1])
print("Liste_integrales[1]:")
Liste_integrales[1].append(3)
print(Liste_integrales[1])

    
print("Liste_integrales[1][2] :")
print(Liste_integrales[1][2] )

for i in range (0, nb_resistances) :
    print(i)
    
    
print("i :", i, "j :", j)
print("integrales[] :", integrales)
print("integrales[j] :", integrales[j])
print("integrales[j][len(integrales[j]-1)]", integrales[j][len(integrales[j])-1])
print("R2[i+j]", R2[i+j])
print("R2[i+nb_resistances+j]", R2[i+nb_resistances+j])
print("debut[i]", debut[i])
print("debut_precedent", debut_precedent)    
    
    
    
    
    
    
    
    

