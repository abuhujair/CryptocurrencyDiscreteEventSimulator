from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=10,
        slow_nodes=0.5,
        low_hash=0.3,
        inter_arrival_time = 1.0,
        inter_arrival_time_block = 10.0,
        simulation_time = 200.0,
        MAX_BLOCK_LENGTH=100
    )