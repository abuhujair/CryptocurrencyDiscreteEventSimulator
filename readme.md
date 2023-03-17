# **DISCRETE EVENT SIMULATOR**
Discrete event simulator for a P2P cryptocurrency network (Similar to etherum). Simulations are used to study the effect of varying network delays and hashing power of nodes on the resultant blockchain. Results of the simulations contains graphs of peer networks and blockchains of individual nodes.

# **Installation**
- Clone the repository

    ```git clone https://github.com/xzaviourr/DiscreteEventSimulator.git```

- Install linux dependencies

    ```sudo apt install graphviz```

- Create virtual environment

    ```python3 -m venv venv```

- Install python dependencies

    ```pip install -r requirements.txt```

- Run the simulator 

    To run simulator in normal mode:
    ```python3 main.py <num_nodes> <slow_nodes> <low_hash> <inter-arrival_time_txn> <inter-arrival_time_block> <simulation_time> <max_block_length>```
    To run simulator in attack mode:
    ```python3 main.py <num_nodes> <slow_nodes> <low_hash> <inter-arrival_time_txn> <inter-arrival_time_block> <simulation_time> <max_block_length> <attack_type> <adv_hash> <adv_connected>```
    attack_type: 1 for Selfish Mining attack, 2 for Stubborn attack.

# **Results**
Results can be found in the results directory after the simulation has completed. 
- **Operational logs** : logs generated are stored in the logs folder, which contains event wise information of the simulation.

- **Peer network** : Network of peers used for the simulation can be seen in the file peer_network.png. Peers are represented with blue and green color specifying low hashing power miner and high hashing power miner respectively. Connections between the peers are represented with red and grey colors specifying fast and slow connections respectively.  

- **Blockchains** : Resultant blockchain present in every peer node can be found in nodes folder, which contains a txt file for each node containing detailed report of the blockchain, and a pdf file containing visual representation of the same. 