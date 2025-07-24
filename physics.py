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
        return num / den

    def power_at_rx(self, tx: PhysicsObject, rx: Tag) -> float:
        """
        Determine the power a tag receives from a transmitter given known
        constants and provided tag information. The output is in mW.

        Arguments:
        tx -- The transmitter in this relationship. Needs the power, gain,
        wavelength, and position attributes
        rx -- The receiver in this relationship. Needs power, gain, and
        position attributes

        This is just the Friss equation.

        If you want the power delivered to a tag from the exciter, just the
        engine's exciter parameter as tx
        """
        p_tx = tx.get_power()
        g_tx = tx.get_gain()
        g_rx = rx.get_gain()
        wavelength = c / tx.get_frequency()
        distance = dist.euclidean(tx.get_position(), rx.get_position())
        return p_tx * g_tx * g_rx * ((wavelength / (4 * pi * distance)) ** 2)

    def v_dc(self, tx: PhysicsObject, rx: Tag) -> float:
        """
        Determine the DC voltage output at rx in volts.

        Arguments:
        tx -- The transmitter in this relationship. Needs the power, gain,
        wavelength, and position attributes
        rx -- The receiver in this relationship. Needs power, gain, resistance,
        and position attributes.

        Returns:
        The voltage output at the receiver
        """
        power = self.power_tag_rx(tx, tx)
        v_pk = sqrt((rx.get_impedance() * power) / 500)
        return v_pk / (sqrt(2))

    def transmitted_voltage(self, tx: Tag, rx: Tag) -> float:
        """
        Get's the voltage that is transmitted from a transmitting tag to a
        receiving tag. This takes into account the exciter as well.
        """
        ex = self.exciter
        # e_freq = ex.frequency
        # e_wavlen = c / e_freq
        # e_pos = ex.position

        # tx_pos = tx.position
        # tx_freq = tx.frequency
        # tx_wavelen = c / tx_freq
        tx_refcoef = tx.get_reflection_coefficient()

        # rx_pos = rx.position
        rx_resist = rx.get_impedance()

        # d_ex_tx = dist.euclidean(e_pos, tx_pos)
        # d_ex_rx = dist.euclidean(e_pos, rx_pos)
        # d_tx_rx = dist.euclidean(tx_pos, rx_pos)
        # i2pi = 1j * 2 * pi

        # Calculate the signal from exciter to tx and rx respectively
        # Passing in 1.0 for both directivities since we're assuming all
        # antennas in the simulation are isotropic at the moment
        sig_ex_tx = self.get_sig_tx_rx(ex, tx)

        # sig_ex_tx = self.attenuation(d_ex_tx, e_wavlen, 1.0, 1.0) * (
        # e ** (i2pi * d_ex_tx / e_wavlen)
        # )

        sig_ex_rx = self.get_sig_tx_rx(ex, rx)
        # sig_ex_rx = self.attenuation(d_ex_rx, e_wavlen, 1.0, 1.0) * (
        #     e ** (i2pi * d_ex_rx / e_wavlen)
        # )

        # Calculate the signal from tx to rx
        sig_tx_rx = (
            sig_ex_tx
            * tx_refcoef
            * self.get_sig_tx_rx(tx, rx)
            # * self.attenuation(d_tx_rx, tx_wavelen, 1.0, 1.0)
            # * (e ** (i2pi * d_tx_rx / tx_wavelen))
        )

        rx_pwr_recieved = sig_ex_rx + sig_tx_rx
        v_pk = sqrt(abs(rx_resist * rx_pwr_recieved) / 500)
        return v_pk / sqrt(2)

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

        pwr_recieved = sum(sigs_to_rx)
        v_pk = sqrt(abs(rx_impedance * pwr_recieved) / 500)
        return v_pk / sqrt(2)
