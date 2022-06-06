import yaml
import argparse
import os
import inspect
import pprint
import sys
import oacommon
from datetime import datetime

gdict={}
cwd = os.getcwd()
oacommon.setgdict(oacommon,gdict)
modulepath = os.path.join(cwd,"modules")
if os.path.exists(modulepath):
    sys.path.append(modulepath)

myself = lambda: inspect.stack()[1][3]
findinlist = lambda y,_list:  [x for x in _list if y in x]
__TRACE__=False
__DEBUG__=False
__DEBUG2__=False
 
def main():
    my_parser = argparse.ArgumentParser(description='exec open-automator tasks',allow_abbrev=False)
    my_parser.add_argument('tasks',metavar='tasks',type=str,help='yaml for task description')
    my_parser.add_argument('-d', action='store_true',help='debug enable')
    my_parser.add_argument('-d2', action='store_true',help='debug2 enable')
    my_parser.add_argument('-t', action='store_true',help='trace enable')
    args = my_parser.parse_args()
    tasksfile =args.tasks
    __DEBUG__=args.d
    __DEBUG2__=args.d2
    __TRACE__=args.t
    gdict['__DEBUG__']=args.d
    gdict['__DEBUG2__']=args.d2
    gdict['__TRACE__']=args.t
    
    #tasksfile = "automator.yaml"
    nowstart = datetime.now()

    print(f"start process tasks form {tasksfile}")
    with open(tasksfile) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    
    #print(conf)
    pprint.pprint(conf)
    tasks = conf[0]['tasks']
    sizetask = len(tasks)
    currtask = 1 
    for task in tasks:
        for key in task.keys():
            if "name" != key:
                print("\n")
                print(f"exec task \"{name}\"  task {currtask} of {sizetask}")
                if __DEBUG__:
                    print(f"\t{key} {task.get(key)}") 
                if "." in key:
                    if __DEBUG2__:
                        print(gdict)
                    m = __import__(key.split('.')[0])
                    mfunc = getattr(m,"setgdict")
                    mfunc(m,gdict)
                    func = getattr(m,key.split('.')[1])
                    func(m,task.get(key))
                    
                else:
                    func = globals()[key]
                    func(task.get(key))
                currtask = currtask +1 
            else:
                name = oacommon.effify(task.get(key))
                #print(f"task:..............................{task.get(key)}")

        #print(task)
    print(f"end process tasks form {tasksfile}")
    nowend = datetime.now()
    delta = (nowend - nowstart).total_seconds()
    print()
    print("*************************************************************")
    print(f"""Open-Automator performed {sizetask} tasks
Start at {nowstart} 
End at {nowend} 
Running Time {delta}s """)
    print("*************************************************************")

if __name__ == '__main__':
    main()

