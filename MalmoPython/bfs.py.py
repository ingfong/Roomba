try:
    from malmo import MalmoPython
except:
    import MalmoPython

from re import X
from PIL.Image import MAX_IMAGE_PIXELS
from numpy.random import randint
import os
import sys
import time
import json
import queue
# from priority_dict import priorityDictionary as PQ

# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

def get_mission_xml():
    obs_size = 5


    max_episode_steps = 1000

    diamond_positions = [[5,5],[5,7],[4,11],[6,11]]
    coal_positions = [[5,4],[4,7],[4,7],[8,6],[6,4],[7,5],[8,8],[14,11],[12,9],[13,8],[10,7],[9,11]]

    blocks = ""

    for x,y in diamond_positions:

        # 6 - 11 - 1

        # 11 - 6 = 5

        # 6 + 5 - 1

        shift = (6 - y)*2

        blocks += "<DrawBlock  x='{}'  y='2' z='{}' type='diamond_ore'/>".format(x+8, y-10 + shift)

    for x,y in coal_positions:
        shift = (6 - y)*2
        shiftx = (6-x)*2
        blocks += "<DrawBlock  x='{}'  y='2' z='{}' type='coal_ore'/>".format(x+6+shiftx, y-10 + shift)

    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

        <About>
            <Summary>Ore Breaking Mission (Upper Bound: BFS)</Summary>
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
                    <DrawCuboid x1="-2" y1="2" z1="-10" x2="17" y2="2" z2="30" type="air" />
                    <DrawCuboid x1="-2" y1="1" z1="-10" x2="17" y2="1" z2="30" type="grass" /> 
                    <DrawCuboid x1="4"  y1="1" z1="-9"  x2="14" y2="1" z2="1" type="bedrock" />
                ''' + blocks + '''
                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="1000000"/>
                <ServerQuitWhenAnyAgentFinishes/>
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>Roomba</Name>
            <AgentStart>
                <Placement x="14.5" y="2" z="1.5" pitch="70" yaw="180"/>
                <Inventory>
                    <InventoryItem slot="0" type="diamond_pickaxe"/>
                </Inventory>
            </AgentStart>
            <AgentHandlers>
                <RewardForTouchingBlockType>
                        <Block type="lava" reward="-1" />
                </RewardForTouchingBlockType>
                <DiscreteMovementCommands/>
                <ObservationFromFullStats/>
                <ObservationFromRay/>
                <ObservationFromGrid>
                    <Grid name="floorAll">
                        <min x="-'''+str(int(10))+'''" y="0" z="-'''+str(int(10))+'''"/>
                        <max x="'''+str(int(0))+'''" y="0" z="'''+str(int(0))+'''"/>
                    </Grid>
                </ObservationFromGrid>
                <VideoProducer want_depth="false">
                    <Width>800</Width>
                    <Height>800</Height>
                </VideoProducer>
                <AgentQuitFromReachingCommandQuota total="'''+str(max_episode_steps)+'''" />
            </AgentHandlers>
        </AgentSection>
    </Mission>'''


def load_grid(world_state):
    """
    Used the agent observation API to get a 21 X 21 grid box around the agent (the agent is in the middle).

    Args
        world_state:    <object>    current agent world state

    Returns
        grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)
    """
    grid = None
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            msg = world_state.observations[-1].text
            observations = json.loads(msg)
            grid = observations.get(u'floorAll', 0)
            break
        
    return grid

def find_start(grid):
    """
    Finds the source and destination block indexes from the list.

    Args
        grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)

    Returns
        start: <int>   source block index in the list
        end:   <int>   destination block index in the list
    """

    # count = 0
    # start = 0
    # for blockType in grid:
    #     if blockType == "emerald_block":
    #         return count
    #     count += 1

    return len(grid) - 1

def extract_action_list_from_path(path_list):
    """
    Converts a block idx path to action list.

    Args
        path_list:  <list>  list of block idx from source block to dest block.

    Returns
        action_list: <list> list of string discrete action commands (e.g. ['movesouth 1', 'movewest 1', ...]
    """
    action_trans = {-11: 'movenorth 1', 11: 'movesouth 1', -1: 'movewest 1', 1: 'moveeast 1'}
    alist = []
    if path_list:
        previous = 0
        curr = 1
        while curr < len(path_list):

            if path_list[curr] == 'attack 0' or path_list[curr] == 'turn 1' or path_list[curr] == 'turn -1':
                alist.append(path_list[curr])
            else:
                alist.append(action_trans[path_list[curr] - path_list[previous]])
                previous = curr
            curr += 1

    return alist

def turn_steve(current, turned_orientation):

    if current == turned_orientation:
        return []

    if current == "north":
        if turned_orientation == "west":
            return ['turn -1']
        elif turned_orientation == 'east':
            return ['turn 1']
        elif turned_orientation == 'south':
            return ['turn 1'] * 2

    if current == "east":
        if turned_orientation == "west":
            return ['turn 1'] * 2
        elif turned_orientation == 'north':
            return ['turn -1']
        elif turned_orientation == 'south':
            return ['turn 1']

    if current == "west":
        if turned_orientation == "north":
            return ['turn 1']
        elif turned_orientation == 'east':
            return ['turn 1'] * 2
        elif turned_orientation == 'south':
            return ['turn -1']

    if current == "south":
        if turned_orientation == "west":
            return ['turn 1']
        elif turned_orientation == 'east':
            return ['turn -1']
        elif turned_orientation == 'north':
            return ['turn 1'] * 2

def ore_count(grid):

    count = 0

    for block in grid:
        if block == 'diamond_ore' or block == 'coal_ore':
            count += 1

    return count


def get_next_ore(last_orientation, grid, start):

    visited = set()

    q = queue.Queue()

    q.put(([],start))

    while not q.empty():

        path, index = q.get()


        if index not in visited and index >= 0 and index < len(grid):

            visited.add(index)

            if grid[index] == "diamond_ore" or grid[index] == "coal_ore":

                last_move = path[-1]
                new_orientation = ""

                #east
                if (last_move - index == -1):
                    path += turn_steve(last_orientation, "east")
                    new_orientation = "east"

                #west
                elif (last_move - index == 1):
                    path += turn_steve(last_orientation, "west")
                    new_orientation = "west"

                #north
                elif (last_move - index == 11):
                    path += turn_steve(last_orientation, "north")
                    new_orientation = "north"

                #south
                elif (last_move - index == -11):
                    path += turn_steve(last_orientation, "south")
                    new_orientation = "south"

                path.append('attack 0')


                grid[index] = "air"
                return (new_orientation, path,index)

            path.append(index)

            if index - 11 >= 0:
                q.put((path[:], index-11))
            if (index + 1)%11 != 0:
                q.put((path[:], index+1))
            if (index + 1)%11 != 1:
                q.put((path[:], index-1))
            if index + 11 < len(grid):
                q.put((path[:], index+11))

    return ([],0)

def get_shortest_path(grid, start):

    orientation = "north"
    block_count = ore_count(grid)
    index = start
    path = []
    for i in range(block_count):
        new_orientation, sub_path, new_index = get_next_ore(orientation, grid,index)
        path += sub_path
        index = new_index
        orientation = new_orientation
    return path




# Create default Malmo objects:
agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print('ERROR:',e)
    print(agent_host.getUsage())
    exit(1)
if agent_host.receivedArgument("help"):
    print(agent_host.getUsage())
    exit(0)

if agent_host.receivedArgument("test"):
    num_repeats = 1
else:
    num_repeats = 10

# for i in range(num_repeats):
# size = int(6 + 0.5*i)
# print("Size of maze:", size)
# my_mission = MalmoPython.MissionSpec(GetMissionXML("0", 0.4 + float(i/20.0), size), True)
my_mission = MalmoPython.MissionSpec(get_mission_xml(), True)
my_mission_record = MalmoPython.MissionRecordSpec()
my_mission.requestVideo(800, 500)
my_mission.setViewpoint(1)

# Attempt to start a mission:
max_retries = 3
my_clients = MalmoPython.ClientPool()
my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

for retry in range(max_retries):
    try:
        agent_host.startMission( my_mission, my_clients, my_mission_record, 0, "%s-%d" % ('Moshe', 1) )
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission", (1), ":",e)
            exit(1)
        else:
            time.sleep(2)

# Loop until mission starts:
print("Waiting for the mission", (1), "to start ",)
world_state = agent_host.getWorldState()
while not world_state.has_mission_begun:
    #sys.stdout.write(".")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print("ASDL;KFJASDL;KFJL")

grid = load_grid(world_state)
start = find_start(grid) # implement this

print(grid)
# action_list = extract_action_list_from_path([])
final_path = get_shortest_path(grid,start)
path = extract_action_list_from_path(final_path)
action_list = path
# action_list = []

# Loop until mission ends:
action_index = 0
while world_state.is_mission_running:
    #sys.stdout.write(".")
    time.sleep(0.1)

    # Sending the next commend from the action list -- found using the Dijkstra algo.
    if action_index >= len(action_list):
        print("Error:", "out of actions, but mission has not ended!")
        time.sleep(2)
    else:
        if action_list[action_index] == 'attack 0':
            time.sleep(1)
        agent_host.sendCommand(action_list[action_index])
        if action_list[action_index] == 'attack 0':
            time.sleep(1)
    action_index += 1
    if len(action_list) == action_index:
        # Need to wait few seconds to let the world state realise I'm in end block.
        # Another option could be just to add no move actions -- I thought sleep is more elegant.
        time.sleep(2)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
# Mission has ended.
