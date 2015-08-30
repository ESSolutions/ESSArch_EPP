from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.conf import settings
from monitoring.models import Log, MonitoringObject
from monitoring.tasks import CheckStorageMediumsTask
from configuration.models import ESSProc

try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
    __shortname__ = 'EPP'
    __description__ = 'ESSArch Preservation Platform'
else:
    __version__ = epp.__version__ 
    __shortname__ = epp.__shortname__
    __description__ = epp.__description__


@login_required
def sysstat(request):
    """
    Build page providing information about the state of the system.
    """
    context = {}

    # Versions    
    context['essarch_info'] = '%s (%s) %s' % (__shortname__, __description__, __version__)

    #StorageMedium status
    media_status = CheckStorageMediumsTask.delay_or_fail(email=None)
    media_status_result = media_status.get(timeout=10)
    context['media_arch'] = media_status_result['ArchTape']
    context['media_empty'] = media_status_result['EmptyTape']
    context['media_error'] = media_status_result['ErrorTape']
    context['media_write'] = media_status_result['WriteTape']
    context['media_add'] = media_status_result['AddTape']
    context['process'] = ESSProc.objects.all()
    context['proc_alarm'] = MonitoringObject.objects.filter(alarm=1) 
    context['time_checked'] = timezone.now()
    return render_to_response('monitoring/sysstat.html',
                              context,
                              RequestContext(request))
    
@login_required
def sysinfo(request):
    """
    Build page providing information about the state of the system.
    """
    from subprocess import Popen, PIPE

    # Shell commands: Name and command
    SHELL_COMMANDS = [
        ('hostname', 'hostname'),
        #('gitversion', 'git log -n 1'),
        ('mysql_version', 'mysql --version'),
        ('python_packages', 'pip freeze'),
    ]

    # Flags in settings: Their expected  and actual values.
    SETTINGS_FLAGS = [
        ('DEBUG', False),
        ('LANGUAGE_CODE', None),
        ('TIME_ZONE', None),
    ]

    def run_shell_command(command, cwd):
        """
        Run command in shell and return results.
        """
        p = Popen(command, shell=True, cwd=cwd, stdout=PIPE)
        stdout = p.communicate()[0]
        if stdout:
            stdout = stdout.strip()
        return stdout

    context = {}

    # Versions
    cwd = settings.SITE_ROOT
    for name, shell_command in SHELL_COMMANDS:
        context[name] = run_shell_command(shell_command, cwd)
    
    context['essarch_info'] = '%s (%s) %s' % (__shortname__, __description__, __version__)

    # Settings Flags
    context['settings_flags'] = []
    for name, expected in SETTINGS_FLAGS:
        actual_setting = getattr(settings, name, None)
        if not expected is None: 
            unexpected = expected != actual_setting
        else:
            unexpected = False
        context['settings_flags'].append({
            'name': name, 
            'unexpected': unexpected,
            'actual': actual_setting
        })

    context['error_msgs'] = Log.objects.filter(level='ERROR')[:2]
    context['warning_msgs'] = Log.objects.filter(level='WARNING')[:2]
    context['info_msgs'] = Log.objects.filter(level='INFO')[:2]
    context['process'] = ESSProc.objects.all()
    context['proc_alarm'] = MonitoringObject.objects.filter(alarm=1) 
    context['time_checked'] = timezone.now()
    return render_to_response('monitoring/sysinfo.html',
                              context,
                              RequestContext(request))

