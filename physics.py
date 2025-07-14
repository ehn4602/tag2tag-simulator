from math import sqrt

import scipy.spatial as dist
from scipy.constants import c, e, pi


class PhysicsEngine:
    def __init__(self, exciter):
        """
        Initialize the physics engine.
        """
        # TODO: Figure out what constants should be supplied to the constructor
        # for future use.
        self.exciter = exciter

    def attenuation(
        dist: float, wavelength: float, tx_directivity=1.0, rx_directivity=1.0
    ) -> float:
        """
        Helper function for calculating the attenuation between two antennas
        """
        num = (4 * pi * dist) ** 2
        den = tx_directivity * rx_directivity * (wavelength**2)
        return num / den

    def power_at_rx(self, tx, rx) -> float:
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
        p_tx = tx.power
        g_tx = tx.gain
        g_rx = rx.gain
        wavelength = c / tx.frequency
        distance = dist.euclidean(tx.position, rx.position)
        return p_tx * g_tx * g_rx * ((wavelength / (4 * pi * distance)) ** 2)

    def v_dc(self, tx, rx) -> float:
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
        v_pk = sqrt((rx.resistance * power) / 500)
        return v_pk / (sqrt(2))

    def transmitted_voltage(self, tx, rx) -> float:
        """
        Get's the voltage that is transmitted from a transmitting tag to a
        receiving tag. This takes into account the exciter as well.
        """
        ex = self.exciter
        e_freq = ex.frequency
        e_wavlen = c / e_freq
        e_pos = ex.position

        tx_pos = tx.position
        tx_freq = tx.frequency
        tx_wavelen = c / tx_freq
        tx_refcoef = tx.active_coefficient

        rx_pos = rx.position
        rx_resist = rx.resistance

        d_ex_tx = dist.euclidean(e_pos, tx_pos)
        d_ex_rx = dist.euclidean(e_pos, rx_pos)
        d_tx_rx = dist.euclidean(tx_pos, rx_pos)
        i2pi = 1j * 2 * pi

        # Calculate the signal from exciter to tx and rx respectively
        # Passing in 1.0 for both directivities since we're assuming all
        # antennas in the simulation are isotropic at the moment
        sig_ex_tx = self.attenuation(d_ex_tx, e_wavlen, 1.0, 1.0) * (
            e ** (i2pi * d_ex_tx / e_wavlen)
        )
        sig_ex_rx = self.attenuation(d_ex_rx, e_wavlen, 1.0, 1.0) * (
            e ** (i2pi * d_ex_rx / e_wavlen)
        )

        # Calculate the signal from tx to rx
        sig_tx_rx = (
            sig_ex_tx
            * tx_refcoef
            * self.attenuation(d_tx_rx, tx_wavelen, 1.0, 1.0)
            * (e ** (i2pi * d_tx_rx / tx_wavelen))
        )

        rx_pwr_recieved = sig_ex_rx + sig_tx_rx
        v_pk = sqrt(abs(rx_resist * rx_pwr_recieved) / 500)
        return v_pk / sqrt(2)
