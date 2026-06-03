import matplotlib.pyplot as plt
import warnings
import os
warnings.filterwarnings('ignore')

import numpy as np
import imageio

from commonroad.geometry.shape import Rectangle
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer, MPDrawParams, DynamicObstacleParams
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.state import CustomState, InitialState
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction

def read_sample_log(path):
    with open(path, 'r') as f:
        data = f.read().splitlines()
    data = [list(map(float, line.split(' '))) for line in data]
    return data

def make_dynamic_obstacle(obstacle_id, data, w=1.8, l=4.3):
    t, x, y, orientation, velocity, acceleration = data[0]
    initial_state = CustomState(
        position=np.array([x, y]),
        velocity=velocity,
        orientation=orientation,
        time_step=0
    ).convert_state_to_state(InitialState())

    state_list = []
    for row in data[1:]:
        t, x, y, orientation, velocity, acceleration = row
        state = CustomState(
            position=np.array([x, y]),
            velocity=velocity,
            orientation=orientation,
            acceleration=acceleration,
            time_step=t
        )
        state_list.append(state)

    trajectory = Trajectory(1, state_list)
    shape = Rectangle(width=w, length=l)
    prediction = TrajectoryPrediction(trajectory, shape)

    obstacle = DynamicObstacle(
        obstacle_id, ObstacleType.UNKNOWN, shape, initial_state, prediction
    )
    return obstacle

def create_animation(scenario, planning_problem_set, time):
    rnd = MPRenderer()
    dp = MPDrawParams()
    dp.time_end = time
    dp.dynamic_obstacle.draw_icon = True
    dp.dynamic_obstacle.draw_shape = True
    rnd.create_video([scenario, planning_problem_set], f"experiments/animation/{str(scenario.scenario_id)}_uppaal.gif", draw_params=dp)
    
def create_animation2(scenario, planning_problem_set, time):
    # Render each time step and save as figures
    for i in range(time):
        plt.figure(figsize=(25, 10))
        rnd = MPRenderer(plot_limits=[-20, 125, -25, 125]) # change this to different scenarios
        rnd.draw_params.time_begin = i
        scenario.draw(rnd)

        draw_params = DynamicObstacleParams()
        draw_params.vehicle_shape.occupancy.shape.facecolor = "yellow"
        draw_params.time_begin = i
        draw_params.time_end = i + 1
 
        for obstacle in obstacles:
            obstacle.draw(rnd, draw_params)
        ego.draw(rnd, draw_params)
        rnd.render()

        plt.savefig(os.path.join(output_fig_path, f"temp{i}.png"))
        plt.close()

    # Create a GIF from the saved figures
    figures_list = [os.path.join(output_fig_path, f"temp{i}.png") for i in range(len(sample))]
    gif_path = os.path.join(root, f"experiments/animation/{str(scenario.scenario_id)}_uppaal.gif")
    with imageio.get_writer(gif_path, mode='I') as writer:
        for filename in figures_list:
            image = imageio.imread(filename)
            writer.append_data(image)


# Define variables for parsing
root = os.path.dirname(__file__)
SCENARIO_PATH = os.path.join(root, 'scenarios/DEU_Ffb-1_3_T-1.xml')
SAMPLING_LOG_PATH = os.path.join(root, 'uppaal/sampling.log')
N_OBS_STATES = 5
N_NEW_OBS = 0

scenario, planning_problem_set = CommonRoadFileReader(SCENARIO_PATH).open()

# Read sample log
sample = read_sample_log(SAMPLING_LOG_PATH)

# Divide data into obstacle states and ego states
ego_states = []
new_obsts = [[] for _ in range(N_NEW_OBS)]

for row in sample:
    t = int(row[0])
    obst = 0
    for idx in range(1, N_NEW_OBS * N_OBS_STATES, N_OBS_STATES):
        new_obsts[obst].append([t] + row[idx:idx + N_OBS_STATES])
        obst += 1
    ego_states.append([t] + row[1 + N_NEW_OBS * N_OBS_STATES:])

# Create the obstacles
obstacles = []
for obst_states in new_obsts:
    obst = make_dynamic_obstacle(scenario.generate_object_id(), obst_states)
    scenario.add_objects(obst)
    obstacles.append(obst)

#scenario.remove_obstacle(scenario.dynamic_obstacles)

ego = make_dynamic_obstacle(scenario.generate_object_id(), ego_states)
scenario.add_objects(ego)
obstacles.append(ego)

# Create output folder for figures
output_fig_path = os.path.join(root, "experiments/animation/figures")
os.makedirs(output_fig_path, exist_ok=True)

create_animation(scenario, planning_problem_set, len(sample))