# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# Tutorial sample #7: The Maze Decorator

try:
    from malmo import MalmoPython
except:
    import MalmoPython

from numpy.random import randint
import os
import sys
import time
import json
import queue
# from priority_dict import priorityDictionary as PQ

# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

def GetMissionXML():

    size = 10
    seed = "0"
    gp = 0.4
    diamond_reward_density = .1
    coal_reward_density = .2
    size = 5
    obs_size = 5
    max_episode_steps = 100

    def get_lava_and_diamonds():
        blocks = '';
        n = size * 2 + 1
        for x in range(n):
            for y in range (n):
                random = randint(101)/100
                if random < diamond_reward_density:
                    blocks += "<DrawBlock x='{}'  y='2' z='{}' type='diamond_ore' />".format(x-size, y-size)
                elif random < coal_reward_density:
                    blocks += "<DrawBlock x='{}'  y='2' z='{}' type='coal_ore' />".format(x-size, y-size)

        for y in range (-1,n+1):
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(size+1, y-size)
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(-size-1, y-size)

        for x in range (-1,n+1):
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(x-size, size+1)
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(x-size, -size-1)
        return blocks

    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

                <About>
                    <Summary>Diamond Collector</Summary>
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
                        <DrawingDecorator>''' + \
                            "<DrawSphere x='-27' y='70' z='0' radius='30' type='air'/>" + \
                            "<DrawCuboid x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='air'/>".format(-size, size, -size, size) + \
                            "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='stone'/>".format(-size, size, -size, size) + \
                            get_lava_and_diamonds() + \
                            '''
                            <DrawBlock x='0'  y='2' z='0' type='air' />
                            <DrawBlock  x='0'  y='1' z='0' type="emerald_block"/>
                        </DrawingDecorator>
                        <ServerQuitWhenAnyAgentFinishes/>
                    </ServerHandlers>
                </ServerSection>

                <AgentSection mode="Survival">
                    <Name>CS175DiamondCollector</Name>
                    <AgentStart>
                        <Placement x="0.5" y="2" z="0.5" pitch="45" yaw="180"/>
                        <Inventory>
                            <InventoryItem slot="0" type="diamond_pickaxe"/>
                        </Inventory>
                    </AgentStart>
                    <AgentHandlers>
                        <RewardForCollectingItem>
                            <Item type="diamond" reward="5"/>
                            <Item type="coal" reward="1"/>
                        </RewardForCollectingItem>
                        <RewardForTouchingBlockType>
                             <Block type="lava" reward="-1" />
                         </RewardForTouchingBlockType>
                        <DiscreteMovementCommands/>
                        <ObservationFromFullStats/>
                        <ObservationFromRay/>
                        <ObservationFromGrid>
                            <Grid name="floorAll">
                                <min x="-'''+str(int(obs_size))+'''" y="0" z="-'''+str(int(obs_size))+'''"/>
                                <max x="'''+str(int(obs_size))+'''" y="0" z="'''+str(int(obs_size))+'''"/>
                            </Grid>
                        </ObservationFromGrid>
                        <AgentQuitFromReachingCommandQuota total="'''+str(max_episode_steps)+'''" />
                        <AgentQuitFromTouchingBlockType>
                            <Block type="bedrock" />
                        </AgentQuitFromTouchingBlockType>
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

    return len(grid)//2

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

    orientations = {"north": 0, "west": 3, "south": 2, "east": 1}

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
my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
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

print()

grid = load_grid(world_state)
start = find_start(grid) # implement this
action_list = extract_action_list_from_path([])



final_path = get_shortest_path(grid,start)
path = extract_action_list_from_path(final_path)
action_list = path

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
