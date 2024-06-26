import numpy as np
import time

import gymnasium as gym

import torch
from torch import nn
import torch.nn.functional as F
from torch.distributions import Categorical


class A2C:
    """
    An A2C trainer.
    """

    def __init__(
            self,
            net,
            env,
            lr,
            gamma,
            beta_v,
            beta_e,
            lr_schedule = None,
            entropy_schedule = None,
        ):
        """
        Initialize the trainer.
        """

        self.net = net
        self.env = env
        self.lr = lr
        self.gamma = gamma
        self.beta_v = beta_v
        self.beta_e = beta_e
        self.lr_schedule = lr_schedule
        self.entropy_schedule = entropy_schedule

        self.optimizer = torch.optim.Adam(net.parameters(), lr = self.lr)


    def get_discounted_returns(self, rewards, values):
        """
        Compute discounted reterns and advantages.
        """

        # initialize recordings
        returns = []
        advantages = []

        # compute returns and advantages from the last timestep
        R = values[-1].item()
        advantage = 0
        
        for i in reversed(range(len(rewards))):
            # get (v, r, v')
            r = rewards[i]
            v = values[i]
            v_next = values[i + 1]

            # compute return for the timestep
            R = r + R * self.gamma

            # compute advantage for the timestep
            delta = r + v_next * self.gamma - v
            advantage = advantage * self.gamma + delta

            # insert 0 for the previous timestep
            returns.insert(0, R)
            advantages.insert(0, advantage)
            
        return torch.Tensor(returns), torch.Tensor(advantages)
    

    def update_model(self, rewards, values, log_probs, entropies):
        """
        Update model parameters.
        """

        # compute returns and advantages
        returns, advantages = self.get_discounted_returns(rewards, values)

        # compute policy loss
        policy_loss = -(log_probs * advantages.detach()).sum()

        # compute value loss
        value_loss = F.mse_loss(values[:-1], returns, reduction = 'sum')

        # compute entropy loss
        entropy_loss = -entropies.sum()

        # compute loss
        loss = policy_loss + self.beta_v * value_loss + self.beta_e * entropy_loss

        # backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
        self.optimizer.step()

        return loss.item(), policy_loss.item(), value_loss.item(), entropy_loss.item()
    

    def train_one_episode(self):
        """
        Train one episode.
        """

        # initialize recordins
        actions = []
        values = []
        log_probs = []
        entropies = []
        rewards = []
        
        # initialize a trial
        done = False
        states_actor, states_critic = None, None

        obs, _ = self.env.reset()
        obs = torch.Tensor(obs).unsqueeze(dim = 0)

        # iterate through a trial
        while not done:
            # step the net
            action, policy, log_prob, entropy, value, states_actor, states_critic = self.net(obs, states_actor, states_critic)

            # step the env
            obs, reward, done, _, info = self.env.step(action.item())
            obs = torch.Tensor(obs).unsqueeze(dim = 0)

            # record results
            actions.append(action.item())
            values.append(value.view(-1))
            log_probs.append(log_prob)
            entropies.append(entropy)
            rewards.append(reward)

        # process the last timestep
        action, policy, log_prob, entropy, value, states_actor, states_critic = self.net(obs, states_actor, states_critic)
        values.append(value.view(-1)) # values have one more step

        # concatenate recordings
        values = torch.cat(values)
        log_probs = torch.cat(log_probs)
        entropies = torch.stack(entropies) # why stack here?

        # update model
        loss, policy_loss, value_loss, entropy_loss = self.update_model(rewards, values, log_probs, entropies)

        # compute the length of an epiosde
        episode_length = len(rewards)

        return loss, policy_loss, value_loss, entropy_loss, episode_length


    def evaluate_one_episode(self, deterministic = False):
        """
        Evaluate one episode.
        """

        # initialize recordings
        rewards = []

        # initialize a trial
        done = False
        states_actor, states_critic = None, None

        obs, _ = self.env.reset()
        obs = torch.Tensor(obs).unsqueeze(dim = 0)

        with torch.no_grad():
            # iterate through a trial
            while not done:
                # step the net
                action, policy, log_prob, entropy, value, states_actor, states_critic = self.net(obs, states_actor, states_critic)

                # greedy action selection
                if deterministic == True:
                    action = torch.argmax(policy)

                # step the env
                obs, reward, done, _, info = self.env.step(action.item())
                obs = torch.Tensor(obs).unsqueeze(dim = 0)

                # record results
                rewards.append(reward)

            return np.sum(rewards)
        

    def learn(self, num_episodes, print_frequency = 2):
        """
        Train the model.
        """

        # initialize recordings
        losses = {
            'loss': [],
            'policy_loss': [],
            'value_loss': [],
            'entropy_loss': [],
        }
        evaluate_rewards = []

        # train the model
        start_time = time.time()
        for episode in range(num_episodes):
            # train the model for one episode
            loss, policy_loss, value_loss, entropy_loss, episode_length = self.train_one_episode()
            
            # evaluate the model for one episode
            evaluate_reward = self.evaluate_one_episode()
        
            # record training data
            # record training data
            losses_episode = {
                'loss': loss,
                'policy_loss': policy_loss,
                'value_loss': value_loss,
                'entropy_loss': entropy_loss,
            }
            for key, item in losses.items():
                losses[key].append(losses_episode[key])
            evaluate_rewards.append(evaluate_reward)

            # print the training process
            self.print_training_process(
                ep_len_mean = episode_length,
                ep_rew_mean = evaluate_reward,
                ep_num = episode + 1,
                time_elapsed = time.time() - start_time,
                data = losses_episode,
                print_frequency = print_frequency
            )

            # update learning rate
            if self.lr_schedule is not None:
                self.update_learning_rate(episode)

            # update entropy regularization
            if self.entropy_schedule is not None:
                self.update_entropy_coef(episode)
        
        return losses, evaluate_rewards
    

    def update_learning_rate(self, episode):
        """
        Update the learning rate based on the episode number.
        """

        if episode < len(self.lr_schedule):
            self.lr = self.lr_schedule[episode]

            for param_group in self.optimizer.param_groups:
                param_group['lr'] = self.lr
    
    
    def update_entropy_coef(self, episode):
        """
        Update the entropy regularization coefficient based on the episode number.
        """

        if episode < len(self.entropy_schedule):
            self.beta_e = self.entropy_schedule[episode]


    def save_net(self, path):
        """
        Save the net.
        """
        
        torch.save(self.net, path)


    def print_training_process(self, ep_len_mean, ep_rew_mean, ep_num, time_elapsed, data, print_frequency = 2):
        """
        Print the training process.
        """

        if ep_num % print_frequency == 0:
            print("-------------------------------------------")
            print("| rollout/                |               |")
            print(f"|    ep_len_mean          | {ep_len_mean:<13} |")
            print(f"|    ep_rew_mean          | {ep_rew_mean:<13.5f} |")
            print("| time/                   |               |")
            print(f"|    ep_num               | {ep_num:<13} |")
            print(f"|    time_elapsed         | {time_elapsed:<13.4f} |")
            print("| train/                  |               |")
            print(f"|    learning_rate        | {self.lr:<13.5f} |")
            print(f"|    loss                 | {data['loss']:<13.4f} |")
            print(f"|    policy_loss          | {data['policy_loss']:<13.4f} |")
            print(f"|    value_loss           | {data['value_loss']:<13.4f} |")
            print(f"|    entropy_loss         | {data['entropy_loss']:<13.4f} |")
            print("-------------------------------------------")





if __name__ == '__main__':

    from environment import *
    from modules import *
    from model.trainer import *

    env = DriftingBandit()
    env = MetaLearningWrapper(env)

    net = RecurrentActorCriticPolicy(
        feature_dim = env.observation_space.shape[0],
        action_dim = env.action_space.n,
        policy_hidden_dim = 32,
        value_hidden_dim = 32,
        lstm_hidden_dim = 128,
    )

    a2c = A2C(
        net = net,
        env = env,
        lr = 3e-4,
        gamma = 0.9,
        beta_v = 0.5,
        beta_e = 0.05,
        # lr_schedule = np.linspace(3e-4, 1e-4, num = 30000),
    )

    losses, rewards = a2c.learn(num_episodes = 30000)

    plt.figure()
    plt.plot(np.array(rewards).reshape(500, -1).mean(axis = 1))
    plt.show()