# Project 3

#### Group Members

Archit Kalla, kalla100@umn.edu, 5582245 - Sockets, tracking server, peer-to-peer connection.

Trey Taylor, tayl1931@umn.edu, 5546464 - Implemented some support code. Some error correction. Support coding.

## Running The Code

To run this code, you will need Python3 installed. No compilation is needed. 

To run the program, first launch the tracking server via:
> python3 tracker.py

To run the peer server, be sure to have a directory for each peer server next to the .py files. Run the peer server via:
> python3 node.py \<IP> \<Port> \<Directory>

## Notes
- Only tested using loopback IP
- The tracking server ip and port is hardcoded, potentially can cause a connection refused due to address and port in use, solution is to wait for a later time to test
- Killing a peer requires 2 CNTRL-C's this is due to pythons Multithreading
- Hashing was done using hashlib
- undefined behavior if it tries to download from itself (should be fine with loopback ip's but is untested)

## Instructions

The client interface supports the following commands:

> updatelist
> getload \<IP> \<Port>
> find \<Filename>
> download \<Filename>
> exit

#### updatelist
A peer which calls updatelist scans their  directory for files and sends the list to the tracking server.

#### getload
A peer which calls getload requests another peer's load.

#### find
A peer which calls find contacts the tracking server, which proceeds to contact other peer servers, obtaining their file list via updatelist.

#### download
A downloading peer which calls download will call find to the tracking server, which will return a list of sending peers who have the file in their directory. The sending peer which will be contacted is based on latency and load. The downloading peer then contacts the sending peer, which then sends the file data to the downloading peer who inserts it into their own directory.

#### exit
A peer which calls exit simply exits the program.

## Design
There are two main parts to the system: the peer and the tracking server. This system also has important and supplementary parts to it as well. The important parts include directories for the peers and the supplementary part includes a latency file.

The peer runs a simple interface loop which takes in tokens from the command line and executes the appropriate function. The peer also maintains a background listening thread that listens to actions called upon by other peers or the tracking server. The peer controls their directory, giving the list of files to the tracking server and sending the file data to downloading peers. The peer also holds a load value, which increments when it is downloading a file, and decrements after it finishes downloading. The peer can decide from which peer it downloads from based on a list of peers which has the sought after file, the peer's load, and the latency between peers. This peer latency is decided via a latency.txt file, which holds combinations of peer to peer latency. If a peer to peer connection in question is not present, the default latency value is 100ms. This latency is applied when a peer attempts to download, as it sets the peer to sleep for an amount of time. When downloading a find command will generate a list of available nodes that can fulfil the request. Then the peerselect function chooses the ideal peer based on parameters discuessed above. This will then send a send command to the peer the file is located on to prepare that peer to be downloaded from. Then the downloading is handled via a seperate thread. The hash is then generated after the download is completed. Once completed it checks agains the hash provided on the tracking server, if different will retry with the same peer continuously.

The tracking server deals with information handling between peers. This consists of letting peers know what other peers have, letting other peers know about each other, and giving some other miscellaneous peer information such as load. When a peer first launches, it connects to the tracking server which holds its information for all peers to use, like ip, port, and filelist. The tracking server when called upon by find will then check across all recognized peers to determine its filelist, or if the peer is down. If the peer is down, its status is set to 0 and is skipped in any following uses. If the tracking server goes down, no persistent data is kept, however it has the ability to rekindle the information as long as any peer makes an attempt to contact the tracking server. If a peer does not further contact the tracking server, it will no longer appear on the tracking server.

### Latency
The function used to decide which peer to download from is called peerselect. peerselect takes the minimum of the sum of the latency and ten times the load for a peer. Having a higher load decreases the available computation and bandwidth needed to serve a peer. However, the higher the latency, the less noticable of an impact the load will have.

## Test cases

Test Case 1: Set up tracking server and then peer.

- Setup: First, launch the tracking server. Once the tracking server is running, launch a peer server. 
- Expected State Change: The tracking server and peer server should be running. The peer server should be ready to take a command.
- Actual State Change: Success.

Test Case 2: Set up peer and then tracking server.

- Setup: First, launch the peer. Once the peer is running, launch the tracking server.
- Expected State Change: The peer server should fail to connect to the tracking server and stop running. Whereas the tracking server will start up.
- Actual State Change: Failure

Test Case 3: Set up tracking server and then two peers.

- Setup: First, launch the tracking server. Once the tracking server is running, two launch a peer servers with different IP port combos. 
- Expected State Change: The tracking server and peer server should be running. The peer server should be ready to take a command.
- Actual State Change: Success.

Test Case 4: Peer calls updatelist

- Setup: Setup for case 1. Afterwards, type "updatelist" in the peer's command line.
- Expected State Change: 
- Actual State Change: Success.

Test Case 5: A peer calls getload on another peer.

- Setup: Setup for case 3. Afterwards, in one peer's command line, type "getload \<IP> \<Port>", where the IP and Port are the same as the other peer.
- Expected State Change: The peer which calls getload should have the load of the other peer appear on the terminal. This value should be 0 (As we are not putting load on the peers yet).
- Actual State Change: Success.

Test Case 6: A peer calls find on a file in another peer's directory.

- Setup: Setup for case 3. Insert a file in one of the peer's directory. Afterwards, in the other peer's command line, type "find \<filename>" where filename is the file made earlier.
- Expected State Change: The peer which wanted to find the file should have the other peer's IP and Port under Found Nodes on the terminal.
- Actual State Change: Success

Test Case 7: A peer calls download on a file in another peer's directory.
- Setup: Setup for case 3. Insert a file in one of the peer's directory. Afterwards, in the other peer's command line, type "download \<filename>" where filename is the file made earlier.
- Expected State Change: In addition to case 6's expected state change, the file from the other peer should now be in the calling peer's directory.
- Actual State Change: Success.

Test Case 8: Tracking server goes down, peers do not contact tracking server after
- Setup: Setup case 3. add a unique file in each directory (test1, test2), execute find on one of the peers for a file Kill the tracking server (CNTRL-C), bring back the tracking server, find the same file
- Expected: The peers terminal should state that there were no peers found with the file
- Actual State Change: Request Denied

Test Case 9: Tracking server goes down, peers do contact tracking server after 
- Setup: setup case 8, except call update list on both peers before find on the file, call find on the file
- Expected: The result should have the peer that has the file present
- Actual State Change: Success.

Test Case 10: Node Crashes, file becomes unavailable from that node
- Setup: Setup case 3, place 2 identical files in each directory for both peers. execute find in the terminal for one of the files. Kill one of the peers using CNTRL-C. call find again
- Expected: the first find should return with both nodes, the second find should return with only 1 node
- Actual State Change: Success

Test Case 11: Add file while peer is running
- Setup: Setup case 3, place a file in a directory visible to peer. Call find on other peer for that file. add another file to directory. call update list on peer with new file directory, call find for the new file from other peer
- Expected: the second find should have the peer with the new file available to it
- Actual State Change: Success
