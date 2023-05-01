#!/usr/bin/env python

import socket
import json
from p2p_types import File, FileList, Node, NodeList
import threading

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 2048  # Normally 1024, but we want fast response
GLOBAL_NODE_LIST = NodeList()

lock = threading.Lock()

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((TCP_IP, TCP_PORT))
# s.listen(1)
# while 1:

#     conn, addr = s.accept()
#     print ('Connection address:', addr)
#     while 1:
#         data = conn.recv(BUFFER_SIZE)
#         if not data: break
#         print ("received data:", data)
#         conn.send(data)  # echo
#     conn.close()




def find(fileName):
    ret_nodeList = NodeList()
    for node in GLOBAL_NODE_LIST.nodes:
        updatelist(node.ip, node.port)
        for file in node.filelist.files:
            if file.name == fileName:
                ret_nodeList.add(node)
                break
    return ret_nodeList



def main():
    #create a socket that can be connected to by all peers
    #listen for connections from peers
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(10)

    #accept connections from peers
    while 1: #stay alive
            
        conn, addr = s.accept()
        print ('Connection address:', addr)
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            print ("received data:", data)
            decoded_Data = data.decode()
            if ("find" in decoded_Data.split(" ")[0]):
                ret_nodelist = find(data.decode().split(" ")[1])
                serialzie_nodelist = json.dumps(ret_nodelist, default=lambda o: o.__dict__)
                conn.send(serialzie_nodelist.encode())
                conn.close()
                break

            #parse the data
            json_data =json.loads(decoded_Data)

            #if this is a node update the node list
            if json_data["type"] == "node": #this will be an init connection
                #update the node list
                #convert the json to a node object
                # node = json.loads(json_data)
                #add the node to the list
                node = Node(json_data['ip'], json_data['port'])
                node.id = json_data['id']
                node.status = json_data['status']
                for i in json_data['filelist']:
                    temp = File()
                    temp.name = i['name']
                    temp.size = i['size']
                    temp.hash = i['hash']
                    node.filelist.add(temp)
                with lock:
                    GLOBAL_NODE_LIST.add(node)

                #send an ACK
            
            elif json_data["type"] == "filelist":
                with lock:
                    for i in GLOBAL_NODE_LIST.nodes:
                        if i.id == json_data['node_id']:
                            i.filelist = FileList(json_data['node_id'])
                            for j in json_data['files']:
                                temp = File()
                                temp.name = j['name']
                                temp.size = j['size']
                                temp.hash_val = j['hash_val']
                                i.filelist.add(temp)
                            break
                
            conn.send("ACK".encode())  # reply with ACK
    
    s.close()


def getload(ip, port):
    #get the load of a peer

    #send a request to the peer
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.send("getload".encode())

    #wait for a response
    reply = s.recv(BUFFER_SIZE)
    #if the peer does not respond set the status of the node to 0

    if not reply: #reply should be an int
        #set this node status to 0
        for node in GLOBAL_NODE_LIST.nodes:
            if node.ip == ip and node.port == port:
                node.status = 0
                break
    else:
        #parse the response
        for node in GLOBAL_NODE_LIST.nodes:
            if node.ip == ip and node.port == port:
                node.load = int(str(reply))
                break
            


    return

def updatelist(ip,port):
    #send update lists to a peer 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.send("updatelist".encode())

    #wait for a response
    reply = s.recv(BUFFER_SIZE)
    reply = reply.decode()
    #parse the response
    if not reply: return -1
    else:
        json_data =json.loads(reply)
        with lock:
            for i in GLOBAL_NODE_LIST.nodes:
                if i.id == json_data['node_id']:
                    i.filelist = FileList(json_data['node_id'])
                    for j in json_data['files']:
                        temp = File()
                        temp.name = j['name']
                        temp.size = j['size']
                        temp.hash_val = j['hash_val']
                        i.filelist.add(temp)
                    break
            #if were here then we have a new node
            node = Node(json_data['ip'], json_data['port'])
            node.id = json_data['id']
            node.status = 1
            for i in json_data['filelist']:
                temp = File()
                temp.name = i['name']
                temp.size = i['size']
                temp.hash = i['hash']
                node.filelist.add(temp)
            GLOBAL_NODE_LIST.add(node)
    s.close()



if __name__=="__main__":
    #create main thread
    #create a thread to listen for connections from peers

    main()

