#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 10:44:24 2017

@author: wroscoe
"""

import time
from statistics import median
from threading import Thread
from .memory import Memory
from prettytable import PrettyTable


class PartProfiler:
    def __init__(self):
        self.records = {}

    def profile_part(self, p):
        self.records[p] = { "times" : [] }

    def on_part_start(self, p):
        self.records[p]['times'].append(time.time())

    def on_part_finished(self, p):
        now = time.time()
        prev = self.records[p]['times'][-1]
        delta = now - prev
        thresh = 0.000001
        if delta < thresh or delta > 100000.0:
            delta = thresh
        self.records[p]['times'][-1] = delta

    def report(self):
        print("Part Profile Summary: (times in ms)")
        pt = PrettyTable()
        pt.field_names = ["part", "max", "min", "avg", "median"]
        for p, val in self.records.items():
            # remove first and last entry because you there could be one-off
            # time spent in initialisations, and the latest diff could be
            # incomplete because of user keyboard interrupt
            arr = val['times'][1:-1]
            if len(arr) == 0:
                continue
            pt.add_row([p.__class__.__name__,
                        "%.2f" % (max(arr) * 1000),
                        "%.2f" % (min(arr) * 1000),
                        "%.2f" % (sum(arr) / len(arr) * 1000),
                        "%.2f" % (median(arr) * 1000)])
        print(pt)


class Vehicle:
    def __init__(self, mem=None):

        if not mem:
            mem = Memory()
        self.mem = mem
        self.parts = []
        self.on = True
        self.threads = []
        self.profiler = PartProfiler()


    def add(self, part, inputs=[], outputs=[], 
            threaded=False, run_condition=None):
        """
        Method to add a part to the vehicle drive loop.

        Parameters
        ----------
            inputs : list
                Channel names to get from memory.
            ouputs : list
                Channel names to save to memory.
            threaded : boolean
                If a part should be run in a separate thread.
        """
        assert type(inputs) is list, "inputs is not a list: %r" % inputs
        assert type(outputs) is list, "outputs is not a list: %r" % outputs
        assert type(threaded) is bool, "threaded is not a boolean: %r" % threaded

        p = part
        print('Adding part {}.'.format(p.__class__.__name__))
        entry={}
        entry['part'] = p
        entry['inputs'] = inputs
        entry['outputs'] = outputs
        entry['run_condition'] = run_condition

        if threaded:
            t = Thread(target=part.update, args=())
            t.daemon = True
            entry['thread'] = t

        self.parts.append(entry)
        self.profiler.profile_part(part)

    def remove(self, part):
        """
        remove part form list
        """
        self.parts.remove(part)


    def start(self, rate_hz=10, max_loop_count=None, verbose=False):
        """
        Start vehicle's main drive loop.

        This is the main thread of the vehicle. It starts all the new
        threads for the threaded parts then starts an infinite loop
        that runs each part and updates the memory.

        Parameters
        ----------

        rate_hz : int
            The max frequency that the drive loop should run. The actual
            frequency may be less than this if there are many blocking parts.
        max_loop_count : int
            Maximum number of loops the drive loop should execute. This is
            used for testing that all the parts of the vehicle work.
        """

        try:

            self.on = True

            for entry in self.parts:
                if entry.get('thread'):
                    #start the update thread
                    entry.get('thread').start()
                    print('Startng update thread {}.'.format(entry['part'].__class__.__name__))

            #wait until the parts warm up.
            print('Starting vehicle...')
            #time.sleep(1)

            loop_count = 0
            while self.on:
                start_time = time.time()
                loop_count += 1

                self.update_parts()

                #stop drive loop if loop_count exceeds max_loopcount
                if max_loop_count and loop_count > max_loop_count:
                    self.on = False

                sleep_time = 1.0 / rate_hz - (time.time() - start_time)
                if sleep_time > 0.0:
                    time.sleep(sleep_time)
                else:
                    # print a message when could not maintain loop rate.
                    if verbose:
                        print('WARN::Vehicle: jitter violation in vehicle loop with value:', abs(sleep_time))

                if verbose and loop_count % 200 == 0:
                    self.profiler.report()

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


    def update_parts(self):
        '''
        loop over all parts
        '''
        for entry in self.parts:

            run = True

            #check run condition, if it exists
            if entry.get('run_condition'):
                run_condition = entry.get('run_condition')
                run = self.mem.get([run_condition])[0]
            
            if run:
                #get part
                p = entry['part']

                #start timing part run
                self.profiler.on_part_start(p)

                #get inputs from memory
                inputs = self.mem.get(entry['inputs'])

                #run the part
                if entry.get('thread'):
                    outputs = p.run_threaded(*inputs)
                else:
                    outputs = p.run(*inputs)

                #save the output to memory
                if outputs is not None:
                    self.mem.put(entry['outputs'], outputs)

                #finish timing part run
                self.profiler.on_part_finished(p)
 

    def stop(self):        
        print('Shutting down vehicle and its parts...')
        for entry in self.parts:
            try:
                entry['part'].shutdown()
                print('Stoping part {}.'.format(entry['part'].__class__.__name__))
            except AttributeError:
                #usually from missing shutdown method, which should be optional
                pass
            except Exception as e:
                print(e)

        self.profiler.report()
