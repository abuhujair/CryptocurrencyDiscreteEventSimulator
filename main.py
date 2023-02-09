from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=50,
        slow_nodes=0.5,
        inter_arrival_time = 1.0,
        inter_arrival_time_block = 5.0,
        simulation_time = 100,
        MAX_BLOCK_LENGTH=250
    )