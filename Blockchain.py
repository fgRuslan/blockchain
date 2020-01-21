import hashlib
import json
from time import time
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from uuid import uuid4
import requests

import nacl.utils
from nacl.public import PrivateKey, Box
import nacl.encoding
import nacl.signing
import base64
import binascii

node_identifier = str(uuid4()).replace('-', '')

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = []

    def balances(self):
        response = {}
        for c in self.chain:
            for t in c['transactions']:
                #import pdb; pdb.set_trace()
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

    def new_block(self, proof, previous_hash=None, time_stamp=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time_stamp or time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, signature=None):
        if (sender != "0") and (sender not in self.balances()):
            return (False, 'Sender not registered with blockchain')

        # Check sufficient funds
        if (sender != "0") and (self.balances()[sender] < amount):
            return (False,'Insufficient amount in account')
        if (amount < 0):
            return(False, 'Negative amount of coins')

        if sender != "0":
            j = {'sender': sender, 'recipient': recipient, 'amount': amount}
            msg = f'sender:{j["sender"]},recipient:{j["recipient"]},amount:{j["amount"]}'
            mysignature = base64.b64decode(signature.encode())
            pub_key = nacl.signing.VerifyKey(sender,encoder=nacl.encoding.HexEncoder)
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
        return self.chain[-1]
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof +=1

        return proof
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.append(parsed_url.netloc)
    def validate_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            block_txs = block['transactions']
            for tx in block_txs:
                if not tx['sender'] == '0':
                    signature = tx['signature']
                    signature = base64.b64decode(signature.encode())
                    pub_key = nacl.signing.VerifyKey(tx['sender'], encoder=nacl.encoding.HexEncoder)

                    j = {'sender': tx['sender'], 'recipient': tx['recipient'], 'amount': tx['amount']}
                    msg = f'sender:{j["sender"]},recipient:{j["recipient"]},amount:{j["amount"]}'

                    if not pub_key.verify(msg.encode(), signature):
                        print(f"Invalid signature at block {block}")
                        return (False, f"Invalid signature at block {block}")
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True
    def resolve_conflicts(self):
        print("resolving conflicts")
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print("Querying chain on node: " + node)
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.validate_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False
    def save_chain(self):
        with open('blockchain.dat', 'w') as outfile:
            json.dump(self.chain, outfile)
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
        last_block = self.last_block
        last_proof = last_block['proof']
        proof = self.proof_of_work(last_proof)

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
