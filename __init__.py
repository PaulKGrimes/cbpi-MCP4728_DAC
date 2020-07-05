from modules import cbpi
from modules.core.props import Property
from modules.core.hardware import ActorBase

import mcp4728

@cbpi.actor
class MCP4728Actor(ActorBase):
    """An actor that uses a four channel MCP4728 12-bit DAC i2c module to control power using output voltages between 0-Vdd or 0-Vref x Gain
    on a single channel.

    The on/off state of the actor can be controlled either by setting the DAC output to zero, or using an additional actor.
    """
    address = Property.Select("DAC Address", [0,1,2,3,4,5,6,7], description="Minor address of the MCP4728 DAC unit. Use 0 unless you have changed the address manually")
    channel = Property.Select("Channel", [0,1,2,3], description="The channel to output the voltage")
    voltage_ref = Property.Select("Reference Voltage", ["Vdd", "Internal 2.048V", "Internal 4.096V"], description="The voltage reference to use.")
    power_control = Property.Select("Power On/Off Mode", ["DAC", "Actor"], description="Power off by setting DAC output to zero, or using another actor")
    power_actor = Property.Actor(label="Power Actor", description="Select the actor to use for on/off control")
    timeout = Property.Number("Notification duration (ms)", True, 5000, description="0ms will disable notifications completely")

    def init(self):
        self.dac = mcp4728.MCP4728(self.address)
        if self.voltage_ref == "Vdd":
            self.dac.set_vref(self.channel, 0)
        else:
            self.dac.set_vref(self.channel, 1)
            if self.voltage_ref == "Internal 4.096V":
                self.dac.set_gain(self.channel, 1)
            else:
                self.dac.set_gain(self.channel, 0)
        self.value = self.dac.get_value(self.channel)

    def set_power(self, power):
        """Set the power as a percentage of the range between minimum and maximum power"""
        self.power = power
        self.value = (4095*power) // 100

        power_actor_name = ""
        for idx, value in cbpi.cache["actors"].iteritems():
            if idx == int(self.power_actor):
                power_actor_name = value.name
        for idx, value in cbpi.cache["actors"].iteritems():
            if idx == int(self.dependency):
                if value.state == 0:
                    pass
                elif value.state == 1:
                    self.dac.write_value(channel, self.value)

    def off(self):
        """Switch the actor off"""
        if self.power_control == "DAC":
            self.dac.write_value(channel, 0)
        else:
            self.api.switch_actor_off(int(self.power_actor))

    def on(self, power=None):
        """Switch the actor on. Always set the power to the max_power or current power setting."""
        if power:
            self.set_power(power)

        if self.power_control == "DAC":
            self.dac.write_value(channel, self.value)
        else:
            self.api.switch_actor_on(int(self.base))
