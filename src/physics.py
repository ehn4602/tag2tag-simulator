from __future__ import annotations
from math import sqrt
from typing import TYPE_CHECKING

import scipy.spatial.distance as dist
from scipy.constants import c, e, pi

if TYPE_CHECKING:
    from tags.tag import Exciter, PhysicsObject, Tag


class PhysicsEngine:
    def __init__(self, exciter: Exciter):
        """
        Initialize the physics engine.
        """
        # TODO: Figure out what constants should be supplied to the constructor
        # for future use.
        self.exciter = exciter

    def attenuation(
        self, distance: float, wavelength: float, tx_directivity=1.0, rx_directivity=1.0
    ) -> float:
        """
        Helper function for calculating the attenuation between two antennas
        """
        num = (4 * pi * distance) ** 2
        den = tx_directivity * rx_directivity * (wavelength**2)
        return den / num

    def get_sig_tx_rx(self, tx: PhysicsObject, rx: Tag):
        """
        Gets the signal from a tag or exciter to another tag
        """
        distance = dist.euclidean(tx.get_position(), rx.get_position())
        wavelen = c / tx.get_frequency()
        return self.attenuation(distance, wavelen, 1.0, 1.0) * (
            e ** (1j * 2 * pi * distance / wavelen)
        )

    def voltage_at_tag(self, tags: dict[str, Tag], recieving_tag: Tag):
        """
        Get's the total voltage delivered to a given tag by the rest of the
        tags. This currently makes the assumption that there are no feedback
        loops in the backscatter for simplicity.
        """
        ex = self.exciter
        rx_impedance = recieving_tag.get_impedance()

        # This will be summed later
        sigs_to_rx = []
        sigs_to_rx.append(self.get_sig_tx_rx(ex, recieving_tag))

        for tag in tags.values():
            tag_mode = tag.get_mode()
            if tag is not recieving_tag and not tag_mode.is_listening():
                # Get all of the signals that are currently being sent to rx

                # TODO Get the reflection coeff of the tag properly
                ref_coef = tag.get_reflection_coefficient()
                sig_ex_tx = self.get_sig_tx_rx(ex, tag)
                sig_tx_rx = (
                    sig_ex_tx * ref_coef * self.get_sig_tx_rx(tag, recieving_tag)
                )
                sigs_to_rx.append(sig_tx_rx)

        pwr_recieved = abs(sum(sigs_to_rx))
        v_pk = sqrt(abs(rx_impedance * pwr_recieved) / 500)
        return v_pk / sqrt(2)
