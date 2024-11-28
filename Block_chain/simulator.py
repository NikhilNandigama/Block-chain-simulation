import random
import heapq
import sys
from anytree import Node
from anytree.exporter import DotExporter
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm
import os



# Global Variables and paramaters
no_of_peers = None
current_time  = 0 # in seconds
max_no_of_transactions = 998 # maximum number of transactions in a block (excluding coinbase txn)
size_of_transaction = 8 # in Kilobits
transaction_id = 0 # unique id for each transaction
block_id = 0 # unique id for each block
mining_time = None # in seconds
mining_fee = 50 # in units
coinbase_id = -1 # id of the coinbase
tmean = None # mean time between transactions
adversary1_id = None # id of the first adversary
adversary2_id = None  # id of the second adversary

queing_delay_constant = 96 # kbits
fast_link_speed = 100*1000 # 100 Mbps in kbps   
slow_link_speed = 5*1000  # 5 Mbps in kbps


CREATE_TXN = 1
FORWARD_TXN = 2
RECIEVE_TXN = 3
CREATE_BLOCK = 4
FORWARD_BLOCK = 5
RECIEVE_BLOCK = 6
SUCCESSFUL_MINING = 7

############################################################################################################

# These are for analysis

blks_in_chain_adversary1 = 0
blks_in_chain_adversary2 = 0
tot_blks_adversary1 = 0
tot_blks_adversary2 = 0

tot_blks_in_chain = 0
tot_mined_blks = 0
############################################################################################################

# Transaction class

class Transaction:

    """
    Transaction class to represent a transaction in the network
    """

    def __init__(self,sender,reciever,amount,time):
        """
        Constructor to initialize the transaction
        Args:
        sender: id of the sender
        reciever: id of the reciever
        amount: amount of the transaction
        time: time of the transaction
        """
        self.sender = sender
        self.reciever = reciever
        self.amount = amount
        global transaction_id
        transaction_id += 1 # unique id for each transaction
        self.transaction_id = transaction_id
        self.time = time



class Event:

    """
    Event class to represent an event in the network
    """

    def __init__(self,scheduled_time:float,sender_id:int,reciever_id:int,item:any,type:int,misc = None):
        """
        Constructor to initialize the event
        Args:
        scheduled_time: scheduled time of the event
        sender_id: sender of the event
        reciever_id: reciever of the event
        item: item associated with the event (transaction or block)
        type: type of the event
        misc: miscellanous data associated with the event
        """
        self.scheduled_time = scheduled_time # sceduled time of the event
        self.sender_id = sender_id # sender of the event
        self.reciever_id = reciever_id # reciever of the event
        self.item = item # item associated with the event (transaction or block)
        self.type = type # type of the event
        self.misc = misc # miscellanous data associated with the event
    
    def __lt__(self,other):
       """
         Overriding the less than operator to compare the scheduled time of the events
         """
       return self.scheduled_time < other.scheduled_time
        

class Events:

    """
    Events class to represent the list of events in the network
    """

    def __init__(self):
        self.event_list = [] # list of events
    
    def add_event(self,event: Event): 
        heapq.heappush(self.event_list,event) # add event to the list
    
    def get_event(self):
        if len(self.event_list) == 0:
            return None # return None if the list is empty
        return heapq.heappop(self.event_list) # return the event with the minimum scheduled time and remove it from the list


