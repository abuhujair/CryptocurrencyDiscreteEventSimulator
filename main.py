from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=10,
        slow_nodes=0.5,
        low_hash=0.2,
        inter_arrival_time = 1,
        inter_arrival_time_block = 10,
        simulation_time = 200,
        MAX_BLOCK_LENGTH=100
    )