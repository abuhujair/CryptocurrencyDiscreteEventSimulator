from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=25,
        slow_nodes=0.5,
        low_hash=0.1,
        inter_arrival_time = 2.5,
        inter_arrival_time_block = 100.0,
        simulation_time = 2500.0,
        MAX_BLOCK_LENGTH=1000
    )