class Block:

    """
    Block class to represent a block in the blockchain
    """

    def __init__(self,transactions_list:list,prev_block_id:int,creator_id:int,time:float,peer_balances:list):
        """
        Constructor to initialize the block
        Args:
        transactions_list: list of transactions in the block
        prev_block_id: id of the previous block
        creator_id: id of the creator of the block
        time: time of creation of the block
        peer_balances: peer balances after the transactions in the block
        """
        self.transactions_list = transactions_list # list of transactions in the block 
        
        if creator_id == -1:
            self.block_id = 0 # genesis block
        else:
            global block_id # unique id for each block
            block_id += 1
            self.block_id = block_id
        self.prev_block_id = prev_block_id # id of the previous block
        self.creator_id = creator_id # id of the creator of the block
        self.time = time # time of creation of the block
        self.parent = None # parent block
        self.children = [] # children blocks
        self.block_size = 8 * (1 + len(transactions_list)) # in Kilobits
        self.depth = 0 # depth of the block in the blockchain
        self.peer_balances = peer_balances # peer balances after the transactions in the block
    
    def add_child(self,child):

        """
        Function to add a child block to the current block
        """

        self.children.append(child) # add the child block to the list of children
        child.parent = self # set the parent of the child block
        child.depth = self.depth + 1 # set the depth of the child block
        child.prev_block_id = self.block_id # set the previous block id of the child block
        return child
        
class BlockChain:

    """
    BlockChain class to represent the blockchain
    """

    def __init__(self):
        self.root = Block([],-1,-1,0,[100]*no_of_peers) # genesis block
        self.seen_blocks = [self.root] # list of blocks seen by the blockchain
        self.max_depth = 0 # maximum depth of the blockchain
        self.longest_chain_id = 0 # block id of the  last block in the longest chain

    def add_block(self,block):
        """
        Function to add a block to the blockchain
        Returns:
        True if the block is added to the blockchain and the longest chain is updated
        False if the block is added to the blockchain but the longest chain is not updated
        """
        self.seen_blocks.append(block) # add the block to the list of seen blocks
        self.prev_block = self.find_block(block.prev_block_id) # find the previous block
        self.prev_block.add_child(block) # add the block as a child of the previous block
        if block.depth > self.max_depth: # check if the longest chain is updated
            self.max_depth = block.depth # update the maximum depth
            self.longest_chain_id = block.block_id # update the block id of the last block in the longest chain
            return True # return True if the longest chain is updated
        return False # return False if the longest chain is not updated

    def find_block(self,block_id):
        """
        Function to find a block in the blockchain using block id 
        """
        for i in self.seen_blocks:
            if i.block_id == block_id:
                return i



        
