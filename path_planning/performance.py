import math
import time
import statistics
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon

from rrt_dubins import RRT
from motion_plan_state import Motion_plan_state
import catalina
from sharkOccupancyGrid import SharkOccupancyGrid

def summary_1(cost_funcs, num_habitats=10, test_num=100):
    '''
        generate a summary about each term of one specific cost function, given randomly chosen environment
    
        cost_func: a list of lists of weights assigned to each term in the cost function
        test_num: the number of tests to run under a specific cost function
        num_habitats: the number of randomly generated habitats

        output:
        cost_avr: a dictionary summarizing the result of each term of the cost function, 
            key will be weight i.e. w1, w2, ...
            value will be the average cost of each term
    '''
    
    start = Motion_plan_state(730, 280)
    goal = Motion_plan_state(900, 350)
    obstacle_array = [Motion_plan_state(757,243, size=10),Motion_plan_state(763,226, size=5)]
    boundary = [Motion_plan_state(700,200), Motion_plan_state(950,400)]
    testing = RRT(start, goal, boundary, obstacle_array, habitat)

    #inner list is the average cost of different environment for each weight 
    avr_list = [[] for _ in range(len(cost_funcs[0]))]
    #generate summary over different weights
    for cost_func in cost_funcs:

        count_list = []

        # a list of cost for each term of the optimal path for each environment
        cost_summary = [[] for _ in range(len(cost_func))]

        for i in range(test_num):

            count = 0
            
            #build random habitats
            habitats = []
            for _ in range(num_habitats):
                habitats.append(testing.get_random_mps(size_max=15))
            
            #find optimal path
            t_end = time.time() + 20.0
            cost_min = float("inf")
            cost_list = []  

            while time.time() < t_end:
                result = testing.exploring(habitats, 0.5, 5, 1)
                count += 1
                if result is not None:
                    cost = result["cost"]
                    if cost[0] < cost_min:
                        cost_min = cost[0]
                        cost_list = cost[1]
            
            count_list.append(count)

            #append cost for each term to cost_summary list
            for i in range(len(cost_list)):
                cost_summary[i].append(cost_list[i])
        
        print(count_list)

        #calculate average cost for each term
        result = []
        for cost in cost_summary:
            result.append(statistics.mean(cost))
        
        for i in range(len(result)):
            avr_list[i].append(float("{:.3f}".format(result[i]/cost_func[i])))#normalize the result
    
    return avr_list

def plot_summary_1(labels, summary):
    x = np.arange(len(labels))  # the label locations
    width = 0.25  # the width of the bars

    weight1 = summary[0]
    weight2 = summary[1]
    weight3 = summary[2]

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, weight1, width, label='weight1')
    rects2 = ax.bar(x, weight2, width, label="weight2")
    rects3 = ax.bar(x + width, weight3, width, label='weight3')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('average cost')
    ax.set_title('average cost in different weight schemes with randomly generated habitats')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()


    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')


    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    fig.tight_layout()

    plt.show()

