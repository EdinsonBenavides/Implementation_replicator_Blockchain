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


# Note: Never commit your key in your code! Use env variables instead:

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
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    # Sign the transaction:
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

    # Enviar la transacción
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

