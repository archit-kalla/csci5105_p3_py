from json import JSONEncoder
import hashlib
class File:
    def __init__(self) -> None:
        self.name = None
        self.size = None
        self.hash_val = None
        self.type= "file"
        pass
    
    def hash_func(self, dir):
        file = open(str(dir) + "/" + str(self.name), "rb")
        hashThis = file.read()
        return str(hashlib.md5(hashThis).hexdigest())
    

class FileList:
    def __init__(self, node_id) -> None:
        self.files = []
        self.node_id = node_id
        self.node_port = None
        self.node_ip = None
        self.type = "filelist"
        pass

    def add(self, file):
        self.files.append(file)
        pass

class Node:
    def __init__(self, ip, port) -> None:
        self.id = None
        self.status = None
        self.ip = ip
        self.port = port
        self.load = None
        self.filelist = None
        self.type = "node"
        pass

class NodeList:
    def __init__(self) -> None:
        self.nodes = []
        self.type = "nodelist"
        
    def add(self, node):
        self.nodes.append(node)
        
    def remove(self, node_ip, node_port):
        for node in self.nodes:
            if node.ip == node_ip and node.port == node_port:
                self.nodes.remove(node)
        
    def remove(self, node_id):
        for node in self.nodes:
            if node.id == node_id:
                self.nodes.remove(node)
        