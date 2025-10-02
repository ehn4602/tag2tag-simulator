import numpy as np

import scipy.spatial.distance as dist
from scipy.constants import c, e, pi

from physics import PhysicsEngine
from typing import TYPE_CHECKING, Iterable
from tags.tag import TagMode
from manager.tag_manager import TagManager

if TYPE_CHECKING:
    from tags.tag import Exciter, PhysicsObject, Tag

class feedback_loop:
    def __init__(self, tag_manager: TagManager, physics: PhysicsEngine):
        self.tag_manager = tag_manager
        self.physics = physics
        
    def channel_matrix(self, tag_ids: list[str]):
        """
        Generate a random channel gain matrix for a given number of tags.
        
        Parameters:
        tag_ids (list[str]): List of tag IDs to include in the channel matrix.
        
        Returns:
        channel matrix (np.ndarray): A 2D numpy array representing the channel gain matrix to simulate feedback loops

        """
        num_tags = len(tag_ids)

        H = np.zeros((num_tags, num_tags))
        for i in range(num_tags):
            for j in range(num_tags):
                if i != j:
                    tag_i: Tag = self.tag_manager.get_tag(tag_ids[i]) #receiver
                    tag_j: Tag = self.tag_manager.get_tag(tag_ids[j]) #transmitter
                    # Physics functions using the tags
                    atten = self.physics.attenuation(dist.euclidean(tag_j.get_position(), tag_i.get_position()), tag_j, tag_i)
                    reflection_coef = self.physics.reflection_coefficient(tag_j)
                    H[i, j] = atten * reflection_coef # calculates effective channel gain: 
                else:
                    H[i, j] = 0  # No self-interference
        return H
    
