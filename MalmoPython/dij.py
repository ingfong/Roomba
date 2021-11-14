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

import os
import sys
import time
import json
from priority_dict import priorityDictionary as PQ
from numpy.random import randint

# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

def GetMissionXML():
    size = 10
    seed = "0"
    gp = 0.4

    def get_lava_and_diamonds():
        blocks = '';
        n = 5 * 2 + 1
        for x in range(n):
            for y in range (n):
                random = randint(101)/100
                if random < .1:
                    blocks += "<DrawBlock x='{}'  y='2' z='{}' type='diamond_ore' />".format(x-5, y-5)
                    blocks += "<DrawBlock x='{}'  y='1' z='{}' type='diamond_ore' />".format(x-5, y-5)
                elif random < .2:
                    blocks += "<DrawBlock x='{}'  y='2' z='{}' type='coal_ore' />".format(x-5, y-5)
                    blocks += "<DrawBlock x='{}'  y='1' z='{}' type='coal_ore' />".format(x-5, y-5)

        for y in range (-1,n+1):
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(5+1, y-5)
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(-5-1, y-5)

        for x in range (-1,n+1):
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(x-5, 5+1)
                blocks += "<DrawBlock x='{}'  y='1' z='{}' type='lava' />".format(x-5, -5-1)
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
                            "<DrawCuboid x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='air'/>".format(-5, 5, -5, 5) + \
                            "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='stone'/>".format(-5, 5, -5, 5) + \
                                get_lava_and_diamonds() + \
                            '''<DrawBlock x='0'  y='2' z='0' type='air' />
                            <DrawBlock x='0'  y='1' z='0' type='stone' />
                        </DrawingDecorator>
                        <ServerQuitWhenAnyAgentFinishes/>
                    </ServerHandlers>
                </ServerSection>

                <AgentSection mode="Survival">
                    <Name>CS175DiamondCollector</Name>
                    <AgentStart>
                        <Placement x="0.5" y="2" z="0.5" pitch="45" yaw="0"/>
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
                                <min x="-10" y="-1" z="-10"/>
                                <max x="10" y="-1" z="10"/>
                            </Grid>
                        </ObservationFromGrid>
                        <AgentQuitFromReachingCommandQuota total="'''+str(100)+'''" />
                        <AgentQuitFromTouchingBlockType>
                            <Block type="bedrock" />
                        </AgentQuitFromTouchingBlockType>
                    </AgentHandlers>
                </AgentSection>
            </Mission>'''
    # return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    #         <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    #           <About>
    #             <Summary>Hello world!</Summary>
    #           </About>

    #         <ServerSection>
    #           <ServerInitialConditions>
    #             <Time>
    #                 <StartTime>1000</StartTime>
    #                 <AllowPassageOfTime>false</AllowPassageOfTime>
    #             </Time>
    #             <Weather>clear</Weather>
    #           </ServerInitialConditions>
    #           <ServerHandlers>
    #               <FlatWorldGenerator generatorString="3;7,44*49,73,35:1,159:4,95:13,35:13,159:11,95:10,159:14,159:6,35:6,95:6;12;"/>
    #               <DrawingDecorator>
    #                 <DrawSphere x="-27" y="70" z="0" radius="30" type="air"/>
    #               </DrawingDecorator>
    #               <MazeDecorator>
    #                 <Seed>'''+str(seed)+'''</Seed>
    #                 <SizeAndPosition width="''' + str(size) + '''" length="''' + str(size) + '''" height="10" xOrigin="-32" yOrigin="69" zOrigin="-5"/>
    #                 <StartBlock type="emerald_block" fixedToEdge="true"/>
    #                 <EndBlock type="redstone_block" fixedToEdge="true"/>
    #                 <PathBlock type="diamond_block"/>
    #                 <FloorBlock type="air"/>
    #                 <GapBlock type="air"/>
    #                 <GapProbability>'''+str(gp)+'''</GapProbability>
    #                 <AllowDiagonalMovement>false</AllowDiagonalMovement>
    #               </MazeDecorator>
    #               <ServerQuitFromTimeUp timeLimitMs="10000"/>
    #               <ServerQuitWhenAnyAgentFinishes/>
    #             </ServerHandlers>
    #           </ServerSection>

    #           <AgentSection mode="Survival">
    #             <Name>CS175AwesomeMazeBot</Name>
    #             <AgentStart>
    #                 <Placement x="0.5" y="56.0" z="0.5" yaw="0"/>
    #             </AgentStart>
    #             <AgentHandlers>
    #                 <DiscreteMovementCommands/>
    #                 <AgentQuitFromTouchingBlockType>
    #                     <Block type="redstone_block"/>
    #                 </AgentQuitFromTouchingBlockType>
    #                 <ObservationFromGrid>
    #                   <Grid name="floorAll">
    #                     <min x="-10" y="-1" z="-10"/>
    #                     <max x="10" y="-1" z="10"/>
    #                   </Grid>
    #               </ObservationFromGrid>
    #             </AgentHandlers>
    #           </AgentSection>
    #         </Mission>'''


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

