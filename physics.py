from math import sqrt
import scipy.spatial.distance as dist
from scipy.constants import c, e, pi


def fspl(dist: float, wavelength: float):
    """
    Helper function for calculating the free-space path loss
    """
    return ((4*pi*dist)/wavelength)**2


class PhysicsEngine:
    def __init__(self, exciter):
        """
        Initialize the physics engine.
        """
        # TODO: Figure out what constants should be supplied to the constructor
        # for future use.
        self.exciter = exciter

    def power_at_rx(self, tx, rx):
        """
        Determine the power a tag receives given known constants and provided
        tag information. The output is in mW.

        Arguments:
        tx -- The transmitter in this relationship. Needs the power, gain,
        wavelength, and position attributes
        rx -- The receiver in this relationship. Needs power, gain, and
        position attributes

        This is just the Friss equation.
        """
        p_tx = tx.power
        g_tx = tx.gain
        g_rx = rx.gain
        wavelength = c/tx.frequency
        distance = dist.euclidean(tx.position, rx.position)
        return p_tx*g_tx*g_rx*((wavelength/(4*pi*distance))**2)

    def v_dc(self, tx, rx):
        """
        Determine the DC voltage output at rx in volts.

        Arguments:
        tx -- The transmitter in this relationship. Needs the power, gain,
        wavelength, and position attributes
        rx -- The receiver in this relationship. Needs power, gain, resistance,
        and position attributes.

        Returns:
        The voltatage output at the receiver
        """
        power = self.power_tag_rx(tx, tx)
        v_pk = sqrt((rx.resistance*power)/500)
        return v_pk/(sqrt(2))

    def transmitted_voltage(self, tx, rx):
        # TODO Make sure that this is all correct with the professor
        # See if there's a way to cut back on the assumptions made
        """
        Get's the voltage that is transmitted from a transmitting tag to a
        receiving tag. This takes into account the exciter as well.
        """
        ex = self.exciter
        e_freq = ex.frequency
        e_wavlen = c/e_freq
        e_pos = ex.position

        tx_pos = tx.position
        tx_freq = tx.frequency
        tx_wavelen = c/tx_freq
        tx_refcoef = tx.reflection_coefficientdd

        rx_pos = rx.position
        rx_resist = rx.resistance
        # TODO This needs to be finalized in terms of how it's handled on the
        # tag end

        d_ex_tx = dist.euclidean(e_pos, tx_pos)
        d_ex_rx = dist.euclidean(e_pos, rx_pos)
        d_tx_rx = dist.euclidean(tx_pos, rx_pos)
        i2pi = 1j*2*pi

        # Calculate the signal from exciter to tx and rx respectively
        # Assuming free space path loss with isotropic antennas for attenuation
        sig_ex_tx = fspl(d_ex_tx, e_wavlen)*(e**(i2pi*d_ex_tx/e_wavlen))
        sig_ex_rx = fspl(d_ex_rx, e_wavlen)*(e**(i2pi*d_ex_rx/e_wavlen))

        # Calculate the signal from tx to rx
        sig_tx_rx = sig_ex_tx*tx_refcoef*fspl(d_tx_rx, tx_wavelen)*(e**(i2pi*d_tx_rx/tx_wavelen))

        rx_pwr_recieved = sig_ex_rx + sig_tx_rx
        v_pk = sqrt((rx_resist*rx_pwr_recieved)/500)
        return v_pk/sqrt(2)
