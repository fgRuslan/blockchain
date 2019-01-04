from tkinter import *
import threading
import requests

exec(open("./Blockchain.py").read())

app = Flask(__name__)

root = Tk()
root.title("PyCoin")

nodes_w = None
nodes_list = None
pk_w = None

sk = None
pk = None

self_addr = "127.0.0.1"
self_port = "5000"

try:
    blockchain.load_chain()
    blockchain.load_pending_tx()
except:
    print("Could not load chain from file")
finally:
    pass
address="Alice"
def save_blockchain():
    blockchain.save_chain()
    blockchain.save_pending_tx()
def load_blockchain():
    blockchain.load_chain()
    blockchain.load_pending_tx()
def send():
    #BUG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #BUG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #BUG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #YOU CAN NOT LOAD SIGNING KEY FROM ITS SERIALIZED VALUE
    #https://github.com/pyca/pynacl/issues/501
    sk = nacl.signing.SigningKey(send_sk.get(), encoder=nacl.encoding.HexEncoder)
    j = {'sender': address,
              'recipient': send_entry.get(),
              'amount': int(send_amount.get())}
    
    msg = f'sender:{j["sender"]},recipient:{j["recipient"]},amount:{j["amount"]}'
    sig = sk.sign(msg.encode())
    j['signature'] = sig
    print(sig)
    req = requests.post(f'http://{self_addr}:{self_port}/transactions/new', json=j)
    print("Transaction: ", req.content.decode())
    save_blockchain()
    load_blockchain()
def save_nodes():
    f = open("nodes.dat", "w")
    lst = []
    lst = nodes_list.get(1.0, END).splitlines()
    json.dump(lst, f)
    f.close()
def discover_nodes():
    try:
        blockchain.discover_peers()
    except:
        print("Could not discover new nodes")
def nodes_window():
    nodes_w = Tk()
    nodes_w.title("List nodes")
    l = Label(nodes_w, text="List of nodes", font="Arial 14")
    global nodes_list
    nodes_list = Text(nodes_w)
    nodes_list_save_button = Button(nodes_w, command=save_nodes, text="Save list of nodes")
    nodes_discover_button = Button(nodes_w, command=discover_nodes, text="Discover new nodes")
    l.pack(pady=10)
    nodes_list.pack()
    nodes_list_save_button.pack(pady=10)
    nodes_discover_button.pack(pady=10)
def gen_pk():
    global sk
    sk = nacl.signing.SigningKey.generate()#.encode(encoder=nacl.encoding.HexEncoder)
    global pk
    pk = sk.verify_key
    pk = pk.encode(encoder=nacl.encoding.HexEncoder)
    sk = sk.encode(encoder=nacl.encoding.HexEncoder)
    pk_list.insert(INSERT, "=PRIVATE=\n")
    pk_list.insert(INSERT, sk)
    pk_list.insert(INSERT, "\n=PUBLIC=\n")
    pk_list.insert(INSERT, pk)#.encode(encoder=nacl.encoding.HexEncoder))
    pk_list.insert(INSERT, "\n\n")
    pass
def new_privkeys():
    pk_w = Tk()
    pk_w.title("Generate new private keys")
    l = Label(pk_w, text="Your private keys", font="Arial 14")
    global pk_list
    pk_list = Text(pk_w)
    pk_gen_new = Button(pk_w, command=gen_pk, text="Generate new private key")
    l.pack(pady=10)
    pk_list.pack()
    pk_gen_new.pack(pady=10)

menubar = Menu(root)
root.config(menu=menubar)

fileMenu = Menu(menubar)
fileMenu.add_command(label="Save", command=save_blockchain)
fileMenu.add_command(label="List nodes", command=nodes_window)
menubar.add_cascade(label="File", menu=fileMenu)
walletmenu = Menu(menubar)
walletmenu.add_command(label="Generate private keys", command=new_privkeys)
menubar.add_cascade(label="Wallet", menu=walletmenu)
#Send section
l1 = Label(text="Отправить", font="Arial 14")
send_entry = Entry(width=50, text="Recipient")
send_amount = Entry(width=50, text="Amount")
send_pk = Entry(width=50, text="Public key")
send_sk = Entry(width=50, text="Private key")
send_button = Button(text="Отправить", command=send)

l1.pack(pady=10)
send_entry.pack()
send_amount.pack()
send_pk.pack()
send_sk.pack()
send_button.pack(pady=10)

root.mainloop()
nodes_w.mainloop()
