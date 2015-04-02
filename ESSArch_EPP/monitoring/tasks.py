'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
from jobtastic import JobtasticTask
from configuration.models import ESSProc, ESSArchPolicy, sm
import psutil, logging, os
from django.core.mail import send_mail, mail_admins
from datetime import datetime
from monitoring.models import MonitoringObject
from essarch.models import storageMedium, robot

logger = logging.getLogger('essarch.monitoring')

class CheckProcessTask(JobtasticTask):
    """
    Check if all ESSArch processes is running
    """
    
    significant_kwargs = [
        ('process_list', str),
    ]
    herd_avoidance_timeout = 5  # Give it 5 seconds
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 10
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 60

    def calculate_result(self, process_list):
        tasks = process_list
        tasks_todo = list(tasks)
        num_tasks = len(tasks)

        # Let folks know we started
        self.update_progress(0, num_tasks)

        # Get ps list from OS        
        logger.info('Try to get process list from OS')
        ps_dict = self.get_ps_dict(process_list)
        logger.info('Succeeded to get process list from OS')
           
        # Create all tasks
        for counter, task in enumerate(tasks):
            if task == tasks_todo.pop(0):
                ESSProc_objs = ESSProc.objects.filter(Path=task)
                if ESSProc_objs:
                    ESSProc_obj = ESSProc_objs[0]
                    ps_objs = ps_dict[task]
                    children_pids = []
                    alarm_flag = None
                    logger.debug('ESSProc_obj name: %s, number: %s' % (ESSProc_obj.Name, len(ps_objs)))
                    for ps_obj in ps_objs:
                        if ps_obj.pid == ESSProc_obj.PID:
                            logger.debug('PID: %s' % ps_obj.pid)
                        elif ps_obj.ppid() == ESSProc_obj.PID:
                            children_pids.append(ps_obj.pid)
                        elif ESSProc_obj.alarm == 0:
                            # Found unknown processes
                            alarm_flag = 1
                            mail_subject = 'Found unknown processes for: %s, PID: %s' % (ESSProc_obj.Name, ps_obj.pid)
                            mail_message = mail_subject
                            mail_admins(mail_subject, mail_message,fail_silently=False)
                            logger.error(mail_message)
                    if ESSProc_obj.Status == '1' and ESSProc_obj.expected_pids == len(ps_objs):
                        # Process is running with correct number of processes.
                        alarm_flag = 0
                        logger.debug('Number of processes is OK')
                    elif ESSProc_obj.alarm == 0 and ESSProc_obj.Status == '1':
                        # Process is running but not correct number of processes.
                        alarm_flag = 1
                        mail_subject = 'Missing some processes for %s!' % ESSProc_obj.Name
                        mail_message = mail_subject
                        mail_admins(mail_subject, mail_message,fail_silently=False)
                        logger.error(mail_message)
                    elif ESSProc_obj.alarm == 0 and ESSProc_obj.Status == '0' and len(ps_objs) > 0:
                        # Process is flagged as stopped but some processes are still running
                        alarm_flag = 1
                        mail_subject = 'The process: %s is flagged as stopped but some processes are still running!' % ESSProc_obj.Name
                        mail_message = mail_subject
                        mail_admins(mail_subject, mail_message,fail_silently=False)
                        logger.error(mail_message)
                    logger.debug('Children PIDs: %s' % children_pids)
                    if alarm_flag == 1:
                        ESSProc_obj.alarm = 1
                    elif alarm_flag == 0:
                        ESSProc_obj.alarm = 0
                    logger.debug('alarm_flag: %s' % alarm_flag)
                    ESSProc_obj.child_pids = children_pids
                    ESSProc_obj.checked = datetime.now()
                    ESSProc_obj.save()                    
                else:
                    ps_pids = []
                    for ps_obj in ps_objs:
                        ps_pids.append(ps_obj.pid)
                    logger.warning('Found process: %s that not listed in ESSProc, PIDs: %s' % (task, ps_pids))
            else:
                event_info = 'check process: %s but task not match pop...' % task
                logger.error(event_info)
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(10)
            self.update_progress(counter, num_tasks, update_frequency=1)
        
    def get_ps_dict(self, process_list):
        """
        Count number of processes is running local server. Return a dict with processes.
        """
        process_dict = {}
        for process_item in process_list:
            process_dict[process_item] = []
        for p in psutil.process_iter():
            for process_item in process_list:
                if process_item in p.cmdline():
                    process_dict[process_item].append(p)
        return process_dict

