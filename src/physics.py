from __future__ import annotations
from math import sqrt, log10
from typing import TYPE_CHECKING, Iterable
import numpy as np

import scipy.spatial.distance as dist
from scipy.constants import c, e, pi
import random

from tags.tag import TagMode

if TYPE_CHECKING:
    from tags.tag import Exciter, PhysicsObject, Tag


def mW_to_dBm(mw: float) -> float:
    if mw <= 0:
        return -999.0
    return 10.0 * log10(mw)

def dBm_to_mW(dbm: float) -> float:
    return 10 ** (dbm / 10.0)

def dbi_to_linear(dbi: float) -> float:
    """Convert gain in dBi to linear scale."""
    return 10 ** (dbi / 10.0)


class PhysicsEngine:
    def __init__(
        self, 
        exciter: Exciter,
        default_power_on_dbm: float = -100.0,  # Typical dbm threshold for passive UHF RFID tags to turn on circuitry
        noise_std_volts: float = 0,  # 0.0001 is 0.1 mV noise
    ):
        """
        Initialize the physics engine.

        Parameters:
            exciter (Exciter): The exciter object.
            default_power_on_dbm (float): The default power threshold (in dBm) for a tag to be considered "powered".
            noise_std_volts (float): Standard deviation of Gaussian noise (in volts) added to envelope-detector output.
                                   Default is 0 (no noise).
        """
        self.exciter = exciter
        self.default_power_on_dbm = default_power_on_dbm
        self.noise_std_volts = noise_std_volts

        # Tag topology caching
        self._cached_state = {
            "tag_names": None,
            "H": None,
            "Gamma": None,
            "h_exciter": None,
            "S": None,
            "hash": None,  # unique snapshot of topology + reflection coeffs
        }

    def attenuation(
        self, distance: float, wavelength: float, tx_gain_dbi=1.0, rx_gain_dbi=1.0
    ) -> float:
        """
        Helper function for calculating the attenuation between two antennas

        Parameters:
            distance (float): Distance between the two antennas in meters.
            wavelength (float): Wavelength in meters.
            tx_gain (float): Transmitting antenna gain in dBi.
            rx_gain (float): Receiving antenna gain in dBi.
        Returns:
            float: Power ratio (unitless) between transmitted and received power.

        # TODO Add Radiating near-field model (1/d^3) for distances < wavelength/(2*pi) (NOT HIGH PRIORITY)
        """
        if distance <= 0:
            return 0.0

        tx_gain = dbi_to_linear(tx_gain_dbi)
        rx_gain = dbi_to_linear(rx_gain_dbi)

        reactive_limit = wavelength / (2 * pi)

        if distance < reactive_limit:
            # Near-field region (reactive near-field, use approximate 1/d^3 model)
            return (tx_gain * rx_gain * (wavelength ** 2)) / ((4 * pi * reactive_limit) ** 2) * (reactive_limit / distance) ** 3
        else:
            # Far-field region (Friis transmission equation, 1/d^2 model)
            num = tx_gain * rx_gain * (wavelength**2)
            den = (4 * pi * distance) ** 2
            return num / den

    def get_sig_tx_rx(self, tx: PhysicsObject, rx: Tag):
        """
        Gets the signal from a tag or exciter to another tag

        Parameters:
            tx (PhysicsObject): The transmitting object.
            rx (Tag): The receiving tag.
        Returns:
            complex: A complex phasor representing the contribution from tx -> rx.
        """
        distance = dist.euclidean(tx.get_position(), rx.get_position())
        wavelen = c / tx.get_frequency()
        att = sqrt(self.attenuation(distance, wavelen, tx.get_gain(), rx.get_gain()))
        return att * (e ** (1j * 2 * pi * distance / wavelen))
    
    def power_from_exciter_at_tag_mw(self, tag: Tag) -> float:
        """
        Gets the power (in mW) delivered from the engine's exciter to the tag antenna input using Friis transmission formula

        Parameters:
            tag (Tag): The receiving tag.
        Returns:
            float: The power (in mW) delivered to the tag.

        Assumptions:
            - exciter.get_power() returns transmit power in mW
            - gains are linear directivities (not dBi). If gain is provided in dBi, convert before using.

        # TODO Check if gains are in linear directivities or dBi(if DBI, convert to linear)
        """
        ex = self.exciter
        power_tx_mw = ex.get_power()
        if power_tx_mw <= 0:
            return 0.0
        
        distance = dist.euclidean(ex.get_position(), tag.get_position())
        wavelength = c / ex.get_frequency()

        power_rx = power_tx_mw * self.attenuation(distance, wavelength, ex.get_gain(), tag.get_gain())
        return max(power_rx, 0.0)
    
    def is_tag_powered(self, tag: Tag) -> bool:
        """
        Determines whether a tag has sufficient harvested power to run logic ("listening" capability).

        Parameters:
            tag (Tag): The tag to check.
        Returns:
            bool: True if the tag is powered, False otherwise.

        Checks for:
            - per-tag attribute `power_on_threshold_dbm` (if present)
            - otherwise uses engine.default_power_on_dbm
        """
        power_tag_mw = self.power_from_exciter_at_tag_mw(tag)
        power_tag_dbm = mW_to_dBm(power_tag_mw)
        threshold_dbm = getattr(tag, "power_on_threshold_dbm", self.default_power_on_dbm)
        return power_tag_dbm >= threshold_dbm
    
    def effective_reflection_coefficient(self, tag: Tag) -> complex:
        """
        Returns the complex reflection coefficient used when the tag is contributing to the channel.
        Rules implemented:
            - If tag is not powered -> return a very small passive reflection (near-zero complex) to represent the tag's metal scatter but not a powered, modulated reflection.
            - If tag.mode.is_listening() -> return a small unmodulated reflection (the envelope detector input typically presents an absorbing load; we model a low baseline reflection).
            - If tag is transmitting (mode != listening) -> return the reflection coefficient based on the antenna and current chip impedances.

        Parameters:
            tag (Tag): The tag to get the reflection coefficient for.
        Returns:
            complex: The effective reflection coefficient.
        """
        PASSIVE_REF_MAG = 0.01  # very small amplitude reflection  # TODO Tune this value
        PASSIVE_REF = complex(PASSIVE_REF_MAG, 0.0)

        if not self.is_tag_powered(tag) or tag.get_mode().is_listening():
            return PASSIVE_REF
        
        # Otherwise tag is actively reflecting (transmit index)
        Z_ant = tag.get_impedance()
        Z_chip = tag.get_chip_impedance()

        try:
            gamma = (Z_chip - Z_ant.conjugate()) / (Z_chip + Z_ant)
        except ZeroDivisionError:
            gamma = complex(0.0, 0.0)

        return gamma

    def _compute_state_hash(self, tags):
        """
        Compute a hash representing the current state of the tags (positions and impedances).

        Parameters:
            tags (dict[str, Tag]): A dictionary of all the tags in the simulation.
        Returns:
            int: A hash value representing the current state.
        """
        data = []
        for tag in tags.values():
            pos = tag.get_position()
            z_chip = tag.get_chip_impedance()
            z_ant = tag.get_impedance()
            data.extend([*pos, complex(z_chip), complex(z_ant)])
        return hash(tuple(round(float(x.real if isinstance(x, complex) else x), 8) for x in data))


    def voltage_at_tag(self, tags: dict[str, Tag], receiving_tag: Tag) -> float:
        """
        Get's the total voltage delivered to a given tag by the rest of the
        tags.
        # TODO Compare this to iteratively finding feedback loops(e.g. bouncing back and forth until difference is small)

        Parameters:
            tags (dict[str, Tag]): A dictionary of all the tags in the simulation.
            receiving_tag (Tag): The tag to get the voltage for.
        Returns:
            float: The voltage at the receiving tag's envelope detector input.
        """
        ex = self.exciter
        rx_impedance = receiving_tag.get_impedance()

        tag_names = list(tags.keys())
        if receiving_tag.get_name() not in tag_names:
            tag_names.append(receiving_tag.get_name())

        n = len(tag_names)
        if n == 0:
            return 0.0

        state_hash = self._compute_state_hash(tags)

        # Check if we can use cached result
        if self._cached_state["hash"] == state_hash and self._cached_state["S"] is not None and self._cached_state["tag_names"] == tag_names:
            S = self._cached_state["S"]
        else:
            # Create H matrix
            H = np.zeros((n, n), dtype=np.complex128)
            for i, name_i in enumerate(tag_names):
                tag_i = tags[name_i] if name_i in tags else receiving_tag
                for j, name_j in enumerate(tag_names):
                    if i == j:
                        continue
                    tag_j = tags[name_j] if name_j in tags else receiving_tag
                    H[i, j] = self.get_sig_tx_rx(tag_j, tag_i)

            # Create Γ
            gammas = np.zeros(n, dtype=np.complex128)
            for j, name_j in enumerate(tag_names):
                tag_j = tags[name_j] if name_j in tags else receiving_tag
                gammas[j] = self.effective_reflection_coefficient(tag_j)
            Gamma = np.diag(gammas)

            # Create h_exciter
            h_exciter = np.zeros(n, dtype=np.complex128)
            for i, name_i in enumerate(tag_names):
                tag_i = tags[name_i] if name_i in tags else receiving_tag
                h_exciter[i] = self.get_sig_tx_rx(ex, tag_i)

            # Solve S = (I - HΓ)^(-1) h_exciter 
            I = np.eye(n, dtype=np.complex128)
            A = I - H @ Gamma
            S = np.linalg.solve(A, h_exciter)

            # Cache the new state
            self._cached_state.update({
                "tag_names": tag_names,
                "H": H,
                "Gamma": Gamma,
                "h_exciter": h_exciter,
                "S": S,
                "hash": state_hash,
            })

        rx_field = S[tag_names.index(receiving_tag.get_name())]
        pwr_received = abs(rx_field)

        # Convert to voltage
        v_pk = sqrt(abs(rx_impedance * pwr_received) / 500.0)
        v_rms = v_pk / sqrt(2.0)

        # AWGN
        if self.noise_std_volts and self.noise_std_volts > 0.0:
            v_rms = max(0.0, random.gauss(v_rms, self.noise_std_volts))

        return v_rms
    
    def modulation_depth_for_tx_rx(
        self, tags: dict[str, Tag], tx: Tag, rx: Tag, tx_indices: Iterable[int] | None = None
    ) -> float:
        """
        Compute modulation depth metric for a specific (tx, rx) pair.

        Parameters:
            tags (dict[str, Tag]): A dictionary of all the tags in the simulation.
            tx (Tag): The transmitting tag.
            rx (Tag): The receiving tag.
            tx_indices (Iterable[int] | None): Optional pair of indices to use for the tx tag. If None, will use [0, 1] if possible.
        Returns:
            float: The modulation depth (absolute voltage difference) at the rx tag when tx switches between the two specified modes.
        """
        # Choose indicies if not provided (avoid listening idx=0)
        if tx_indices is None:
            num_tx = len(tx.chip_impedances)
            if num_tx >= 3:
                idx0, idx1 = 1, 2
            elif num_tx >= 2:
                idx0, idx1 = 0, 1
            else:
                idx0, idx1 = 0, 0
        else:
            idx0, idx1 = tuple(tx_indices)


        original_mode = tx.get_mode()

        # Get voltage when tx is in state at index idx0
        tx.set_mode(TagMode(idx0))
        v0 = self.voltage_at_tag(tags, rx)

        # Get voltage when tx is in state at index idx1
        tx.set_mode(TagMode(idx1))
        v1 = self.voltage_at_tag(tags, rx)

        # Restore original mode
        tx.set_mode(original_mode)
        
        return abs(v1 - v0)
