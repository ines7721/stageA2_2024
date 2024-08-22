import time
from machine import ADC, Pin, mem32

# Initialisation de l'ADC
tension_ref_analog = ADC(Pin(2, Pin.IN))

# Configurer les registres pour la fréquence d'échantillonnage
mem32[0x40007000 + 0x630] = 111111111111111 #nombre d'échantillons stockés max
mem32[0x40007000 + 0x5F8] = 0x0 #fréquence d'échantillonnage
check_freq = mem32[0x40007000 + 0x5F8] #lecture
print("Entrée registre fréquence d'échantillonnage =", check_freq)
print(" ")

#temps d'acquisition : 0
mem32[0x40007000 + 0x518]  = 0x00020000

#oversample :
mem32[0x40007000 + 0x5F4] = 0


#mesure du temps d'éxecution de commandes sur micropython :
start = time.ticks_us()
a = 0
end = time.ticks_us()
#mid = end - start #avec cette ligne temps écoulé final > 1000 ms
#print(end - start) #183 - 244 - 305
tension_ref = tension_ref_analog.read_u16()
print((time.ticks_us() - end))



def mesure_durees(samples=4):
    duree_echantillonnage = [] #temps que prend l'ADC entre le début d'un échantillon et la fin de l'échantillon
    horloge_echantillonnage = [] #temps que prend l'ADC entre la micro-seconde de début de l'échantillonnage d'un échantillon et la micro-seconde de début du prochain échantillon
    duree_entre_deux = [] #temps qui s'écoule entre la fin d'un échantillon et le début du prochain

    # Stocker les timestamps
    start_times = []
    end_times = []

    for _ in range(samples):
        start_sampling = time.ticks_us()  # Début de l'échantillon
        tension_ref = tension_ref_analog.read_u16()  # Lecture ADC
        end_sampling = time.ticks_us()  # Fin de l'échantillon
        
        start_times.append(start_sampling)
        end_times.append(end_sampling)
        
    # Calculer les durées après avoir capturé les timestamps
    for i in range(samples):
        calcul_duree_echantillonnage = time.ticks_diff(end_times[i], start_times[i])
        duree_echantillonnage.append(calcul_duree_echantillonnage)
        
        if i < samples - 1:
            sampling_clock = time.ticks_diff(start_times[i + 1], start_times[i])
            between_duration = time.ticks_diff(start_times[i + 1], end_times[i])
            horloge_echantillonnage.append(sampling_clock)
            duree_entre_deux.append(between_duration)
        
    return duree_echantillonnage, horloge_echantillonnage, duree_entre_deux

# Measure durations for 100 samples
duree_echantillonnage, horloge_echantillonnage, duree_entre_deux = mesure_durees()

# Print the results and calculate frequencies
print("Durée d'échantillonnage : temps que prend l'ADC entre le début d'un échantillon et la fin de l'échantillon :")
for i, duration in enumerate(duree_echantillonnage):
    frequency = 1 / (duration * 1e-6) if duration > 0 else 0
    print(f"Échantillon {i+1}: {duration} us, Fréquence: {frequency:.2f} Hz")

print("\nHorloge d'échantillonnage : temps que prend l'ADC entre la micro-seconde de début de l'échantillonnage d'un échantillon et la micro-seconde de début du prochain échantillon")
for i, clock in enumerate(horloge_echantillonnage):
    frequency = 1 / (clock * 1e-6) if clock > 0 else 0
    print(f"Échantillon {i+1}: {clock} us, Fréquence: {frequency:.2f} Hz")

print("\nDurée entre deux échantillons : temps qui s'écoule entre la fin d'un échantillon et le début du prochain")
for i, duration in enumerate(duree_entre_deux):
    frequency = 1 / (duration * 1e-6) if duration > 0 else 0
    print(f"Échantillon {i+1}: {duration} us, Fréquence: {frequency:.2f} Hz")
