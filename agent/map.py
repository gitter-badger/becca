
import utils as ut
import viz_utils

import itertools
import numpy as np

class Map(object):
    """ The object responsible for feature extraction. 
    This includes assembling inputs of various types, determining their co-activity, creating features,
    and using the feature map at each time step to translate the input into feature activity.
    """
    
    def __init__(self, num_transitions, max_feature_outputs, name='map_name'):

        self.name = name
        self.num_transitions = num_transitions
        self.max_feature_outputs = max_feature_outputs
        self.num_features = 0
        
        """ Once a co-activity value exceeds this value, nucleate a new feature """ 
        #self.NEW_FEATURE_THRESHOLD = 0.1            # real,  x >= 0
        self.NEW_FEATURE_THRESHOLD = 0.0003            # real,  x >= 0
        
        """ If the minimum co-activity between each of the elements of a growing feature 
        and the next candidates is lower than this value, don't add any more. 
        """
        self.MIN_SIG_COACTIVITY =  0.3 * self.NEW_FEATURE_THRESHOLD # real,  0 < x <= 1.0
        self.PLASTICITY_UPDATE_RATE = 0.01 * self.NEW_FEATURE_THRESHOLD # real, 0 < x < 1, small
        #self.PLASTICITY_UPDATE_RATE = 0.1 * self.NEW_FEATURE_THRESHOLD # real, 0 < x < 1, small
        
        """ Determines how much an input's contribution to exciting features
        dissipates its contribution to the co-activity estimate.
        """
        self.DISSIPATION_FACTOR = 0.3               # real, 0 < x 
                
        """ The exponent used in dividing inputs' energy between the features that they activate """
        self.ACTIVATION_WEIGHTING_EXPONENT = 10     # real, 1 < x 
                
        self.features_full = False        
        self.previous_input = np.zeros((self.num_transitions, 1))
        self.feature_activity = np.zeros((self.max_feature_outputs, 1))
        self.feature_map = np.zeros((self.max_feature_outputs, self.num_transitions))
        self.coactivity = np.zeros((self.num_transitions, self.num_transitions))
        self.combination = np.ones(self.coactivity.shape) - np.eye(self.coactivity.shape[0])
                           

    def update(self, new_input):
        """ Make a first pass at the feature activation levels by multiplying across the feature map """
        initial_feature_activities = np.dot(self.feature_map, new_input)

        """ Find the activity levels of the features contributed to by each input """
        feature_contribution_map = np.zeros(self.feature_map.shape)
        feature_contribution_map[np.nonzero(self.feature_map)] = 1.
        activated_feature_map = initial_feature_activities * feature_contribution_map
        
        """ Find the largest feature activity that each input contributes to """
        max_activation = np.max(activated_feature_map, axis=0) + ut.EPSILON

        """ Divide the energy that each input contributes to each feature """
        input_inhibition_map = np.power(activated_feature_map / max_activation, 
                                        self.ACTIVATION_WEIGHTING_EXPONENT)

        """ Find the effective strength of each input to each feature after inhibition """
        inhibited_inputs = input_inhibition_map * new_input.transpose()
        self.feature_activity = np.sum( self.feature_map * inhibited_inputs, axis=1)[:,np.newaxis]

        """ Calculate how much energy each input has left to contribute to the co-activity estimate """
        final_activated_feature_map = self.feature_activity * feature_contribution_map
        combined_weights = np.sum(final_activated_feature_map, axis=0) + ut.EPSILON
        coactivity_inputs = new_input * 2 ** (-combined_weights[:, np.newaxis] * self.DISSIPATION_FACTOR)
        
        """ As appropriate, update the co-activity estimate and create new features """                 
        # debug
        #if np.random.random_sample() < 1.:
            #print 'ni', new_input[np.nonzero(new_input)].ravel()
            #print 'fa', self.feature_activity[np.nonzero(self.feature_activity)].ravel()
            #print 'ci', coactivity_inputs[np.nonzero(coactivity_inputs)].ravel()
        if not self.features_full:
            self.update_coactivity_matrix(coactivity_inputs)
            self.create_new_features()
        
        return self.feature_activity[:self.num_features,:]


    def update_coactivity_matrix(self, new_input):
        """ Update an estimate of co-activity between every feature and every other feature """
        instant_coactivity = np.dot(new_input, new_input.transpose())
        
        """ Determine the upper bound on the size of the incremental step toward the instant co-activity """
        delta_coactivity = np.tile(new_input.transpose(), (new_input.size, 1)) * \
                                (instant_coactivity - self.coactivity)
                     
        """ Adapt co-activity toward instant co-activity by the calculated step size at the prescibed rate """
        self.coactivity += self.PLASTICITY_UPDATE_RATE * delta_coactivity
        return
    
    
    def create_new_features(self):
        """ If the right conditions have been reached, create a new feature """    
        mutual_coactivity = np.minimum(self.coactivity, self.coactivity.T)
        """ Make sure that disallowed combinations are not used to nucleate new features """
        mutual_coactivity_nuclei = mutual_coactivity * self.combination * self.combination.T
        max_coactivity = np.max(mutual_coactivity_nuclei)
        #if np.random.random_sample() <1.:
        #    print 'max_coactivity', max_coactivity        
        if max_coactivity > self.NEW_FEATURE_THRESHOLD:
            
            """ Nucleate a new feature under the two elements for which co-activity is a maximum """
            indices1, indices2 = (mutual_coactivity_nuclei == max_coactivity).nonzero()
            which_index = np.random.random_integers(0, len(indices1)-1)
            index1 = indices1[which_index]
            index2 = indices2[which_index]
            added_feature_indices = [index1, index2]
            for element in itertools.product(added_feature_indices, added_feature_indices):
                mutual_coactivity[element] = 0
            
            """ Add elements one at a time in a greedy fashion """
            coactivity_threshold = self.MIN_SIG_COACTIVITY
            while True:
                candidate_match_strength = np.min(mutual_coactivity[:,added_feature_indices], axis=1)
                
                """ Find the next most co-active feature """ 
                if (np.max(candidate_match_strength) <= coactivity_threshold):
                    break
                max_match_strength = np.max(candidate_match_strength)
                max_match_strength_indices = (candidate_match_strength == max_match_strength).nonzero()[0]
                index = max_match_strength_indices[np.random.random_integers(0, 
                                                    len(max_match_strength_indices)-1)]
                added_feature_indices.append(index)
                for element in itertools.product(added_feature_indices, added_feature_indices):
                    mutual_coactivity[element] = 0

            """ Add the new feature to the feature map """
            self.feature_map[self.num_features, added_feature_indices] = \
                                1. / np.float(len(added_feature_indices))  
            self.num_features += 1
            self.disallow_generation_crossing(added_feature_indices)
            
            #debug
            if True:
                print 'adding feature', self.num_features - 1, 'consiting of transitions:'
                num_features_lo = np.sqrt(self.num_transitions)
                for index in added_feature_indices:
                    index_cause = np.floor(index / num_features_lo)
                    index_effect = np.mod(index, num_features_lo)
                    print '           cause', index_cause, '  effect', index_effect
            
            if self.num_features >= self.max_feature_outputs:
                self.features_full = True
                print('==Max number of features reached (' + str(self.max_feature_outputs) + ')==') 
        return 

          
    def disallow_generation_crossing(self, added_feature_indices):
        """ Find the elements that cannot be grouped with the parents of the feature """
        new_index = self.num_features - 1
        
        """ Adopt the disallowed combinations of all parents """
        for element in added_feature_indices:
            self.combination[new_index,:] = np.minimum( 
                self.combination[new_index,:], self.combination[element,:])
            
        """ Disallow combinations with any of the parents too """
        self.combination[new_index,added_feature_indices] = 0
            
        """ Disallow combinations between the parents """
        for element in itertools.product(added_feature_indices, added_feature_indices):
            self.combination[element] = 0
        return 
        
        
    def get_transition_goals(self, goal_input):
        """ Multiply the feature goals across the transitions that contribute to them, 
        and perform a bounded sum over all features to get the goal associated with each
        transition.
        """
        if goal_input.size > 0:
            goal_input = ut.pad(goal_input, (self.max_feature_outputs, 0))
            return ut.bounded_sum(self.feature_map * goal_input, axis=0)
        else:
            return np.zeros((self.num_transitions, 1))
        
    def get_projection(self, feature_index):
        feature = np.zeros((self.max_feature_outputs, 1))
        feature[feature_index, 0] = 1.
        projection = np.sign(np.max(self.feature_map * feature, axis=0))[np.newaxis, :]
        return projection
        
    def visualize(self, save_eps=False):
        mutual_coactivity = np.minimum(self.coactivity, self.coactivity.T)
        viz_utils.visualize_array(mutual_coactivity, label=self.name + '_coactivity', save_eps=save_eps)
        viz_utils.visualize_array(self.feature_map, label=self.name + '_feature_map')
        coverage = np.reshape(np.sum(self.feature_map, axis=0), (int(np.sqrt(self.feature_map.shape[1])), -1))
        viz_utils.visualize_array(coverage, label=self.name + '_feature_map_coverage')
        #goals = np.reshape(ut.bounded_sum(self.feature_map * self.goal_input, axis=0), (int(np.sqrt(self.feature_map.shape[1])), -1))
        #viz_utils.visualize_array(goals, label=self.name + '_transition_goals')
        
        return
    
