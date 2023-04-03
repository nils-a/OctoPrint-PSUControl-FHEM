# coding=utf-8
from __future__ import absolute_import

__author__ = "Nils Andresen <Nils@Nils-Andresen.de>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2023 Nils Andresen - Released under terms of the AGPLv3 License"

import octoprint.plugin

class PSUControl_FHEM(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.RestartNeedingPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.config = dict()
        self.mockPower = False


    def get_settings_defaults(self):
        return dict(
            address = '',
            plug = 0
        )


    def on_settings_initialized(self):
        self.reload_settings()


    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))


    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)


    def get_sysinfo(self):
        cmd = dict(system=dict(get_sysinfo=dict()))
        result = self.send(cmd)

        try:
            return result['system']['get_sysinfo']
        except (TypeError, KeyError):
            self._logger.error("Expecting get_sysinfo, got result={}".format(result))
            return dict()

    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        self.mockPower = True

    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        self.mockPower = False

    def get_psu_state(self):
        self._logger.debug("get_psu_state")
        return self.mockPower

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

    def get_settings_version(self):
        return 1

    def on_settings_migrate(self, target, current=None):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(
            psucontrol_fhem=dict(
                displayName="PSU Control - FHEM",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="nils-a",
                repo="OctoPrint-PSUControl-FHEM",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/nils-a/OctoPrint-PSUControl-FHEM/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - FHEM"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_FHEM()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
