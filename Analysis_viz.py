import pandas as pd

lst = dict(nx.degree_centrality(model.G))
lst_2 = dict(nx.betweenness_centrality(model.G))
lst_3 = dict(nx.eigenvector_centrality(model.G))
lst_4 = dict(nx.closeness_centrality(model.G))

df_degree = pd.DataFrame(lst.items(), columns=['node', 'degree_centrality'])
ax1 = df_degree.plot.hexbin(x='node',
                      y='degree_centrality',
                            gridsize = 10,
                            cmap = 'viridis')
ax5 = df_degree.plot.scatter(x='node',
                      y='degree_centrality',
                             c = 'DarkBlue')

df_betweenness = pd.DataFrame(lst_2.items(), columns=['nodes', 'betweeness_centrality'])
ax2 = df_betweenness.plot.hexbin(x='nodes',
                      y='betweeness_centrality',
                            gridsize = 10,
                            cmap = 'viridis')
ax8 = df_betweenness.plot.scatter(x='nodes',
                      y='betweeness_centrality',
                            c = 'purple')

df_eig = pd.DataFrame(lst_3.items(), columns=['node', 'eigenvector_centrality'])
ax3 = df_eig.plot.hexbin(x='node',
                      y='eigenvector_centrality',
                            gridsize = 10,
                            cmap = 'viridis')

ax6 = df_eig.plot.scatter(x='node',
                      y='eigenvector_centrality',
                             c = 'Red')
df_close = pd.DataFrame(lst_4.items(), columns=['node', 'closeness_centrality'])
ax4 = df_close.plot.hexbin(x='node',
                      y='closeness_centrality',
                            gridsize = 10,
                            cmap = 'viridis')
ax7 = df_close.plot.scatter(x='node',
                      y='closeness_centrality',
                            c = 'green')
