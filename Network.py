import networkx as nx
import time, enum, math
import numpy as np
import pandas as pd
import pylab as plt
import matplotlib.pyplot as plt
import networkx as nx
import panel as pn
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from panel import widgets as pnw
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid
from mesa.time import RandomActivation


class Spider(Agent):
    def __init__(self, unique_id, model, age, fecundity, growth, state):
        super().__init__(unique_id, model)
        self.age = age
        self.satiation = 0
        self.fecundity = fecundity
        self.growth_rate = growth
        self.state = state

    def move(self):
        print("Spider moving")
        if self.pos is not None:
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            new_position = self.random.choice(possible_steps)

            self.satiation -= 1

            if self.model.grid.is_cell_empty(new_position):
                self.model.grid.move_agent(self, new_position)
            else:
                cellmates = self.model.grid.get_cell_list_contents([new_position])
                for mate in cellmates:
                    if isinstance(mate, Prey):
                        self.satiation += 10
                        self.model.grid.remove_agent(mate)
                    else:
                        pass

            if self.satiation <= 0:
                self.model.grid.remove_agent(self)

    def grow(self):
        while 6 <= self.age <= 10:
            self.age += 2
            self.growth_rate += 1  # Increase growth rate when age is between 6 and 10
        else:
            self.age += 1
        if self.age >= 12 and self.random.random() < self.fecundity:
            self.reproduce()
        if self.age >= 24:
            self.model.grid.remove_agent(self)

    def reproduce(self):
        if self.growth_rate and self.age >= 12:
            possible_moves = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            if len(possible_moves) > 0:
                empty_neighbors = [
                    cell for cell in possible_moves if self.model.grid.is_cell_empty(cell)
                ]
                if empty_neighbors:
                    new_position = self.random.choice(empty_neighbors)
                    new_spider = Spider(
                        self.model.next_id(),
                        self.model,
                        age=0,
                        fecundity=self.fecundity,
                        growth=self.growth_rate,
                        state=self.state)
                    self.model.grid.place_agent(new_spider, new_position)
                    self.model.schedule.add(new_spider)

    def light_interaction(self, lights_in_cells):
        if self.pos is not None:
            for light in lights_in_cells:
                if isinstance(light, Lights):
                    self.satiation += 10
                    if light.diameter > 0:
                        neighbors = self.model.grid.get_neighbors(
                            self.pos,
                            moore=True,
                            include_center=False,
                            radius=light.diameter,
                        )
                        for neighbor in neighbors:
                            if isinstance(neighbor, Spider) and neighbor.pos is not None:
                                neighbor.growth_rate *= 2  # Double the growth rate for spider neighbors


class Prey(Agent):
    def __init__(self, unique_id, model, age, survival):
        super().__init__(unique_id, model)
        self.age = age
        self.survival = survival

    def move(self):
        print("Prey Moving")
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        self.model.schedule.add(agent_instance=self.datacollector)


class Lights(Agent):
    def __init__(self, unique_id, model, diameter):
        super().__init__(unique_id, model)
        self.diameter = diameter


class Environment(NetworkGrid):
    def out_of_bounds(self, pos):
        if pos is not None:
            x, y = pos  # Unpack the coordinates
            return x < 0 or x >= self.width or y < 0 or y >= self.height
        else:
            return True  # Return True if pos is None


