from commonroad.common.file_reader import CommonRoadFileReader
import sys
import logging
import os
import numpy as np
from parseCR.utils import write_large_block


# %% load the files and parameters
template_file = os.path.dirname(__file__) + "/uppaal/template.xml" 
# read template files and store lines
with open(template_file, 'r', encoding='utf-8') as template_file:
        lines = template_file.readlines()

input_file_folder = os.path.dirname(__file__) + "/scenarios"
output_file_folder = os.path.dirname(__file__) + "/uppaal/models"
if not os.path.exists(output_file_folder):
        os.makedirs(output_file_folder)

for xml_file in os.listdir(input_file_folder):

    # xml_file = "ZAM_Ramp-1_1-T-1.xml" # "ZAM_Tutorial-1_2_T-1.xml" or "DEU_Ffb-1_3_T-1.xml" or "ZAM_Ramp-1_1-T-1.xml"
    xml_file_path = input_file_folder + "/" + xml_file
    file_name, _ = os.path.splitext(xml_file)

    output_file = output_file_folder + "/" + file_name + "_generated_lanelet.xml"

    # Parse the XML file
    scenario, planning_problem_set = CommonRoadFileReader(xml_file_path).open()

    # SCALE = 10000 # the scaling factor from double to int
    P = 1
    BASE = 10
    EXPONENT = 1
    MAXT = 50
    DEFAULT_VAL = 0.0
    RADAR = 100
    THRESHOLD = 0.02
    N1 = 1 # sense period
    N2 = 4 # decision-making period
    MAXACT= 2
    MAXOBS = scenario.dynamic_obstacles.__len__()
    # Ego vehicle parameters
    EV_WIDTH = 1
    EV_LENGTH = 4.5
    EV_ORI = 0 # initial orientation

    # MAXP is to set the maximal number of points of a lane
    for lane in scenario.lanelet_network.lanelets:
        # merge the lane points if they are on the same straight line 
        if np.all(lane.left_vertices[:, 1] == lane.left_vertices[0, 1]) or np.all(lane.left_vertices[:, 0] == lane.left_vertices[0, 0]):
            lane.left_vertices = lane.left_vertices[[0, -1]]
        if np.all(lane.right_vertices[:, 1] == lane.right_vertices[0, 1]) or np.all(lane.right_vertices[:, 0] == lane.right_vertices[0, 0]):
            lane.right_vertices = lane.right_vertices[[0, -1]]

    MAXP = max(len(lane.left_vertices) for lane in scenario.lanelet_network.lanelets)
    # MAXL is the number of lanes in the lanelet network
    MAXL = len(scenario.lanelet_network.lanelets)
    # MAXSO is the number of static obstacles
    MAXSO = max(1, len(scenario.static_obstacles))
    # MAXDO is the number of dynamic obstacles
    MAXDO = max(1, len(scenario.dynamic_obstacles))
    # MAXTP kept at 1 for backward compatibility (Obstacle now uses behavior automaton, not trajectories)
    MAXTP = 1
    # MAXPRE is the maximal number of predecessor lanes 
    MAXPRE = max(1, max(len(lane.predecessor) for lane in scenario.lanelet_network.lanelets))
    # MAXSUC is the maximal number of successor lanes 
    MAXSUC = max(1, max(len(lane.successor) for lane in scenario.lanelet_network.lanelets))
    # TIMESTEPSIZE is the step time size
    TIMESTEPSIZE = scenario.dt


    # %% construct the lanelet network declaration in c code
    ST_BOUND_leftLane_str_set = []
    ST_BOUND_rightLane_str_set = []
    ST_LANE_lane_str_set = []
    ST_LANE_laneNet_str = []
    for i, lane in enumerate(scenario.lanelet_network.lanelets):
        # get lane information
        lane_ID = lane.lanelet_id
        lane_predecessor = [] if lane.predecessor == [] else lane.predecessor # TODO: check predecessor and successor, they can be multiple
        lane_successor = [] if lane.successor == [] else lane.successor
        lane_adjLeft = lane.adj_left
        lane_adjRight = lane.adj_right

        # lane_marking type: 'dashed', 'solid', 'unknown'
        lane_markingLeft = True if lane.line_marking_left_vertices.value == 'dashed' else False
        lane_markingRight = True if lane.line_marking_right_vertices.value == 'dashed' else False
        
        # if same_direction is True, return True, if False or None, return False
        lane_dirLeft = True if (lane.adj_left_same_direction == True) else False
        lane_dirRight = True if (lane.adj_right_same_direction == True) else False

        # parse the left and right lanes and scale the position
        leftLane = (lane.left_vertices*pow(BASE,EXPONENT)).astype(int)
        rightLane = (lane.right_vertices*pow(BASE,EXPONENT)).astype(int)
        # merge the lane points if they are on the same straight line 
        if np.all(leftLane[:, 1] == leftLane[0, 1]) or np.all(leftLane[:, 0] == leftLane[0, 0]):
            leftLane = leftLane[[0, -1]]
        if np.all(rightLane[:, 1] == rightLane[0, 1]) or np.all(rightLane[:, 0] == rightLane[0, 0]):
            rightLane = rightLane[[0, -1]]

        # construct the string declaration
        # append {NONE, NONE} to meet the fixed-length array
        leftLane_str = "{" + ", ".join(["{" + ", ".join(map(str, point)) + "}" for point in leftLane]) + (MAXP - len(leftLane))*", {NONE, NONE}" + "}" # e.g., '{{-86, 7}, {-64, 6}, {NONE, NONE}}'
        ST_BOUND_left = f"const ST_BOUND leftLane{i + 1} = {{{leftLane_str}, {lane_markingLeft}}};" # e.g., 'const ST_BOUND leftLane1 = {{{-86, 7}, {-64, 6}}, True};'
        rightLane_str = "{" + ", ".join(["{" + ", ".join(map(str, point)) + "}" for point in rightLane]) + (MAXP - len(rightLane))*", {NONE, NONE}" + "}"
        ST_BOUND_right = f"const ST_BOUND rightLane{i + 1} = {{{rightLane_str}, {lane_markingRight}}};"

        # construct the lane string declaration, e.g., 'const ST_LANE lane1 ={1, leftLane1, rightLane1, None, None, 2, False, None, False'
        # extend the lane_predecessor and lane_successor to meet the fixed-length array
        lane_predecessor += (MAXPRE - len(lane_predecessor))*[None]
        lane_successor += (MAXSUC - len(lane_successor))*[None]
        ST_LANE_lane = f"const ST_LANE lane{i + 1} = " + "{" + ", ".join([f"{lane_ID}", f"leftLane{i + 1}", f"rightLane{i + 1}", 
                                                                        f"{lane_predecessor}", f"{lane_successor}", f"{lane_adjLeft}",
                                                                        f"{lane_dirLeft}", f"{lane_adjRight}", f"{lane_dirRight}"]) + "};"
        # collect the declearations
        ST_BOUND_leftLane_str_set.append(ST_BOUND_left)
        ST_BOUND_rightLane_str_set.append(ST_BOUND_right)
        ST_LANE_lane_str_set.append(ST_LANE_lane)
        ST_LANE_laneNet_str.append(f"lane{i + 1}")

    ST_LANE_laneNet_str = "const ST_LANE laneNet[MAXL] = {" + ", ".join(ST_LANE_laneNet_str) + "};"


    # %% construct the static obstacles declaration in c code
    ST_RECTANGLE_obs_str_set = []
    for static_obs in scenario.static_obstacles:
        obs_pos = (static_obs.initial_state.position*pow(BASE,EXPONENT)).astype(int)
        obs_ori = int(static_obs.initial_state.orientation*pow(BASE,EXPONENT))
        obs_width = int(static_obs.obstacle_shape.width*pow(BASE,EXPONENT))
        obs_length = int(static_obs.obstacle_shape.length*pow(BASE,EXPONENT))
        ST_RECTANGLE_obs_pos = "{" + ", ".join(map(str, obs_pos)) + "}"
        ST_RECTANGLE_obs_str_single = "{" + ", ".join([ST_RECTANGLE_obs_pos, f"{obs_width}", f"{obs_length}", f"{obs_ori}"]) + "}" # e.g., {{2000, 700}, 200, 450, 0}
        ST_RECTANGLE_obs_str_set.append(ST_RECTANGLE_obs_str_single)

    # If static obstacles is zero, do not define “statisObs[MAXSO]”.
    if len(ST_RECTANGLE_obs_str_set) == 0:
        ST_RECTANGLE_obs_str1 = "const bool staticObsExists = false;"
        ST_RECTANGLE_obs_str2 = "const ST_RECTANGLE staticObs[MAXSO] = {{{NONE, NONE}, NONE, NONE, NONE}};"

    else:
        ST_RECTANGLE_obs_str1 = "const bool staticObsExists = true;"
        ST_RECTANGLE_obs_str2 = "const ST_RECTANGLE staticObs[MAXSO] = {" + ", ".join(ST_RECTANGLE_obs_str_set) + "};" # e.g., const ST_RECTANGLE staticObs[MAXSO] = {{{2000, 700}, 200, 450, 0}};

    # %% construct the dynamic obstacles declaration in c code
    initCS_str_set = []
    shapeObs_str_set = []
    behavior_str_set = []
    Obstacle_str_set = []
    Obs_naming_set = []
    obs_count = 0

    for dyn_obs in scenario.dynamic_obstacles:
        obs_width = int(dyn_obs.obstacle_shape.width*pow(BASE,EXPONENT))
        obs_length = int(dyn_obs.obstacle_shape.length*pow(BASE,EXPONENT))
        obs_id = obs_count
        obs_count = obs_count + 1

        # const ST_DSTATE initCS1 = {{2.25, 3.50}, 2.30, 0.0, 0.0, 0.0};
        obs_ini_pos = dyn_obs.initial_state.position
        obs_ini_vel = dyn_obs.initial_state.velocity
        obs_ini_ori = dyn_obs.initial_state.orientation
        obs_ini_acc = dyn_obs.initial_state.acceleration
        obs_ini_jerk = DEFAULT_VAL
        obs_ini_yaw = dyn_obs.initial_state.yaw_rate
        ST_RECTANGLE_obs_ini_pos = "{" + ", ".join(map(str, obs_ini_pos)) + "}"
        initCS_str = f"const ST_DSTATE initCS{obs_id} = {{" + ", ".join([ST_RECTANGLE_obs_ini_pos,
                    f"{obs_ini_vel}", f"{obs_ini_ori}", f"{obs_ini_acc}", f"{obs_ini_jerk}" ,f"{obs_ini_yaw}"]) + "};"
        initCS_str_set.append(initCS_str)

        # const ST_RECTANGLE shapeObs1 = {{225, 350}, 200, 450, 0};
        obs_ini_pos_int = "{" + ", ".join(map(str, (obs_ini_pos*pow(BASE,EXPONENT)).astype(int))) + "}"
        shapeObs_str = f"const ST_RECTANGLE shapeObs{obs_id} = {{" + ", ".join([obs_ini_pos_int,
                        f"{int(dyn_obs.obstacle_shape.width*pow(BASE,EXPONENT))}",
                        f"{int(dyn_obs.obstacle_shape.length*pow(BASE,EXPONENT))}",
                        f"{int(obs_ini_ori*pow(BASE,EXPONENT))}"]) + "};"
        shapeObs_str_set.append(shapeObs_str)

        # Infer behavior parameter ranges from trajectory if available
        if hasattr(dyn_obs, 'prediction') and dyn_obs.prediction is not None:
            traj = dyn_obs.prediction.trajectory.state_list
            if len(traj) > 0:
                speeds = [s.velocity for s in traj if hasattr(s, 'velocity') and s.velocity is not None]
                if speeds:
                    v_min_val = max(0.0, min(speeds) * 0.5)
                    v_max_val = max(speeds) * 1.5
                else:
                    v_min_val = 5.0
                    v_max_val = 20.0
            else:
                v_min_val = 5.0
                v_max_val = 20.0
        else:
            v_min_val = 5.0
            v_max_val = 20.0

        behavior_str = (
            f"const ST_OBEHAVIOR obsBehavior{obs_id} = {{"
            f"d2i({v_min_val}), d2i({v_max_val}), "
            f"d2i(3.0), d2i(4.0), "
            f"d2i(0.3), d2i(50.0), "
            f"d2i(0.0)"
            f"}};"
        )
        behavior_str_set.append(behavior_str)

        # obs1 = Obstacle(1, initCS1, shapeObs1, obsBehavior1);
        Obstacle_str = f"obs{obs_id} = Obstacle({obs_id}, initCS{obs_id}, shapeObs{obs_id}, obsBehavior{obs_id});"
        Obstacle_str_set.append(Obstacle_str)

        # Obs_naming
        Obs_naming_set.append(f"obs{obs_id}")

    # %% construct the goal declaration
    planning_problem = list(planning_problem_set.planning_problem_dict.values())

    ST_PLANNING_str_set = []
    ego_init_str_set = []
    for planning_problem_veh in planning_problem:
        try:
            init_ego = planning_problem_veh.initial_state
            goal_pos = planning_problem_veh.goal.state_list[0].position.center
        except AttributeError:
            try:
                goal_pos = planning_problem_veh.goal.state_list[0].position.shapes[0].center
            except AttributeError:
                logging.error("Could not find goal position in the specified format. Exiting.")
                sys.exit(1)
        if not isinstance(goal_pos, np.ndarray):
            goal_pos = np.array([goal_pos.x, goal_pos.y])
        goal_pos = (goal_pos*pow(BASE,EXPONENT)).astype(int)
        ST_PLANNING_obs_str = "{" + ", ".join(map(str, goal_pos)) + "}"
        ST_PLANNING_str_set.append(ST_PLANNING_obs_str)

        ego_ini_pos = np.array(init_ego.position)
        ego_ini_vel = init_ego.velocity
        ego_ini_ori = init_ego.orientation
        ego_ini_acc = init_ego.acceleration
        ego_ini_jerk = DEFAULT_VAL
        ego_ini_yaw = init_ego.yaw_rate
        #ST_RECTANGLE_ego_ini_pos = "{" + ", ".join(map(str, ego_ini_pos)) + "}"
        DOUBLE_ego_ini_pos = "{" + ", ".join(map(str, ego_ini_pos)) + "}"
        INT32_ego_ini_pos = "{" + ", ".join(map(str, (ego_ini_pos*pow(BASE,EXPONENT)).astype(int))) + "}"
        init_ego_str = "const ST_DSTATE initEgo = {" + ", ".join([DOUBLE_ego_ini_pos, f"{ego_ini_vel}", 
                        f"{ego_ini_ori}", f"{ego_ini_acc}", f"{ego_ini_jerk}", f"{ego_ini_yaw}"]) + "};\n"
        #init_ego_shape_str = "const ST_RECTANGLE initShapeEgo = {{" + ", ".join(map(str, (ego_ini_pos*pow(BASE,EXPONENT)).astype(int))) + "}, 100, 450, 0};"
        #init_ego_shape_str = "const ST_RECTANGLE initShapeEgo = {" + ", ".join([INT32_ego_ini_pos, f"{(EV_WIDTH*pow(BASE,EXPONENT)).astype(int)}", 
        #                    f"{(EV_LENGTH*pow(BASE,EXPONENT)).astype(int)}", f"{(EV_ORI*pow(BASE,EXPONENT)).astype(int)}"]) + "};"
        init_ego_shape_str = "const ST_RECTANGLE initShapeEgo = {" + ", ".join([INT32_ego_ini_pos, f"{EV_WIDTH*pow(BASE,EXPONENT)}",
                            f"{int(EV_LENGTH*pow(BASE,EXPONENT))}", f"{EV_ORI*pow(BASE,EXPONENT)}"]) + "};\n"
        ego_init_str_set.append(init_ego_str)
        ego_init_str_set.append(init_ego_shape_str)

    ST_PLANNING_str = "const ST_PLANNING planning = {" + ", ".join(ST_PLANNING_str_set) + "};" # e.g., const ST_PLANNING planning = {{3000, 0}};
    ST_EGO_INIT_str = "".join(ego_init_str_set)

    # Build complete ego section: initEgo + initShape + rules + initLane + all instances
    # initLane = 0 means first lane in laneNet array (index, not lanelet_id)
    ego_full_str = (
        ST_EGO_INIT_str
        + "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};\n"
        + "const int[0,MAXL] initLane = 0;\n"
        + "move = Act_Move(0);\n"
        + "turn = Act_Turn(1);\n"
        + "controller = Controller(initLane,initEgo,initShapeEgo,rules);\n"
        + "timer = Timer();\n"
        + "dynamics = Dynamics();\n"
        + "rewardMachine = Rewards();\n"
    )

    # %% construct the definition and hyperparameter declaration in c code
    P_str = f"const int P = {P};"
    MAX_TIME_str = f"const uint16_t MAXTIME = {MAXT};"
    MAXL_str = f"const int MAXL = {MAXL};"
    NONE_str = "const int NONE = -1;"
    MAXP_str = f"const int MAXP = {MAXP};"
    MAXSO_str = f"const int MAXSO = {MAXSO};"
    MAXDO_str = f"const int MAXDO = {MAXDO};"
    MAXTP_str = f"const int MAXTP = {MAXTP};"
    MAXPRE_str = f"const int MAXPRE = {MAXPRE};"
    MAXSUC_str = f"const int MAXSUC = {MAXSUC};"
    TIMESTEPSIZE_str = f"const double TIMESTEPSIZE = {TIMESTEPSIZE};"
    THRES_str = f"const double THRESHOLD = {THRESHOLD};"
    RADAR_str = f"const double RADAR = {RADAR};"
    BASE_str = f"const uint8_t BASE = {BASE};"
    EXPONENT_str = f"const uint8_t EXPONENT = {EXPONENT};"
    N1_str = f"const uint8_t N1 = {N1};"
    N2_str = f"const uint8_t N2 = {N2};"
    MAXACT_str = f"const uint8_t MAXACT = {MAXACT};"
    ACTTYPE_str = "typedef int[0,MAXACT-1] act_id_t;"
    #MAXOBS_str = f"const uint8_t MAXOBS = {MAXOBS};"
    if(MAXOBS == 0):
        MAXOBS_str = f"const uint8_t MAXOBS = 1;"
    else:
        MAXOBS_str = f"const uint8_t MAXOBS = {MAXOBS};"
    OBSTYPE_str = "typedef int[0,MAXOBS-1] obs_id_t;"

    PHOLDER_str = "const ST_PAIR PHOLDER = {NONE,{{NONE,NONE},NONE,NONE,NONE,NONE,NONE}};"
    
    if Obs_naming_set == []:
        system_str = "system timer, move, turn, controller, dynamics, rewardMachine;"
    else:
        system_str = "system timer, " + ", ".join(Obs_naming_set) + ", move, turn, controller, dynamics, rewardMachine;"

    # %% write in the xml templates
    # Markers for generated sections
    start_markers = {
        "<declaration>// Generated scenario starts",
        "<system>// Generated moving obstacles starts",
        "// Generated ego vehicle starts",
        "// Generated model instances starts",
    }
    end_markers = {
        "// Generated scenario ends",
        "// Generated moving obstacles ends",
        "// Generated ego vehicle ends",
        "// Generated model instances ends",
    }

    scenario_prompt = "<declaration>// Generated scenario starts"
    moving_obs_prompt = "<system>// Generated moving obstacles starts"
    model_prompt = "// Generated model instances starts"
    ego_prompt = "// Generated ego vehicle starts"

    in_generated_section = False

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            stripped = line.strip()

            # Detect start of a generated section
            if stripped in start_markers:
                in_generated_section = True
                file.write(line)  # Write the marker line itself

                # Now write the generated content for this section
                if stripped == scenario_prompt:
                    file.write(P_str + "\n")
                    file.write(MAX_TIME_str + "\n")
                    file.write(MAXP_str + "\n")
                    file.write(NONE_str + "\n")
                    file.write(MAXL_str + "\n")
                    file.write(MAXSO_str + "\n")
                    file.write(MAXDO_str + "\n")
                    file.write(MAXTP_str + "\n")
                    file.write(MAXPRE_str + "\n")
                    file.write(MAXSUC_str + "\n")
                    file.write(THRES_str + "\n")
                    file.write(TIMESTEPSIZE_str + "\n")
                    file.write(RADAR_str + "\n")
                    file.write(N1_str + "\n")
                    file.write(N2_str + "\n")
                    file.write(MAXACT_str + "\n")
                    file.write(ACTTYPE_str + "\n")
                    file.write(BASE_str + "\n")
                    file.write(EXPONENT_str + "\n")
                    file.write(MAXOBS_str + "\n")
                    file.write(OBSTYPE_str + "\n")

                    write_large_block(file)

                    for i in range(MAXL):
                        ST_BOUND_leftLane = ST_BOUND_leftLane_str_set[i].replace('False', 'false').replace('True', 'true')
                        ST_BOUND_rightLane = ST_BOUND_rightLane_str_set[i].replace('False', 'false').replace('True', 'true')
                        ST_LANE_lane = ST_LANE_lane_str_set[i].replace('False', 'false').replace('True', 'true').replace('None', 'NONE').replace('[', '{').replace(']', '}')
                        file.write(ST_BOUND_leftLane + "\n")
                        file.write(ST_BOUND_rightLane + "\n")
                        file.write(ST_LANE_lane + "\n")
                        file.write("\n")

                    file.write(ST_LANE_laneNet_str + "\n")
                    file.write("\n")
                    file.write(ST_RECTANGLE_obs_str1 + "\n")
                    file.write(ST_RECTANGLE_obs_str2 + "\n\n")
                    file.write(ST_PLANNING_str + "\n\n")

                elif stripped == moving_obs_prompt:
                    for i in range(len(scenario.dynamic_obstacles)):
                        file.write(initCS_str_set[i] + "\n")
                        file.write(shapeObs_str_set[i] + "\n")
                        file.write(behavior_str_set[i] + "\n")
                        file.write(Obstacle_str_set[i] + "\n")

                elif stripped == ego_prompt:
                    file.write(ego_full_str)

                elif stripped == model_prompt:
                    file.write(system_str + "\n")

                continue  # Don't write this line again below

            # Detect end of a generated section
            if stripped in end_markers:
                in_generated_section = False
                file.write(line)  # Write the end marker
                continue

            # Skip template lines inside generated sections (they are defaults)
            if in_generated_section:
                continue

            # Normal line — write as-is
            file.write(line)


