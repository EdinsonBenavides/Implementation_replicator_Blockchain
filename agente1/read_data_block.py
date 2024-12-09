import json
import os
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


def read_data():
    # Note: Never commit your key in your code! Use env variables instead:

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

    # Obtenemos los valores de las variables del contrato
    value_demanda = contract.functions.getPotenciaDemandada().call()
    number_agentes = contract.functions.getNumberAgentes().call()
    sum_potencias = contract.functions.sumPotencias().call()
    print(f'Potencia demandada: {value_demanda}, Numero de agentes: {number_agentes}')
    print(f'Suma de potencias: {sum_potencias}')
    