# FYR analysis application
A web-based application that offers storage, analysis, and graphing capabilities

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Standards](#standards)
- [Functionality](#functionality)
- [Database](#database)
- [FAQ](#faq)
- [Acknowledgements](#Acknowleddgements)
- [License](#license)

---

## Installation
Our database is hosted with <a href="https://www.mongodb.com/" target="_blank">`MongoDB`</a>
The Compass tool is offered by Mongo to help interact and visualize with data. 
Development will require running Mongo locally.

See `requirements.txt` for a complete list of requirements that needs to be available.
Install all of these by running this command in bash:
```
pip install -r requirements.txt
```

#### Running a development environment

Navigate to the project root folder.

In bash, such as Ubuntu, you can use:
```
./scripts/execute.sh
```
This will launch a server running on http://127.0.0.1:5000

## Usage

TODO: describe the steps that a user would take:
 - uploading and analysing a brand new data set (starting from maestro)
 - viewing a dataset that was previously uploaded


## Standards

TODO: Naming standards

TODO: Formatting standards

#### Code pipeline standards
Pull from the Development branch at the start of every day's session. Commit regularly and push
at the end of the day.
When tasks are finished, save them in a branch with a description title (i.e. feature/init_stats_graphs,
or fix/validate_file_names_error) and then create a Pull Request (PR) with the development branch.
Each PR will be reviewed and either sent back for fixes or merged. On a weekly basis, the Development
branch will be merged with Staging, which will be tested and then merged with Production. 


## Functionality

#### Import
-TODO: what is validated on the home page
-TODO: what happens in the importer

#### Analysis
-TODO: what labelling changes happen based on the inputs
-TODO: describe analysis including inflections, RFUs at that inflection, Ct thresholds, 
curve fits (currently happens in graphing)

#### Graphing
-TODO: 3 dataframes currently set up
-TODO: methodology of passing plot into IO stream into url object into blueprint into html

#### Statistics
-TOOD: describe pd dataframe that we build
-TOOD: describe possible outputs/graphs that are getting built


## Database

Each collection has a file that defines what a single measurement looks like. Here are the locations 
of those files: 
- Dataset: `flaskr.database.dataset.py`
- Well: `flaskr.database.measurement_models.measurement.py`
- Protocol: `flaskr.database.protocol_models.protocol.py`
- Components: `flaskr.components.component_models.component.py`

In addition, there is a corresponding folder for each of these collections that contains the following:
- Repository - used to create and add a new object to a certain collection
- Collection - used to create a generator to loop through objects in a collection
- Factory - creates and instantiates an object
Refer to `framework.abstract.abstract_repository` to add functionality that should be accessible to 
all repositories (and to see what currently exists).

#### Examples
To access a single dataset and print the wells corresponding to it: 
```
from flaskr.database.dataset_models.repository import Repository
dataset_repository = Repository()
dataset = dataset_repository.get_by_id(self.dataset_id)
print(dataset.get_well_collection())

```

To loop through wells with the 10 ng/uL YRNA concentration and print the inflections:
```
from flaskr.database.measurement_models.collection import Collection as MeasurementCollection

measurement_collection = MeasurementCollection()
measurement_collection.add_filter('concentration','10 ng/uL')
for idx, measurement in enumerate(measurement_collection):
    print(measurement.get_inflections)
```

## FAQ

1. What data is in '______' collection?

⋅⋅* The Mongodb Compass tool can be used to view the collections. Each collection has a file that
defines it's properties.

2. Where are the sunflower seeds?

⋅⋅* Ask John to restock



## Acknowledgements

Thank you to the developers who have--and still are--putting in the time and effort to make this 
an application worth using. We appreciate Stephanie McCalla for coming up with the ideas and original matlab code to 
process inflection points. Thank you to Joe Hudelson for transcending the boundaries between 
the lab and our code each and every day; Brian Bauer for stewardship of the entire front-end and every bomber piece 
of advice, Bill Griffin for diving into the deep end and coming up with the ideas and enthusiasm that fire us up, 
and Claire Seibold for finally starting some documentation. 

An enormous thank you has to get sent out to the entire lab team, Alex Albers, Tre Blohm, John Kaiser, Joe Hudelson (x2), 
and Sarj Patel. Each of these people have been infinitely patient with countless Internal Server Errors, changes every 
few days, and too many responses, 'No idea why that's happening, we'll look into it'. Not only have they had the patience,
they have had the compassion and motivation to help us improve our systems and repeatedly explain what the different betwee
samples and groups are. Brainstorming sessions with the entire team are a sight to behold.

Last but not least, thank you to Chris Booth for the flame that started this project. What started as a simple assignment, 
converting matlab to python, has grown to be a real cutting-edge software. It could not have happened, nearly every step of 
the way, without Chris recognizing the importance and dreaming big. 


## License

FYR Diagnostics
