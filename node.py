import os
import pathlib
import sys
from p2p_types import File, FileList, Node, NodeList
import socket
import json
import uuid
import threading
import time

TRACKER_TCP_IP = '127.0.0.1'
TRACKER_TCP_PORT = 5025

NODE_TCP_IP = '127.0.0.1'
NODE_TCP_PORT = 5010

UNDEFINED_LATENCY = 100
BUFFER_SIZE = 2048
MESSAGE = "Hello, World!"
LOAD = 0
DIRECTORY = "folder"

NODE_ID = str(uuid.uuid4())

# s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((TRACKER_TCP_IP, TRACKER_TCP_PORT))
# s.send(MESSAGE.encode())
# data = s.recv(BUFFER_SIZE)
# s.close()

def peerSelect(nodeList):
    selectedNode = None
    selectVal = 100000
    for node in nodeList.nodes:
        latency = getLatency(node.ip, node.port)
        load = getload(node.ip, node.port)
        if selectVal > latency + 10*load:
            selectedNode = node
            selectVal = latency + 10*load
    
    return selectedNode

def getLatency(ip, port):
    latFile = open("latency.txt", "r")
    for line in latFile:
        info = line.split(" ")
        if len(info) < 5:
            continue
        if info[0] == NODE_TCP_IP and info[1] == str(NODE_TCP_PORT) and info[2] == ip and info[3] == str(port):
            latFile.close()
            return int(info[4])
    latFile.close()
    return UNDEFINED_LATENCY

def scan(dir):
    filelist = FileList(NODE_ID) 
    path = pathlib.Path('.')
    for entry in path.iterdir():
        if entry.is_dir() and str(entry) == dir:
            path = pathlib.Path('./'+dir)
            for item in path.iterdir():
                if item.is_file():
                    file = File()
                    name = str(item)
                    name = name.split("/")[1]
                    file.name = name
                    file.size = os.path.getsize(str(item))
                    file.hash_val = file.hash_func(DIRECTORY)
                    filelist.add(file)
            return filelist
    return filelist

def updatelist():
    #update the local list of files 
    updated_filelist = scan(DIRECTORY)
    updated_filelist.node_port = NODE_TCP_PORT
    updated_filelist.node_id = NODE_TCP_IP

    #send the list to the tracker
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((TRACKER_TCP_IP, TRACKER_TCP_PORT))
    serialized_filelist = json.dumps(updated_filelist, default=lambda o: o.__dict__)
    s.send(serialized_filelist.encode())
    s.close()
    return

def updatelist_2(conn):
    #update the local list of files 
    updated_filelist = scan(DIRECTORY)
    updated_filelist.node_port = NODE_TCP_PORT
    updated_filelist.node_id = NODE_TCP_IP

    #send the list to the tracker
    serialized_filelist = json.dumps(updated_filelist, default=lambda o: o.__dict__)
    conn.send(serialized_filelist.encode())
    return



def download_thread(file, ip, port):
    #download a file from a peer
    correct_download = False
    global LOAD
    LOAD+=1
    while correct_download == False:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((NODE_TCP_IP, NODE_TCP_PORT+1+LOAD))
        s.listen(10)
        latency = getLatency(ip, port)
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect((ip, port))
        cmd = "send " + str(file.name)+" "+str(NODE_TCP_IP)+" "+str(NODE_TCP_PORT+1+LOAD)
        s2.send(cmd.encode())

        reply = s2.recv(BUFFER_SIZE)
        if not reply:
            return
        reply = reply.decode()
        if reply == "ACK":
            print("ACK")
        s2.close
        conn, addr = s.accept()
        
        print ('Connection address:', addr)
        file_write = open(DIRECTORY+"/"+file.name, "wb")
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            time.sleep(latency/1000)
            file_write.write(data)
        file_write.close()
        conn.close()
        s.close()

        #create a file object

        new_file = File()
        new_file.name = file.name
        new_file.size = os.path.getsize(DIRECTORY+"/"+file.name)
        new_file.hash_val = new_file.hash_func(DIRECTORY)

        if new_file.hash_val == file.hash_val:
            print("File downloaded successfully")
            correct_download = True
        else:
            print("File download failed")
            os.remove(DIRECTORY+"/"+file.name)
    LOAD-=1
    return



