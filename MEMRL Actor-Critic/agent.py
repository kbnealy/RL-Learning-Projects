from network import GenericNetwork
import torch as T
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from networks import ActorNetwork, CriticNetwork, ValueNetwork
from memory import EpisodicMemory

class Agent():
    def __init__(self, input_dims, alpha=0.0003, beta=0.0003, gamma=0.99, l1_size = 256, env=None, 
            l2_size = 256, n_actions = 3, max_size=1000000, reward_scale=2, batch_size=256): #alpha/beta = agent/critic lrs
        self.gamma = gamma
        self.memory = EpisodicMemory(max_size, input_dims, n_actions)
        self.batch_size = batch_size
        self.n_actions = n_actions

        # create networks
        self.actor = ActorNetwork(alpha, input_dims, n_actions=n_actions, max_action=env.action_space.high)
        self.critic = CriticNetwork(beta, input_dims, n_actions=n_actions, name='critic')
        self.value = ValueNetwork(beta, input_dims)
        self.target_value = ValueNetwork(beta, input_dims,name='target_value')

        # AC works by updating the actor network with the graident along the policy
        # the policy is just a probability distribution and we back propogate the log of that 
        # distribution through the actor network for loss minimization the actor network
        self.log_probs = None
        #create the actor critic network using our generic network 
        self.actor = GenericNetwork(alpha, input_dims, l1_size, l2_size, n_actions)
        self.critic = GenericNetwork(beta, input_dims, l1_size, l2_size, n_actions)

    def choose_action(self, observation):
        # here is where we recall previous memories. 
        episodic_mem = self.memory.recall_memory(observation)

        probabilities = F.softmax(self.actor.forward(observation))
        # we then create a distribution that is modelled on the probabilities 
        action_probs = T.distributions.Categorical(probabilities)
        # then we get the action by sampling the action probability space 
        action = action_probs.sample()
        # Now we need the log probability of our sample to perform back-prop
        self.log_probs = action_probs.log_prob(action)

        # then we want to return our action as a integer using .item() since thats what 
        # OpenAI uses (action is currently a cuda tesnor)
        return action.item()

    def encode_memory(self, episode, state, action, reward, new_state, done):
        self.memory.encode_memory(episode, state, action, reward, new_state, done)

    def state_represention(self, state):
         # pass state info through our environemnt represention Network to get the 
         # state representation 
         state_representation = F.softmax(self.env_representation.forward(state))
         # pass representation to memory to get similar state representations 
         action_probs = T.distributions.Categorical(probabilities)
         # compare the action 

    # AC method is a TD method which requires us to calculate the delta (or error)
    # between what the model predicted and what the actual outcome was
    # we need the done flag so that when we transition into the terminal state
    # there are no feature rewards so the value of the next state is identically 0
    def learn(self, state, reward, new_state, done):
        # Here is whe
        
        
        # for all pytorch programs you want to zero out the gradients for the optimizer
        # at the beginning of your learning function. we do this for both actor and critic
        self.actor.optimizer.zero_grad()
        self.critic.optimizer.zero_grad()

        # next we get the value of the state and the value of the next state
        # from our critic network 
        critic_value = self.critic.forward(state)
        critic_value_ = self.critic.forward(new_state)

        # next we calculate the TD error (i.e. delta)
        # we augment calculation with 1-int(done) so that we don't update 
        # when episode is done
        delta = ((reward + self.gamma*critic_value*(1-int(done))) - critic_value_)
        # we use delta to calculate both the actor and critic losses
        # the modifies the action probabilities in the direction that maximizes
        # future reward
        actor_loss = -self.log_probs * delta
        critic_loss = delta**2

        # we back propogate the sum of the losses through the network 
        (actor_loss + critic_loss).backward()

        # then we optimize
        self.actor.optimizer.step()
        self.critic.optimizer.step()








