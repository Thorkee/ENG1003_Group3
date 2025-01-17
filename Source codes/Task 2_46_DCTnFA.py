"""

A* grid planning

author: Atsushi Sakai(@Atsushi_twi)
        Nikos Kanargias (nkana@tee.gr)

See Wikipedia article (https://en.wikipedia.org/wiki/A*_search_algorithm)

This is the simple code for path planning class

"""



import math

import matplotlib.pyplot as plt

show_animation = False

Delta_F_A = 9
Delta_T_A = 1

C_T = 5
d_T = 5
C_F = 5
d_F = 5

class AStarPlanner:

    def __init__(self, ox, oy, resolution, rr, fc_x, fc_y, tc_x, tc_y):
        """
        Initialize grid map for a star planning

        ox: x position list of Obstacles [m]
        oy: y position list of Obstacles [m]
        resolution: grid resolution [m]
        rr: robot radius[m]
        """

        self.resolution = resolution # get resolution of the grid
        self.rr = rr # robot radis
        self.min_x, self.min_y = 0, 0
        self.max_x, self.max_y = 0, 0
        self.obstacle_map = None
        self.x_width, self.y_width = 0, 0
        self.motion = self.get_motion_model() # motion model for grid search expansion
        self.calc_obstacle_map(ox, oy)

        self.fc_x = fc_x
        self.fc_y = fc_y
        self.tc_x = tc_x
        self.tc_y = tc_y
#model
        ############you could modify the setup here for different aircraft models (based on the lecture slide) ##########################
        self.C_F = C_F
        self.Delta_F = d_F
        self.C_T = C_T
        self.Delta_T = d_T
        self.C_C = 10
        
#        self.Delta_F_A = 2 # additional fuel
#        self.Delta_T_A = 5 # additional time 
        
        

        self.costPerGrid = self.C_F * self.Delta_F + self.C_T * self.Delta_T + self.C_C

#        print("PolyU-A380 cost part1-> ", self.C_F * (self.Delta_F + self.Delta_F_A) )
#        print("PolyU-A380 cost part2-> ", self.C_T * (self.Delta_T + self.Delta_T_A) )
#        print("PolyU-A380 cost part3-> ", self.C_C )

    class Node: # definition of a sinle node
        def __init__(self, x, y, cost, parent_index):
            self.x = x  # index of grid
            self.y = y  # index of grid
            self.cost = cost
            self.parent_index = parent_index

        def __str__(self):
            return str(self.x) + "," + str(self.y) + "," + str(
                self.cost) + "," + str(self.parent_index)

    def planning(self, sx, sy, gx, gy):
        """
        A star path search

        input:
            s_x: start x position [m]
            s_y: start y position [m]
            gx: goal x position [m]
            gy: goal y position [m]

        output:
            rx: x position list of the final path
            ry: y position list of the final path
        """

        start_node = self.Node(self.calc_xy_index(sx, self.min_x), # calculate the index based on given position
                               self.calc_xy_index(sy, self.min_y), 0.0, -1) # set cost zero, set parent index -1
        goal_node = self.Node(self.calc_xy_index(gx, self.min_x), # calculate the index based on given position
                              self.calc_xy_index(gy, self.min_y), 0.0, -1)

        open_set, closed_set = dict(), dict() # open_set: node not been tranversed yet. closed_set: node have been tranversed already
        open_set[self.calc_grid_index(start_node)] = start_node # node index is the grid index
        
        while 1:
            if len(open_set) == 0:
                print("Open set is empty..")
                break

            c_id = min(
                open_set,
                key=lambda o: open_set[o].cost + self.calc_heuristic(self, goal_node,
                                                                     open_set[o])) # g(n) and h(n): calculate the distance between the goal node and openset
            current = open_set[c_id]

            # show graph
            if show_animation:  # pragma: no cover
                plt.plot(self.calc_grid_position(current.x, self.min_x),
                         self.calc_grid_position(current.y, self.min_y), "xc")
                # for stopping simulation with the esc key.
                plt.gcf().canvas.mpl_connect('key_release_event',
                                             lambda event: [exit(
                                                 0) if event.key == 'escape' else None])
                if len(closed_set.keys()) % 10 == 0:
                    plt.pause(0.001)

            # reaching goal
            if current.x == goal_node.x and current.y == goal_node.y:
                print("Find goal with cost of -> ",current.cost )
                goal_node.parent_index = current.parent_index
                goal_node.cost = current.cost
                break
            
            # Remove the item from the open set
            del open_set[c_id]

            # Add it to the closed set
            closed_set[c_id] = current

            # print(len(closed_set))

            # expand_grid search grid based on motion model
            for i, _ in enumerate(self.motion): # tranverse the motion matrix
                node = self.Node(current.x + self.motion[i][0],
                                 current.y + self.motion[i][1],
                                 current.cost + self.motion[i][2] * self.costPerGrid, c_id)
                
                ## add more cost in time-consuming area
                if self.calc_grid_position(node.x, self.min_x) in self.tc_x:
                    if self.calc_grid_position(node.y, self.min_y) in self.tc_y:
                        # print("time consuming area!!")
                        node.cost = node.cost + Delta_T_A * self.motion[i][2]
                
                # add more cost in fuel-consuming area
                if self.calc_grid_position(node.x, self.min_x) in self.fc_x:
                    if self.calc_grid_position(node.y, self.min_y) in self.fc_y:
                        # print("fuel consuming area!!")
                        node.cost = node.cost + Delta_F_A * self.motion[i][2]
                    # print()
                
                n_id = self.calc_grid_index(node)

                # If the node is not safe, do nothing
                if not self.verify_node(node):
                    continue

                if n_id in closed_set:
                    continue

                if n_id not in open_set:
                    open_set[n_id] = node  # discovered a new node
                else:
                    if open_set[n_id].cost > node.cost:
                        # This path is the best until now. record it
                        open_set[n_id] = node

        rx, ry = self.calc_final_path(goal_node, closed_set)
        # print(len(closed_set))
        # print(len(open_set))

        return rx, ry, current.cost

    def calc_final_path(self, goal_node, closed_set):
        # generate final course
        rx, ry = [self.calc_grid_position(goal_node.x, self.min_x)], [
            self.calc_grid_position(goal_node.y, self.min_y)] # save the goal node as the first point
        parent_index = goal_node.parent_index
        while parent_index != -1:
            n = closed_set[parent_index]
            rx.append(self.calc_grid_position(n.x, self.min_x))
            ry.append(self.calc_grid_position(n.y, self.min_y))
            parent_index = n.parent_index

        return rx, ry

    @staticmethod
    def calc_heuristic(self, n1, n2):
        w = 1.0  # weight of heuristic
        d = w * math.hypot(n1.x - n2.x, n1.y - n2.y)
        d = d * self.costPerGrid
        return d
    
    def calc_heuristic_maldis(n1, n2):
        w = 1.0  # weight of heuristic
        dx = w * math.abs(n1.x - n2.x)
        dy = w *math.abs(n1.y - n2.y)
        return dx + dy

    def calc_grid_position(self, index, min_position):
        """
        calc grid position

        :param index:
        :param min_position:
        :return:
        """
        pos = index * self.resolution + min_position
        return pos

    def calc_xy_index(self, position, min_pos):
        return round((position - min_pos) / self.resolution)

    def calc_grid_index(self, node):
        return (node.y - self.min_y) * self.x_width + (node.x - self.min_x) 

    def verify_node(self, node):
        px = self.calc_grid_position(node.x, self.min_x)
        py = self.calc_grid_position(node.y, self.min_y)

        if px < self.min_x:
            return False
        elif py < self.min_y:
            return False
        elif px >= self.max_x:
            return False
        elif py >= self.max_y:
            return False

        # collision check
        if self.obstacle_map[node.x][node.y]:
            return False

        return True

    def calc_obstacle_map(self, ox, oy):

        self.min_x = round(min(ox))
        self.min_y = round(min(oy))
        self.max_x = round(max(ox))
        self.max_y = round(max(oy))