def download(file):
    #download a file from a peer
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.connect((TRACKER_TCP_IP, TRACKER_TCP_PORT))
    except ConnectionRefusedError:
        print("Connection refused, cannot download the file, tracker is down")
        s.close()
        return
    cmd = "find " + str(file.name)
    s.send(cmd.encode())

    reply = s.recv(BUFFER_SIZE)
    reply = reply.decode()

    nodeList_json = json.loads(reply)
    found_nodes = NodeList()
    if len(nodeList_json['nodes']) == 0:
        print("No nodes found with the file")
        s.close()
        return
    
    for node in nodeList_json['nodes']:
        temp = Node(node['ip'], node['port'])
        for file_temp in node['filelist']['files']:
            if file_temp['name'] == file.name:
                file.hash_val = file_temp['hash_val']
        found_nodes.add(temp)
    print(found_nodes.nodes)
    #get load and latency
    ideal_node = peerSelect(found_nodes)

    
    s.close()
    download_thread_var = threading.Thread(target=download_thread, args=(file, ideal_node.ip, ideal_node.port))
    download_thread_var.start()

    return

def send(file, ip, port):
    #send a file to a peer
    port = int(port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
    except ConnectionRefusedError:
        print("Connection refused, cannot send the file")
        s.close()
        return

    with open(DIRECTORY+"/"+file, "rb") as f:
        while True:

            data = f.read(BUFFER_SIZE)
            if not data:
                break
            s.sendall(data)
    s.close()
    return

def getload(ip, port):
    #get the load of a peer
    port = int(port)
    #send a request to the peer
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:

        s.connect((ip, port))
    except ConnectionRefusedError:
        print("Connection refused, cannot get load")
        s.close()
        return "Nothing"
    s.send("getload".encode())

    #wait for a response
    reply = s.recv(BUFFER_SIZE)
    if not reply:
        print("NACK")
    else:
        reply=reply.decode()
        return int(str(reply))


    return

def init_connection():
    #send the list to the tracker
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((TRACKER_TCP_IP, TRACKER_TCP_PORT))
    this_node = Node(NODE_TCP_IP, NODE_TCP_PORT)
    this_node.id = NODE_ID
    this_node.status = 1
    this_node.load = LOAD
    this_node.filelist = scan(DIRECTORY)


    this_node_searlized = json.dumps(this_node, default=lambda o: o.__dict__)
    s.send(this_node_searlized.encode()) #send
    
    reply = s.recv(BUFFER_SIZE) # reply
    if not reply:
        print("NACK")
    else:
        print("ACK")
    s.close()


def recv_comms():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((NODE_TCP_IP, NODE_TCP_PORT))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        data = conn.recv(BUFFER_SIZE)
        decoded_Data = data.decode()
        command = decoded_Data.split(" ")[0]
        args = decoded_Data.split(" ")[1:]
        if decoded_Data == "getload":
            conn.send(str(LOAD).encode())
        elif decoded_Data.split(" ")[0] == "send":
            send(args[0], args[1], args[2])
            conn.send("ACK".encode())
        elif decoded_Data.split(" ")[0] == "updatelist":
            updatelist_2(conn)

            
def command_loop():
    while True:
        usr_in = input("> ")
        cmd = usr_in.split(" ")[0]
        args = usr_in.split(" ")[1:]

        if cmd == "download":
            file_name = args[0]
            temp_file_obj = File()
            temp_file_obj.name = file_name
            download(temp_file_obj)
        elif cmd == "updatelist":
            updatelist()
        elif cmd == "getload":
            print(getload(args[0], args[1]))
        elif cmd == "exit":
            break
        elif cmd == "find":
            find(args[0])
        else:
            print("Invalid command")

def find(filename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.connect((TRACKER_TCP_IP, TRACKER_TCP_PORT))
    except ConnectionRefusedError:
        print("Connection refused, tracking server is down")
        return
    cmd = "find " + str(filename)
    s.send(cmd.encode())

    reply = s.recv(BUFFER_SIZE)
    if not reply:
        print("NACK OR NO FILE FOUND")
    else:
    
        reply = reply.decode()
        nodeList_json = json.loads(reply)
        found_nodes = NodeList()
        if len(nodeList_json['nodes']) == 0:
            print("No nodes found")
            return -1
        for node in nodeList_json['nodes']:
            temp = Node(node['ip'], node['port'])
            found_nodes.add(temp)
        
        print("Found nodes:")
        for node in found_nodes.nodes:
            print(node.ip, node.port)
    s.close()




def main():
    #main loop to interact with node
    recv_conns_thread = threading.Thread(target=recv_comms)
    print("Node starting and connecting to tracking server"")
    init_connection()
    recv_conns_thread.start()
    command_loop()
    
    return 0

if __name__ == "__main__":
    NODE_TCP_IP = sys.argv[1]
    NODE_TCP_PORT = int(sys.argv[2])
    DIRECTORY = sys.argv[3]
    main()