class CheckProcFilesTask(JobtasticTask):
    """
    Check if all proc files have size > 0
    """
    
    significant_kwargs = [
        ('proc_log_path', str),
    ]
    herd_avoidance_timeout = 5  # Give it 5 seconds
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 10
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 60

    def calculate_result(self, proc_log_path):
        
        tasks = []
        for item in os.listdir(proc_log_path):
            if item[-4:] == '.log':
                tasks.append(item)
        tasks_todo = list(tasks)
        num_tasks = len(tasks)
        
        # Delete MonitoringObject if key not exists in tasks
        for MonitoringObject_obj in MonitoringObject.objects.all():
            if not MonitoringObject_obj.key in tasks:
                MonitoringObject_obj.delete()

        # Let folks know we started
        self.update_progress(0, num_tasks)
           
        # Create all tasks
        for counter, task in enumerate(tasks):
            MonitoringObject_obj, created = MonitoringObject.objects.get_or_create(key=task)
            alarm_flag = None
            alarm_sub = ''
            alarm_msg = ''
            if task == tasks_todo.pop(0):
                f_stat = os.stat(os.path.join(proc_log_path,task))
                if f_stat.st_size == 0:
                    alarm_flag = 0
                    alarm_sub = 'Proc logfile: %s, size %s byte' % (task,f_stat.st_size)
                    alarm_msg = alarm_sub
                    logger.debug(alarm_msg)
                else:
                    alarm_flag = 1
                    alarm_sub = 'Proc logfile: %s size is greater than zero, which indicates having a serious problem.' % (task)
                    alarm_msg = alarm_sub
                    if MonitoringObject_obj.alarm == 0:
                        mail_admins(alarm_sub, alarm_msg, fail_silently=False)
                    logger.error(alarm_msg)
            else:
                event_info = 'check proc logfile: %s but task not match pop...' % task
                logger.error(event_info)
            if alarm_flag == 1:
                MonitoringObject_obj.alarm = 1
            elif alarm_flag == 0:
                MonitoringObject_obj.alarm = 0
            logger.debug('alarm_flag: %s' % alarm_flag)
            MonitoringObject_obj.alarm_sub = alarm_sub
            MonitoringObject_obj.alarm_msg = alarm_msg
            MonitoringObject_obj.checked = datetime.now()
            MonitoringObject_obj.save() 
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(10)
            self.update_progress(counter, num_tasks, update_frequency=1)        
            
