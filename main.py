from modules.simulator import Simulator


if __name__ == '__main__':
    bc = Simulator(
        num_nodes=10,
        slow_nodes=0.5,
        inter_arrival_time = 10.0,
        simulation_time = 100
    )