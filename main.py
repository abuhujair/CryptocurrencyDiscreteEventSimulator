import sys
import settings # To initialize the code
from modules.simulator import Simulator


if __name__ == '__main__':
    # if len(sys.argv) == 8:
    #     obj = Simulator(
    #         num_nodes = int(sys.argv[1]),
    #         slow_nodes = float(sys.argv[2]),
    #         low_hash = float(sys.argv[3]),
    #         inter_arrival_time = float(sys.argv[4]),
    #         inter_arrival_time_block = float(sys.argv[5]),
    #         simulation_time = float(sys.argv[6]),
    #         MAX_BLOCK_LENGTH = float(sys.argv[7]),
    #     )
    # elif len(sys.argv) == 11:
    #     obj = Simulator(
    #         num_nodes = int(sys.argv[1]),
    #         slow_nodes = float(sys.argv[2]),
    #         low_hash = float(sys.argv[3]),
    #         inter_arrival_time = float(sys.argv[4]),
    #         inter_arrival_time_block = float(sys.argv[5]),
    #         simulation_time = float(sys.argv[6]),
    #         MAX_BLOCK_LENGTH = float(sys.argv[7]),
    #         attack_type = int(sys.argv[8]),
    #         adv_hash = float(sys.argv[9]),
    #         adv_connected = float(sys.argv[10])
    #     )

    # else:
    #     print("Invalid arguments.")
    #     print("Syntax for general mode : python3 main.py <num_nodes> <slow_nodes> <low_hash> <inter-arrival_time_txn> <inter-arrival_time_block> <simulation_time> <max_block_length>")
    #     print("Syntax for simulating attack: python3 main.py <num_nodes> <slow_nodes> <low_hash> <inter-arrival_time_txn> <inter-arrival_time_block> <simulation_time> <max_block_length> <attack_type> <adv_hash> <adv_connected>")
    #     print("To simulate Selfish Mining attack: attack_type = 1")
    #     print("To simulate Stubborn Mining attack: attack_type = 2")
    #     exit(1)
    
    obj = Simulator(
        num_nodes = 50,
        slow_nodes = 0.5,
        low_hash = 0.5,
        inter_arrival_time = 1,
        inter_arrival_time_block = 10,
        simulation_time = 100,
        MAX_BLOCK_LENGTH = 500,
        attack_type = 1,
        adv_hash = 0.25,
        adv_connected = 0.50
    )

    print("Simulation ended successfully.")
    exit(0)
