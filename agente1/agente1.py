import paho.mqtt.client as mqtt
import json
import threading
import time
import signal
import sys
import os
import queue
import pandas as pd
import numpy as np
from web3 import Web3, EthereumTesterProvider
from web3.middleware import construct_sign_and_send_raw_middleware
from dotenv import load_dotenv

# Traemos información del contrato
try:
    with open('contract.json', 'r') as file:
        data_contract = json.load(file)
        # Traemos el ABI
        abiContract = data_contract["abi"]
        # Dirección del Contrato
        addressContract = data_contract["adress_contract"]
        # Nodo de Alchemy donde esta desplegado el contrato
        Nodo_Alchemy = data_contract["Nodo_Alchemy"]
except json.JSONDecodeError as e:
    print(f"Error al leer información del contrato JSON: {e}")

# Crear cola
Q  = queue.Queue()
lock = threading.Lock()

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
topic_admin = info_config["topic_admin"]
# Configuración agente

a = info_config['parametros']['a']
b = info_config['parametros']['b']
c = info_config['parametros']['c']

# Variable global para optimización
global_data = {}
state_optimizacion = False
publicadores = topics_public.keys()
lastet_data = {publicador:[0,0] for publicador in publicadores}
lastet_data[ID_agente] = [0,0] 

global_data = lastet_data.copy()

class AgentP2P():

    def __init__(self,a,b,c,P_d,numAgents,numID):

        self.a = a
        self.b = b
        self.c = c
        self.x_k = (P_d/numAgents)
        self.p = self.x_k
        self.p_evulution = [self.p]
        self.fi_evolution = [self.f_i()]
        self.f_mean = 1
        self.P_d = P_d
        self.numIter = 0
        self.alpha = 0.001
        self.numID = numID
        self.sumX = P_d
        self.numAgents = numAgents

    def f_i(self):

        fi = -(self.b + 2*(self.c*self.p))  + 2e3

        return fi

    def X_k(self):

        #self.x_k = self.p*(self.f_i()/self.f_mean)
        #self.x_k = self.p + self.alpha*self.p*(self.f_i()*self.sumX-self.f_mean)
        self.x_k = self.p + self.alpha*(self.p/self.P_d)*(self.f_i()*self.sumX-self.f_mean)
        self.p = self.x_k
        print("prueba potencia: ", self.p)
        self.p_evulution.append(self.x_k)

    def calculateXk(self):

        self.X_k()
        self.numIter += 1

    def getFi(self):
        self.fi_evolution.append(self.f_i())
        return self.f_i()

    def setF_mean(self, f_mean):
        self.f_mean = f_mean

    def setSumX(self, sumX):
        self.sumX = sumX

    def getXk(self):
        return self.x_k
    
    def calculate_Fmean(self, data):
        sum_data = 0
        keys_data = data.keys()
        for i in keys_data:
            sum_data += data[i][0]*data[i][1]
        self.setF_mean(sum_data)

        return self.f_mean
    def calculate_sumX(self, data):
        sum_data = 0
        keys_data = data.keys()
        for i in keys_data:
            sum_data += data[i][1]
        self.setSumX(sum_data)

        return self.sumX
    
# Función de publicación
def publish(data,topic, broker):
    global publish_flag
    global state_optimizacion
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
            time.sleep(0.01)  # Esperar 5 segundos antes de publicar nuevamente
    except Exception as e:
        print(f"Error al conectar o publicar: {e}")
    finally:
        # Desconectarse del broker
        if True: #not publish_flag:
            client.disconnect()
            print("Cliente MQTT desconectado")

# Función de suscripción
def subscribe(topic,broker):
    # Función callback cuando se recibe un mensaje
    global state_optimizacion
    global global_data
    
    def on_message(client, userdata, message):
        global state_optimizacion
        global global_data
        try:
            # Convertir el payload a un diccionario
            data = json.loads(message.payload.decode())
            print(f"Mensaje recibido en {message.topic}: {data}")
            if data['publicador'] == admin:
                state_optimizacion = data['state_optimizacion']
                with open('state_optimization.json', 'w') as file:
                    json.dump(data, file)
                
            else:
                """
                # Escribir el mensaje recibido en un archivo JSON
                with open('received_messages' + data['publicador'] + '.json', 'w') as file:
                    json.dump(data, file)

                """
                with lock:
                    global_data[data['publicador']] = data["variables"]
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
        

