from tkinter import *
import threading

import nacl.utils
from nacl.public import PrivateKey, Box
import nacl.encoding
import nacl.signing

exec(open("./Blockchain.py").read())

app = Flask(__name__)

root = Tk()
root.title("PyCoin")

nodes_w = None
nodes_list = None
pk_w = None

try:
    blockchain.load_chain()
    blockchain.load_pending_tx()
except:
    print("Could not load chain from file")
finally:
    pass
address=node_identifier
def save_blockchain():
    blockchain.save_chain()
    blockchain.save_pending_tx()
def send():
    blockchain.new_transaction(address, send_entry.get(), int(send_amount.get()))
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
    sk = nacl.signing.SigningKey.generate()#.encode(encoder=nacl.encoding.HexEncoder)
    pk = sk.verify_key
    pk_list.insert(INSERT, "=PRIVATE=\n")
    pk_list.insert(INSERT, sk.encode(encoder=nacl.encoding.HexEncoder))
    pk_list.insert(INSERT, "\n=PUBLIC=\n")
    pk_list.insert(INSERT, pk.encode(encoder=nacl.encoding.HexEncoder))
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
send_entry = Entry(width=50)
send_amount = Entry(width=50)
send_button = Button(text="Отправить", command=send)

l1.pack(pady=10)
send_entry.pack()
send_amount.pack()
send_button.pack(pady=10)

root.mainloop()
nodes_w.mainloop()