def find_start_end(grid):
    """
    Finds the source and destination block indexes from the list.

    Args
        grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)

    Returns
        start: <int>   source block index in the list
        end:   <int>   destination block index in the list
    """
    #------------------------------------
    #
    #   Fill and submit this code
    #
    start = 0
    end = 0

    for i in range(len(grid)): 
        if (grid[i] == 'emerald_block') :
            start = i
        
        if (grid[i] == 'redstone_block') :
            end = i
        

    return (start, end)

    #-------------------------------------

def extract_action_list_from_path(path_list):
    """
    Converts a block idx path to action list.

    Args
        path_list:  <list>  list of block idx from source block to dest block.

    Returns
        action_list: <list> list of string discrete action commands (e.g. ['movesouth 1', 'movewest 1', ...]
    """
    action_trans = {-21: 'movenorth 1', 21: 'movesouth 1', -1: 'movewest 1', 1: 'moveeast 1'}
    alist = []
    for i in range(len(path_list) - 1):
        curr_block, next_block = path_list[i:(i + 2)]
        alist.append(action_trans[next_block - curr_block])

    return alist


def dijkstra_shortest_path(grid_obs, source):
    """
    Finds the shortest path from source to destination on the map. It used the grid observation as the graph.
    See example on the Tutorial.pdf file for knowing which index should be north, south, west and east.

    Args
        grid_obs:   <list>  list of block types string representing the blocks on the map.
        source:     <int>   source block index.
        dest:       <int>   destination block index.

    Returns
        path_list:  <list>  block indexes representing a path from source (first element) to destination (last)
    """
    #------------------------------------
    #
    #   Fill and submit this code
    #

    diamonds = []

    print(grid_obs)
    for i in range(-110, 112):
        print("iterations:", i)
        if grid_obs[i] == 'diamond_block':
            diamonds.append(i)

    curr = [[1, [0 for i in range(len(diamonds))]]]
    visited = {[1, [0 for i in range(len(diamonds))]]}

    # https://leetcode.com/problems/shortest-path-to-get-all-keys/discuss/364604/Simple-Python-BFS-Solution-(292-ms-beat-97.78)
    # essentially implement this leet code problem 

    


    # for value in track:
    #     for adjacent_value in [-21, 21, 1, -1]:
    #         n = track[value] + 1
    #         if value + adjacent_value in track and n < track[value+adjacent_value]:
    #             track[value + adjacent_value] = n
    #             paths[value + adjacent_value] = paths[value] + [value +  adjacent_value]
    
    return [1, 2, 3]
    #-------------------------------------

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
    num_repeats = 1

for i in range(num_repeats):
    size = int(6 + 0.5*i)
    print("Size of maze:", size)
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
            agent_host.startMission( my_mission, my_clients, my_mission_record, 0, "%s-%d" % ('Moshe', i) )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission", (i+1), ":",e)
                exit(1)
            else:
                time.sleep(2)

    # Loop until mission starts:
    print("Waiting for the mission", (i+1), "to start ",)
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission", (i+1), "running.")

    grid = load_grid(world_state)
    start = 0 # implement this
    path = dijkstra_shortest_path(grid, start)  # implement this
    action_list = extract_action_list_from_path(path)
    # print("Output (start,end)", (i+1), ":", (start,end))
    print("Output (path length)", (i+1), ":", len(path))
    print("Output (actions)", (i+1), ":", action_list)
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
            agent_host.sendCommand(action_list[action_index])
        action_index += 1
        if len(action_list) == action_index:
            # Need to wait few seconds to let the world state realise I'm in end block.
            # Another option could be just to add no move actions -- I thought sleep is more elegant.
            time.sleep(2)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission", (i+1), "ended")
    # Mission has ended.