class EcosystemModel(Model):
  grid = None
  def __init__(
        self,
        num_spiders,
        num_prey,
        num_lights,
        spider_fecundity,
        spider_growth,
        prey_survival,
        lights_luminosity,
        width,
        height,
        steps,
        delay,
        layout
    ):
        super().__init__()
        self.schedule = RandomActivation(self)

        self.num_spiders = num_spiders
        self.num_prey = num_prey
        self.num_lights = num_lights
        self.spider_fecundity = spider_fecundity
        self.spider_growth = spider_growth
        self.prey_survival = prey_survival
        self.lights_luminosity = lights_luminosity
        self.steps = steps
        self.delay = delay
        self.layout = layout

        self.G = nx.erdos_renyi_graph(n=self.num_spiders + self.num_prey + self.num_lights, p=0.2)
        self.grid = NetworkGrid(self.G)
        self.datacollector = DataCollector(model_reporters = {"Spiders": self.count_spiders, "Prey": self.count_prey, "Lights": self.count_lights})

        self.running = True

        self.spiders_count = 0
        # Create agents
        for i, node in enumerate(self.G.nodes()):
            if i < self.num_spiders:
                a = Spider(i + 1, self, age=0, fecundity=self.spider_fecundity, growth=1, state=None)
            elif i < self.num_spiders + self.num_prey:
                a = Prey(i + 1, self, age=0, survival=self.prey_survival)
            else:
                a = Lights(i + 1, self, diameter=5)
            self.schedule.add(a)
            # add agent
            self.grid.place_agent(a, node)
  def count_spiders(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, Spider))
  def count_prey(self):
    return sum(1 for agent in self.schedule.agents if isinstance(agent, Prey))
  def count_lights(self):
    return sum(1 for agent in self.schedule.agents if isinstance(agent, Lights))

  def step(self):
    self.schedule.step()
    self.datacollector.collect(self)

  def plot_network(self):
      graph = self.G
      pos = nx.spring_layout(graph, seed=42)

      plt.figure(figsize=(10, 8))

      self.datacollector = DataCollector(agent_reporters={"Spiders": self.count_spiders})
      self.schedule.add(self.datacollector)

      # Plotting lights
      lights = [agent for agent in self.schedule.agents if isinstance(agent, Lights)]
      nx.draw_networkx_nodes(graph, pos, nodelist=[agent.unique_id for agent in lights], node_size=100, node_color='yellow')

      # Plotting prey
      prey = [agent for agent in self.schedule.agents if isinstance(agent, Prey)]
      nx.draw_networkx_nodes(graph, pos, nodelist=[agent.unique_id for agent in prey], node_size=100, node_color='green')

      # Plotting spiders
      spiders = [agent for agent in self.schedule.agents if isinstance(agent, Spider)]
      nx.draw_networkx_nodes(graph, pos, nodelist=[agent.unique_id for agent in spiders], node_size=100, node_color='red')

      # Plotting edges
      edges = graph.edges()
      nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color='gray')

      plt.title("Ecosystem Network Visualization")
      plt.show()

def main():
  model = EcosystemModel(300, 100, 18, 0.2, 1, 0.1, 5, 10, 10, 20, 0.5, 2)
  for _i in range(50):
      model.step()


  def spider_sum(agent):
    sum = 0
    for a in agent.model.schedule.agents:
      if isinstance(a, Spider):
        sum += 1
    return sum
  def prey_sum(agent):
    sum = 0
    for a in agent.model.schedule.agents:
      if isinstance(a, Prey):
        sum += 1
    return sum
  # sum(1 for agent in model.schedule.agents if isinstance(agent, Spider))})
  if __name__ == '__main__':
    main()

cmap = ListedColormap(["pink", "black", "green",])

def plot_grid(model,fig,layout='spring',title='Ecosystem Network'):
    graph = model.G
    if layout == 'kamada-kawai':
        pos = nx.kamada_kawai_layout(graph)
    elif layout == 'circular':
        pos = nx.circular_layout(graph)
    else:
        pos = nx.spring_layout(graph, iterations=5, seed=8)
    ax=fig.add_subplot()
    states = [int(i.state) if hasattr(i,'state') and i.state is not None else 0 for i in model.grid.get_all_cell_contents()]
    colors = [cmap(i) for i in states]

    nx.draw(graph, pos, node_size=100, edge_color='green', node_color=colors, #with_labels=True,
            alpha=0.9,font_size=14)
    return

#example usage
fig,ax=plt.subplots(1,1,figsize=(16,10))
model = EcosystemModel(50, num_prey= 2 , num_lights= 2, spider_fecundity= 2, prey_survival= 2, lights_luminosity= 2 , width=10, height=10, spider_growth= 5, steps= 5, delay= 5, layout= 5)
model.step()
f=plot_grid(model,fig,layout='kamada-kawai')