def readDataInitialBlockchain():

    # Note: Never commit your key in your code! Use env variables instead:

    # Nos conectamos al nodo de alchemy
    w3 = Web3(Web3.HTTPProvider(Nodo_Alchemy))

    # Cargar las variables del archivo .env
    load_dotenv()

    # Instanciamos la direccion de la cuenta (llave publica)
    account_address = os.getenv('Public_Key')
    # Instanciamos la llave privada
    private_key = os.getenv('Private_Key')

    # Obtenemos el nonce
    nonce = w3.eth.get_transaction_count(account_address)

    # Creamos una instancia del contrato
    contract = w3.eth.contract(address= addressContract, abi=abiContract)

    # Obtenemos los valores de las variables del contrato
    value_demanda = contract.functions.getPotenciaDemandada().call()
    number_agentes = contract.functions.getNumberAgentes().call()

    return [value_demanda,number_agentes]

def readDataOptimizationBlockchain():

    # Note: Never commit your key in your code! Use env variables instead:

    # Nos conectamos al nodo de alchemy
    w3 = Web3(Web3.HTTPProvider(Nodo_Alchemy))

    # Cargar las variables del archivo .env
    load_dotenv()

    # Instanciamos la direccion de la cuenta (llave publica)
    account_address = os.getenv('Public_Key')
    # Instanciamos la llave privada
    private_key = os.getenv('Private_Key')

    # Obtenemos el nonce
    nonce = w3.eth.get_transaction_count(account_address)

    # Creamos una instancia del contrato
    contract = w3.eth.contract(address= addressContract, abi=abiContract)

    # Obtenemos los valores de las variables del contrato
    sum_potencias = contract.functions.sumPotencias().call()

    return sum_potencias

