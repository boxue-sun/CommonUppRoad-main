# import functions to read xml file and visualize commonroad objects
import matplotlib.pyplot as plt
import os
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer

# Specify the folder path
folder_path = os.path.dirname(__file__) + "\\data_xml"
fig_path = os.path.dirname(__file__) + "\\figs"
if not os.path.exists(fig_path):
    os.makedirs(fig_path)

# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    # Check if the file is a regular file (not a directory)
    if os.path.isfile(os.path.join(folder_path, filename)):
        file_path = os.path.join(folder_path, filename)
        # read in the scenario and planning problem set
        scenario, planning_problem_set = CommonRoadFileReader(file_path).open()
        # plot the planning problem and the scenario for the fifth time step
        plt.figure(figsize=(25, 10))
        rnd = MPRenderer()
        rnd.draw_params.time_begin = 5
        scenario.draw(rnd)
        planning_problem_set.draw(rnd)
        rnd.render()
        # plt.show()
        # Save the plot to a file
        plt.savefig(fig_path + "\\" + filename + '.png')
        plt.close()
