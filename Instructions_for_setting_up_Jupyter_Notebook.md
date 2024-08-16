# Instructions for installing Anaconda, Python and Jupyter Notebooks to run the Marine Institute CTD processing system
## Install Anaconda Navigator
	https://docs.anaconda.com/free/anaconda/install/windows/

Locate or create a directory on the local machine, where all the Notebooks will be contained.

## Install relevant packages
Open an Anaconda Prompt window (tip: type into windows search) and use the [anaconda_env_setup_commands.txt](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/blob/main/anaconda_env_setup_commands.txt) file to see the list of commands to be used to install required python version and python packages.

Confirm the environment has been created by entering the following command and checking the list:
	
    conda env list

## Open a Jupyter Notebook
In the windows searchbar type Jupyter Notebook and click on the one with your environment appended in brackets. A browser window will open where you can navigate to the mi-ctd-data-processing folder and click on a Notebook to begin testing. The notebooks use Python's *bokeh* package to create interactive dashboards, *bokeh* requires a local Jupyter environment to be at http://localhost:8888/, see [here](https://docs.bokeh.org/en/latest/) for more information on *bokeh*.

To operate or test the Notebooks:

The CTD Profiles Processing Jupyter Notebook ([CTD_Profiles_Processing.ipynb](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/blob/main/CTD_Profiles_Processing.ipynb))  processes the raw Seabird SBE911 data and saves processed data and metadata to a set of folders. In order to run this notebook successfully raw files and metadata (where available) must be in place.

### Create working directory with required directory set-up
First create a directory folder (either locally or on a networked drive) named 'CTD', which will hold a copy of the raw data and ultimately contain all the processed output files.

Within 'CTD' folder create a sub-folder per vessel, named with vessel abbreviation. At the MI these will be 'CE' and 'TC' for Celtic Explorer and Tom Crean respectively.

Within each vessel folder create a year sub-folder for each year that you have data for, e.g. '2022' & '2023'.

Within each year folder per vessel create a cruise sub-folder named using the given cruise ID. e.g. 'CE23004'. This cruise ID is important and will be required by the Notebooks to index all cruise data for that cruise.

Within the cruise folder create a raw data folder titled 'raw_files' and copy all raw data to it for that cruise. 
Raw data files per CTD cast must include .XMLcon and .hex files but should also include .hdr and .bl files too, for each cast.

Also within the cruise folder create a 'logsheets' sub-folder and place the electronic logsheet containing all metadata into this folder.
If an SBE35 was used on the rig place all SBE35 files into a 'SBE35' sub-folder in the cruise folder. SBE35 files must be individual files per cast and must be named the same as raw .hex files per cast.

Once all data is in place and the Profiles Notebook is open in a browser, processing can commence.

## Running the Jupyter Notebook
To run the notebook from the begining it is good practice to clear the kernel first. Do this by clicking 'Kernel', then clicking 'Restart & Clear Output' from the top toolbar on the Notebook browser page.
	
There are two types of cells, markdown cells (human readable text) and code cells (Python), each of which can be run by clicking 'Run' from the toolbox.

***Note:** Running markdown cells simply moves down to next cells.*
	
Run sequentially down through the cells, following the self contained SOP and instructions within.
	
## Some useful links for beginners:
### Anaconda:
https://blog.hubspot.com/website/anaconda-python

https://docs.anaconda.com/free/anaconda/getting-started/index.html

### Python:
https://www.python.org/about/gettingstarted/

### Jupyter Notebooks:
https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/
https://realpython.com/jupyter-notebook-introduction/