def send_data_block(data):
    # Nos conectamos al nodo de alchemy
    w3 = Web3(Web3.HTTPProvider(Nodo_Alchemy))

    # Cargar las variables del archivo .env
    load_dotenv()

    # Instanciamos la direccion de la cuenta (llave publica)
    account_address = os.getenv('Public_Key')
    # Instanciamos la llave privada
    private_key = os.getenv('Private_Key')

    # Obtenemos el nonces
    nonce = w3.eth.get_transaction_count(account_address)

    # Creamos una instancia del contrato
    contract = w3.eth.contract(address= addressContract, abi=abiContract)

    transaction = contract.functions.sendData(data).build_transaction({
        'chainId': 80002,  # ID de la red (1 para mainnet)
        'gas': 1000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    # Sign the transaction:
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

    # Enviar la transacción
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Esperar a que la transacción sea minada (procesada)
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)  # 120 segundos de timeout
        print(f'Transacción confirmada en el bloque: {receipt.blockNumber}')
    except Exception as e:
        print(f'Error: {e}')

    try:
        with open('register_transactions.txt', 'a') as file:
            file.write(str(w3.to_hex(tx_hash)) + "," + str(data) + '.\n')
    except:
        pass
    
# Crear hilos para publicar y suscribir
#publish_thread = threading.Thread(target=publish)
subscribe_thread = threading.Thread(target=subscribe,args=(topic_suscrib,broker))
write_thread = threading.Thread(target=writerJsonData)

# Iniciar hilos
#publish_thread.start()
subscribe_thread.start()
write_thread.start()

time.sleep(1)

try:
    with open('state_optimization.json', 'r') as file:
        info_state_opti = json.load(file)

except json.JSONDecodeError as e:
    print(f"Error al leer state_optimization JSON: {e}")

while True:

    if state_optimizacion:

        # Bandera para controlar el bucle de publicación
        publish_flag = True

        num_iteraciones = info_state_opti['num_iteraciones']

        num_iteration = 0
        P_D = info_state_opti['potencia_demandada']
        Num_agentes = info_state_opti['numero_de_agentes']
        agente = AgentP2P(a,b,c,P_D,Num_agentes,ID_agente)

        fi = agente.getFi()
        xk = agente.getXk()
        lastet_data[ID_agente] = [fi,xk]

        with lock:
            global_data[ID_agente] = [fi,xk]
            Q.put(global_data)
        # Datos que queremos enviar como mensaje JSON

        data_admin = {
            "publicador": ID_agente,
            "potencia": xk,
            "iteracion": num_iteration
            }

        data = {
                "publicador": ID_agente,
                "variables": [fi,xk],
                "iteracion": num_iteration
            }
        
        # Primera publicacion al administrados
        publish(data_admin,topic_admin,broker)
        send_data_block(int(xk*1000))
        #time.sleep(5)
        # Envia por primera vez la información a los agentes
        for publicador in publicadores:
            publish(data,topics_public[publicador],broker)

        #time.sleep(10)

        # Empiezan las comunicaciones para iterar
        for num_iteration in range(1,num_iteraciones+1):
            
            """
            time.sleep(0.1)
            for publicador in publicadores:
                try:
                    with open('received_messages' + publicador + '.json', 'r') as file:
                        info_data_received = json.load(file)

                except json.JSONDecodeError as e:
                    print(f"Error al leer received_messages JSON: {e}")

                lastet_data[publicador] = info_data_received["variables"]
            """
            try:
                with open('data_optimización.json', 'r') as file:
                    info_data_received = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error al leer state_optimization JSON: {e}")
                
            print(lastet_data)
            lastet_data = info_data_received.copy()
            f_mean= agente.calculate_Fmean(lastet_data)
            sumX = agente.calculate_sumX(lastet_data)
            agente.calculateXk()
            fi = agente.getFi()
            xk = agente.getXk()

            lastet_data[ID_agente] = [fi,xk]

            print(f"prueba: {lastet_data[ID_agente][0]} y {lastet_data[ID_agente][1]}")
            print(lastet_data)
            with lock:
                global_data[ID_agente] = [fi,xk]
                Q.put(global_data)

            data = {
                "publicador": ID_agente,
                "variables": [fi,xk],
                "iteracion": num_iteration
            }
            for publicador in publicadores:
                publish(data,topics_public[publicador],broker)

            if (num_iteration%50 == 0):

                const_decimales = 1000
                data_admin = {
                "publicador": ID_agente,
                "potencia": xk,
                "iteracion": num_iteration
                }
                publish(data_admin,topic_admin,broker)

                send_data_block(int(agente.p*const_decimales))

                sum_SC = readDataOptimizationBlockchain()

                sumT = sum_SC/const_decimales
                if (sumT- agente.P_d < 0):
                    addP = abs(sumT-agente.P_d)/agente.numAgents
                    agente.p = xk + addP
                elif (sumT- agente.P_d > 0):
                    addP = abs(sumT-agente.P_d)/agente.numAgents
                    agente.p = xk - addP

            if num_iteration == num_iteraciones:
                state_optimizacion = False

            if not state_optimizacion:
                fi_evolution = agente.fi_evolution
                p_evolution = agente.p_evulution
                # Encontrar la longitud máxima
                max_length = max(len(agente.fi_evolution), len(agente.p_evulution))
                # Extender las listas a la misma longitud
                fi_evolution.extend([np.nan] * (max_length - len(fi_evolution)))
                p_evolution.extend([np.nan] * (max_length - len(p_evolution)))
                data_np = np.array([fi_evolution,p_evolution]).T
                data_evolution = pd.DataFrame(data_np, columns=['Fitness',"Potencia"])
                data_evolution.to_csv('evolution_data.csv')
                
                break
        publish(data_admin,topic_admin,broker)
        fi_evolution = agente.fi_evolution
        p_evolution = agente.p_evulution
        # Encontrar la longitud máxima
        max_length = max(len(agente.fi_evolution), len(agente.p_evulution))
        # Extender las listas a la misma longitud
        fi_evolution.extend([np.nan] * (max_length - len(fi_evolution)))
        p_evolution.extend([np.nan] * (max_length - len(p_evolution)))
        data_np = np.array([fi_evolution,p_evolution]).T
        data_evolution = pd.DataFrame(data_np, columns=['Fitness',"Potencia"])
        data_evolution.to_csv('evolution_data.csv')
        # Fin de sección de iteracion
    else:
        publish_flag = False


# Esperar a que los hilos terminen
#publish_thread.join()
subscribe_thread.join()
write_thread.join()