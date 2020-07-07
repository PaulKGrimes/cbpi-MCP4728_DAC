from modules import cbpi
from modules.core.props import Property
from modules.core.hardware import ActorBase

import mcp4728


@cbpi.actor
class MCP4728Actor(ActorBase):
    """An actor that uses a four channel MCP4728 12-bit DAC i2c module to control power using output voltages between
    0-Vdd or 0-Vref x Gain on a single channel.

    The on/off state of the actor can be controlled either by setting the DAC output to zero, or using an additional
    actor.
    """
    address = Property.Select("DAC Address", [0, 1, 2, 3, 4, 5, 6, 7],
                              description="Minor address of the MCP4728 DAC unit. Use 0 unless you have changed the address manually")
    channel = Property.Select("Channel", [0, 1, 2, 3],
                              description="DAC channel to use")
    volt_ref = Property.Select("Reference Voltage", ["Vdd", "Internal 2.048V", "Internal 4.096V"],
                               description="Voltage Reference for DAC channel")
    power_ctrl = Property.Select("Power Control", ["Zero DAC", "Actor"],
                                 description="Power control method")
    power_actor = Property.Actor("Power On/Off Actor", description="Actor to use to control power")
    timeout = Property.Number("Notification duration (ms)", True, 5000,
                              description="0ms will disable notifications completely")

    def init(self):
        address = int(self.address)
        channel = int(self.channel)

        self.dac = mcp4728.MCP4728(address)
        cbpi.notify("Connected to MCP4728",
                    "DAC Address {:d}: DAC Channel {:d}".format(address, channel),
                    timeout=None)

        if self.volt_ref == "Vdd":
            self.dac.set_vref(channel, 0)
        else:
            self.dac.set_vref(channel, 1)
            if self.volt_ref == "Internal 4.096V":
                self.dac.set_gain(channel, 1)
            else:
                self.dac.set_gain(channel, 0)

        self.value = self.dac.get_value(channel)
        cbpi.notify("MCP4728 Current Value", "Channel {:d}: Value {:d}".format(channel, self.value), timeout=None)

    def set_power(self, power):
        """Set the power as a percentage of the range between minimum and maximum power"""
        channel = int(self.channel)

        self.power = power
        self.value = (4095 * power) // 100

        if self.power_ctrl == "Zero DAC":
            if self.state == 0:
                pass
            elif self.state == 1:
                self.dac.set_value(channel, self.value)

        value = self.dac.get_value(channel)
        cbpi.notify("MCP4728 Current Value", "Channel {:d}: Value {:d}".format(channel, value), timeout=None)

    def off(self):
        """Switch the actor off"""
        channel = int(self.channel)

        if self.power_ctrl == "Actor":
            self.api.switch_actor_off(int(self.power_actor))
        else:
            self.dac.set_value(channel, 0)

        value = self.dac.get_value(channel)
        cbpi.notify("MCP4728 Current Value", "Channel {:d}: Value {:d}".format(channel, value), timeout=None)

    def on(self, power=None):
        """Switch the actor on. Set the power to the given value or the current power setting."""
        channel = int(self.channel)

        if self.power_ctrl == "Actor":
            self.api.switch_actor_on(int(self.power_actor))

        self.dac.set_value(channel, self.value)

        value = self.dac.get_value(channel)
        cbpi.notify("MCP4728 Current Value", "Channel {:d}: Value {:d}".format(channel, value), timeout=None)

