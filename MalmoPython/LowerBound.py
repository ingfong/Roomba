# Rllib docs: https://docs.ray.io/en/latest/rllib.html
# Malmo XML docs: https://docs.ray.io/en/latest/rllib.html

try:
    from malmo import MalmoPython
except:
    import MalmoPython

import sys
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import randint

import gym, ray
from gym.spaces import Discrete, Box
from ray.rllib.agents import ppo


class DiamondCollector(gym.Env):

    def __init__(self, env_config):  
        # Static Parameters
        self.size = 5
        self.reward_density = .1
        self.penalty_density = .02
        self.obs_size = 5
        self.observation = None
        self.max_episode_steps = 100
        self.log_frequency = 10
        self.total_score = []
        self.action_dict = {
            0: 'move 1',  # Move one block forward
            1: 'turn 1',  # Turn 90 degrees to the right
            2: 'turn -1',  # Turn 90 degrees to the left
        }

        # Rllib Parameters
        self.action_space = Discrete(len(self.action_dict))
        self.observation_space = Box(0, 1, shape=(2 * self.obs_size * self.obs_size, ), dtype=np.float32)

        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)

        # DiamondCollector Parameters
        self.obs = None
        self.log_data = None
        self.allow_break_action = False
        self.episode_step = 0
        self.episode_return = 0
        self.returns = []
        self.steps = []

    def reset(self):
        """
        Resets the environment for the next episode.

        Returns
            observation: <np.array> flattened initial obseravtion
        """
        # Reset Malmo
        world_state = self.init_malmo()

        # Reset Variables
        self.returns.append(self.episode_return)
        current_step = self.steps[-1] if len(self.steps) > 0 else 0
        self.steps.append(current_step + self.episode_step)
        self.episode_return = 0
        self.episode_step = 0
        
        

        # Log
        if len(self.returns) > self.log_frequency + 1 and \
            len(self.returns) % self.log_frequency == 0:
                pass

        # Get Observation
        self.obs, self.allow_break_action = self.get_observation(world_state)

        return self.obs

    def step(self, action):
        """
        Take an action in the environment and return the results.

        Args
            action: <int> index of the action to take

        Returns
            observation: <np.array> flattened array of obseravtion
            reward: <int> reward from taking action
            done: <bool> indicates terminal state
            info: <dict> dictionary of extra information
        """

        #helper funciton actions
        # Get Action
        command = self.action_dict[action]
        if self.allow_break_action:
            time.sleep(.5)
            self.agent_host.sendCommand('attack 0')
            time.sleep(.5)
            self.episode_step += 1
        else:
            self.agent_host.sendCommand(command)
            time.sleep(.2)
            self.episode_step += 1

        # Get Observation
        world_state = self.agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
        self.obs, self.allow_break_action = self.get_observation(world_state) 

        # Get Done
        done = not world_state.is_mission_running 

        if done:
            print("done")
            print(self.log_data)
            if self.log_data:
                total = 0
                for i in self.log_data:
                    if i['type'] == 'coal':
                        total += i['quantity']
                    if i['type'] == 'diamond':
                        total += i['quantity'] * 2
                self.total_score.append(total)
                self.log_data = None
            else:
                self.total_score.append(0)
            print(self.total_score)
                
        else:
            if len(self.observation['inventory']) > 1:
                self.log_data = self.observation['inventory']
                print("YET HERE", self.log_data)
        

        # Get Reward
        reward = 0
        for r in world_state.rewards:
            reward += r.getValue()
        self.episode_return += reward

        return self.obs, reward, done, dict()

    def get_mission_xml(self):

        return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

            <About>
                <Summary>Ore Breaking Mission (Lower Bound: Random Movement)</Summary>
            </About>

            <ServerSection>
                <ServerInitialConditions>
                    <Time>
                        <StartTime>12000</StartTime>
                        <AllowPassageOfTime>false</AllowPassageOfTime>
                    </Time>
                    <Weather>clear</Weather>
                </ServerInitialConditions>
                <ServerHandlers>
                    <FlatWorldGenerator generatorString="3;7,2;1;"/>
                    <DrawingDecorator>
                        <DrawCuboid x1="-2" y1="46" z1="-10" x2="17" y2="50" z2="30" type="air" />
                        <DrawCuboid x1="-2" y1="45" z1="-10" x2="17" y2="45" z2="30" type="grass" /> 
                        <DrawCuboid x1="3" y1="45" z1="0" x2="15" y2="45" z2="12" type="lava" />
                        <DrawCuboid x1="4"  y1="45" z1="1"  x2="14" y2="45" z2="11" type="bedrock" /> 
                        <DrawBlock x='0'  y='2' z='0' type='air' />
                    </DrawingDecorator>
                    <ServerQuitFromTimeUp timeLimitMs="1000000"/>
                    <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
            </ServerSection>

            <AgentSection mode="Survival">
                <Name>Roomba</Name>
                <AgentStart>
                    <Placement x="4.5" y="46.0" z="1.5" pitch="70" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="diamond_pickaxe"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ObservationFromFullInventory flat="false"/>
                    <RewardForTouchingBlockType>
                            <Block type="lava" reward="-1" />
                    </RewardForTouchingBlockType>
                    <DiscreteMovementCommands/>
                    <ObservationFromFullStats/>
                    <InventoryCommands/>
                    <VideoProducer want_depth="false">
                        <Width>800</Width>
                        <Height>800</Height>
                    </VideoProducer>
                    <ObservationFromRay/>
                    <AgentQuitFromReachingCommandQuota total="'''+str(self.max_episode_steps)+'''" />
                </AgentHandlers>
            </AgentSection>
        </Mission>'''

    def init_malmo(self):
        """
        Initialize new malmo mission.
        """
        my_mission = MalmoPython.MissionSpec(self.get_mission_xml(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.requestVideo(800, 500)
        my_mission.setViewpoint(1)


        diamond_positions = [[5,5],[5,7],[4,11],[6,11]]
        coal_positions = [[5,4],[4,7],[4,7],[8,6],[6,4],[7,5],[8,8],[14,11],[12,9],[13,8],[10,7],[9,11]]

        for x,y in diamond_positions:
            my_mission.drawBlock(x,46,y, "diamond_ore")
        for x,y in coal_positions:
            my_mission.drawBlock(x,46,y,"coal_ore")

        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

        for retry in range(max_retries):
            try:
                self.agent_host.startMission( my_mission, my_clients, my_mission_record, 0, 'DiamondCollector' )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:", e)
                    exit(1)
                else:
                    time.sleep(2)

        world_state = self.agent_host.getWorldState()
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                print("\nError:", error.text)

        return world_state

    def get_observation(self, world_state):
        """
        Use the agent observation API to get a flattened 2 x 5 x 5 grid around the agent. 
        The agent is in the center square facing up.

        Args
            world_state: <object> current agent world state

        Returns
            observation: <np.array> the state observation
            allow_break_action: <bool> whether the agent is facing a diamond
        """
        obs = np.zeros((2 * self.obs_size * self.obs_size, ))
        allow_break_action = False

        while world_state.is_mission_running:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')

            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)

                # Get observation
                self.observation = observations
                # grid = observations['floorAll']
                # for i, x in enumerate(grid):
                #     obs[i] = x == 'diamond_ore' or x == 'lava'

                # Rotate observation with orientation of agent
                obs = obs.reshape((2, self.obs_size, self.obs_size))
                yaw = observations['Yaw']
                if yaw >= 225 and yaw < 315:
                    obs = np.rot90(obs, k=1, axes=(1, 2))
                elif yaw >= 315 or yaw < 45:
                    obs = np.rot90(obs, k=2, axes=(1, 2))
                elif yaw >= 45 and yaw < 135:
                    obs = np.rot90(obs, k=3, axes=(1, 2))
                obs = obs.flatten()

                allow_break_action = observations['LineOfSight']['type'] == 'diamond_ore' or observations['LineOfSight']['type'] == 'coal_ore'

                break

        return obs, allow_break_action

    def log_returns(self):
        """
        Log the current returns as a graph and text file

        Args:
            steps (list): list of global steps after each episode
            returns (list): list of total return of each episode
        """
        box = np.ones(self.log_frequency) / self.log_frequency
        returns_smooth = np.convolve(self.returns[1:], box, mode='same')
        plt.clf()
        plt.plot(self.steps[1:], returns_smooth)
        plt.title('Diamond Collector')
        plt.ylabel('Return')
        plt.xlabel('Steps')
        plt.savefig('returns.png')

        


if __name__ == '__main__':
    ray.init()
    trainer = ppo.PPOTrainer(env=DiamondCollector, config={
        'env_config': {},           # No environment parameters to configure
        'framework': 'torch',       # Use pyotrch instead of tensorflow
        'num_gpus': 0,              # We aren't using GPUs
        'num_workers': 0            # We aren't using parallelism
    })

    while True:
        print(trainer.train())

