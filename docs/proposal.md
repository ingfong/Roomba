---
layout: default
title:  Proposal
---

# {{ page.title }}

## Summary of Project
Our project’s goal is to create an AI agent that is able to gain the most points by killing animals within the allotted time limit. Each animal will be assigned a point value based upon our scoring system. The AI should know based on the information provided the optimal path to take in order to obtain the highest score. 

For the input, we will give the AI agent the world boundaries through a grid system as well as the AI agent’s location relative to the system. The AI will also have the knowledge of each animal’s location and point value.

We anticipate using reinforcement learning in order to have our AI agent find the most optimal path to maximize points from killing animals along the way.

## AI/ML Algorithms 
To achieve the goal of the project, we will likely use Tabular Q-learning (reinforcement learning) to teach the AI agent to choose the optimal state. 

## Evaluation Plan
To evaluate the success of this project, we’ll look at the optimal path the AI should take. To quantitatively determine the success of our AI agent’s ability to behave correctly, we will look at the actual points accumulated in comparison to the optimal score. Over time, to improve the metric, the AI agent should look to decrease the difference in points accumulated to the optimal score. At the bare minimum, animals with a high value should be killed more often than animals with low value. Our baseline would be the AI choosing a path that is not influenced by the point value of the animals it kills along the way.

The metric will involve rewarding the AI for killing animals with positive values, but negatively punishing the AI when it kills animals with negative values. The specific reward value is based on specific groups. The end goal is to create an AI agent that will attempt to only kill animals that have positive values, target animals that have the highest value, and ignore animals with negative values. 

## Appointment with the Instructor
10/26/2021 at 3:45pm 