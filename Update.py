import mesa
import random
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import Slider


n_ecosystem_starts = 0

class Spider(Agent):
    def __init__(self, unique_id, model, age, fecundity, growth):
        super().__init__(unique_id, model)
        self.age = age
        self.satiation = 100
        self.fecundity = fecundity
        # self.grid = mesa.space.MultiGrid(width, height, True)
        self.growth_rate = growth

    def step(self):
        print("Spider step (move, grow, reproduce, light_interaction)")
        self.move()
        print('between move and grow, pos:', self.pos)
        self.grow()
        print('ABOUT:self(spider).model.grid.get_cell_list_contents(',
              self.pos, ')')
        lights_in_cells = self.model.grid.get_cell_list_contents([self.pos])
        self.light_interaction(lights_in_cells)
        if self.satiation <= 0:
            print('STARVATION of agent', self, 'pos:', self.pos, 'satiation:', self.satiation)
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)

    def move(self):
        print("Spider moving, starting at", self.pos)
        if not self.pos:
            print("*warning* - spider agent had a None position")
            return
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)

        self.satiation -= 1

        if self.model.grid.is_cell_empty(new_position):
            # empty destination, just move there!
            print('SPIDER_MOVE: old', self.pos)
            print('SPIDER_MOVE: new', new_position)
            self.model.grid.move_agent(self, new_position)
        else:
            # if others are in this cell, and they are prey, start
            # eating
            cellmates = self.model.grid.get_cell_list_contents([new_position])
            for mate in cellmates:
                print(f'cellmate_ID_{mate.unique_id}:', mate)
                if isinstance(mate, Prey):
                    print(f'    it was PREY_{mate.unique_id}; eat it!')
                    self.satiation -= 10
                    # self.model.schedule.remove(mate)
                    mate.remove()
                    # self.model.schedule.remove(mate)
                    self.model.grid.remove_agent(mate)


    def grow(self):
        print('spider grow(), pos:', self.pos, 'age:', self.age)
        while 6 <= self.age <= 10:
            self.age += 2
            self.growth_rate += 1  # Increase growth rate when age is between 6 and 10
        else:
            self.age += 1
        if self.age >= 10 and self.random.random() < self.fecundity:
            self.reproduce()
        if self.age >= 20:      # die at age 24
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)

    def reproduce(self):
        if self.growth_rate and self.age >= 12:
            possible_moves = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            if len(possible_moves) > 0:
                empty_neighbors = [cell for cell in possible_moves
                                   if self.model.grid.is_cell_empty(cell)]
                if empty_neighbors:
                    new_position = self.random.choice(empty_neighbors)
                    new_spider = Spider(self.model.next_id(), self.model, age=0,
                                        fecundity=self.fecundity, growth=self.growth_rate)
                    self.model.grid.place_agent(new_spider, new_position)
                    self.model.schedule.add(new_spider)


    def light_interaction(self, lights_in_cells):
        if self.pos is not None:  # Add this check to ensure the position is not None
            for light in lights_in_cells:
                if isinstance(light, Lights):
                    self.satiation += 10
                    if light.diameter > 0:
                        neighbors = self.model.grid.get_neighbors(self.pos, moore=True,
                                                                  include_center=False,
                                                                  radius=light.diameter)
                        for neighbor in neighbors:
                            if isinstance(neighbor, Spider) and neighbor.pos is not None:  
                                neighbor.growth_rate *= 2  # Double the growth rate for spider neighbors


