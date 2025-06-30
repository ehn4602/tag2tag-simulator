from math import sqrt, pi
import scipy.spatial.distance as dist
from scipy.constants import c


class PhysicsEngine:
    def __init__(self):
        """
        Initialize the physics engine.
        """
        # TODO: Figure out what constants should be supplied to the constructor
        # for future use.
        pass

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

    def tag_peak_voltage_output(self, tx, rx):
        """
        Determine the peak voltage output at a tag in volts.

        Arguments:
        tx -- The transmitter in this relationship. Needs the power, gain,
        wavelength, and position attributes
        rx -- The receiver in this relationship. Needs power, gain, resistance,
        and position attributes.

        Returns:
        The volatage output at the receiver
        """
        power = self.power_tag_rx(tx, tx)
        return sqrt((rx.resistance*power)/500)