def generate_model_for_scenario(scenario, planning_problem_set, output_path):
    """
    为单个场景生成 UPPAAL 模型（供 adversarial_search.py 批量调用）。

    参数:
        scenario: CommonRoad scenario 对象
        planning_problem_set: 规划问题集
        output_path: 输出 XML 文件路径
    """
    template_file = os.path.dirname(__file__) + "/uppaal/template.xml"
    with open(template_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    P = 1
    BASE = 10
    EXPONENT = 1
    MAXT = 50
    DEFAULT_VAL = 0.0
    RADAR = 100
    THRESHOLD = 0.02
    N1 = 1
    N2 = 4
    MAXACT = 2
    EV_WIDTH = 1
    EV_LENGTH = 4.5
    EV_ORI = 0

    if scenario.dynamic_obstacles:
        MAXOBS = len(scenario.dynamic_obstacles)
    else:
        MAXOBS = 1

    for lane in scenario.lanelet_network.lanelets:
        if np.all(lane.left_vertices[:, 1] == lane.left_vertices[0, 1]) or \
           np.all(lane.left_vertices[:, 0] == lane.left_vertices[0, 0]):
            lane.left_vertices = lane.left_vertices[[0, -1]]
        if np.all(lane.right_vertices[:, 1] == lane.right_vertices[0, 1]) or \
           np.all(lane.right_vertices[:, 0] == lane.right_vertices[0, 0]):
            lane.right_vertices = lane.right_vertices[[0, -1]]

    MAXP = max(len(lane.left_vertices) for lane in scenario.lanelet_network.lanelets)
    MAXL = len(scenario.lanelet_network.lanelets)
    MAXSO = max(1, len(scenario.static_obstacles))
    MAXDO = max(1, len(scenario.dynamic_obstacles))
    MAXTP = 1
    MAXPRE = max(1, max(len(lane.predecessor) for lane in scenario.lanelet_network.lanelets))
    MAXSUC = max(1, max(len(lane.successor) for lane in scenario.lanelet_network.lanelets))
    TIMESTEPSIZE = scenario.dt

    # --- Build lanelet declarations ---
    ST_BOUND_leftLane_str_set = []
    ST_BOUND_rightLane_str_set = []
    ST_LANE_lane_str_set = []
    ST_LANE_laneNet_str = []

    for i, lane in enumerate(scenario.lanelet_network.lanelets):
        lane_ID = lane.lanelet_id
        lane_predecessor = [] if lane.predecessor == [] else lane.predecessor
        lane_successor = [] if lane.successor == [] else lane.successor
        lane_adjLeft = lane.adj_left
        lane_adjRight = lane.adj_right
        lane_markingLeft = True if lane.line_marking_left_vertices.value == 'dashed' else False
        lane_markingRight = True if lane.line_marking_right_vertices.value == 'dashed' else False
        lane_dirLeft = True if (lane.adj_left_same_direction == True) else False
        lane_dirRight = True if (lane.adj_right_same_direction == True) else False

        leftLane = (lane.left_vertices * pow(BASE, EXPONENT)).astype(int)
        rightLane = (lane.right_vertices * pow(BASE, EXPONENT)).astype(int)
        if np.all(leftLane[:, 1] == leftLane[0, 1]) or np.all(leftLane[:, 0] == leftLane[0, 0]):
            leftLane = leftLane[[0, -1]]
        if np.all(rightLane[:, 1] == rightLane[0, 1]) or np.all(rightLane[:, 0] == rightLane[0, 0]):
            rightLane = rightLane[[0, -1]]

        leftLane_str = "{" + ", ".join(["{" + ", ".join(map(str, point)) + "}" for point in leftLane]) + \
                       (MAXP - len(leftLane)) * ", {NONE, NONE}" + "}"
        ST_BOUND_left = f"const ST_BOUND leftLane{i + 1} = {{{leftLane_str}, {lane_markingLeft}}};"
        rightLane_str = "{" + ", ".join(["{" + ", ".join(map(str, point)) + "}" for point in rightLane]) + \
                        (MAXP - len(rightLane)) * ", {NONE, NONE}" + "}"
        ST_BOUND_right = f"const ST_BOUND rightLane{i + 1} = {{{rightLane_str}, {lane_markingRight}}};"

        lane_predecessor += (MAXPRE - len(lane_predecessor)) * [None]
        lane_successor += (MAXSUC - len(lane_successor)) * [None]
        ST_LANE_lane = f"const ST_LANE lane{i + 1} = " + "{" + ", ".join([
            f"{lane_ID}", f"leftLane{i + 1}", f"rightLane{i + 1}",
            f"{lane_predecessor}", f"{lane_successor}", f"{lane_adjLeft}",
            f"{lane_dirLeft}", f"{lane_adjRight}", f"{lane_dirRight}"]) + "};"

        ST_BOUND_leftLane_str_set.append(ST_BOUND_left)
        ST_BOUND_rightLane_str_set.append(ST_BOUND_right)
        ST_LANE_lane_str_set.append(ST_LANE_lane)
        ST_LANE_laneNet_str.append(f"lane{i + 1}")

    ST_LANE_laneNet_str = "const ST_LANE laneNet[MAXL] = {" + ", ".join(ST_LANE_laneNet_str) + "};"

    # --- Static obstacles ---
    ST_RECTANGLE_obs_str_set = []
    for static_obs in scenario.static_obstacles:
        obs_pos = (static_obs.initial_state.position * pow(BASE, EXPONENT)).astype(int)
        obs_ori = int(static_obs.initial_state.orientation * pow(BASE, EXPONENT))
        obs_width = int(static_obs.obstacle_shape.width * pow(BASE, EXPONENT))
        obs_length = int(static_obs.obstacle_shape.length * pow(BASE, EXPONENT))
        pos_str = "{" + ", ".join(map(str, obs_pos)) + "}"
        ST_RECTANGLE_obs_str_single = "{" + ", ".join([pos_str, f"{obs_width}", f"{obs_length}", f"{obs_ori}"]) + "}"
        ST_RECTANGLE_obs_str_set.append(ST_RECTANGLE_obs_str_single)

    if len(ST_RECTANGLE_obs_str_set) == 0:
        ST_RECTANGLE_obs_str1 = "const bool staticObsExists = false;"
        ST_RECTANGLE_obs_str2 = "const ST_RECTANGLE staticObs[MAXSO] = {{{NONE, NONE}, NONE, NONE, NONE}};"
    else:
        ST_RECTANGLE_obs_str1 = "const bool staticObsExists = true;"
        ST_RECTANGLE_obs_str2 = "const ST_RECTANGLE staticObs[MAXSO] = {" + \
                                ", ".join(ST_RECTANGLE_obs_str_set) + "};"

    # --- Dynamic obstacles with behavior params ---
    initCS_str_set = []
    shapeObs_str_set = []
    behavior_str_set = []
    Obstacle_str_set = []
    Obs_naming_set = []
    obs_count = 0

    for dyn_obs in scenario.dynamic_obstacles:
        obs_id = obs_count
        obs_count += 1

        pos = dyn_obs.initial_state.position
        vel = dyn_obs.initial_state.velocity
        ori = dyn_obs.initial_state.orientation
        acc = dyn_obs.initial_state.acceleration if hasattr(dyn_obs.initial_state, 'acceleration') else DEFAULT_VAL

        pos_str = "{" + ", ".join(map(str, pos)) + "}"
        initCS_str = f"const ST_DSTATE initCS{obs_id} = {{{pos_str}, {vel}, {ori}, {acc}, {DEFAULT_VAL}, {DEFAULT_VAL}}};"
        initCS_str_set.append(initCS_str)

        pos_int = "{" + ", ".join(map(str, (pos * pow(BASE, EXPONENT)).astype(int))) + "}"
        shapeObs_str = f"const ST_RECTANGLE shapeObs{obs_id} = {{{pos_int}, " + \
                       f"{int(dyn_obs.obstacle_shape.width * pow(BASE, EXPONENT))}, " + \
                       f"{int(dyn_obs.obstacle_shape.length * pow(BASE, EXPONENT))}, " + \
                       f"{int(ori * pow(BASE, EXPONENT))}}};"
        shapeObs_str_set.append(shapeObs_str)

        # Infer speed range from trajectory or use adversarial params
        adv = getattr(dyn_obs, '_adversarial_params', {})
        max_speed_factor = adv.get('max_speed_factor', 1.0)
        brake_aggr = adv.get('brake_aggressiveness', 4.0)

        if hasattr(dyn_obs, 'prediction') and dyn_obs.prediction is not None:
            traj = dyn_obs.prediction.trajectory.state_list
            if len(traj) > 0:
                speeds = [s.velocity for s in traj if hasattr(s, 'velocity') and s.velocity is not None]
                if speeds:
                    v_min_val = max(0.0, min(speeds) * 0.5)
                    v_max_val = max(speeds) * 1.5 * max_speed_factor
                else:
                    v_min_val = 5.0
                    v_max_val = 20.0 * max_speed_factor
            else:
                v_min_val = 5.0
                v_max_val = 20.0 * max_speed_factor
        else:
            v_min_val = 5.0
            v_max_val = 20.0 * max_speed_factor

        behavior_str = (
            f"const ST_OBEHAVIOR obsBehavior{obs_id} = {{"
            f"d2i({v_min_val}), d2i({v_max_val}), "
            f"d2i(3.0), d2i({brake_aggr}), "
            f"d2i(0.3), d2i(50.0), "
            f"d2i(0.0)"
            f"}};"
        )
        behavior_str_set.append(behavior_str)

        Obstacle_str = f"obs{obs_id} = Obstacle({obs_id}, initCS{obs_id}, shapeObs{obs_id}, obsBehavior{obs_id});"
        Obstacle_str_set.append(Obstacle_str)
        Obs_naming_set.append(f"obs{obs_id}")

    # --- Goal declaration ---
    planning_problem = list(planning_problem_set.planning_problem_dict.values())
    ST_PLANNING_str_set = []
    ego_init_str_set = []

    for pp in planning_problem:
        try:
            init_ego = pp.initial_state
            goal_pos = pp.goal.state_list[0].position.center
        except AttributeError:
            try:
                goal_pos = pp.goal.state_list[0].position.shapes[0].center
            except AttributeError:
                logging.error("Could not find goal position. Exiting.")
                sys.exit(1)
        if not isinstance(goal_pos, np.ndarray):
            goal_pos = np.array([goal_pos.x, goal_pos.y])
        goal_pos = (goal_pos * pow(BASE, EXPONENT)).astype(int)
        ST_PLANNING_str_set.append("{" + ", ".join(map(str, goal_pos)) + "}")

        ego_pos = np.array(init_ego.position)
        ego_vel = init_ego.velocity
        ego_ori = init_ego.orientation
        ego_acc = init_ego.acceleration if hasattr(init_ego, 'acceleration') else DEFAULT_VAL

        ego_pos_double = "{" + ", ".join(map(str, ego_pos)) + "}"
        ego_pos_int = "{" + ", ".join(map(str, (ego_pos * pow(BASE, EXPONENT)).astype(int))) + "}"
        init_ego_str = "const ST_DSTATE initEgo = {" + ", ".join([
            ego_pos_double, f"{ego_vel}", f"{ego_ori}", f"{ego_acc}",
            f"{DEFAULT_VAL}", f"{DEFAULT_VAL}"]) + "};\n"
        init_ego_shape_str = "const ST_RECTANGLE initShapeEgo = {" + ", ".join([
            ego_pos_int, f"{int(EV_WIDTH * pow(BASE, EXPONENT))}",
            f"{int(EV_LENGTH * pow(BASE, EXPONENT))}",
            f"{int(EV_ORI * pow(BASE, EXPONENT))}"]) + "};\n"
        ego_init_str_set.append(init_ego_str)
        ego_init_str_set.append(init_ego_shape_str)

    ST_PLANNING_str = "const ST_PLANNING planning = {" + ", ".join(ST_PLANNING_str_set) + "};"
    ST_EGO_INIT_str = "".join(ego_init_str_set)

    # Build complete ego section
    ego_full_str = (
        ST_EGO_INIT_str
        + "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};\n"
        + "const int[0,MAXL] initLane = 0;\n"
        + "move = Act_Move(0);\n"
        + "turn = Act_Turn(1);\n"
        + "controller = Controller(initLane,initEgo,initShapeEgo,rules);\n"
        + "timer = Timer();\n"
        + "dynamics = Dynamics();\n"
        + "rewardMachine = Rewards();\n"
    )

    # --- Hyperparameters ---
    if Obs_naming_set == []:
        system_str = "system timer, move, turn, controller, dynamics, rewardMachine;"
    else:
        system_str = "system timer, " + ", ".join(Obs_naming_set) + \
                     ", move, turn, controller, dynamics, rewardMachine;"

    # --- Write output ---
    start_markers = {
        "<declaration>// Generated scenario starts",
        "<system>// Generated moving obstacles starts",
        "// Generated ego vehicle starts",
        "// Generated model instances starts",
    }
    end_markers = {
        "// Generated scenario ends",
        "// Generated moving obstacles ends",
        "// Generated ego vehicle ends",
        "// Generated model instances ends",
    }

    scenario_prompt = "<declaration>// Generated scenario starts"
    moving_obs_prompt = "<system>// Generated moving obstacles starts"
    model_prompt = "// Generated model instances starts"
    ego_prompt = "// Generated ego vehicle starts"

    in_generated_section = False

    with open(output_path, 'w', encoding='utf-8') as file:
        for line in lines:
            stripped = line.strip()

            if stripped in start_markers:
                in_generated_section = True
                file.write(line)

                if stripped == scenario_prompt:
                    file.write(f"const int P = 1;\n")
                    file.write(f"const uint16_t MAXTIME = {MAXT};\n")
                    file.write(f"const int MAXP = {MAXP};\n")
                    file.write("const int NONE = -1;\n")
                    file.write(f"const int MAXL = {MAXL};\n")
                    file.write(f"const int MAXSO = {MAXSO};\n")
                    file.write(f"const int MAXDO = {MAXDO};\n")
                    file.write(f"const int MAXTP = {MAXTP};\n")
                    file.write(f"const int MAXPRE = {MAXPRE};\n")
                    file.write(f"const int MAXSUC = {MAXSUC};\n")
                    file.write(f"const double THRESHOLD = {THRESHOLD};\n")
                    file.write(f"const double TIMESTEPSIZE = {TIMESTEPSIZE};\n")
                    file.write(f"const double RADAR = {RADAR};\n")
                    file.write(f"const uint8_t N1 = {N1};\n")
                    file.write(f"const uint8_t N2 = {N2};\n")
                    file.write(f"const uint8_t MAXACT = {MAXACT};\n")
                    file.write("typedef int[0,MAXACT-1] act_id_t;\n")
                    file.write(f"const uint8_t BASE = {BASE};\n")
                    file.write(f"const uint8_t EXPONENT = {EXPONENT};\n")
                    file.write(f"const uint8_t MAXOBS = {MAXOBS};\n")
                    file.write("typedef int[0,MAXOBS-1] obs_id_t;\n")

                    from parseCR.utils import write_large_block
                    write_large_block(file)

                    for i in range(MAXL):
                        sl = ST_BOUND_leftLane_str_set[i].replace('False', 'false').replace('True', 'true')
                        sr = ST_BOUND_rightLane_str_set[i].replace('False', 'false').replace('True', 'true')
                        st = ST_LANE_lane_str_set[i].replace('False', 'false').replace('True', 'true') \
                             .replace('None', 'NONE').replace('[', '{').replace(']', '}')
                        file.write(sl + "\n")
                        file.write(sr + "\n")
                        file.write(st + "\n\n")

                    file.write(ST_LANE_laneNet_str + "\n\n")
                    file.write(ST_RECTANGLE_obs_str1 + "\n")
                    file.write(ST_RECTANGLE_obs_str2 + "\n\n")
                    file.write(ST_PLANNING_str + "\n\n")

                elif stripped == moving_obs_prompt:
                    for i in range(len(scenario.dynamic_obstacles)):
                        file.write(initCS_str_set[i] + "\n")
                        file.write(shapeObs_str_set[i] + "\n")
                        file.write(behavior_str_set[i] + "\n")
                        file.write(Obstacle_str_set[i] + "\n")

                elif stripped == ego_prompt:
                    file.write(ego_full_str)

                elif stripped == model_prompt:
                    file.write(system_str + "\n")

                continue

            if stripped in end_markers:
                in_generated_section = False
                file.write(line)
                continue

            if in_generated_section:
                continue

            file.write(line)

            if line.strip() == model_prompt:
                file.write(system_str + "\n")
            