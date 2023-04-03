# coding=utf-8
from __future__ import absolute_import

__author__ = "Nils Andresen <Nils@nils-andresen.de>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2023 Nils Andresen - Released under terms of the AGPLv3 License"

import octoprint.plugin
import requests

class PSUControl_FHEM(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.RestartNeedingPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.config = dict()
        self.mockPower = False
        self.csrf = None


    def get_settings_defaults(self):
        return dict(
            address = '',
            device_name = '',
            verify_tls = False,
            set_on = 'on',
            set_off = 'off',
            reading = 'state'
        )


    def on_settings_initialized(self):
        self.config = dict()
        self.reload_settings()
        self.load_csrf()


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
        self.load_csrf()


    def get_sysinfo(self):
        cmd = dict(system=dict(get_sysinfo=dict()))
        result = self.send(cmd)

        try:
            return result['system']['get_sysinfo']
        except (TypeError, KeyError):
            self._logger.error("Expecting get_sysinfo, got result={}".format(result))
            return dict()

    def turn_psu_on(self):
        if(not self.config['address']):
             return

        self._logger.debug("Switching PSU On")
        self.send_to_fhem('set {0} {1}'.format(self.config['device_name'], self.config['set_on']))

    def turn_psu_off(self):
        if(not self.config['address']):
             return

        self._logger.debug("Switching PSU Off")
        self.send_to_fhem('set {0} {1}'.format(self.config['device_name'], self.config['set_off']))

    def get_psu_state(self):
        if(not self.config['address']):
            return False

        self._logger.debug("get_psu_state")
        resp = self.send_to_fhem('jsonlist2 {0}'.format(self.config['device_name']))
        list = resp.json()
        if(list is None):
            self._logger.warn('Error getting list data.')
            self._logger.debug(resp.content)
            return False

        val = list['Results'][0]['Readings'][self.config['reading']]['Value']
        self._logger.debug('{0} from readings is: {1}'.format(self.config['reading'], val))
        if(val == self.config['set_off']):
            return False
        elif(val == self.config['set_on']):
            return True
        elif(val.startswith('set_')):
            self._logger.debug('device is being changed, currently')
            return False # rather 'unknown' or 'unchanged'
        else:
            self._logger.error('unknown status in reading: {0}'.format(val))
            return False

    def send_to_fhem(self, command, recurse=False):
        url='{0}/fhem'.format(self.config['address'])
        verify_tls=self.config['verify_tls']
        auth=None
        params={
            'cmd':command,
            'XHR':1,
            'fwcsrf': self.csrf
        }
        args={
            'verify': verify_tls,
            'auth': auth,
        }

        self._logger.debug('sending command \'{0}\' to server {1}'.format(command, url))
        resp = requests.get(url, params=params, **args)
        if(resp.status_code == 400 and resp.headers['X-FHEM-csrfToken'] != self.csrf and not recurse):
            # csrf error.
            self._logger.debug('encountered new CSRF')
            self.csrf = resp.headers['X-FHEM-csrfToken']
            return self.send_to_fhem(command, True)

        if(not resp.ok):
            self._logger.error('got status {0} when accessing {1}'.format(resp.status_code, url))

        self.csrf = resp.headers['X-FHEM-csrfToken']
        return resp

    def load_csrf(self):
        if(not self.config['address']):
            return
        self.send_to_fhem('jsonlist2 {0}'.format(self.config['device_name']))

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
                user="nils-org",
                repo="OctoPrint-PSUControl-FHEM",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/nils-org/OctoPrint-PSUControl-FHEM/archive/{target_version}.zip"
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
