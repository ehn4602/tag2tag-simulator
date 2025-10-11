import numpy as np

class FeedbackLoop:

    """
    Purpose:
    ----------
    Implements a simplified feedback loop for the Tag2Tag simulator.
    At each simulation tick, it computes the received signals at each tag
    based on the current transmitting tags, a channel matrix,
    exciter contribution, and noise. Then it feeds the resulting voltages
    into each tag’s processing machine to drive state transitions.
    
    Note: This version is simplified for testing the feedback loop mechanics.
    Some physics (attenuation, phase, chip reflection) are placeholders and
    marked with TODOs for future refinement.
    """

    def __init__(self, tag_manager, exciter, noise_std = 0.0):
        """
        Initialize the feedback loop.
        
        Parameters:
        - tag_manager: TagManager instance containing all tags and PhysicsEngine
        - exciter: Exciter object providing the incident field to the tags
        - noise_std: Standard deviation of Gaussian noise to add to received signals
        """
        self.tag_manager = tag_manager
        self.exciter = exciter
        self.noise_std = noise_std

    def get_tag_order(self):
        """
        Create a deterministic ordering of tags for indexing in matrices.
        Returns: tag_ids: list of tag IDs in a stable order
        """

        tag_ids = list(self.tag_manager.tags.keys())
        return tag_ids

    def build_H(self, tag_ids):
        """
        Builds a channel matrix H where H[i,j] represents the effect of transmitter j on receiver i.

        Currently SIMPLIFIED: uses a placeholder reflection coefficient (1.0) instead of computing distance,
        attenuation, phase, and chip reflection.

        Param:
        - tag_ids: list of tag IDs in a stable order

        Returns:
        - H: complex numpy array of shape (n_tags, n_tags)
        """

        n = len(tag_ids)
        H = np.zeros((n, n), dtype=complex)

        for i, rx_id in enumerate(tag_ids):
            for j, tx_id in enumerate(tag_ids):
                if i == j:
                    continue
                # -- Simplified physics
                # TODO: replace with distance-based attenuation and phase shift, gamma_j
                gamma_j = 1.0
                H[i, j] = gamma_j
        return H
    
    def compute_x(self, tag_ids):
        """
        Compute the transmitted signals vector x based on which tags are transmitting. Represents how each tag
        reflects/re-radiates the incidient field at the current tick.

        SIMPLIFIED: uses a placeholder reflection coefficient (1.0) for transmitting tags.

        Parameter:
        - tag_ids: list of tag IDs in a stable order

        Returns:
        - x: complex numpy array of length n_tags
        """
        x = np.zeros(len(tag_ids), dtype = complex)
        for j , tag_id in enumerate(tag_ids):
            tag = self.tag_manager.tags[tag_id]
            if tag.mode.is_listening():
                x[j] = 0.0
            else:
                # -- Simplified physics
                # TODO: replace with actual e_inc_j * gamma_j from PhysicsEngine
                x[j] = 1.0
        return x

    def compute_exciter_field(self, tag_ids):
        """
        Purpose:
        ----------
        Compute the exciter’s direct field contribution at each tag.
        
        Simplification:
        - Currently returns all ones; real implementation should use
          get_sig_tx_rx to calculate actual exciter field at each tag.
        
        Parameters:
        - tag_ids: ordered list of tag IDs
        
        Returns:
        - h_exciter: complex numpy array of length n_tags
        """
        h_exciter = np.ones(len(tag_ids), dtype=complex)  # placeholder
        return h_exciter
    
    def add_noise(self, y):
        """
        Add complex Gaussian noise to received phasor vector (y). Noise represents thermal/ambient nosie in real radio systems

        Parameters:
        - y: complex numpy array of length n_tags (received phasor vector)

        Returns:
        - y_noisy: complex numpy array with added noise
        """
        noise = (np.random.randn(*y.shape) + 1j * np.random.randn(*y.shape)) * (self.noise_std)
        return y + noise

    def compute_received_voltages(self, y):
        """ 
        Converts received phasors y into voltage magnitudes at each tag

        Simplification:
        - Uses abs value of phasor as voltage. Real implementation should compute RMS voltage based on tag
        impedance and power

        Parameters:
        - y: complex numpy array of length n_tags (received phasor vector)

        Returns:
        - v: numpy array of voltages at each tag
        """

        v = np.abs(y)  # placeholder
        return v
    
    def inject_to_tags(self, tag_ids, voltages):
        """
        Feeds the received voltages into each tag's processing machine to drive state machine updates
        and schedule future transmissions

        Parameters:
        - tag_ids: list of tag IDs in a stable order
        - voltages: numpy array of voltages at each tag
        """

        for i, tag_id in enumerate(tag_ids):
            tag = self.tag_manager.tags[tag_id]
            tag.tag_machine.processing_machine.on_recv_voltage(voltages[i])

    def step(self):
        """
        Perform a single tick of the feedback loop:
        1. Determine tag order
        2. Build channel matrix H
        3. Compute transmitter vector x
        4. Compute exciter field h_exciter
        5. Compute received phasors y
        6. Add noise
        7. Convert to voltages
        8. Feed voltages into tag state machines
        """
        tag_ids = self.get_tag_order()
        H = self.build_H(tag_ids)
        x = self.compute_x(tag_ids)
        h_exciter = self.compute_exciter_field(tag_ids)
        y = H @ x + h_exciter ## core propogational calculation -> H @ x (matrix vector multiplication, computing all tag to tag contribution) 
        ## + exciter contribution
        ## y - total complex phasor received at each tag i (sum of fields from all other transm tags + directed field from exciter)
        y = self.add_noise(y)
        v = self.compute_received_voltages(y)
        self.inject_to_tags(tag_ids, v)