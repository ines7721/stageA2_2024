from machine import Pin, ADC, mem32
import time
import math


#résolution :
mem32[0x40007000 + 0x5F0] = 1
check_resolution = mem32[0x40007000 + 0x5F0]
if check_resolution == 1 :
    nb_b = "10 bits"
if check_resolution == 0 :
    nb_b = "8 bits"
print("Résolution SAADC -", nb_b)
print("")

#echantillons max dans le buffer (valeur max) :
mem32[0x40007000 + 0x360] = 0x7FFF

#frequence d'échantillonnage :
mem32[0x40007000 + 0x500] = 1
mem32[0x40007000 + 0x00C] = 1
mem32[0x40007000 + 0x5F8] = 1010000000001 #CC = 80
#  mem32[0x40007000 + 0x5F8] = 1111111100001 #CC = 2040
                            

#oversample :
mem32[0x40007000 + 0x5F4] = 0

def mesure() :
    start_sampling = time.ticks_us()
    t1 = ADC(Pin(2, Pin.IN))
    end_sampling = time.ticks_us()
    t2 = t1.read_u16()
    t3 = (3.3*t2)/65536
    
    start_times.append(start_sampling)
    end_times.append(end_sampling)
    
    return t3
        
    
def calcul_frequence() :
    for i in range(nb_echantillons):
        calcul_duree_echantillonnage = time.ticks_diff(end_times[i], start_times[i])
        duree_echantillonnage.append(calcul_duree_echantillonnage)
        
        if i < nb_echantillons - 1:
            sampling_clock = time.ticks_diff(start_times[i + 1], start_times[i])
            between_duration = time.ticks_diff(start_times[i + 1], end_times[i])
            horloge_echantillonnage.append(sampling_clock)
            duree_entre_deux.append(between_duration)
        
    return duree_echantillonnage, horloge_echantillonnage, duree_entre_deux


nb_echantillons = 10
i = 0
start_times = []
end_times = []
duree_echantillonnage = []
horloge_echantillonnage = []
duree_entre_deux = []

for i in range(nb_echantillons) :
    t3 = mesure()
    print("tension =", t3)
    
duree_echantillonnage, horloge_echantillonnage, duree_entre_deux = calcul_frequence()
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



