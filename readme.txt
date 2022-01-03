
README - BioReactor PID Controller

Classes and simulated actuators execute a fictional PID system controller to monitor bioreactor feedstock rates. The directory structure is organized into mechanical controllers (actuators such as pumps); classes for the recipe; classes for each stage of the recipe; and a PID controller class.


Recipe input format as JSON:

recipe = {
              1:{
                   'feed_type':'timed',
                   'start_parameters': {'rate': 10}, # pump rate in mL/min
                   'stop_parameters': {'stop_type':'time',
                                       'stop_value': 1} # duration in minutes
                       },
              2:{
                    'feed_type':'bolus',
                    'start_parameters':{},
                    'stop_parameters':{'stop_type':'mass',
                                       'stop_value': 5}  # target mass in grams
                       },
              3:{
                    'feed_type':'linear',
                    'start_parameters':{'inc_rate': -1}, # acceleration in mL/min^2
                    'stop_parameters':{'stop_type':'rate',
                                       'stop_value': 5}  # stop rate in mL/min
                       }
             }
 

Assumptions written into script:

> Scale readings are more precise and reliable than pump speed readings. Scales have higher precision, whereas pumps are prone to inaccuracies from solution viscocity (& other colligative effects), pressure gradients, bubbles, priming, and wear.

> If no pump rate is provided for bolus (set mass) type recipe, either global default pump speed will be used (if recipe initializes with bolus stage), or if already running, continues current pump rate from immediately preceding recipe stage

> Easy to work with numerical parameters assumed at top of utils.py for ease of testing: Glucose feedstock density = 1g/mL, nominal volume per pump step = 0.2mL, default pump rate = 600 steps/min, etc.

> Pump type somewhat fictional/idealized, as discrete steps suggesting syringe pump, which would require loading full volume of plunger prior to use (rendering scale readings of feedstock meaningless).

> Dead volume of pump is accounted for by PID and priming, but not rigorously so, as priming needs are dependent on pump type.


Counterassumptions made: (i.e. somewhat contradicting prompt)

> Additonal sensors and actuators exist beyond what was stated in prompt. Namely:
  > Valve (e.g. 8-port inline valve) connects pump and vessle for priming purposes.
  > There exists a pressure sensor, as pressure readings may be required for safety purposes. (Semiclosed vessle in experimental conditions containing culture that will generate pressure - possible safety hazard if culture grows too fast.)

Addtional functions required for running experiment (but left empty; beyond scope of assessment):

> feedstock empty - checks if feedstock ran out based on ,mass

> pump prime - primes pump with feedstock solution

> pump calibration - measures scaled-based mass-transfer rate for given pump speed

> pump contamination - determines if reactor conditions pose risk of feedstock contamination. Shuts valve and experiment accordingly

> sensor consistency -checks if all three sensor readings are consistent w/ each other 

> PID tuning algorithm: would need actual data to build a functioning tuning system.