class Peer:

    """
    Peer class to represent a peer in the network
    """
    
    def __init__(self,id,is_slow,hashing_power,selfish=False):
        """
        Constructor to initialize the peer
        Args:
        id: id of the peer
        is_slow: whether the peer is slow
        lowCPU: whether the peer has low CPU
        low_hashing_power: hashing power of the peer if it is lowCPU
        """
        self.id = id
        self.is_slow = is_slow
        self.BlockChain = BlockChain()
        self.adjacency_list = [0]*no_of_peers
        self.neighbours = [] # list of connected neighbours
        self.hashing_power = hashing_power
        self.transactions_list = []
        self.unaccepted_blocks = [] # list of unaccepted blocks
        self.no_of_created_blocks = 0
        self.is_selfish = selfish
        self.selfish_blocks = [] # list of selfish blocks
        self.parent_block = None # parent block
        self.lead = 0 # lead of the selfish miner
    
    def create_Transaction(self,txn,time):
        """
        Function to create a transaction
        """
        for i in self.neighbours: # forward the transaction to the neighbours
            queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant) # queuing delay
            frwd_event = Event(time+queuing_delay,self.id,i,txn,FORWARD_TXN) # create a forward event
            events.add_event(frwd_event) # add the forward event to the list of events
        
        # schedule the next transaction
        next_transaction_time = time + random.expovariate(1 / tmean) # time of the next transaction
        next_reciever = random.sample(range(no_of_peers),1)[0] # reciever of the next transaction
        while next_reciever == self.id:
            next_reciever =  random.sample(range(no_of_peers),1)[0]
        next_amount = random.randint(1,3)
        next_txn = Transaction(self.id,next_reciever,next_amount,next_transaction_time)
        event = Event(next_transaction_time,self.id,next_reciever,next_txn,CREATE_TXN)
        events.add_event(event)
        
            

    def recieve_transaction(self,txn,sender_id,time):
        """
        Function to recieve a transaction
        """
        if txn in self.transactions_list: # check if the transaction is already seen
            pass
        else:
            self.transactions_list.append(txn) # add the transaction to the list of seen transactions
            for i in self.neighbours:
                if i == sender_id: # forward the transaction to the neighbours and not the sender
                    continue
                queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                event = Event(time+queuing_delay,self.id,i,txn,FORWARD_TXN)
                events.add_event(event)


    def forward_transaction(self,txn,reciever_id,time):
        """
        Function to forward a transaction
        """
        prop_delay = N.propgation_delay[self.id][reciever_id]
        transmission_delay = (size_of_transaction/N.link_speeds[self.id][reciever_id])
        event = Event(time+prop_delay+transmission_delay,self.id,reciever_id,txn,RECIEVE_TXN)
        events.add_event(event)

	
	
    def recieve_block(self,block,time,sender_id):

        """
        Function to recieve a block
        """
        if self.is_selfish:
            if block in self.BlockChain.seen_blocks: # check if the block is already seen
                return
            else:
                honest_chain_length = self.longest_chain() # length of the honest longest chain

                if self.BlockChain.find_block(block.prev_block_id)!= None: # check if the previous block is seen
                    if(self.validate_block(block)): # validate the block
                        if self.BlockChain.add_block(block): # add the block to the blockchain and if the longest chain is updated, schedule the next block creation
                            
                            # schedule the next block creation if the longest chain is updated
                            event = Event(time,self.id,None,None,CREATE_BLOCK) 
                            events.add_event(event)
                        if block.depth > honest_chain_length: # check if the longest honest chain is updated
                            if len(self.selfish_blocks) == 0:
                                lead_diff = 0
                            else:  
                                lead_diff = self.selfish_blocks[-1].depth - block.depth # lead difference
                            if lead_diff < 2:
                                # this covers the both case 1 and case 2 of the assignment statement
                                self.release_all_selfish_blks(time) # release all the selfish blocks if the lead difference is less than 2
                                
                            else:
                                    # if the lead difference is greater than 2, forward one block
                                    # for everyone one block recievd to the neighbours
                                    blk = self.selfish_blocks[0]
                                    for i in self.neighbours:
                                        queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                                        event = Event(time+queuing_delay,self.id,i,blk,FORWARD_BLOCK)
                                        events.add_event(event)
                                    self.selfish_blocks.pop(0)

                                
                        for i in self.unaccepted_blocks:
                            # check if the unaccepted blocks can be added to the blockchain
                            if self.BlockChain.find_block(i.prev_block_id)!= None:
                                honest_chain_length = self.longest_chain()
                                if self.BlockChain.add_block(i):
                                    # schedule the next block creation if the longest chain is updated
                                    event = Event(time,self.id,None,None,CREATE_BLOCK)
                                    events.add_event(event)
                                self.unaccepted_blocks.remove(i) # remove the block from the list of unaccepted blocks
                                if i.depth > honest_chain_length:
                                    if len(self.selfish_blocks) == 0:
                                        lead_diff = 0
                                    else:  
                                        lead_diff = self.selfish_blocks[-1].depth - i.depth
                                    if lead_diff < 2:
                                        self.release_all_selfish_blks(time)
                                    else:
                                        blk = self.selfish_blocks[0]
                                        for i in self.neighbours:
                                            queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                                            event = Event(time+queuing_delay,self.id,i,blk,FORWARD_BLOCK)
                                            events.add_event(event)
                                        self.selfish_blocks.pop(0)
                    else:
                        # add the block to the list of unaccepted blocks if the block is not valid 
                        self.unaccepted_blocks.append(block)
                else:
                    self.unaccepted_blocks.append(block)
            
                        
            

        else:
            if block in self.BlockChain.seen_blocks: # check if the block is already seen
                return
            else:
                if self.BlockChain.find_block(block.prev_block_id)!= None: # check if the previous block is seen
                    if(self.validate_block(block)): # validate the block
                        if self.BlockChain.add_block(block): # add the block to the blockchain and if the longest chain is updated, schedule the next block creation
                            
                            # schedule the next block creation if the longest chain is updated
                            event = Event(time,self.id,None,None,CREATE_BLOCK) 
                            events.add_event(event)
                            

                        for i in self.neighbours:
                            if i == sender_id: # forward the block to the neighbours and not the sender
                                continue
                            queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                            event = Event(time+queuing_delay,self.id,i,block,FORWARD_BLOCK)
                            events.add_event(event)
                            
                        for i in self.unaccepted_blocks:
                            # check if the unaccepted blocks can be added to the blockchain
                            if self.BlockChain.find_block(i.prev_block_id)!= None:
                                if self.BlockChain.add_block(i):
                                    # schedule the next block creation if the longest chain is updated
                                    event = Event(time,self.id,None,None,CREATE_BLOCK)
                                    events.add_event(event)
                                self.unaccepted_blocks.remove(i) # remove the block from the list of unaccepted blocks
                    else:
                        # add the block to the list of unaccepted blocks if the block is not valid 
                        # and forward it to the neighbours
                        self.unaccepted_blocks.append(block)
                        for i in self.neighbours:
                            if i == sender_id:
                                continue
                            queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                            event = Event(time+queuing_delay,self.id,i,block,FORWARD_BLOCK)
                            events.add_event(event)

                else:
                    # add the block to the list of unaccepted blocks if the previous block is not seen
                    # and forward it to the neighbours
                    self.unaccepted_blocks.append(block)
                    for i in self.neighbours:
                        if i == sender_id:
                            continue
                        queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                        event = Event(time+queuing_delay,self.id,i,block,FORWARD_BLOCK)
                        events.add_event(event)

        
    def create_block(self,time):
        """
        Function to create a block
        """
        if self.hashing_power == 0:
            return
        transaction_copy = []
        if self.is_selfish:
            coinbase_txn = Transaction(coinbase_id,self.id,mining_fee,time)
            transaction_copy.append(coinbase_txn)
        else:
            transaction_copy = self.transactions_list.copy()
            parent_block = self.BlockChain.find_block(self.BlockChain.longest_chain_id)
            while parent_block.block_id != -1 and parent_block.block_id != 0:
                for i in parent_block.transactions_list:
                    if i in transaction_copy:
                        transaction_copy.remove(i) # remove the transactions already in the blockchain
                parent_block = parent_block.parent
            
            # transaction_copy has the transactions that are not in the longest chain in the blockchain
            
                
            if len(transaction_copy) > max_no_of_transactions:
                transaction_copy = transaction_copy[:max_no_of_transactions]
            
            # create the coinbase transaction and add it to the list of transactions
            coinbase_txn = Transaction(coinbase_id,self.id,mining_fee,time)
            transaction_copy.append(coinbase_txn)

        # update the peer balances after the transactions in the block
        peer_balances = self.BlockChain.find_block(self.BlockChain.longest_chain_id).peer_balances.copy()
        for i in transaction_copy:
            if i.sender == coinbase_id:
                peer_balances[self.id] += mining_fee
            else:
                if peer_balances[i.sender] <  i.amount:
                    transaction_copy.remove(i)
                else:    
                    peer_balances[i.sender] -= i.amount
                    peer_balances[i.reciever] += i.amount

        # create the block
        hashing_time = random.expovariate(self.hashing_power / mining_time)
        new_block = Block(transaction_copy,self.BlockChain.longest_chain_id,self.id,time+hashing_time,peer_balances)
        
        # schedule the mining of the block
        event = Event(time +hashing_time,self.id,None,new_block,SUCCESSFUL_MINING,self.BlockChain.longest_chain_id)
        events.add_event(event)

    def forward_block(self,block,time,reciever_id):
        """
        Function to forward a block
        """
        prop_delay = N.propgation_delay[self.id][reciever_id]
        transmission_delay = (block.block_size/N.link_speeds[self.id][reciever_id])
        event = Event(time+prop_delay+transmission_delay,self.id,reciever_id,block,RECIEVE_BLOCK)
        events.add_event(event)
    
    def successful_block(self,time,block,previous_longest_chain):
        """
        Function to mine a block
        """
        global tot_mined_blks
        global tot_blks_adversary1
        global tot_blks_adversary2
        if previous_longest_chain == self.BlockChain.longest_chain_id:
            # add the block to the blockchain and forward it to the neighbours if the longest chain is not updated
            # i.e no other peer has mined a block before this peer
     
            ############################################################################################################
            # These are for analysis 
            tot_mined_blks += 1
            if self.id == adversary1_id:
                tot_blks_adversary1 += 1
            if self.id == adversary2_id:
                tot_blks_adversary2 += 1
            ############################################################################################################

            if self.BlockChain.add_block(block):
                event = Event(time,self.id,None,None,CREATE_BLOCK)
                events.add_event(event)
            self.no_of_created_blocks += 1
            if self.is_selfish:
                self.selfish_blocks.append(block)
                self.lead +=1
            else:
                for i in self.neighbours:
                # forward the block to the neighbours
                    queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                    event = Event(time+queuing_delay,self.id,i,block,FORWARD_BLOCK)
                    events.add_event(event)
    
    def longest_chain(self):
        """
        return the length of the longest honest chain
        """
        k = 0
        for i in self.BlockChain.seen_blocks:
            if i in self.selfish_blocks:
                continue
            if i.depth > k:
                k = i.depth
        return k
                
    
    def validate_block(self,block):
        """
        Function to validate a recieved block
        """
        
        #  balances are stored near the peer, and these balances are used to validate the block
        balance = self.BlockChain.find_block(block.prev_block_id).peer_balances.copy()
        for i in block.transactions_list:
            if i.sender == coinbase_id:
                balance[block.creator_id] += mining_fee
            else:
                balance[i.sender] -= i.amount
                balance[i.reciever] += i.amount
        block.peer_balances = balance
        for i in range(no_of_peers):
            if balance[i] < 0:
                return False
        return True
    
    def release_all_selfish_blks(self,time):
        """
        release all the selfish blocks to the neighbours
        """
        for j in self.selfish_blocks:
            for i in self.neighbours:
                queuing_delay = random.expovariate(N.link_speeds[self.id][i]/queing_delay_constant)
                event = Event(time+queuing_delay,self.id,i,j,FORWARD_BLOCK)
                events.add_event(event)
        self.selfish_blocks = []


