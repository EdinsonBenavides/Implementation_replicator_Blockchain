import paho.mqtt.client as mqtt
import json
import threading
import time
import signal
import sys
import queue

# Crear cola
Q  = queue.Queue()

# Leer el archivo JSON de configuración 
with open('config.json', 'r') as file:
    info_config = json.load(file)

# Configuración del broker
broker = info_config['broker']
port = info_config['port']
topics_public = info_config['topics_public']
topic_suscrib = info_config['topic_suscriptor']
ID_agente = info_config['ID_agente']
admin = info_config['admin']

# Configuración admin
global_data = {}
state_optimizacion = info_config['state_optimizacion']

publicadores = topics_public.keys()
lastet_data = {publicador:0 for publicador in publicadores} 

global_data = lastet_data.copy()

data = {"publicador": "admin",
 "state_optimizacion": state_optimizacion, 
 "potencia_demandada": 1200, 
 "numero_de_agentes": 3, 
 "num_iteraciones":100, 
 "data":global_data
}

# Función de publicación
def publish(data,topic, broker):
    global publish_flag
    # Convertir el diccionario a una cadena JSON
    message_str = json.dumps(data)

    # Crear una instancia del cliente
    client = mqtt.Client()

    try:
        # Conectarse al broker
        client.connect(broker, port, 60)
        if publish_flag:
            # Publicar el mensaje
            client.publish(topic, message_str)
            print(f"Mensaje JSON publicado en {topic}: {message_str}")
            time.sleep(1)  # Esperar 5 segundos antes de publicar nuevamente
    except Exception as e:
        print(f"Error al conectar o publicar: {e}")
    finally:
        # Desconectarse del broker
        client.disconnect()
        print("Cliente MQTT desconectado")

# Función de suscripción
def subscribe(topic,broker):
    # Función callback cuando se recibe un mensaje
    global global_data
    def on_message(client, userdata, message):
        try:
            # Convertir el payload a un diccionario
            data = json.loads(message.payload.decode())
            print(f"Mensaje recibido en {message.topic}: {data}")
            
            global_data[data['publicador']] = data["potencia"]
            Q.put(global_data)

        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")

    # Crear una instancia del cliente
    client = mqtt.Client()

    try:
        # Asignar la función callback
        client.on_message = on_message
        # Conectarse al broker
        client.connect(broker, port, 60)
        # Suscribirse al tema
        client.subscribe(topic)
        print(f"suscrito a: {topic}")
        # Mantenerse en escucha
        client.loop_forever()
    except Exception as e:
        print(f"Error al conectar o suscribir: {e}")


def writerJsonData():
    global state_optimizacion

    while True:
        if state_optimizacion:
            data = Q.get()
            with open('data_optimización.json', 'w') as file:
                json.dump(data, file)


# Crear hilos para publicar y suscribir
#publish_thread = threading.Thread(target=publish)
subscribe_thread = threading.Thread(target=subscribe,args=(topic_suscrib,broker))
write_thread = threading.Thread(target=writerJsonData)

# Iniciar hilos
#publish_thread.start()
subscribe_thread.start()
write_thread.start()

time.sleep(1)

publish_flag = True

while True:
    state_optimizacion = info_config['state_optimizacion']
    with open('config.json', 'r') as file:
        info_config = json.load(file)
        file.close()
    data = {"publicador": "admin",
    "state_optimizacion": state_optimizacion, 
    "potencia_demandada": 1200, 
    "numero_de_agentes": 3, 
    "num_iteraciones":10000, 
    "data":global_data
    }

    # Envia por primera vez la información a los agentes
    for publicador in publicadores:
        publish(data,topics_public[publicador],broker)




# Esperar a que los hilos terminen
#publish_thread.join()
subscribe_thread.join()
write_thread.join()
