import random
import matplotlib.pyplot as plt

# Class to represent a voter
class Voter:
    def __init__(self, id, correct_vote_probability):
        """
        id: int
            The id of the voter
        correct_vote_probability: float
            The probability of the voter voting correctly
        """
        self.id = id
        self.correct_vote_probability = correct_vote_probability
        self.weight = 1
        self.weight_history = []
        self.trustworthiness = 0.5
        self.trustworthiness_history = []
        
"""
The following code simulates the behavior of voters in a voting system. The voters are divided into three categories:
"""
no_of_voters = int(input("Enter the number of voters: "))
fraction_of_malicious_voters = float(input("Enter the fraction of malicious voters: "))
fraction_of_very_trustworthy_voters = float(input("Enter the fraction of very trustworthy voters: "))
number_of_iterations = int(input("Enter the number of iterations: "))

voters = []
no_of_malicious_voters = int(no_of_voters * fraction_of_malicious_voters)
no_of_very_trustworthy_voters = int((no_of_voters-no_of_malicious_voters) * fraction_of_very_trustworthy_voters)
no_of_normal_voters = no_of_voters - no_of_malicious_voters - no_of_very_trustworthy_voters



# Learning rates
learning_rate1 = 0.001
learning_rate2 = 0.001

# Initialize the voters
k = 0
for i in range(no_of_malicious_voters):
    voters.append(Voter(k, 0))
    k += 1
for i in range(no_of_very_trustworthy_voters):
    voters.append(Voter(k, 0.9))
    k += 1
for i in range(no_of_normal_voters):
    voters.append(Voter(k, 0.7))
    k += 1

# Simulate the voting process
for i in range(number_of_iterations):
    l = [] # List to store the votes of the voters
    for voter in voters:
        # Voter votes randomly based on the correct_vote_probability
        vote = random.choices([1,0],[voter.correct_vote_probability,1-voter.correct_vote_probability], k=1)[0]
        l.append(vote)
        voter.weight_history.append(voter.weight)
        voter.trustworthiness_history.append(voter.trustworthiness) 

    
    # Calculate the estimated vote  
    estimated_vote = 0
    for i in range(len(voters)):
        estimated_vote += voters[i].weight * l[i]
    estimated_vote = estimated_vote/sum([voter.weight for voter in voters])
    if estimated_vote < 0.5:
        estimated_vote = 0
    else:
        estimated_vote = 1
    
    # Update the trustworthiness and weight of the voters
    for i in range(len(l)):
        if l[i] == estimated_vote:
            voters[i].trustworthiness = (voters[i].trustworthiness * len(voters[i].trustworthiness_history) + 1)/(len(voters[i].trustworthiness_history) + 1)
            if voters[i].weight >= 1:
                voters[i].weight = voters[i].weight + learning_rate2*(1/voters[i].weight)
            else:
                voters[i].weight = voters[i].weight + learning_rate2*(voters[i].weight)
        else:
            voters[i].trustworthiness = (voters[i].trustworthiness * len(voters[i].trustworthiness_history))/(len(voters[i].trustworthiness_history) + 1)
            voters[i].weight = voters[i].weight - learning_rate1*voters[i].weight


# Calculate the average weights and trustworthiness of the voters
avg_weights_1 = [0]*number_of_iterations
avg_weights_2 = [0]*number_of_iterations
avg_weights_3 = [0]*number_of_iterations

avg_trustworthiness_1 = [0]*number_of_iterations
avg_trustworthiness_2 = [0]*number_of_iterations
avg_trustworthiness_3 = [0]*number_of_iterations
for i in range(number_of_iterations):
    for voter in voters:
        if voter.correct_vote_probability == 0:
            avg_weights_1[i] += voter.weight_history[i]
            avg_trustworthiness_1[i] += voter.trustworthiness_history[i]
        elif voter.correct_vote_probability == 0.9:
            avg_weights_2[i] += voter.weight_history[i]
            avg_trustworthiness_2[i] += voter.trustworthiness_history[i]
        else:
            avg_weights_3[i] += voter.weight_history[i]
            avg_trustworthiness_3[i] += voter.trustworthiness_history[i]

    avg_weights_1[i] = avg_weights_1[i]/no_of_malicious_voters
    avg_weights_2[i] = avg_weights_2[i]/no_of_very_trustworthy_voters
    avg_weights_3[i] = avg_weights_3[i]/no_of_normal_voters

    avg_trustworthiness_1[i] = avg_trustworthiness_1[i]/no_of_malicious_voters
    avg_trustworthiness_2[i] = avg_trustworthiness_2[i]/no_of_very_trustworthy_voters
    avg_trustworthiness_3[i] = avg_trustworthiness_3[i]/no_of_normal_voters

# Plot the average weights of the voters
plt.plot(range(number_of_iterations), avg_weights_1, label='Malicious Voters')
plt.plot(range(number_of_iterations), avg_weights_2, label='Very Trustworthy Voters')
plt.plot(range(number_of_iterations), avg_weights_3, label='Normal Voters')
plt.xlabel('No of articles')
plt.ylabel('Average Weights')
plt.legend()
# plt.show()
plt.savefig(f'Weight_{fraction_of_malicious_voters}_{fraction_of_very_trustworthy_voters}.png')
plt.close()

# Plot the average trustworthiness of the voters
plt.plot(range(number_of_iterations), avg_trustworthiness_1, label='Malicious Voters')
plt.plot(range(number_of_iterations), avg_trustworthiness_2, label='Very Trustworthy Voters')
plt.plot(range(number_of_iterations), avg_trustworthiness_3, label='Normal Voters')
plt.xlabel('No of articles')
plt.ylabel('Average Trustworthiness')
plt.legend()
# plt.show()
plt.savefig(f'Trustworthiness_{fraction_of_malicious_voters}_{fraction_of_very_trustworthy_voters}.png')