class Network:

    """
    Network class to represent the network
    """

    def __init__(self,no_of_peers,zeta1,zeta2,tmean):
        """
        Constructor to initialize the network
        Args:
        no_of_peers: number of peers in the network
        slow: percentage of slow peers
        lowCPU: percentage of lowCPU peers
        tmean: mean time between transactions
        """
        self.peers = [] # list of peers
        self.zeta1_power = float(zeta1)/float(100)
        self.zeta2_power = float(zeta2)/float(100)
        self.tmean = tmean
        self.connected_graph = False # whether the network is connected
        self.no_of_peers = no_of_peers
        no_of_slow = int(no_of_peers/2) # number of slow peers
        self.propgation_delay = [[random.uniform(0.010,0.500) for _ in range(no_of_peers)] for _ in range(no_of_peers)]

        # create the peers and assign the slow and lowCPU attributes
        slow_list = [1] * no_of_slow + [0] * (no_of_peers - no_of_slow)
        random.shuffle(slow_list)

        # assign the selfish nodes
        selfish_nodes = random.sample(range(no_of_peers),2)
        global adversary1_id, adversary2_id
        adversary1_id, adversary2_id = selfish_nodes

        # make sure that the selfish nodes are not slow
        if slow_list[adversary1_id] == 1:
            slow_list[adversary1_id] = 0
            for i in range(no_of_peers):
                if slow_list[i] == 0 and i != adversary2_id and i != adversary1_id:
                    slow_list[i] = 1
                    break
        if slow_list[adversary2_id] == 1:
            slow_list[adversary2_id] = 0
            for i in range(no_of_peers):
                if slow_list[i] == 0 and i != adversary2_id and i != adversary1_id:
                    slow_list[i] = 1
                    break

        print("Selfish nodes: ",selfish_nodes)


        
        honest_mining_power = float(100-zeta1-zeta2)/float(100*(self.no_of_peers-2))
        for i in range(no_of_peers):
            if i == adversary1_id:
                self.peers.append(Peer(i,slow_list[i],self.zeta1_power,True))
            elif i == adversary2_id:
                self.peers.append(Peer(i,slow_list[i],self.zeta2_power,True))
            else:
                self.peers.append(Peer(i,slow_list[i],honest_mining_power))
        
        # create the link speeds between the peers
        self.link_speeds = [[fast_link_speed for _ in range(no_of_peers)] for _ in range(no_of_peers)] # 100 Mbps in kbps
        for i in range(no_of_peers):
            for j in range(no_of_peers):
                if self.peers[i].is_slow or self.peers[j].is_slow:
                    self.link_speeds[i][j] =  slow_link_speed # 5 Mbps in kbps

    def create_adjacency_list(self):

        """
        Function to create the adjacency list of the network
        until the network is connected
        """

        while not self.connected_graph:
            for i in range(no_of_peers):
                self.peers[i].adjacency_list = [0]*no_of_peers
                self.peers[i].neighbours = []

            for i in range(no_of_peers):
                # making sure that each peer has atleast 3 neighbours and atmost 6 neighbours
                # neighbours are selected randomly
                # network should have atleast 6 peers
                no_of_neighbours = random.randint(max(0,3-len(self.peers[i].neighbours)),max(0,6-len(self.peers[i].neighbours)))
                neighbours = random.sample(range(no_of_peers),no_of_neighbours)
                for j in neighbours:
                    if self.peers[i].adjacency_list[j] == 0 and i != j:
                        self.peers[i].adjacency_list[j] = 1
                        self.peers[j].adjacency_list[i] = 1
                        self.peers[j].neighbours.append(i)
                        self.peers[i].neighbours.append(j)
            
            self.connected_graph=self.check_connected_network()

    def check_connected_network(self):
        """
        Function to check if the network is connected
        """
        visited = [0]*no_of_peers
        q = [0]
        visited[0] = 1
        while len(q) != 0:
            v = q.pop(0)
            for i in self.peers[v].neighbours:
                if visited[i] == 0:
                    visited[i] = 1
                    q.append(i)
        if 0 in visited:
            return False
        return True
    
    def generate_intitial_transaction(self):
        """
        Function to generate the initial transactions
        """

        for i in range(no_of_peers):

            reciever = random.sample(range(self.no_of_peers),1)[0]
            while reciever == i:
                reciever = random.sample(range(self.no_of_peers),1)[0]
            amount = random.randint(1,3)
            var_time = random.expovariate(1 / tmean)
            event = Event(var_time,i,reciever,Transaction(i,reciever,amount,var_time),CREATE_TXN)
            events.add_event(event)
    
    def generate_initial_block(self):
        """
        Function to generate the initial block
        """
        for i in range(no_of_peers):
            event = Event(0,i,None,None,CREATE_BLOCK)
            events.add_event(event)


