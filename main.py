from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=10,
        slow_nodes=0.5,
        low_hash=0.65,
        inter_arrival_time = 10.0,
        inter_arrival_time_block = 100.0,
        simulation_time = 500,
        MAX_BLOCK_LENGTH=100
    )