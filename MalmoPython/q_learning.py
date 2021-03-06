from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import range
from builtins import object
try:
    from malmo import MalmoPython
except:
    import MalmoPython
import json
import logging
import math
import os
import random
import sys
import time
import malmoutils
import matplotlib 
import matplotlib.pyplot as plt

matplotlib.use('TKAgg')

if sys.version_info[0] == 2:
    # Workaround for https://github.com/PythonCharmers/python-future/issues/262
    import Tkinter as tk
else:
    import tkinter as tk

save_images = False
if save_images:        
    from PIL import Image
    
malmoutils.fix_print()

class TabQAgent(object):
    """Tabular Q-learning agent for discrete state/action spaces."""

    def __init__(self, actions=[], epsilon=0.05, alpha=0.4, gamma=.6, debug=False, canvas=None, root=None):
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.training = True

        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.actions = actions
        self.q_table = {}
        self.canvas = canvas
        self.root = root
        
        self.rep = 0

    def loadModel(self, model_file):
        """load q table from model_file"""
        with open(model_file) as f:
            self.q_table = json.load(f)

    def training(self):
        """switch to training mode"""
        self.training = True


    def evaluate(self):
        """switch to evaluation mode (no training)"""
        self.training = False

    def act(self, world_state, agent_host, current_r ):
        """take 1 action in response to the current world state"""
        
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text) # most recent observation

        if obs['LineOfSight']['type'] == 'diamond_ore' or obs['LineOfSight']['type'] == 'coal_ore' or obs['LineOfSight']['type'] == 'gold_ore' or obs['LineOfSight']['type'] == 'iron_ore' :
            time.sleep(.175)
            agent_host.sendCommand('attack 0')
            time.sleep(.175)
            return current_r
        
        self.logger.debug(obs)
        if not u'XPos' in obs or not u'ZPos' in obs:
            self.logger.error("Incomplete observation received: %s" % obs_text)
            return 0
        current_s = "%d:%d" % (int(obs[u'XPos']), int(obs[u'ZPos']))
        self.logger.debug("State: %s (x = %.2f, z = %.2f)" % (current_s, float(obs[u'XPos']), float(obs[u'ZPos'])))
        if current_s not in self.q_table:
            self.q_table[current_s] = ([0] * len(self.actions))

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q_table[self.prev_s][self.prev_a]
            self.q_table[self.prev_s][self.prev_a] = old_q + self.alpha * (current_r
                + self.gamma * max(self.q_table[current_s]) - old_q)

        self.drawQ( curr_x = int(obs[u'XPos']), curr_y = int(obs[u'ZPos']) )

        # select the next action
        rnd = random.random()
        if rnd < self.epsilon:
            a = random.randint(0, len(self.actions) - 1)
            self.logger.info("Random action: %s" % self.actions[a])
        else:
            m = max(self.q_table[current_s])
            self.logger.debug("Current values: %s" % ",".join(str(x) for x in self.q_table[current_s]))
            l = list()
            for x in range(0, len(self.actions)):
                if self.q_table[current_s][x] == m:
                    l.append(x)
            y = random.randint(0, len(l)-1)
            a = l[y]
            self.logger.info("Taking q action: %s" % self.actions[a])

        agent_host.sendCommand(self.actions[a])
        self.prev_s = current_s
        self.prev_a = a

        return current_r

    def run(self, agent_host):
        """run the agent on the world"""

        total_reward = 0
        current_r = 0
        tol = 0.01
        
        self.prev_s = None
        self.prev_a = None
        
        # wait for a valid observation
        world_state = agent_host.peekWorldState()
        while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
            world_state = agent_host.peekWorldState()
        # wait for a frame to arrive after that
        num_frames_seen = world_state.number_of_video_frames_since_last_state
        while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
            world_state = agent_host.peekWorldState()
        world_state = agent_host.getWorldState()
        for err in world_state.errors:
            print(err)

        if not world_state.is_mission_running:
            return 0, 0 # mission already ended
            
        assert len(world_state.video_frames) > 0, 'No video frames!?'
        
        obs = json.loads( world_state.observations[-1].text )
        
        if save_images:
            # save the frame, for debugging
            frame = world_state.video_frames[-1]
            image = Image.frombytes('RGB', (frame.width, frame.height), bytes(frame.pixels) )
            iFrame = 0
            self.rep = self.rep + 1
            image.save( 'rep_' + str(self.rep).zfill(3) + '_saved_frame_' + str(iFrame).zfill(4) + '.png' )
            
        # take first action
        total_reward += self.act(world_state,agent_host,current_r)
        
        require_move = True
        check_expected_position = True
        
        # main loop:
        while world_state.is_mission_running:
        
            # wait for the position to have changed and a reward received
            print('Waiting for data...', end=' ')
            while True:
                world_state = agent_host.peekWorldState()
                if not world_state.is_mission_running:
                    print('mission ended.')
                    break
                if len(world_state.rewards) > 0 and not all(e.text=='{}' for e in world_state.observations):
                    obs = json.loads( world_state.observations[-1].text )
                    curr_x = obs[u'XPos']
                    curr_z = obs[u'ZPos']
                    if require_move:
                        break
                    else:
                        print('received.')
                        break
            # wait for a frame to arrive after that
            num_frames_seen = world_state.number_of_video_frames_since_last_state
            while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
                world_state = agent_host.peekWorldState()
                
            num_frames_before_get = len(world_state.video_frames)
            
            world_state = agent_host.getWorldState()
            for err in world_state.errors:
                print(err)
            current_r = sum(r.getValue() for r in world_state.rewards)

            if save_images:
                # save the frame, for debugging
                if world_state.is_mission_running:
                    assert len(world_state.video_frames) > 0, 'No video frames!?'
                    frame = world_state.video_frames[-1]
                    image = Image.frombytes('RGB', (frame.width, frame.height), bytes(frame.pixels) )
                    iFrame = iFrame + 1
                    image.save( 'rep_' + str(self.rep).zfill(3) + '_saved_frame_' + str(iFrame).zfill(4) + '_after_' + self.actions[self.prev_a] + '.png' )
                
            if world_state.is_mission_running:
                assert len(world_state.video_frames) > 0, 'No video frames!?'
                num_frames_after_get = len(world_state.video_frames)
                assert num_frames_after_get >= num_frames_before_get, 'Fewer frames after getWorldState!?'
                frame = world_state.video_frames[-1]
                obs = json.loads( world_state.observations[-1].text )
                curr_x = obs[u'XPos']
                curr_z = obs[u'ZPos']
                print('New position from observation:',curr_x,',',curr_z,'after action:',self.actions[self.prev_a], end=' ') #NSWE
                if check_expected_position:
                    curr_x_from_render = frame.xPos
                    curr_z_from_render = frame.zPos
                else:
                    print()
                prev_x = curr_x
                prev_z = curr_z
                # act
                total_reward += self.act(world_state, agent_host, current_r)
                
        # process final reward
        self.logger.debug("Final reward: %d" % current_r)
        total_reward += current_r

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q_table[self.prev_s][self.prev_a]
            self.q_table[self.prev_s][self.prev_a] = old_q + self.alpha * ( current_r - old_q )
            
        self.drawQ()
        data = dict()
        if 'inventory' in obs:
            if len(obs['inventory']) > 1:
                data[obs['inventory'][1]['type']] = obs['inventory'][1]['quantity']
            if len(obs['inventory']) > 2:
                data[obs['inventory'][2]['type']] = obs['inventory'][2]['quantity']
            if len(obs['inventory']) > 3:
                data[obs['inventory'][3]['type']] = obs['inventory'][3]['quantity']
            if len(obs['inventory']) > 4:
                data[obs['inventory'][4]['type']] = obs['inventory'][4]['quantity']
        return (total_reward, data)
        
    def drawQ( self, curr_x=None, curr_y=None ):
        if self.canvas is None or self.root is None:
            return
        self.canvas.delete("all")
        action_inset = 0.1
        action_radius = 0.1
        curr_radius = 0.2
        action_positions = [ ( 0.5, 1-action_inset ), ( 0.5, action_inset ), ( 1-action_inset, 0.5 ), ( action_inset, 0.5 ) ]
        min_value = -20
        max_value = 20
        for x in range(world_x):
            for y in range(world_y):
                s = "%d:%d" % (x,y)
                self.canvas.create_rectangle( (world_x-1-x)*scale, (world_y-1-y)*scale, (world_x-1-x+1)*scale, (world_y-1-y+1)*scale, outline="#fff", fill="#000")
                for action in range(4):
                    if not s in self.q_table:
                        continue
                    value = self.q_table[s][action]
                    color = int( 255 * ( value - min_value ) / ( max_value - min_value )) # map value to 0-255
                    color = max( min( color, 255 ), 0 ) # ensure within [0,255]
                    color_string = '#%02x%02x%02x' % (255-color, color, 0)
                    self.canvas.create_oval( (world_x - 1 - x + action_positions[action][0] - action_radius ) *scale,
                                             (world_y - 1 - y + action_positions[action][1] - action_radius ) *scale,
                                             (world_x - 1 - x + action_positions[action][0] + action_radius ) *scale,
                                             (world_y - 1 - y + action_positions[action][1] + action_radius ) *scale, 
                                             outline=color_string, fill=color_string )
        if curr_x is not None and curr_y is not None:
            print("first move", curr_x, curr_y)
            self.canvas.create_oval( (world_x - 1 - curr_x + 0.5 - curr_radius ) * scale, 
                                     (world_y - 1 - curr_y + 0.5 - curr_radius ) * scale, 
                                     (world_x - 1 - curr_x + 0.5 + curr_radius ) * scale, 
                                     (world_y - 1 - curr_y + 0.5 + curr_radius ) * scale, 
                                     outline="#fff", fill="#fff" )
        self.root.update()


