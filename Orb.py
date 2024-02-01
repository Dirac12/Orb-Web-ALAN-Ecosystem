import mesa
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import Slider
from random import Random


class Spider(Agent):
   def __init__(self, unique_id, model, age, fecundity, growth, width, height):
       super().__init__(unique_id, model)
       self.age = age
       self.satiation = 0
       self.fecundity = fecundity
       self.grid = mesa.space.MultiGrid(width, height, True)
       self.growth_rate = growth

   def move(self):
     print("Spider moving")
     if self.pos is not None:  # Add this check to ensure the position is not None
         possible_steps = self.grid.get_neighborhood(
             self.pos, moore=True, include_center=False
         )
         new_position = self.random.choice(possible_steps)

         self.satiation -= 1

         if self.grid.is_cell_empty(new_position):
             self.grid.move_agent(self, new_position)
         else:
             cellmates = self.grid.get_cell_list_contents([new_position])
             for mate in cellmates:
                 if isinstance(mate, Prey):
                     self.satiation += 10
                     self.grid.remove_agent(mate)
                 else:
                     pass

         if self.satiation <= 0:
             self.grid.remove_agent(self)


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
         possible_moves = self.grid.get_neighborhood(
             self.pos, moore=True, include_center=False
         )
         if len(possible_moves) > 0:
             empty_neighbors = [cell for cell in possible_moves if self.grid.is_cell_empty(cell)]
             if empty_neighbors:
                 new_position = self.random.choice(empty_neighbors)
                 new_spider = Spider(self.model.next_id(), self.model, age=0, fecundity=self.fecundity, growth=self.growth_rate)
                 self.grid.place_agent(new_spider, new_position)
                 self.model.schedule.add(new_spider)



   def light_interaction(self, lights_in_cells):
     if self.pos is not None:  # Add this check to ensure the position is not None
         for light in lights_in_cells:
             if isinstance(light, Lights):
                 self.satiation += 10
                 if light.diameter > 0:
                     neighbors = self.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=light.diameter)
                     for neighbor in neighbors:
                         if isinstance(neighbor, Spider) and neighbor.pos is not None:  
                             neighbor.growth_rate *= 2  # Double the growth rate for spider neighbors


class Prey(Agent):
   def __init__(self, unique_id, model, age, survival, width, height):
       super().__init__(unique_id, model)
       self.age = age
       self.grid = mesa.space.MultiGrid(width, height, True)
       self.survival = survival


   def move(self):
     print("Prey Moving")
     possible_steps = self.grid.get_neighborhood(
       self.pos, moore=True, include_center=False
      )
     new_position = self.random.choice(possible_steps)
     self.grid.move_agent(self, new_position)
     self.schedule.add(self)


class Lights(Agent):
   def __init__(self, unique_id, model, diameter):
       super().__init__(unique_id, model)
       self.diameter = diameter

class Environment(MultiGrid):
  def out_of_bounds(self, pos):
    if pos is not None:  # Add a check to ensure pos is not None
      x, y = pos  # Unpack the coordinates
      return x < 0 or x >= self.width or y < 0 or y >= self.height
    else:
      return True  # Return True if pos is None

class EcosystemModel(Model):
  def __init__(self, num_spiders, num_prey, num_lights, spider_fecundity, spider_growth, prey_survival, lights_luminosity, width, height):
    super().__init__()
    self.schedule = RandomActivation(self)
    self.grid = Environment(width, height, True)
    self.num_spiders = num_spiders
    self.num_prey = num_prey
    self.num_lights = num_lights
    self.spider_fecundity = spider_fecundity
    self.spider_growth = spider_growth
    self.prey_survival = prey_survival
    self.lights_luminosity = lights_luminosity
    self.datacollector = DataCollector(agent_reporters={"Spiders": lambda m: sum(1 for agent in m.schedule.agents if isinstance(agent, Spider))})

    for _i in range(self.num_spiders):
      x = self.random.randrange(self.grid.width)
      y = self.random.randrange(self.grid.height)
      spider = Spider(self.next_id(), self, age=0, fecundity=self.spider_fecundity, growth=self.spider_growth, width=width, height=height)
      self.grid.place_agent(spider, (x, y))
      self.schedule.add(spider)

    for _i in range(self.num_prey):
      x = self.random.randrange(self.grid.width)
      y = self.random.randrange(self.grid.height)
      prey = Prey(self.next_id(), self, age=0, survival=self.prey_survival, width=width, height=height)
      self.grid.place_agent(prey, (x, y))
      self.schedule.add(prey)


  def step(self):
    print("Step called")
    self.schedule.step()
    for agent in self.schedule.agents:
      if isinstance(agent, Spider):
        agent.move()
        agent.grow()
        agent.reproduce()
        lights_in_cells = self.grid.get_cell_list_contents([agent.pos])
        agent.light_interaction(lights_in_cells)
      elif isinstance(agent, Prey):
        agent.move()
    self.datacollector.collect(self)


params = {
   "num_prey": Slider('Number of Prey', 100, 10, 300),
   "num_spiders": Slider('Number of Spiders', 100, 10, 300),
   "num_lights": Slider('Number of Lights', 100, 10, 300),
   "spider_fecundity": Slider('Spider Fecundity', 0.5, 0, 1, step=0.01),
   "spider_growth": Slider('Spider Growth Rate', 1, 0, 5, step=0.01),
   "prey_survival": Slider('Prey Survival', 0.5, 0, 1, step=0.01),
   "lights_luminosity": Slider('Lights Luminosity', 1, 0, 5, step=0.01),
   "width": 50,
   "height": 40
}


def agent_portrayal(agent):
  portrayal = {"Shape": "circle",
               "Filled": "true",
               "Layer": 0,
               "r": 0.75,
               "x": agent.pos[0],  # Include the x-coordinate of the agent's position
               "y": agent.pos[1]}  # Include the y-coordinate of the agent's position

  if isinstance(agent, Spider):
      portrayal["Color"] = "green"
      if agent.age >= 12:
          portrayal["Color"] = "LimeGreen"  # Reproductive success
      if agent.age >= 24:
          portrayal["Color"] = "Red"  # Spider is dying
      return portrayal
  elif isinstance(agent, Prey):
      portrayal["Color"] = "blue"
      return portrayal
  elif isinstance(agent, Lights):
      portrayal["Color"] = "yellow"
      return portrayal



chart = ChartModule([{"Label": "Spiders", "Color": "green"}], data_collector_name="datacollector")

grid = CanvasGrid(agent_portrayal, params["width"], params["height"], 500, 400)

server = ModularServer(EcosystemModel,
   [grid, chart],
   "Ecosystem Model",
   model_params=params)
server.launch()
