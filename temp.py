import networkx as nx
import matplotlib.pyplot as plt

# Create a new directed graph
G = nx.DiGraph()

# Add nodes to the graph
G.add_node("Genesis Block")
G.add_node("Block 1")
G.add_node("Block 2")
G.add_node("Block 3")

# Add edges to the graph to show the relationship between the blocks
G.add_edge("Genesis Block", "Block 1")
G.add_edge("Block 1", "Block 2")
G.add_edge("Block 2", "Block 3")

# Draw the graph using a spring layout
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True)

# Display the graph
plt.show()