import base64
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import nacl.encoding
import nacl.signing
import nacl.utils
import requests
from nacl.exceptions import BadSignatureError

import os

node_identifier = str(uuid4()).replace('-', '')


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = []

        self.block_count = 0

    def balances(self):
        response = {}
        for number in self.block_count:
            c = self.load_block(number)
            for t in c['transactions']:
                # import pdb; pdb.set_trace()
                if t['sender'] not in response:
                    response[t['sender']] = 0
                if t['recipient'] not in response:
                    response[t['recipient']] = 0
                response[t['sender']] -= t['amount']
                response[t['recipient']] += t['amount']
            # Transactions not yet in the chain (not sure right way to include these..)
            for t in self.current_transactions:
                if t['sender'] not in response:
                    response[t['sender']] = 0
                if t['recipient'] not in response:
                    response[t['recipient']] = 0
                response[t['sender']] -= t['amount']
                response[t['recipient']] += t['amount']
            return response
    def get_block_count(self):
        # path joining version for other paths
        DIR = './blockchain'
        return len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    def new_block(self, proof, previous_hash=None, time_stamp=None):
        block = {
            'index': self.block_count,
            'timestamp': time_stamp or time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block),
        }
        self.current_transactions = []

        self.save_block(block, self.block_count)
        self.block_count = self.get_block_count()

        return block

    def new_transaction(self, sender, recipient, amount, signature=None):
        if (sender != "0") and (sender not in self.balances()):
            return (False, 'Sender not registered with blockchain')

        # Check sufficient funds
        if (sender != "0") and (self.balances()[sender] < amount):
            return (False, 'Insufficient amount in account')
        if (amount < 0):
            return (False, 'Negative amount of coins')

        if sender != "0":
            j = {'sender': sender, 'recipient': recipient, 'amount': amount}
            msg = f'sender:{j["sender"]},recipient:{j["recipient"]},amount:{j["amount"]}'
            mysignature = base64.b64decode(signature.encode())
            pub_key = nacl.signing.VerifyKey(sender, encoder=nacl.encoding.HexEncoder)
            if not pub_key.verify(msg.encode(), mysignature):
                print("Invalid signature")
                return (False, "Invalid signature")
        sig = signature
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': sig,
        })
        self.save_pending_tx()
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.load_block(self.block_count)

    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        previous_hash = self.hash(self.last_block)
        proof = 0
        while self.valid_proof(last_proof, proof, previous_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.append(parsed_url.netloc)

    def validate_block(self, my_block):
        last_block = self.load_block(self.block_count)
        block = self.load_block(my_block)
        # my_block = self.load_block(block)
        block_txs = block['transactions']
        for tx in block_txs:
            if not tx['sender'] == '0':
                signature = tx['signature']
                signature = base64.b64decode(signature.encode())
                pub_key = nacl.signing.VerifyKey(tx['sender'], encoder=nacl.encoding.HexEncoder)

                j = {'sender': tx['sender'], 'recipient': tx['recipient'], 'amount': tx['amount']}
                msg = f'sender:{j["sender"]},recipient:{j["recipient"]},amount:{j["amount"]}'

                try:
                    okay = pub_key.verify(msg.encode(), signature)
                except BadSignatureError:
                    okay = False
                if not okay:
                    print(f"Invalid signature at block {block['index']}")
                    return False
        if block['previous_hash'] != self.hash(last_block):
            return False
        if not self.valid_proof(last_block['proof'], block['proof'], last_block['previous_hash']):
            return False
        # last_block = block
        return True

    def resolve_conflicts(self):
        print("resolving conflicts")
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        # max_length = len(self.chain)
        max_length = self.block_count

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print("Querying chain on node: " + node)
            count = requests.get(f'http://{node}/length')
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']

                for other_block_index in range(0, count):
                    response = requests.get(f'http://{node}/chain?index={other_block_index}')
                    block = response.json()['chain']
                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.validate_block(block):
                        if self.load_block(other_block_index) != block:
                            max_length = length
                            new_block = block
                            self.save_block(new_block)
                    else:
                        return False

            return True

    def save_chain(self):
        with open('blockchain.dat', 'w') as outfile:
            json.dump(self.chain, outfile)

    def save_block(self, block_data, number=None):
        print(block_data)
        my_number = number or block_data['index']
        with open(f'blockchain/{my_number}.dat', 'w') as outfile:
            json.dump(block_data, outfile)

    # NOTE: This function is meant to be called regularly because we need to sync our chain
    def load_block(self, number):
        file_object = open(f'blockchain/{number}.dat', 'r')
        dict_object = json.load(file_object)
        self.block_count = self.get_block_count()
        return dict_object

    def load_chain(self):
        file_object = open('blockchain.dat', 'r')
        dict_object = json.load(file_object)
        self.chain = dict_object

    def save_pending_tx(self):
        with open('pending_txs.dat', 'w') as outfile:
            json.dump(self.current_transactions, outfile)

    def load_pending_tx(self):
        with open('pending_txs.dat', 'r') as file_object:
            self.current_transactions = json.load(file_object)

    def save_nodes(self):
        with open('nodes.dat', 'w') as outfile:
            json.dump(self.nodes, outfile)

    def load_nodes(self):
        file_object = open('nodes.dat', 'r')
        dict_object = json.load(file_object)
        self.nodes = dict_object

    def mine(self, miner_address):
        # Мы запускаем алгоритм подтверждения работы, чтобы получить следующее подтверждение…
        last_block = self.load_block(self.block_count - 1)
        proof = self.proof_of_work(last_block)

        # Мы должны получить вознаграждение за найденное подтверждение
        # Отправитель “0” означает, что узел заработал крипто-монету
        self.new_transaction(
            sender="0",
            recipient=miner_address,
            amount=50,
        )
        # Создаем новый блок, путем внесения его в цепь
        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)

    def discover_peers(self):
        load_nodes()
        neighbours = self.nodes
        peers = []
        for node in neighbours:
            response = requests.get(f'http://{node}/peers/list')
            if response.status_code == 200:
                peers = response.json()
                print(peers)

        final_list = []
        for num in peers:
            if num not in final_list:
                final_list.append(num)
        for peer in final_list:
            self.nodes.append(peer)
        save_nodes()
        if len(peers) > 0:
            return True
        else:
            return False


blockchain = Blockchain()
blockchain.new_block(previous_hash=1, proof=100, time_stamp=1337)


def load_all():
    try:
        blockchain.load_chain()
        blockchain.load_pending_tx()
    except:
        print("Could not load chain from file")
    finally:
        pass


def save_all():
    try:
        blockchain.save_chain()
        blockchain.save_pending_tx()
    except:
        print("Could not save chain to file")
    finally:
        pass


def save_nodes():
    try:
        blockchain.save_nodes()
    except:
        print("Could not save nodes to file")
    finally:
        pass


def load_nodes():
    try:
        blockchain.load_nodes()
    except:
        print("Could not load nodes from file")
    finally:
        pass
