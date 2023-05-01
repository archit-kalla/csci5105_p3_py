import os
import pathlib

def Scan(dir):
    filelist = []
    path = pathlib.Path('.')
    for entry in path.iterdir():
        if entry.is_dir() and str(entry) == dir:
            path = pathlib.Path('./'+dir)
            for item in path.iterdir():
                if item.is_file():
                    filelist.append(item)
            return filelist
    return filelist

print("test")
filelist = Scan('folder')
print(filelist)