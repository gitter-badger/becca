""" 
One-dimensional grid task.

This task tests an brain's ability to choose an appropriate action.
It is straightforward. Reward and punishment is clear and immediate.  
There is only one reward state and it can be reached in a single 
step.
"""
import numpy as np
from base_world import World as BaseWorld

class World(BaseWorld):
    """
    One-dimensional grid world.

    In this task, the brain steps forward and backward along 
    a nine-position line. The fourth position is rewarded and 
    the ninth position is punished. There is also a slight 
    punishment for effort expended in taking actions. 
    Occasionally the brain will get
    involuntarily bumped to a random position on the line.
    This is intended to be a simple-as-possible 
    task for troubleshooting BECCA. 
    Optimal performance is a reward of about 90 per time step.

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
        self.reward_magnitude = 1.
        self.energy_cost =  self.reward_magnitude / 100.
        self.jump_fraction = 0.1
        self.name = 'grid_1D'
        self.name_long = 'one dimensional grid world'
        print "Entering", self.name_long
        self.num_sensors = 9
        self.num_actions = 8
        self.action = np.zeros(self.num_actions)
        self.world_state = 0
        self.simple_state = 0
        self.world_visualize_period = 1e6
        self.brain_visualize_period = 1e3
    
    def step(self, action): 
        """
        Advance the world one time step.

        Parameters
        ----------
        action : array of floats
            The set of action commands to execute.

        Returns
        -------
        self.reward : float
            The amount of reward or punishment given by the world.
        self.sensors : array of floats
            The values of each of the sensors.
        """
        self.action = action
        self.action = np.round(self.action)
        self.timestep += 1 

        """
        Find the step size as combinations of the action commands
            action[i]     result
                   0      1 step to the right
                   1      2 steps to the right
                   2      3 steps to the right
                   3      4 steps to the right
                   4      1 step to the left
                   5      2 steps to the left
                   6      3 steps to the left
                   7      4 steps to the left
        """
        step_size = (self.action[0] + 
                 2 * self.action[1] + 
                 3 * self.action[2] + 
                 4 * self.action[3] - 
                     self.action[4] - 
                 2 * self.action[5] - 
                 3 * self.action[6] - 
                 4 * self.action[7])
        # Action cost is an approximation of metabolic energy.
        # Action cost is proportional to the number of steps taken.
        self.energy=(self.action[0] + 
                 2 * self.action[1] + 
                 3 * self.action[2] + 
                 4 * self.action[3] + 
                     self.action[4] + 
                 2 * self.action[5] + 
                 3 * self.action[6] + 
                 4 * self.action[7])

        self.world_state = self.world_state + step_size        

        # At random intervals, jump to a random position in the world.
        if np.random.random_sample() < self.jump_fraction:
	        self.world_state = self.num_sensors * np.random.random_sample()

        # Ensure that the world state falls between 0 and 9.
        self.world_state -= self.num_sensors * np.floor_divide(
                self.world_state, self.num_sensors)
        self.simple_state = int(np.floor(self.world_state))
        if self.simple_state == 9:
            self.simple_state = 0

        # Represent the presence or absence of the current position in the bin.
        sensors = np.zeros(self.num_sensors)
        sensors[self.simple_state] = 1
        reward = self.assign_reward(sensors)

        return sensors, reward

    def assign_reward(self, sensors):
        """
        Calculate the total reward corresponding to the current state

        Parameters
        ----------
        sensors : array of floats
            The current sensor values.

        Returns
        -------
        reward : float
            The reward associated the set of input sensors.
        """
        reward = 0.
        reward -= sensors[8] * self.reward_magnitude
        reward += sensors[3] * self.reward_magnitude
        # Punish actions just a little
        reward -= self.energy  * self.energy_cost
        reward = np.maximum(reward, -self.reward_magnitude)

        return reward
        
    def visualize_world(self, brain):
        """ 
        Show what's going on in the world.
        """
        state_image = ['.'] * (self.num_sensors + self.num_actions + 2)
        state_image[self.simple_state] = 'O'
        state_image[self.num_sensors:self.num_sensors + 2] = '||'
        action_index = np.where(self.action > 0.1)[0]
        if action_index.size > 0:
            for i in range(action_index.size):
                state_image[self.num_sensors + 2 + action_index[i]] = 'x'
        print(''.join(state_image))
           
