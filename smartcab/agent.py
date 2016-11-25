import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator
import numpy as np
import matplotlib.pyplot as plt



class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env, alpha, gamma, epsilon):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.actions = (None, 'forward', 'left', 'right')
        self.state = None
        self.old_state = None
        #A (3*2^4)x4 matrix that represents states and possible actions.
        #Each value in that state row and action column represents the Q(S, A)
        self.Q = [[0]*4 for _ in  range((2**13))] 
        self.alpha = 0.5 if alpha is None else alpha #The learning rate
        self.gamma = 0.5 if gamma is None else gamma #The utility factor
        self.epsilon = 0.05 if epsilon is None else epsilon #The random action in policy rate
        self.success_tracker = [] #keeping track of success
        self.reached_last = False #keeping treack if last trial reached the target

    def reset(self, destination=None):
        self.planner.route_to(destination)
        #Prepare for a new trip; reset any variables here, if required
        # if self.reached_last:
        #     self.success_tracker.append(1.0)
        # else:
        #     self.success_tracker.append(0.0)
        temp = self.reached_last
        self.reached_last = False
        return temp

    def params(self):
        return self.alpha, self.gamma, self.epsilon

    #Translates a state to a number to access an array index
    #possible values are from 0 to 15
    def state_to_num(self, state):
        count = 0
        if state['oncoming'] == None:
            count += 2**0
        elif state['oncoming'] == 'left':
            count += 2**1
        elif state['oncoming'] == 'right':
            count += 2**2
        elif state['oncoming'] == 'forward':
            count += 2**3
        if state['left'] == None:
            count += 2**4
        elif state['left'] == 'left':
            count += 2**5
        elif state['left'] == 'right':
            count += 2**6
        elif state['left'] == 'forward':
            count += 2**7
        if state['light'] == 'green':
            count += 2**8
        else:
            count += 2**9
        if state['waypoint'] == 'left':
            count += 2**10
        if state['waypoint'] == 'right':
            count += 2**11
        if state['waypoint'] == 'forward':
            count += 2**12
        return count

    #convers from action to number to allow for array indexing
    def action_to_num(self, action):
        if action is None:
            return 0
        elif action == "forward":
            return 1
        elif action == "left":
            return 2
        elif action == "right":
            return 3
        else:
            assert False

    #convers from number to action, allowing to convert from array index to action
    def num_to_action(self, num):
        if num == 0:
            return None
        if num == 1:
            return 'forward'
        if num == 2:
            return 'left'
        if num == 3:
            return 'right'
        assert False

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # Update state
        self.old_state = self.state
        self.state = {'waypoint': self.next_waypoint, 'oncoming': inputs['oncoming'], 'light': inputs['light'], 'right':inputs['right'], 'left':inputs['left']}

        # Select action according to your policy
        if random.random() < (1-self.epsilon):
            #choose optimal path action so far
            state_num = self.state_to_num(self.state)
            m = max(self.Q[state_num][:])
            index = self.Q[state_num].index(m)
            action = self.num_to_action(index)
        else:
            #choose random next action to follow
            action = random.choice(self.actions)


        # Execute action and get reward
        reward, done = self.env.act(self, action)
        if done and reward==12:
            self.reached_last = True
        stateNum = self.state_to_num(self.state)

        # Learn policy based on state, action, reward
        # Q = alpha*(reward + gamma*max()) + (1-alpha)*Q
        if self.old_state != None:
            old_s_n = self.state_to_num(self.old_state)
            maxOldState=max(self.Q[old_s_n][:])
        else:
            maxOldState = 0.5
        oldQ = self.Q[stateNum][self.action_to_num(action)]
        self.Q[stateNum][self.action_to_num(action)] = self.alpha*(reward + self.gamma*maxOldState) + (1-self.alpha)*oldQ
        # print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]
        # if t % 100 == 0:
        #     print("Q: ", np.array(self.Q))


def plot_results(results):
    #first process the data
    for params, record in results.iteritems():
        n = len(record)
        alpha, gamma, epsilon = params

        #calculate the cumulative success in the last 10 runs
        temp_results= []
        for i in np.arange(9, len(record)):
            temp_results.append(sum(record[i-9:i+1])/10.0)
        results[params] = temp_results

        #plot the results of this simulation run given the parameters
        plt.figure()
        legend = "alpha: {}, gamma: {}, epsilon: {}".format(alpha, gamma, epsilon)
        # print("numbers to compare: ", len(temp_results), len(list(range(1, n-8))))
        plt.plot(list(range(1, n-8)), temp_results)
        plt.legend('upper left', labels=[legend])
        plt.xlabel("Trials")
        plt.ylabel("Success rate on the past 10 trials")
        # plt.show()
        plt.savefig("images/plot"+str(alpha)+str(gamma)+str(epsilon)+".jpg")
    print(results)


def run():
    import numpy as np
    import matplotlib.pyplot as plt

    #test the simulation with a range of parameters
    results = {}
    for epsilon in np.arange(0.1,0.5,0.2):
        for gamma in np.arange(0.0,1.0, 0.3):
            for alpha in np.arange(0.0, 1.0, 0.3):  
                """Run the agent for a finite number of trials."""

                # Set up environment and agent
                e = Environment()  # create environment (also adds some dummy traffic)
                a = e.create_agent(LearningAgent, alpha, gamma, epsilon)  # create agent
                e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
                # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

                # Now simulate it
                sim = Simulator(e, update_delay=0.0, display=False)  # create simulator (uses pygame when display=True, if available)
                # NOTE: To speed up simulation, reduce update_delay and/or set display=False

                sim.run(n_trials=100)  # run for a specified number of trials
                # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line
                (alpha, gamma, epsilon), res = sim.get_results()
                results[(alpha, gamma, epsilon)] = res
    plot_results(results)



if __name__ == '__main__':
    run()
