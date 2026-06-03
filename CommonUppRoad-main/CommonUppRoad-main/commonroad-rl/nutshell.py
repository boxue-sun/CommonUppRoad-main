import gym
import commonroad_rl.gym_commonroad

# kwargs overwrites configs defined in commonroad_rl/gym_commonroad/configs.yaml
env = gym.make("commonroad-v1",
		# if installed via pip add the paths to the data folders and uncomment the following two lines
		# meta_scenario_path=meta_scenario_path, #path to meta scenario specification
		# train_reset_config_path= training_data_path, #path to training pickels
               action_configs={"action_type": "continuous"},
               goal_configs={"observe_distance_goal_long": True, "observe_distance_goal_lat": True},
               surrounding_configs={"observe_lane_circ_surrounding": False,
               		     "fast_distance_calculation": False,
                                    "observe_lidar_circle_surrounding": True,
                                    "lidar_circle_num_beams": 20},
               reward_type="sparse_reward",
               reward_configs={"sparse_reward":{"reward_goal_reached": 50.,
                                      "reward_collision": -100.,
                                      "reward_off_road": -50.,
      					"reward_time_out": -10.,
					"reward_friction_violation": 0.}})

all_obs = []
all_actions = []
all_revs = []

observation = env.reset()
initial_observation = observation

for _ in range(500):
    # env.render() # rendered images with be saved under ./img
    action = env.action_space.sample() # your agent here (this takes random actions)
    observation, reward, done, info = env.step(action)

    all_obs.append(observation)
    all_actions.append(action)
    all_revs.append(reward)

    if done:
        observation = env.reset()

env.close()
