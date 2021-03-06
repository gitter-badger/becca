"""
A multi-step variation on the one-dimensional grid task.

This is intended to be as similar as possible to the 
one-dimensional grid task, but requires multi-step planning 
or time-delayed reward assignment for optimal behavior.
"""
import numpy as np
from .base_world import World as BaseWorld

class World(BaseWorld):
    """
    One-dimensional grid world, multi-step variation

    In this world, the agent steps forward and backward along a line. 
    The fourth position is rewarded and the ninth position is punished. 
    Optimal performance is a reward of about 85 per time step.
    
    Attributes
    ----------
    action : array of floats
        The most recent set of action commands received. 
    brain_visualize_period : int
        The number of time steps between creating a full visualization of
        the ``brain``.
    energy_cost : float
        The punishment per position step taken.
    jump_fraction : float
        The fraction of time steps on which the agent jumps to 
        a random position.
    name : str
        A name associated with this world.
    name_long : str
        A longer name associated with this world.
    num_actions : int
        The number of action commands this world expects. This should be 
        the length of the action array received at each time step.
    num_sensors : int
        The number of sensor values the world returns to the brain 
        at each time step.
    reward_magnitude : float
        The magnitude of the reward and punishment given at 
        rewarded or punished positions.
    simple_state : int
        The nearest integer position of the agent in the world.
    world_state : float
        The actual position of the agent in the world. This can be fractional.
    world_visualize_period : int
        The number of time steps between creating visualizations of 
        the world.
    """
    def __init__(self, lifespan=None):
        """
        Initialize the world.

        Parameters
        ----------
        lifespan : int 
            The number of time steps to continue the world.
        """
        BaseWorld.__init__(self, lifespan)
        self.energy_cost = 0.01
        self.jump_fraction = 0.1
        self.display_state = False
        self.name = 'grid_1D_ms'
        self.name_long = 'multi-step one dimensional grid world'
        print "Entering", self.name_long
        self.num_sensors = 9
        self.num_actions = 2
        self.action = np.zeros((self.num_actions,1))
        self.world_state = 0            
        self.simple_state = 0
        self.world_visualize_period = 1e6
        self.brain_visualize_period = 1e3
            
    def step(self, action): 
        """
        Advance the world by one time step

        Parameters
        ----------
        action : array of floats
            The set of action commands to execute.

        Returns
        -------
        reward : float
            The amount of reward or punishment given by the world.
        sensors : array of floats
            The values of each of the sensors.
        """
        self.action = action.ravel()
        self.action[np.nonzero(self.action)] = 1.
        self.timestep += 1 
        energy = self.action[0] + self.action[1]
        self.world_state += self.action[0] - self.action[1]
        # Occasionally add a perturbation to the action to knock it 
        # into a different state 
        if np.random.random_sample() < self.jump_fraction:
            self.world_state = self.num_sensors * np.random.random_sample()
        # Ensure that the world state falls between 0 and 9
        self.world_state -= self.num_sensors * np.floor_divide(
                self.world_state, self.num_sensors)
        self.simple_state = int(np.floor(self.world_state))
        # TODO do this more elegantly
        if self.simple_state == 9:
            self.simple_state = 0
        # Assign sensors as zeros or ones. 
        # Represent the presence or absence of the current position in the bin.
        sensors = np.zeros(self.num_sensors)
        sensors[self.simple_state] = 1
        # Assign reward based on the current state 
        reward = sensors[8] * -1.
        reward += sensors[3] 
        # Punish actions just a little 
        reward -= energy * self.energy_cost
        reward = np.max(reward, -1)
        return sensors, reward

    def visualize_world(self, brain):
        """ 
        Show what's going on in the world.
        """
        state_image = ['.'] * self.num_sensors
        state_image[self.simple_state] = 'O'
        print(''.join(state_image))
