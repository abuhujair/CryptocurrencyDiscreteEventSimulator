from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=100,
        slow_nodes=0.5,
        low_hash=0.3,
        inter_arrival_time = 10.0,
        inter_arrival_time_block = 40.0,
        simulation_time = 1000,
        MAX_BLOCK_LENGTH=400
    )