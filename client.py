from tkinter import *
import threading

exec(open("./Blockchain.py").read())

app = Flask(__name__)

root = Tk()
root.title("PyCoin")

nodes_w = None
nodes_list = None

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
    #f.write(nodes_list.get(1.0, END))
    f.close()
    pass
def nodes_window():
    nodes_w = Tk()
    nodes_w.title("List nodes")
    l = Label(nodes_w, text="List of nodes", font="Arial 14")
    global nodes_list
    nodes_list = Text(nodes_w)
    nodes_list_save_button = Button(nodes_w, command=save_nodes, text="Save list of nodes")
    l.pack(pady=10)
    nodes_list.pack()
    nodes_list_save_button.pack(pady=10)

menubar = Menu(root)
root.config(menu=menubar)

fileMenu = Menu(menubar)
fileMenu.add_command(label="Save", command=save_blockchain)
fileMenu.add_command(label="List nodes", command=nodes_window)
menubar.add_cascade(label="File", menu=fileMenu)
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