############################################################################################################
# Analysis
def analysis():
    global blks_in_chain_adversary1
    global blks_in_chain_adversary2
    k=0
    # find a peer which is not a neighbour of the adversaries and not an adversary for the analysis
    for i in range(no_of_peers):
        if i not in N.peers[adversary1_id].neighbours and i not in N.peers[adversary2_id].neighbours and i != adversary1_id and i != adversary2_id:
            k = i
            break
    blk = N.peers[k].BlockChain.find_block(N.peers[k].BlockChain.longest_chain_id)
    while blk.block_id != 0:
        # print(blk.creator_id)
        if blk.creator_id == adversary1_id:
            blks_in_chain_adversary1 += 1
        if blk.creator_id == adversary2_id:
            blks_in_chain_adversary2 += 1
        blk = blk.parent
        
    # store the output in the output folder

    with open(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}/Analysis.txt", 'w') as f:
        f.write(f"No of peers: {no_of_peers}\nHashing_power_of_adversary1: {zeta1}\nHashing_power_of_adversary2: {zeta2}\nTmean: {tmean}\nMax_iterations: {max_iterations}\nMining_time: {mining_time}\n")
        tot_blks_in_chain = N.peers[0].BlockChain.max_depth
        f.write(f"Adversary1 id: "+str(adversary1_id)+"\n")
        f.write(f"Adversary2 id: "+str(adversary2_id)+"\n")
        f.write(f"Adversary1 blocks in chain: "+str(blks_in_chain_adversary1)+"\n")
        f.write(f"Total blocks mined by Adversary1: "+str(tot_blks_adversary1)+"\n")
        f.write(f"Adversary2 blocks in chain: "+str(blks_in_chain_adversary2)+"\n")
        f.write(f"Total blocks mined by Adversary2: "+str(tot_blks_adversary2)+"\n")
        if tot_blks_adversary1 != 0:
            print("MPU node adv1: ",blks_in_chain_adversary1/tot_blks_adversary1)
            f.write(f"MPU node adv1: " + str(blks_in_chain_adversary1/tot_blks_adversary1) + "\n")
        else:
            f.write(f"MPU node adv1: 0\n")
        if tot_blks_adversary2 != 0:
            print("MPU node adv2: ", blks_in_chain_adversary2/tot_blks_adversary2)
            f.write(f"MPU node adv2: " + str(blks_in_chain_adversary2/tot_blks_adversary2) + "\n")
        else:
            f.write(f"MPU node adv2: 0\n")
        if tot_mined_blks != 0:
            print("MPU node overall: ",tot_blks_in_chain/tot_mined_blks)
            f.write(f"MPU node overall: " + str(tot_blks_in_chain/tot_mined_blks) + "\n")
        else:
            print("MPU node overall: 0")
            f.write(f"MPU node overall: 0\n")  
        if tot_blks_in_chain != 0:
            print("Fraction of Adversary1 blocks in main chain:",str(blks_in_chain_adversary1/tot_blks_in_chain))
            f.write(f"--Fraction of Adversary1 blocks in main chain: "+str(blks_in_chain_adversary1/tot_blks_in_chain)+"\n")
            print("Fraction of Adversary2 blocks in main chain:",blks_in_chain_adversary2/tot_blks_in_chain)
            f.write(f"Fraction of Adversary1 blocks in main chain: "+str(blks_in_chain_adversary2/tot_blks_in_chain)+"\n")
        else:
            print("Fraction of Adversary1 blocks in main chain: 0")
            f.write(f"--Fraction of Adversary1 blocks in main chain: 0\n")
            print("Fraction of Adversary1 blocks in main chain: 0")
            f.write(f"Fraction of Adversary1 blocks in main chain: 0\n")

    f.close()       

    for i in range(no_of_peers):

        # create the blockchain image
        nodes = {}
        for block in N.peers[i].BlockChain.seen_blocks:
            color = 'black'
            if block.creator_id == adversary1_id:
                color = 'red'
            if block.creator_id == adversary2_id:
                color = 'blue'
            if block.block_id == N.peers[i].BlockChain.longest_chain_id:
                color = 'green'
            nodes[block.block_id] = Node(f"Block ID: {block.block_id}\nMiner ID: {block.creator_id}\nTime: {block.time}\n Depth: {block.depth}, No of trans: {len(block.transactions_list)}\n", color=color)
        for block in N.peers[i].BlockChain.seen_blocks:
            if block.parent is not None:
                nodes[block.block_id].parent = nodes[block.parent.block_id]
        DotExporter(nodes[N.peers[i].BlockChain.root.block_id], nodeattrfunc=lambda node: f'color="{node.color}"').to_picture(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}/Peer_{i}_BlockChain_Image.png")

    # create the peer network graph
    Peer_Network_Graph = nx.Graph()
    for peer in N.peers:
        Peer_Network_Graph.add_node(peer.id)
    for peer in N.peers:
        for neighbour_id in peer.neighbours:
            Peer_Network_Graph.add_edge(peer.id, neighbour_id)
    plt.figure(figsize=(20,20))
    nx.draw(Peer_Network_Graph, with_labels = True, node_size=500, font_size=12)
    plt.savefig(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}/Peer_Network.png")


