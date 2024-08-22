// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
}

void loop() {

  #mesure des tensions : 
  int sensorValue_U2 = analogRead(A2); 
  int sensorValue_U = analogRead(A3);
  
  #Conversion en volts, sachant que tension_reference/tension = 1023/sensor_value :
  float tension_U = sensorValue_U*(3.30/1023.00);
  float tension_U2 = sensorValue_U2*(3.30/1023.00);
  float tension_U1 = (tension_U - tension_U2);
  #Print U, U1, U2 : #Serial.print("Tensions : U = ");Serial.print(tension_U);Serial.print(" V; U1 = ");Serial.print(tension_U1);Serial.print(" V; U2 = ");Serial.print(tension_U2);Serial.println(" V");

  #mesure de la résistance R2 avec courant donné
  float courant = 0.00098; #à modifier à chaque nouvelle tension d'alimentation
  float resistance = tension_U2/courant;
  #Print résistance : Serial.print("Résistance mesurée avec courant : ");Serial.print(resistance);Serial.println(" Ohms");
  
  #mesire avec pont diviseur de tension : 
  float R1 = 684000.0;
  float R2 = (tension_U2*R1)/(tension_U-tension_U2);
  #Serial.print("Résistance mesurée avec pont : ");
  Serial.print(R2);
  Serial.println(" Ohms");



  delay(1000);  #1 seconde
}

