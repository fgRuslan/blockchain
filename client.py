from tkinter import *
import threading

exec(open("./Blockchain.py").read())

app = Flask(__name__)

root = Tk()
root.title("PyCoin")
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
    pass
def send():
    blockchain.new_transaction(address, send_entry.get(), int(send_amount.get()))
    pass
menubar = Menu(root)
root.config(menu=menubar)

fileMenu = Menu(menubar)
fileMenu.add_command(label="Save", command=save_blockchain)
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
