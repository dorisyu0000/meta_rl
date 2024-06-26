# Meta-RL 
Meta Learning: Meta-learning, also known as "learning to learn," refers to a subfield of machine learning in which an artificial intelligence system is trained to improve its ability to learn and adapt to new tasks or environments. The key idea behind meta-learning is to leverage experience from previous learning tasks to acquire knowledge or skills that can be applied to new, unseen tasks more efficiently.

<p align="center">
  <!-- <img src="images/meta_rl.png" width="350"> -->
  <img src="./images/meta_rl.png" width="100%"> 
  <i>Meta RL Architacture(Botvinick, et al. 2019).</i>
</p>

Usually the train and test tasks are different but drawn from the same family of problems; i.e., experiments in the papers included multi-armed bandit with different reward probabilities, mazes with different layouts, same robots but with different physical parameters in simulator, and many others.


## Introduction 
In this repo, I will investigate whether meta-reinforcement learning agents has a hippocampal-like mechanisms for retrieving long-term memories during decision-making. Specifically, I train a series of meta-reinforcement learning agents on a four-arm bandit task. Then I will examine the agents' behavior to determine if they exhibit patterns previously suggested as indicative of episodic-like sampling, a process akin to the retrieval of episodic memories in the human hippocampus. However, my findings suggest that the observed behaviors can be better attributed to the agents' flexible use of working memory, rather than episodic-like retrieval from long-term memory stores. Ultimately, I find no compelling evidence supporting the involvement of hippocampal-like mechanisms for episodic memory retrieval in the decision-making processes of these meta-reinforcement learning agents.
<p align="center">
  <!-- <img src="images/bandit.png" width="350"> -->
  <img src="./images/bandit.png" width="100%"> 
  <i>Bandits and the Harlow Task(Botvinick, et al. 2019).</i>
</p>

## Research Papers 

- Wang, J.X., Kurth-Nelson, Z., Kumaran, D. et al. Prefrontal cortex as a meta-reinforcement learning system. Nat Neurosci 21, 860–868 (2018). https://doi.org/10.1038/s41593-018-0147-8

- Botvinick, M., Ritter, S., Wang, J. X., Kurth-Nelson, Z., Blundell, C., Hassabis, D. (2019). Reinforcement Learning, Fast and Slow. Trends in Cognitive Sciences. https://doi.org/10.1016/j.tics.2019.02.006

- Bornstein AM, Norman KA. Reinstated episodic context guides sampling-based decisions for reward. Nat Neurosci. 2017 Jul;20(7):997-1003. doi: 10.1038/nn.4573. 

## Dependencies
Python 3.7+ 

Ensure you have the required dependencies:
```
pip install requirements.txt 
```

## Code Structure Overview

- `enviorment` conatain enviorment class:  Gym environment representing a multi-armed bandit 
- `model` TD learning model 
- `modules` LSTMs with 128 units
- `A2C` Advantage Actor-Critic
- `trianing` trian the model with A2C policy gradiant

## Result 

I have incorporated a [notebook](analyses.ipynb) to show all the results and analysis. 