class CheckStorageMediumsTask(JobtasticTask):
    """
    Check if tapemedia is marked as FUll och Error
    """
    
    significant_kwargs = [
        #('email', str),
    ]
    herd_avoidance_timeout = 5  # Give it 5 seconds
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 10
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 60

    def calculate_result(self, email='admin'):
        
        tasks = robot.objects.all()
        tasks_todo = list(tasks)
        num_tasks = len(tasks)

        ArchTape_list = []
        WriteTape_list = []
        EmptyTape_list = []
        ErrorTape_list = []
        AddTape_list = []

        # Let folks know we started
        self.update_progress(0, num_tasks)
    
        # Populating MinTape_dict and target_dict
        target_dict = {}
        MinTape_dict = {}
        ESSArchPolicy_objs = ESSArchPolicy.objects.filter(PolicyStat=1)
        for ep_obj in ESSArchPolicy_objs:
            sm_objs = []
            for i in [1,2,3,4]:
                sm_obj = sm()
                sm_obj.id = i
                sm_obj.status = getattr(ep_obj,'sm_%s' % i)
                sm_obj.type = getattr(ep_obj,'sm_type_%s' % i)
                sm_obj.format = getattr(ep_obj,'sm_format_%s' % i)
                sm_obj.blocksize = getattr(ep_obj,'sm_blocksize_%s' % i)
                sm_obj.maxCapacity = getattr(ep_obj,'sm_maxCapacity_%s' % i)
                sm_obj.minChunkSize = getattr(ep_obj,'sm_minChunkSize_%s' % i)
                sm_obj.minContainerSize = getattr(ep_obj,'sm_minContainerSize_%s' % i)
                sm_obj.minCapacityWarning = getattr(ep_obj,'sm_minCapacityWarning_%s' % i)
                sm_obj.target = getattr(ep_obj,'sm_target_%s' % i)
                sm_objs.append(sm_obj)
            
            for sm_obj in sm_objs:
                if sm_obj.status == 1 and sm_obj.minCapacityWarning > 0:
                    try:
                        if not MinTape_dict[sm_obj.target] > sm_obj.minCapacityWarning:
                            MinTape_dict[sm_obj.target] = sm_obj.minCapacityWarning
                    except KeyError:
                        MinTape_dict[sm_obj.target] = sm_obj.minCapacityWarning
                        target_dict[sm_obj.target] = 0       

        # Create all tasks
        for counter, task in enumerate(tasks):
            alarm_flag = None
            alarm_sub = ''
            alarm_msg = ''
            if task == tasks_todo.pop(0):
                if task.status == 'ArchTape':
                    event_info = '%s - Slot:%s' % (task.t_id, task.slot_id)
                    ArchTape_list.append(event_info)
                elif task.status == 'WriteTape':
                    event_info = '%s - Slot:%s' % (task.t_id, task.slot_id)
                    WriteTape_list.append(event_info)
                elif task.status == 'Ready':
                    event_info = '%s - Slot:%s' % (task.t_id, task.slot_id)
                    EmptyTape_list.append(event_info)
                    for target in target_dict.keys():
                        if task.t_id.startswith(target):
                            target_dict[target] += 1
            else:
                event_info = 'check proc logfile: %s but task not match pop...' % task
                logger.error(event_info)
 
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(10)
            self.update_progress(counter, num_tasks, update_frequency=1)
        
        # Check if minimum number of new tapes is available
        for target in target_dict.keys():
            if target_dict[target] < MinTape_dict[target]:
                AddTape_list.append(target)

        # Populating ErrorTape_list
        error_tape_objs = storageMedium.objects.exclude(storageMediumStatus=0).filter(storageMediumStatus__gt=30)
        for error_tape_obj in error_tape_objs:
            slot_id = None
            for task in tasks:
                if error_tape_obj.storageMediumID == task.t_id:
                    slot_id = task.slot_id
                    break         
            event_info = '%s - Slot:%s' % (error_tape_obj.storageMediumID, slot_id)
            ErrorTape_list.append(event_info)

        if email == 'admin':
            # Send mail report to admins
            timestamp = datetime.now()
            alarm_sub = 'Daily media report %s' % timestamp 
            alarm_msg = '%s\n' % alarm_sub
            alarm_msg += '\nArchive tapes online:\n'
            for item in ArchTape_list:
                alarm_msg += '%s\n' % item
            alarm_msg += '\nAdd new tapes starting with:\n'
            for item in AddTape_list:
                alarm_msg += '%s\n' % item
            alarm_msg += '\nWrite tapes:\n'
            for item in WriteTape_list:
                alarm_msg += '%s\n' % item
            alarm_msg += '\nEmpty tapes:\n'
            for item in EmptyTape_list:
                alarm_msg += '%s\n' % item
            alarm_msg += '\nError tapes:\n'
            for item in ErrorTape_list:
                alarm_msg += '%s\n' % item
            mail_admins(alarm_sub, alarm_msg, fail_silently=False)
        
        return {
            'ArchTape': ArchTape_list,
            'WriteTape':  WriteTape_list,
            'EmptyTape': EmptyTape_list,
            'ErrorTape': ErrorTape_list,
            'AddTape': AddTape_list,
        }