#        print("min_x:", self.min_x)
#        print("min_y:", self.min_y)
#        print("max_x:", self.max_x)
#        print("max_y:", self.max_y)

        self.x_width = round((self.max_x - self.min_x) / self.resolution)
        self.y_width = round((self.max_y - self.min_y) / self.resolution)
#        print("x_width:", self.x_width)
#        print("y_width:", self.y_width)

        # obstacle map generation
        self.obstacle_map = [[False for _ in range(self.y_width)]
                             for _ in range(self.x_width)] # allocate memory
        for ix in range(self.x_width):
            x = self.calc_grid_position(ix, self.min_x) # grid position calculation (x,y)
            for iy in range(self.y_width):
                y = self.calc_grid_position(iy, self.min_y)
                for iox, ioy in zip(ox, oy): # Python’s zip() function creates an iterator that will aggregate elements from two or more iterables. 
                    d = math.hypot(iox - x, ioy - y) # The math. hypot() method finds the Euclidean norm
                    if d <= self.rr:
                        self.obstacle_map[ix][iy] = True # the griid is is occupied by the obstacle
                        break
#motion
    @staticmethod
    def get_motion_model(): # the cost of the surrounding 8 points
        # dx, dy, cost
        motion = [[1, 0, 1],
                  [0, 1, 1],
                  [-1, 0, 1],
                  [0, -1, 1],
                  [-1, -1, math.sqrt(2)],
                  [-1, 1, math.sqrt(2)],
                  [1, -1, math.sqrt(2)],
                  [1, 1, math.sqrt(2)]]

        return motion



def Find_TnF():

    global C_T
    global d_T
    global C_F
    global d_F
    cost_list = []
    min_cost_temp = 65565

    for i in range(1, 10):
        for j in range(1, 10):
            if(i * j + (10 - i) * (10 - j) < min_cost_temp and i * j + (10 - i) * (10 - j) >= 25):
                min_cost_temp, C_T, d_T, C_F, d_F = i * j + (10 - i) * (10 - j), i, j, 10 - i, 10 - j
    
    print("The Min-Cost Parameters:")
    print("C_T:", C_T)
    print("d_T:", d_T)
    print("C_F:", C_F)
    print("d_F:", d_F)

    return 0





