Decision Support System for Higher Education
==============================

This repo describes the implementation of  data manipulation for DSS for Higher Education within a MicroStrategy environment.
------------



Overview of the repository:
├── LICENSE            <-	Description of the MIT license.
├── .gitignore         <-	Defines the elements not integrated in Git.
├── README.md          <-	Description of the project.
├── data (only local)
│   ├── external       <-	Additional files necessary for preparation in CSV format.
│   ├── interim        <-	Prepared data in pickle format.
│   ├── processed      <-	Final files in CSV format for import into MicroStrategy.
│   └── raw            <-	Extracted data from exam and student databases.
│
├── models (only local) <-	Stored machine learning models. 
│
├── reports            <-	Reports and link to the full paper
│   ├── importance     <-	Visualization of feature importance from the random 
│   │                       Forest model.
│   └── figures        <-	Storage of the graphs used in the work.
│
├── requirements.txt   <-	Overview of the necessary libraries.
│
└── src                <-	Source code of the project.
    ├── __init__.py    
    │
    ├── data           
    │   └── make_dataset.py
    │
    ├── features       
    │   └── build_features.py
    │
    ├── models         
    │   │                 
    │   ├── apriori.py
    │   └── compare_models.py
    │
    └── visualization  
        └── visualize.py