def run_model(num_prey, num_lights, num_spiders, spider_fecundity, prey_survival, lights_luminosity, spider_growth, width, height, steps, delay, layout):
    model = EcosystemModel(num_lights=num_lights, num_prey=num_prey, num_spiders=num_spiders, prey_survival=prey_survival, lights_luminosity=lights_luminosity, spider_growth=spider_growth, spider_fecundity=spider_fecundity, width=width, height=height, steps=steps, delay=delay, layout=layout)

    fig1 = plt.Figure(figsize=(8,6))
    ax1 = fig1.add_subplot(1,1,1)
    grid_pane.object = ax1  # Assign the subplot to grid_pane.object
    fig2 = plt.Figure(figsize=(8,6))
    ax2 = fig2.add_subplot(1,1,1)
    states_pane.object = ax2

    # Draw initial grid plot
    plot_grid(model, grid_fig, layout=layout)

    # Draw initial states plot (if needed)
    # ...

    # Update the canvas
    grid_fig.canvas.draw()
    # states_fig.canvas.draw()  # Uncomment this line if you have a separate states plot

    # Step through the model and plot at each step

    #step through the model and plot at each step
    for i in range(steps):
        model.step()
        plot_grid(model, grid_fig, title='step=%s' %i, layout=layout)
        grid_fig.canvas.draw()
        time.sleep(delay)

grid_pane=pn.pane.Matplotlib(plt.Figure(),width=500,height=400)
states_pane = pn.pane.Matplotlib(plt.Figure(),width=400,height=300)
go_btn = pnw.Button(name='run',width=100,button_type='primary')
pop_input = pnw.IntSlider(name='population',value=100,start=10,end=1000,step=10,width=100)
num_prey_input = pnw.IntSlider(name='num_prey',value=100,start=10,end=200,width=100)
num_lights_input = pnw.IntSlider(name='num_lights',value=100,start=10,end=200,width=100)
num_spiders_input = pnw.IntSlider(name='num_spiders',value=100,start=10,end=200,width=100)
spider_fecundity_input = pnw.IntSlider(name ='spider_fecunidty', value=100, start=10, end=100,width=100)
lights_luminosity_input = pnw.IntSlider(name ='lights_luminosity', value=100, start=10, end=100, width=100)
prey_survival_input = pnw.IntSlider(name ='prey_survival', value=100, start=10, end=100, width=100)
spider_growth_input = pnw.IntSlider(name ='spider_growth', value=100, start=10, end=100, width=100)
steps_input = pnw.IntSlider(name='steps',value=20,start=5,end=100,width=100)
delay_input = pnw.FloatSlider(name='delay',value=.2,start=0,end=3,step=.2,width=100)
layout_input = pnw.Select(name='layout',options=['spring','circular','kamada-kawai'],width=100)
widgets = pn.WidgetBox(go_btn,pop_input,num_prey_input, num_lights_input,num_spiders_input, spider_fecundity_input, spider_growth_input, lights_luminosity_input, steps_input, delay_input, layout_input)

pn.extension()

grid_fig, grid_ax = plt.subplots(1, 1, figsize=(8, 6))
states_fig, states_ax = plt.subplots(1, 1, figsize=(8, 6))


def execute(event):
    # Clear previous plots
    grid_ax.clear()
    states_ax.clear()
    # Run the model
    run_model(num_prey_input.value, num_lights_input.value, num_spiders_input.value, spider_fecundity_input.value, prey_survival_input.value, lights_luminosity_input.value, spider_growth_input.value, steps_input.value, layout_input.value, delay_input.value)
    # Draw the updated plots
    grid_fig.canvas.draw()
    states_fig.canvas.draw()

# Watch the button click event
go_btn.param.watch(execute, 'clicks')


pn.Row(pn.Column(widgets),grid_pane,states_pane,sizing_mode='stretch_width')
