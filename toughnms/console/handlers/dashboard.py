#!/usr/bin/env python
# coding:utf-8
import os
import subprocess
import os.path
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughnms.console.handlers.base import BaseHandler
from toughlib.permit import permit
from toughnms.console.handlers.base import MenuSys

##############################################################################
# basic
##############################################################################

class ToughError(Exception):
    def __init__(self, message):
        self.message = message


def run_command(command, raise_error_on_fail=False, shell=True, env=None):
    _result = dict(code=0)
    run_env = os.environ.copy()
    if env: run_env.update(env)
    proc = subprocess.Popen(command, shell=shell,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=run_env)
    stdout, stderr = proc.communicate('through stdin to stdout')
    result = proc.returncode, stdout, stderr
    if proc.returncode > 0 and raise_error_on_fail:
        error_string = "* Could not run command (return code= %s)\n" % proc.returncode
        error_string += "* Error was:\n%s\n" % (stderr.strip())
        error_string += "* Command was:\n%s\n" % command
        error_string += "* Output was:\n%s\n" % (stdout.strip())
        if proc.returncode == 127:  # File not found, lets print path
            path = os.getenv("PATH")
            error_string += "Check if y/our path is correct: %s" % path
        raise ToughError(error_string)
    else:
        return result


def warp_html(code, value):
    _value = value.replace("\n", "<br>")
    _value = _value.replace("RUNNING", "<strong><font color=green>RUNNING</font></strong>")
    _value = _value.replace("STARTING", "<strong><font color='#CC9900'>STARTING</font></strong>")
    _value = _value.replace("FATAL", "<strong><font color=red>FATAL</font></strong>")
    if code > 0:
        _value = '<font color="#CC0000">%s</font>' % _value
    return _value


def execute(cmd):
    try:
        rcode, stdout, stderr = run_command(cmd, True)
        return dict(value=warp_html(rcode, (stdout or stderr)))
    except ToughError, err:
        import traceback
        traceback.print_exc()
        return dict(value=warp_html(1, err.message))


##############################################################################
# web handler
##############################################################################

@permit.route(r"/dashboard", u"控制面板", MenuSys, is_menu=True, order=1.0000)
class DashboardHandler(BaseHandler):

    @cyclone.web.authenticated
    def get(self):
        group_count = self.nagapi.count_hostgroup()
        host_count = self.nagapi.count_host()
        service_count = self.nagapi.count_service()
        self.render("index.html", 
            group_count = self.nagapi.count_hostgroup(),
            host_count = self.nagapi.count_host(),
            service_count = self.nagapi.count_service(),
            alert_count = self.mongodb.query_alert(None,None,None).count())


permit.add_route(DashboardHandler, r"/", u"控制面板", MenuSys, order=1.0001)

@permit.route(r"/dashboard/update", u" 刷新服务", MenuSys, order=1.0002)
class UpdateHandler(BaseHandler):
    @cyclone.web.authenticated
    def post(self):
        return self.render_json(**execute("supervisorctl status all"))