def summary_2(start, goal, obstacle_array, boundary, habitats, shark_dict, sharkGrid, test_num, test_time, plot_interval, weights):
    '''generate the average cost of optimal paths of one weight scheme'''
    cost_list = [[]for _ in range(math.ceil(test_time//plot_interval))]
    improvement = []

    for _ in range(test_num):
        rrt = RRT(goal, goal, boundary, obstacle_array, habitats)
        if weights[1] == "random time":
            plan_time = True
            if weights[2] == "trajectory time stamp":
                traj_time_stamp = True
            else:
                traj_time_stamp = False
        elif weights[1] == "random (x,y)":
            plan_time = False
            traj_time_stamp = False
        result = rrt.exploring(shark_dict, sharkGrid, 0.5, 5, 1, traj_time_stamp=traj_time_stamp, max_plan_time=test_time, max_traj_time=500, plan_time=plan_time, weights=weights[0])
        if result:
            cost = result["cost list"]
            for i in range(len(cost)):
                cost_list[i].append(cost[i])
    
    cost_mean = []
    for i in range(len(cost_list)):
        temp_mean = statistics.mean(cost_list[i])
        if i >= 1:
            improvement.append("{:.0%}".format(temp_mean / cost_mean[-1]))
        cost_mean.append(temp_mean)
    
    #plot_summary_2(time_list, cost_list)
    #print(cost_mean, improvement)
    return cost_mean, improvement

def plot_summary_2(x_list, y_list):

    for i in range(len(x_list)):
        plt.plot(x_list[i], y_list[i])

    # Add some text for labels, title and custom x-axis tick labels, etc.
    plt.ylabel('optimal sum cost')
    plt.title('RRT performance')

    plt.show()

def summary_3(start, goal, boundary, boundary_poly, obstacle_array, habitats, shark_dict, test_num, plan_time, plot_interval):
    '''draw average cost of optimal path from different weight schemes as a function of time'''
    results = []
    improvements = []
    time_list = [plot_interval + i * plot_interval for i in range(math.ceil(plan_time//plot_interval))]

    weight1 = [[1, -3, -3, -3], "random time", "trajectory time stamp"]
    weight2 = [[1, -3, -3, -3], "random time", "planning time stamp"]
    weight3 = [[1, -3, -3, -3], "random (x,y)"]
    weights = [weight1, weight2, weight3]

    sharkTesting = SharkOccupancyGrid(shark_dict, 20, boundary_poly, 5, 50)
    sharkGrid = sharkTesting.convert()
    
    for weight in weights:
        result, improvement = summary_2(start, goal, obstacle_array, boundary, habitats, shark_dict, sharkGrid, test_num, plan_time, plot_interval, weight)
        results.append(result)
        improvements.append(improvement)

    plt.figure(1)
    for i in range(len(results)):
        plt.plot(time_list, results[i], label=str(weights[i]))
    plt.ylabel('Optimal Path Cost')
    plt.xlabel('Planning Time')
    plt.title('Optimal Path Cost VS Planning Time')
    plt.legend()
    plt.show()
    plt.close()

    # plt.figure(2)
    # for i in range(len(improvements)):
    #     print(time_list[1:], improvements[i])
    #     plt.plot(time_list[1:], improvements[i], label=str(weights[i]))
    # plt.ylabel('Proportion Cost Optimization')
    # plt.xlabel('Planning Time')
    # plt.title('Percent Optimization over Planning Time')
    # plt.legend()
    # plt.show()
    # plt.close()

def plot_time_stamp(start, goal, boundary, obstacle_array, habitats):
    '''draw time stamp distribution of one rrt_rubins path planning algorithm'''
    rrt = RRT(start, goal, boundary, obstacle_array, habitats)
    result = rrt.exploring(habitats, 0.5, 5, 1, max_plan_time=10.0, weights=[1,-4.5,-4.5])
    time_stamp_list = result["time stamp"]
    bin_list = time_stamp_list.keys()
    num_time_list = []
    for time_bin in bin_list:
        num_time_list.append(len(time_stamp_list[time_bin]))
    
    plt.title("time stamp distribution")
    plt.xlabel("time stamp bin")
    plt.ylabel("number of motion_plan_states")
    #plt.xticks(self.bin_list)
    plt.bar(bin_list, num_time_list, color="g")
    
    plt.show()

#initialize start, goal, obstacle, boundary, habitats for path planning
start = catalina.create_cartesian(catalina.START, catalina.ORIGIN_BOUND)
start = Motion_plan_state(start[0], start[1])

goal = catalina.create_cartesian(catalina.GOAL, catalina.ORIGIN_BOUND)
goal = Motion_plan_state(goal[0], goal[1])


obstacles = []
for ob in catalina.OBSTACLES:
    pos = catalina.create_cartesian((ob.x, ob.y), catalina.ORIGIN_BOUND)
    obstacles.append(Motion_plan_state(pos[0], pos[1], size=ob.size))
        
boundary = []
boundary_poly = []
for b in catalina.BOUNDARIES:
    pos = catalina.create_cartesian((b.x, b.y), catalina.ORIGIN_BOUND)
    boundary.append(Motion_plan_state(pos[0], pos[1]))
    boundary_poly.append((pos[0],pos[1]))
boundary_poly = Polygon(boundary_poly)
        
boat_list = []
for boat in catalina.BOATS:
    pos = catalina.create_cartesian((boat.x, boat.y), catalina.ORIGIN_BOUND)
    boat_list.append(Motion_plan_state(pos[0], pos[1], size=boat.size))
        
#testing data for habitats
habitats = []
for habitat in catalina.HABITATS:
    pos = catalina.create_cartesian((habitat.x, habitat.y), catalina.ORIGIN_BOUND)
    habitats.append(Motion_plan_state(pos[0], pos[1], size=habitat.size))
        
#testing data for shark trajectories
shark_dict = {1: [Motion_plan_state(-102 + (0.1 * i), -91 + (0.1 * i), traj_time_stamp=i) for i in range(1,501)], 
    2: [Motion_plan_state(-150 - (0.1 * i), 0 + (0.1 * i), traj_time_stamp=i) for i in range(1,501)]}
summary_3(start, goal, boundary, boundary_poly, obstacles+boat_list, habitats, shark_dict, 10, 15, 0.5)