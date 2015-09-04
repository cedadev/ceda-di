"""
Module containing useful functions for the command-line interfaces.
"""

import os
import sys
import csv

import simplejson as json


def sanitise_args(config):
    """
    Sanitise command-line configuration.

    :param config: Config dictionary (from docopt)
    :returns: Config dictionary with all keys stripped of '<' '>' and '--'
    """
    sane_conf = {}
    for key, value in config.iteritems():
        if value is not None:
            key = key.lstrip("-><").rstrip("><")
            sane_conf[key] = value

    return sane_conf


def read_conf(conf_path):
    """
    Read configuration file into a dictionary.

    :param conf_path: Path to the JSON configuration file
    :returns: Dict containing parsed JSON conf
    """
    try:
        with open(conf_path, "r") as conf:
            return json.load(conf)
    except IOError:
        err_path = os.path.abspath(conf_path)
        sys.stderr.write(  # Continued on next line
            "Can't read configuration file\n%s\n\n" % err_path)
        return {}


def get_settings(conf_path, args):
    # Default configuration options
    # These are overridden by the config file and command-line arguments
    defaults = {
        "json-path": "json/",
        "log-path": "log/",
        "log-file": "log/",
        "logging": {
            "format": "[%(levelname)s] (%(name)s) %(message)s"
        }
    }

    conf_file = read_conf(conf_path)

    # Apply updates to CONFIG dictionary in priority order
    # Configuration priority: CONFIG < CONF_FILE < ARGS
    # (CONFIG being lowest, ARGS being highest)
    defaults.update(conf_file)
    defaults.update(args)

    return defaults


def build_file_list(path):
    """
    :Return Directory 
    :return: A list of file paths
    """            
    file_list = []
    for root, _, files in os.walk(path, followlinks=True):
        for each_file in files:
            file_list.append(os.path.join(root, each_file))

    return file_list

def write_list_to_file(file_list, file):
    f = open(file, 'w')
    
    for item in file_list:
        f.writelines(item)
        f.write("\n")
    
    f.close()
    
    
def find_dataset(file, dataset_id):
    """
    :Returns: The path of the given dataset id. 
    """
    vars = {}
    with open(file) as l_file:
        for line in l_file:
            if not line.startswith("#") :
                name, var = line.partition("=")[::2]
                vars[name.strip()] = var.strip()
    if dataset_id == "all" :
        return vars
    else :
        return vars[dataset_id]


def get_number_of_running_lotus_tasks() :
    
    """
    Returns the number of running jobs in lotus. 
    Counting is based on the observation that if there are not any jobs running then the system
    returns a single line of text otherwise returns a line with headers and a list of running processes.  
    TODO : Add some regex matching in order to identify the output.     
    """
    
    num_of_running_tasks = subprocess.check_output('bjobs', stderr=subprocess.STDOUT, shell=True).count("\n") 
            
    if num_of_running_tasks > 0 :
        num_of_running_tasks = num_of_running_tasks   - 1
                 
    return num_of_running_tasks
    
    
def run_tasks_in_lotus(task_list, max_number_of_tasks_to_submit):
    
    """
    Submits the commands supplied in lotus making sure that
    max_number_of_jobs is not exceeded. 
    """
        
    init_wait_time = 15
    wait_time = init_wait_time
    dec = 1
    iterations_counter = 0
             
        
    print "Max number of jobs to submit in each step :" + str(max_number_of_tasks_to_submit) + ". "\
        + "\nTotal number commands to run " + str(len(task_list)) + ". " 
                    
    print "==============================="
      
        
    while len(task_list) > 0 :            
        
        #Find out if other jobs can be submitted.
        num_of_running_tasks = get_number_of_running_lotus_tasks() 
        num_of_tasks_to_submit = max_number_of_tasks_to_submit - num_of_running_tasks             
        iterations_counter = iterations_counter + 1             
           
        print "Iteration :" + str(iterations_counter) + ". " 
        print "Number of jobs running  :" + str(num_of_running_tasks) + ". "    
        print "Number of jobs to submit in this step :" + str(num_of_tasks_to_submit) + ". "
            
        #Submit jobs according to availability.
        for i in range(0, num_of_tasks_to_submit):
            
            if len(task_list) == 0 : 
                break
            
            #Is there an extract op ?
            task = task_list[0]
            task_list.remove(task)
                                            
            command = "bsub " + task 
            
            
            print str(i +1) + ". " +"Executng :" + command
            subprocess.call(command, shell=True)
            
            
        print "Number of tasks waiting to be submitted :" + str(len(task_list)) + ". "           
                        
        #Wait in case some process terminates. 
        print "Waiting for :" + str(wait_time) + " secs."            
        time.sleep(wait_time)
                                        
                              
        #If nothing can be submitted wait again.
        if num_of_jobs_to_submit == 0:
            wait_time = wait_time - dec
            if (wait_time == 0):
                wait_time = init_wait_time
        
        print "==============================="   
    
    