############################################################################################################

no_of_peers = int(input("Enter the number of peers: "))
zeta1 = int(input("Enter the percentage hashing power of selfish miner1: "))
zeta2 = int(input("Enter the percentage hashing power of selfish miner2: "))
tmean = float(input("Enter the mean time between transactions(in milliseconds): "))/1000
mining_time = float(input("Enter the mean time between the blocks(in milliseconds): "))/1000
max_iterations = 2000000 # maximum number of iterations
events = Events()

# create the network and initialize the blockchain
N = Network(no_of_peers,zeta1,zeta2,tmean)
N.create_adjacency_list()
N.generate_initial_block()
N.generate_intitial_transaction()

# store the output in the output folder
# clear the output folder if it already exists
if not os.path.exists(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}"):
    os.makedirs(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}")
else:
    for the_file in os.listdir(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}"):
        file_path = os.path.join(f"output_{no_of_peers}_{zeta1}_{zeta2}_{tmean}_{mining_time}_{max_iterations}", the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

# run the simulation
for _ in tqdm(range(max_iterations)):
    event = events.get_event()
    if event == None:
        break # break if there are no more events
    else:
        # process the event and update the current time
        current_time = event.scheduled_time
        if event.type == CREATE_TXN:
            N.peers[event.sender_id].create_Transaction(event.item,event.scheduled_time)
        elif event.type == FORWARD_TXN:
            N.peers[event.sender_id].forward_transaction(event.item,event.reciever_id,event.scheduled_time)
        elif event.type == RECIEVE_TXN:
            N.peers[event.reciever_id].recieve_transaction(event.item,event.sender_id,event.scheduled_time)
        elif event.type == CREATE_BLOCK:
            N.peers[event.sender_id].create_block(event.scheduled_time)
        elif event.type == FORWARD_BLOCK:
            N.peers[event.sender_id].forward_block(event.item,event.scheduled_time,event.reciever_id)
        elif event.type == RECIEVE_BLOCK:
            N.peers[event.reciever_id].recieve_block(event.item,event.scheduled_time,event.sender_id)
        elif event.type == SUCCESSFUL_MINING:
            N.peers[event.sender_id].successful_block(event.scheduled_time,event.item,event.misc)


# release all the selfish blocks at the end of the simulation
if len(N.peers[adversary1_id].selfish_blocks) != 0:
    N.peers[adversary1_id].release_all_selfish_blks(current_time)
if len(N.peers[adversary2_id].selfish_blocks) != 0:
    N.peers[adversary2_id].release_all_selfish_blks(current_time)

# only process the forward block and recieve block events at the end of the simulation
# to make sure that all the blocks are added to the blockchain and all peers have the same blockchain
while events.event_list:
    event = events.get_event()
    current_time = event.scheduled_time
    if event.type == RECIEVE_TXN:
            N.peers[event.reciever_id].recieve_transaction(event.item,event.sender_id,event.scheduled_time)
    elif event.type == RECIEVE_BLOCK:
            N.peers[event.reciever_id].recieve_block(event.item,event.scheduled_time,event.sender_id)
    elif event.type == FORWARD_TXN:
            N.peers[event.sender_id].forward_transaction(event.item,event.reciever_id,event.scheduled_time)
    elif event.type == FORWARD_BLOCK:
            N.peers[event.sender_id].forward_block(event.item,event.scheduled_time,event.reciever_id)
    

print("Analysis of the output...")
print("adversary1_id: ",adversary1_id)
print("adversary2_id: ",adversary2_id)
analysis() # analysis of the output
