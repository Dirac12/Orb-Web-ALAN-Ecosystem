
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa_viz_tornado.UserParam import Slider
import random


class Spider(Agent):
   def __init__(self, unique_id, model, age, fecundity, growth):
       super().__init__(unique_id, model)
       self.age = age
       self.satiation = 0
       self.fecundity_rate = fecundity
       self.growth_rate = growth


   def move(self):
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
       if self.age >= 12 and self.model.random.random() < self.fecundity_rate:
           self.reproduce()
       if self.age >= 24:
           self.model.grid.remove_agent(self)


   def reproduce(self):
       if self.growth_rate and self.age >= 12:
           possible_moves = self.model.grid.get_neighborhood(
               self.pos, moore=True, include_center=False
           )
           if len(possible_moves) > 0:
               empty_neighbors = [cell for cell in possible_moves if self.model.grid.is_cell_empty(cell)]
               if empty_neighbors:
                   new_position = self.random.choice(empty_neighbors)
                   if new_position:
                       new_spider = Spider(self.model.next_id(), self.model, age=0, fecundity=self.fecundity_rate, growth=self.growth_rate)
                       self.model.grid.place_agent(new_spider, new_position)
                       self.model.schedule.add(new_spider)


   def light_interaction(self, lights_in_cells):
       if self.pos is not None:  # Add this check to ensure the position is not None
           for light in lights_in_cells:
               if isinstance(light, Lights):
                   self.satiation += 10
                   if light.diameter > 0:
                       neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=light.diameter)
                       for neighbor in neighbors:
                           if isinstance(neighbor, Spider) and neighbor.pos is not None:
                               neighbor.growth_rate *= 2  # Double the growth rate for spider neighbors


class Prey(Agent):
   def __init__(self, unique_id, model, age, survival):
       super().__init__(unique_id, model)
       self.age = age
       self.survival = survival


   def move(self):
       possible_steps = self.model.grid.get_neighborhood(
           self.pos, moore=True, include_center=False
       )
       new_position = self.random.choice(possible_steps)
       self.model.grid.move_agent(self, new_position)


class Lights(Agent):
   def __init__(self, unique_id, model, luminosity, diameter):
       super().__init__(unique_id, model)
       self.diameter = diameter


class Environment(MultiGrid):
   def out_of_bounds(self, pos):
       if pos is not None:  # Add a check to ensure pos is not None
           x, y = pos  # Unpack the coordinates
           return x < 0 or x >= self.width or y < 0 or y >= self.height
       else:
           return True  # Return True if pos is None


def initial_pos(model):
   x = 0
   y = model.random.randrange(model.grid.height)
   for i in range(36):
       new_light = Lights(model.next_id(), model, luminosity=1, diameter=2)  # Set a default diameter
       model.grid.place_agent(new_light, (x, y))
       model.schedule.add(new_light)


class EcosystemModel(Model):
   def __init__(self, width, height, num_spiders, num_prey, num_lights, spider_fecundity, spider_growth, prey_survival, lights_luminosity):
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


       for i in range(self.num_spiders):
           x = self.random.randrange(self.grid.width)
           y = self.random.randrange(self.grid.height)
           spider = Spider(self.next_id(), self, age=0, fecundity=self.spider_fecundity, growth=self.spider_growth)
           self.grid.place_agent(spider, (x, y))
           self.schedule.add(spider)


       for i in range(self.num_prey):
           x = self.random.randrange(self.grid.width)
           y = self.random.randrange(self.grid.height)
           prey = Prey(self.next_id(), self, age=0, survival=self.prey_survival)
           self.grid.place_agent(prey, (x, y))
           self.schedule.add(prey)


       initial_pos(self)


   def step(self):
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
           else:
               pass


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
                "r": 0.75}
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


grid = CanvasGrid(agent_portrayal, params["width"], params["height"], 500, 400)
server = ModularServer(EcosystemModel, [grid], "Ecosystem Model", params)
server.port = 8521
server.launch()
