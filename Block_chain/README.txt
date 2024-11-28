Required packages:

anyTree : to install use-> pip install anyTree
networkx: to install use-> pip install networkx
tqdm: to install use->  pip install tqdm
matplotlib: to install use-> pip install matplotlib

Running the program:

run python3 simulator.py
and then enter the number of peers, percent of slow peers, percent of lowCPU peers

If you cannot see the clear BlockChain image or the program is taking longer to run, reduce the maximum number of  iterations (max_iterations)


Output:

Output is stored in the output_{no_of_peers}_{zeta1}_{zeta2}_{lowCPU_percent}_{tmean}_{mining_time}_{max_iterations} directory

It contains BlockChain diagram and log file for each peers
It contains the Peer to Peer Network graph
It also contains Overall information about the Simulation in Peer_Network.txt 

Assumptions:

-> The blocks with the red border indicate the blocks created by adversary 1
-> The blocks with the blue border indicate the blocks created by adversary 2
-> The block with a green border indicates the last block of the longest chain of that Node
-> All the analysis is made by keeping 20 peers, and transaction inter-arrival time  as 10ms and block inter-arrival time as 100ms So that latency also comes into effect
-> At the end of the Simulation all the blocks stored by the selfish nodes are released, so the effect of selfish mining can be shown.