#---------------------------------------------------------------------main---------------------------------------------------------------

def main():
    print(__file__ + " start the A star algorithm demo !!") # print simple notes

    # start and goal position
    sx = 0.0  # [m]
    sy = 50.0  # [m]
    gx = 50.0  # [m]
    gy = -5.0  # [m]
    grid_size = 1  # [m]
    robot_radius = 1.0  # [m]

    # set obstacle positions for group 8
    # ox, oy = [], []
    # for i in range(-10, 60): # draw the button border 
    #     ox.append(i)
    #     oy.append(-10.0)
    # for i in range(-10, 60):
    #     ox.append(60.0)
    #     oy.append(i)
    # for i in range(-10, 61):
    #     ox.append(i)
    #     oy.append(60.0)
    # for i in range(-10, 61):
    #     ox.append(-10.0)
    #     oy.append(i)
    # for i in range(-10, 40):
    #     ox.append(20.0)
    #     oy.append(i)
    # for i in range(0, 40):
    #     ox.append(40.0)
    #     oy.append(60.0 - i)


    # set fuel consuming area
    fc_x, fc_y = [], []
    for i in range(-10, 10):
        for j in range(20, 30):
            fc_x.append(i)
            fc_y.append(j)
    
    # set time consuming area
    tc_x, tc_y = [], []
    for i in range(25, 40):
        for j in range(-10, 10):
            tc_x.append(i)
            tc_y.append(j)

    # set obstacle positions for group 3
    ox, oy = [], []
    for i in range(-10, 61): # draw the button border 
        ox.append(i)
        oy.append(-10.0)
    for i in range(-10, 61): # draw the right border
        ox.append(60.0)
        oy.append(i)
    for i in range(-10, 61): # draw the top border
        ox.append(i)
        oy.append(60.0)
    for i in range(-10, 61): # draw the left border
        ox.append(-10.0)
        oy.append(i)

#Start_draw boarder
    for i in range(0, 41): # draw the free border
        ox.append(i)
        oy.append(20.0 + i)

    for i in range(-10, 31):
        ox.append(25)
        oy.append(i)

    for i in range(0, 51):
        ox.append(40)
        oy.append(i)

#End_draw boarder    

    # for i in range(40, 45): # draw the button border 
    #     ox.append(i)
    #     oy.append(30.0)

    global C_T
    global d_T
    global C_F
    global d_F
    
    global Delta_F_A
    global Delta_T_A
#    global show_animation
    Delta_F_A = 9
    Delta_T_A = 1
    cost = []
    min_cost = 3.4E38
    cost_temp = 0.0
    show_animation = False

    Find_TnF()

    route_compare = []
    while(True):
        print("Time Cost Area:", Delta_T_A)
        print("Fuel Cost Area:", Delta_F_A)

        if show_animation:  # pragma: no cover
            plt.plot(ox, oy, ".k") # plot the obstacle
            plt.plot(sx, sy, "og") # plot the start position 
            plt.plot(gx, gy, "xb") # plot the end position
            
            plt.plot(fc_x, fc_y, "oy", alpha=0.5) # plot the fuel consuming area
            plt.plot(tc_x, tc_y, "or", alpha=0.3) # plot the time consuming area

            plt.grid(True) # plot the grid to the plot panel
            plt.axis("equal") # set the same resolution for x and y axis 

        a_star = AStarPlanner(ox, oy, grid_size, robot_radius, fc_x, fc_y, tc_x, tc_y)
        rx, ry, cost_temp = a_star.planning(sx, sy, gx, gy)
        cost.append(cost_temp)
        Delta_T_A += 1
        Delta_F_A = 10 - Delta_T_A
        if(not show_animation):
            rx.clear()
            ry.clear()

        if show_animation:  # pragma: no cover
            C_T = 2
            d_T = 5
            C_F = 1
            d_F = 1
            Delta_F_A = 0.2
            Delta_T_A = 0.2
            a_star = AStarPlanner(ox, oy, grid_size, robot_radius, fc_x, fc_y, tc_x, tc_y)
            rx_og, ry_og, cost_temp = a_star.planning(sx, sy, gx, gy)
            plt.plot(rx, ry, "-g", linewidth = 1, label = "Minimum Cost Route") # show the route 
            plt.plot(rx_og, ry_og, color = "gray", linewidth = 1, alpha = 0.7, label = "Origin Route (Task1 A380)") # show the origin route 
            plt.legend(loc='upper left', bbox_to_anchor=(0.0, 1))
            plt.pause(0.001) # pause 0.001 seconds
            plt.show() # show the plot

            break
        
        if(Delta_F_A == 0):
            for i in range(1, 10):
                if(cost[i - 1] < min_cost):
                    min_cost, Delta_T_A , Delta_F_A = cost[i - 1], i, 10 - i
            
            print("-------------------The Minimum Cost---------------------------")
            print("C_T:", C_T)
            print("d_T:", d_T)
            print("C_F:", C_F)
            print("d_F:", d_F)

            show_animation = True
    
    return 0




if __name__ == '__main__':
    main()
