The acceptance tests are a set of Python scripts intended to be used
to verify an IPC-9852 Hermes implementation. They can be modified and
extended easily and don't need more than a Python interpreter
(version 3.8 or higher is recommended).

Project consists of 
* app - optional graphical user interface (requires kivy)
* mgr - includes a CLI entry point
* mgr/notebooks - jupyter notebook alternative for running test cases
* mgr/hermes_test_manager - includes hermes_test_api, an API to interface external Python code from CI/CD
* mgr/hermes_test_manager/ipc_hermes - the IPC-9852 Hermes implementation used
* mgr/hermes_test_manager/test_cases - the actual test cases

Some test cases can also be executed using pytest e.g., inside Visual Studio Code or from command line 

Conda environment for running the code is included. Before running the code for the first time, run the following command to create a new environment if you're using any Conda such as Anaconda
"conda env create -f hermes_github.yaml"