def get_mission_xml(negative_reward):

    # World A
    diamond_positions = [[4,11], [14,11], [12,9], [9,11]]
    coal_positions = [[5,4],[4,7],[8,6],[6,4],[7,5],[8,8],[5,5], [7,6], [5,7], [5,8], [6,11]]
    gold_positions= [[12,6], [13,4], [14,3], [13,8], [10,7]]
    iron_positions = [[6,7], [8,10], [10,5], [14,5]]

    # World B
    # diamond_positions = [[5,5],[5,7],[4,11],[6,11]]
    # coal_positions = [[5,4],[4,7],[8,6],[6,4],[7,5],[8,8],[14,11],[12,9],[13,8],[10,7],[9,11]]
    # gold_positions= [[5, 8], [7,6], [12,6], [13,4], [14,3]]
    # iron_positions = [[6,7], [8,10], [10,5], [14,5], [14,1]]

    ores = ""

    for x,y in diamond_positions:
        ores += "<DrawBlock x='"+ str(x) + "'  y='46' z='" + str(y) + "' type='diamond_ore' />"
    for x,y in coal_positions:
        ores += "<DrawBlock x='"+ str(x) + "'  y='46' z='" + str(y) + "' type='coal_ore' />"
    for x,y in iron_positions:
        ores += "<DrawBlock x='"+ str(x) + "'  y='46' z='" + str(y) + "' type='iron_ore' />"
    for x,y in gold_positions:
        ores += "<DrawBlock x='"+ str(x) + "'  y='46' z='" + str(y) + "' type='gold_ore' />"


    #change ServerQuitFromTimeUp in order to change total world time

    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <About>
        <Summary>Ore Breaking Mission (Tabular Q)</Summary>
    </About>
    
    <ModSettings>
        <MsPerTick>10</MsPerTick>
    </ModSettings>
    <ServerSection>
        <ServerInitialConditions>
                <Time>
                    <StartTime>12000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
                <AllowSpawning>false</AllowSpawning>
        </ServerInitialConditions>
        <ServerHandlers>
        <FlatWorldGenerator generatorString="3;7,2;1;"/>
        <DrawingDecorator>
            <!-- coordinates for cuboid are inclusive -->
            <DrawCuboid x1="-2" y1="46" z1="-10" x2="17" y2="50" z2="30" type="air" />            <!-- limits of our arena -->
            <DrawCuboid x1="-2" y1="45" z1="-10" x2="17" y2="45" z2="30" type="grass" /> 
            <DrawCuboid x1="3" y1="45" z1="0" x2="15" y2="45" z2="12" type="lava" />           <!-- lava floor -->
            <DrawCuboid x1="4"  y1="45" z1="1"  x2="14" y2="45" z2="11" type="bedrock" />      <!-- floor of the arena -->
            <!-- the starting marker --> 
            ''' + ores +  '''                           
        </DrawingDecorator>
        <ServerQuitFromTimeUp timeLimitMs="50000"/>
        <ServerQuitWhenAnyAgentFinishes/>
        </ServerHandlers>
    </ServerSection>
    <AgentSection mode="Survival">
        <Name>Roomba</Name>
        <AgentStart>
        <Placement x="4.5" y="46.0" z="1.5" pitch="70" yaw="0"/>
        <Inventory>
            <InventoryItem slot="0" type="iron_pickaxe"/>
        </Inventory>
        </AgentStart>
        <AgentHandlers>
        <ObservationFromFullInventory flat="false"/>
        <ObservationFromFullStats/>
        <InventoryCommands/>
        <VideoProducer want_depth="false">
            <Width>640</Width>
            <Height>480</Height>
        </VideoProducer>
        <ChatCommands/>
        <DiscreteMovementCommands/>
        <ObservationFromRay/>
        <RewardForTouchingBlockType>
            <Block reward=" ''' + str(negative_reward) +  '''" type="lava" behaviour="onceOnly"/>
            <Block reward="-1000.0" type="stone" behaviour="onceOnly"/>
        </RewardForTouchingBlockType>
        <RewardForCollectingItem>
            <Item reward="200.0" type="diamond"/>
            <Item reward="100.0" type="iron_ore"/>
            <Item reward="150.0" type="gold_ore"/>
            <Item reward="50.0" type="coal"/>
        </RewardForCollectingItem>
        <RewardForSendingCommand reward="-10"/>
        <AgentQuitFromTouchingBlockType>
            <Block type="lava" />
            <Block type="stone"/>
        </AgentQuitFromTouchingBlockType>
        </AgentHandlers>
    </AgentSection>
    </Mission>'''

agent_host = MalmoPython.AgentHost()

# Find the default mission file by looking next to the schemas folder:
schema_dir = None
try:
    schema_dir = os.environ['MALMO_XSD_PATH']
except KeyError:
    print("MALMO_XSD_PATH not set? Check environment.")
    exit(1)
mission_file = os.path.abspath(os.path.join(schema_dir, '..', 
    'sample_missions', 'cliff_walking_1.xml')) # Integration test path
if not os.path.exists(mission_file):
    mission_file = os.path.abspath(os.path.join(schema_dir, '..', 
        'Sample_missions', 'cliff_walking_1.xml')) # Install path
if not os.path.exists(mission_file):
    print("Could not find cliff_walking_1.xml under MALMO_XSD_PATH")
    exit(1)

# add some args
agent_host.addOptionalStringArgument('mission_file',
    'Path/to/file from which to load the mission.', mission_file)
agent_host.addOptionalFloatArgument('alpha',
    'Learning rate of the Q-learning agent.', 0.4)
agent_host.addOptionalFloatArgument('epsilon',
    'Exploration rate of the Q-learning agent.', 0.05)
agent_host.addOptionalFloatArgument('gamma', 'Discount factor.', .6)
agent_host.addOptionalFlag('load_model', 'Load initial model from model_file.')
agent_host.addOptionalStringArgument('model_file', 'Path to the initial model file', '')
agent_host.addOptionalFlag('debug', 'Turn on debugging.')

malmoutils.parse_command_line(agent_host)

# -- set up the python-side drawing -- #
scale = 40
world_x = 11
world_y = 11
root = tk.Tk()
root.wm_title("Q-table")
canvas = tk.Canvas(root, width=world_x*scale, height=world_y*scale, borderwidth=0, highlightthickness=0, bg="black")
canvas.grid()
root.update()

neg_reward = -9000

if agent_host.receivedArgument("test"):
    num_maps = 1
else:
    num_maps = 1

for imap in range(num_maps):

    # -- set up the agent -- #
    actionSet = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1", 'turn 1', 'turn -1']

    agent = TabQAgent(
        actions=actionSet,
        epsilon=agent_host.getFloatArgument('epsilon'),
        alpha=agent_host.getFloatArgument('alpha'),
        gamma=agent_host.getFloatArgument('gamma'),
        debug = agent_host.receivedArgument("debug"),
        canvas = canvas,
        root = root)

    # -- set up the mission -- #
    mission_file = agent_host.getStringArgument('mission_file')
    with open(mission_file, 'r') as f:
        print("Loading mission from %s" % mission_file)
        mission_xml = f.read()
    my_mission = MalmoPython.MissionSpec(get_mission_xml(-10000), True)
    my_mission.removeAllCommandHandlers()
    my_mission.allowAllDiscreteMovementCommands()
    my_mission.requestVideo( 800, 800 )
    my_mission.setViewpoint( 1 )

    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    max_retries = 3
    agentID = 0
    expID = 'tabular_q_learning'

    num_repeats = 1000
    cumulative_rewards = []
    all_data = []
    master = []
    f = open("data.txt", "w")
    lava = False
    for i in range(num_repeats):
        
        print("\nMap %d - Mission %d of %d:" % ( imap, i+1, num_repeats ))

        my_mission_record = malmoutils.get_default_recording_object(agent_host, "./save_%s-map%d-rep%d" % (expID, imap, i))

        for retry in range(max_retries):
            try:
                if lava:
                    if neg_reward >= -900000000000000000:
                        neg_reward = neg_reward * 10
                    my_mission = MalmoPython.MissionSpec(get_mission_xml(neg_reward), True)
                    my_mission.removeAllCommandHandlers()
                    my_mission.allowAllDiscreteMovementCommands()
                    my_mission.requestVideo( 800, 800 )
                    my_mission.setViewpoint( 1 )
                    lava = False

                agent_host.startMission( my_mission, my_clients, my_mission_record, agentID, "%s-%d" % (expID, i) )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:",e)
                    exit(1)
                else:
                    time.sleep(2.5)

        print("Waiting for the mission to start", end=' ')
        world_state = agent_host.getWorldState()
        while not world_state.has_mission_begun:
            print(".", end="")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            for error in world_state.errors:
                print("Error:",error.text)
        print()

        # -- run the agent in the world -- #
        cumulative_reward, end_data = agent.run(agent_host)
        print('Cumulative reward: %d' % cumulative_reward)
        print('Data: ',  end_data)
        cumulative_rewards += [ cumulative_reward ]
        
        # -- numbers for graph -- #
        score = 0
        if end_data: 
            if 'diamond' in end_data:
                score += end_data['diamond']*4
            if 'coal' in end_data:
                score += end_data['coal']
            if 'gold_ore' in end_data:
                score += end_data['gold_ore']*3
            if 'iron_ore' in end_data:
                score += end_data['iron_ore']*2
        
        if cumulative_reward != 0:
            all_data.append(score)
        
        if cumulative_reward < -8000:
            lava = True

        # -- clean up -- #
        time.sleep(0.5) # (let the Mod reset)
        if len(all_data) % 10 == 0:
            master.append(sum(all_data[-10:])/10.0)
            f.write(str(all_data))
            plt.plot(master)
            plt.plot([27 for i in range(len(master))])
            plt.plot([0.9591836734693877 for i in range(len(master))])
            plt.title('Diamond & Ore Optimal Path')
            plt.ylabel('Score')
            plt.xlabel('iteration')
            plt.savefig('returns.png')

    print("Done.")

    print("Cumulative rewards for all %d runs:" % num_repeats)
    print(cumulative_rewards)