class Prey(Agent):
    def __init__(self, unique_id, model, age, survival):
        super().__init__(unique_id, model)
        self.age = age
        # self.grid = mesa.space.MultiGrid(width, height, True)
        self.survival = survival

    def step(self):
        print("Prey step")
        self.move()

    def move(self):
        print(f"PREY_{self.unique_id}_MOVE old:", self.pos)
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, 
          moore=True, 
          include_center=False
        )
        print('prey possible:', possible_steps)
        new_position = self.random.choice(possible_steps)
        print(f"PREY_{self.unique_id}_MOVE new:", new_position)
        self.model.grid.move_agent(self, new_position)
        print(f"PREY_{self.unique_id}_MOVE after:", self.pos)
    def reproduce(self):
      if self.age >= 2:
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)      
      if self.age >= 1:
          possible_moves = self.model.grid.get_neighborhood(
              self.pos, moore=True, include_center=False
          )
          if len(possible_moves) > 0:
              empty_neighbors = [cell for cell in possible_moves
                                 if self.model.grid.is_cell_empty(cell)]
              if empty_neighbors:
                  new_position = self.random.choice(empty_neighbors)
                  new_prey = Prey(self.model.next_id(), self.model, age=0, survival=self.survival)
                  self.model.grid.place_agent(new_prey, new_position)
                  self.model.schedule.add(new_prey)


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
    def __init__(self, num_spiders, num_prey, num_lights, spider_fecundity, spider_growth,
                 prey_survival, lights_luminosity, width, height):
        super().__init__()
        global n_ecosystem_starts
        print('before: n_ecosystem_starts:', n_ecosystem_starts)
        n_ecosystem_starts += 1
        self.schedule = RandomActivation(self)
        self.grid = Environment(width, height, True)
        self.num_spiders = num_spiders
        self.num_prey = num_prey
        self.num_lights = num_lights
        self.spider_fecundity = spider_fecundity
        self.spider_growth = spider_growth
        self.prey_survival = prey_survival
        self.lights_luminosity = lights_luminosity
        self.datacollector = DataCollector(
           {"Spiders": lambda m: len([agent for agent in m.schedule.agents if isinstance(agent, Spider)]),
            "Prey": lambda m: len([agent for agent in m.schedule.agents if isinstance(agent, Prey)]),
            "Lights": lambda m: len([agent for agent in m.schedule.agents if isinstance(agent, Lights)])
           }
       )
        for _i in range(self.num_spiders):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            spider = Spider(self.next_id(), self, age=0, fecundity=self.spider_fecundity,
                            growth=self.spider_growth)
            self.grid.place_agent(spider, (x, y))
            self.schedule.add(spider)

        for _i in range(self.num_prey):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            prey = Prey(self.next_id(), self, age=0, survival=self.prey_survival)
            self.grid.place_agent(prey, (x, y))
            self.schedule.add(prey)
            print('ADDED_PREY:', prey.unique_id)

        for _i in range(self.num_lights):
          x = self.random.randrange(self.grid.width)
          y = self.random.randrange(self.grid.height)
          lights = Lights(self.next_id(), self, diameter=self.lights_luminosity)
          self.grid.place_agent(lights, (x, y))
          self.schedule.add(lights)
          print('ADDED_Lights:', lights.unique_id)
          
        print('=====================================')


    def step(self):
        print("Ecosystem Step called")
        self.schedule.step()
        self.datacollector.collect(self)


params = {
    "num_prey": Slider('Number of Prey', 100, 10, 300),
    "num_spiders": Slider('Number of Spiders', 100, 10, 300),
    "num_lights": Slider('Number of Lights', 19, 10, 19),
    "spider_fecundity": Slider('Spider Fecundity', 0.5, 0, 1, step=int(0.01)),
    "spider_growth": Slider('Spider Growth Rate', 1, 0, 5, step=int(0.01)),
    "prey_survival": Slider('Prey Survival', 0.5, 0, 1, step=int(0.01)),
    "lights_luminosity": Slider('Lights Luminosity', 1, 0, 5, step=int(0.01)),
    "width": 50,
    "height": 40
}


def agent_portrayal(agent):
    portrayal = {
      "Shape": "circle",
      "Filled": "true",
      "Layer": 0,
      "r": 0.75,
      "x": agent.pos[0],  # Include the x-coordinate of the agent's position
      "y": agent.pos[1]
    }  # Include the y-coordinate of the agent's position

    if isinstance(agent, Spider):
        portrayal["Color"] = "green"
        if agent.age >= 10 and agent.age <=20:
            portrayal["Color"] = "LimeGreen"  # Reproductive success
        if agent.age >= 20 :
            portrayal["Color"] = "red"  # Spider is dying
        return portrayal
    elif isinstance(agent, Prey):
        portrayal["Color"] = "blue"
        return portrayal
    elif isinstance(agent, Lights):
        portrayal["Color"] = "yellow"
        return portrayal
    else:
        print('*warning* - agent was not Spider or Prey or Lights - weird')


def main():
    grid = CanvasGrid(agent_portrayal,
                      params["width"], params["height"],
                      20*params["width"], 20*params["height"])
    chart = ChartModule([{"Label": "Spiders",
       "Color": "green"}],
     data_collector_name='datacollector')
    chart_1 = ChartModule([{"Label": "Prey",
     "Color": "blue"}],
     data_collector_name='datacollector')
    chart_2 = ChartModule([{"Label": "Lights",
       "Color": "yellow"}],
     data_collector_name='datacollector')
    server = ModularServer(EcosystemModel,
                           [grid, chart, chart_1, chart_2],
                           "Ecosystem Model",
                           model_params=params)
    server.launch()


def spider_sum(agent):
    sum = 0
    for a in agent.model.schedule.agents:
        if isinstance(a, Spider):
           sum += 1
    return sum
    # sum(1 for agent in model.schedule.agents if isinstance(agent, Spider))})

def prey_sum(agent):
    sum = 0
    for a in agent.model.schedule.agents:
        if isinstance(a, Prey):
           sum += 1
    return sum
    # sum(1 for agent in model.schedule.agents if isinstance(agent, Spider))})


if __name__ == '__main__':
    main()
