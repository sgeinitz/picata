
## PICATA: Peer Instruction and Continuous Assessment via a (digital) Teaching Assistant

### Overview 

PICATA is a tool for instructors who wish to combine Peer Instruction (PI) and
Continuous Assessments (CA) utilizing results from students' earlier CA data.
For more information on the PICA method see this [paper](https://link.springer.com/chapter/10.1007/978-3-031-74627-7_1).

Currently, this terminal-based tool works with the Canvas Learning Management System (LMS) using the 
[CanvasAPI](https://github.com/ucfopen/canvasapi). In addition to increased functionality, development 
plans for this project include extending it to other LMSs and creating a richer interface. Suggestions 
for other functionality/features (see Issues), as well as any feedback on the project, are welcomed. 


### Installation

Note that installation and usage of PICATA requires some basic knowledge on how
to use command line in a terminal. If necessary, there are many brief
tutorials/lessons available to help in this area, e.g.,
[freecodecamp.org](https://www.freecodecamp.org/news/command-line-for-beginners/).

1. **Clone the repository**:
    [clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) this repository to your local system. This can either be done 
in just one place on your local system, or separately for each course that it will be used in. The latter option is our preferred method since we tend to have a separate directory for each course we teach, and prefer to keep the course data separate.

2. **Generate a Canvas API Token**:
    Naviagte to the `picata` directory then run configuration setup script by simply typing, `./configure.sh` at the terminal prompt.
   ```bash
   cd picata
   ```
   ```bash
   ./configure.sh
   ```
   You will be prompted to enter:
   - Your institution's Canvas LMS base URL (you can find this on your Canvas home page).
   - The token can be created by navigating to _'Account'_, then _'Settings'_. Towards the bottom of this window in your LMS you will see a blue button, _'+ New Access Token_'. Click on this button to copy/download the token to your local system, but be careful not to share it (e.g. do not save it a shared directory). 
 
This will prompt the creation of the _data/_ and _figures/_ subdirectories.

3. **Verify Setup**:

Once this is complete, double check that the configuration script, _set_env.sh_ has been created, that it has the correct values for your URL and token, and that the
subdirectories have been created. 
  ```bash
   _set_env.sh_
   ```
   ```bash
   env
   ```
   This command will list all environment variables, allowing you to confirm that the necessary variables have been set correctly.

4. **Verify Python Libraries**:
    Before running the project, ensure that all required Python libraries are installed:
    1. Install the required libraries using `pip`:
    
    ```bash
    pip install -r requirements.txt 
    ```
    
    2. Alternatively, you can install each library individually if needed.

        * ![canvasapi](https://img.shields.io/badge/canvasapi-2.2.0-blue)
        * ![matplotlib](https://img.shields.io/badge/matplotlib-3.3.4-brightgreen)
        * ![numpy](https://img.shields.io/badge/numpy-1.22.0-yellow)
        * ![pandas](https://img.shields.io/badge/pandas-1.3.4-orange)
        * ![requests](https://img.shields.io/badge/requests-2.32.0-red)
        * ![scipy](https://img.shields.io/badge/scipy-1.10.0-lightgrey)
        * ![seaborn](https://img.shields.io/badge/seaborn-0.11.2-blueviolet)

    If no errors are thrown, the libraries are successfully installed.


### Usage

There are two main workflows that are a part of utilizing PICA in a course. The first is in creating the pairs of students 
to work together on a (collaborative) CA, i.e., quiz, in their LMS. This requires that the students' previous (independent) 
CA. This first workflow is the one that is currently implemented here in PICATA and can be carried out by following these steps:
1. Open a command line terminal and navigate to the __picata__ directory containing the repository that was cloned during installation (see above). 
2. Run the configuration script to set the environment variables by typing, `source set_env.sh`, at the terminal prompt. 
3. Before running the picata script to create student pairs, you will first need to mark which students are physically present in the classroom. 
This is the same class session in which students will take the collaborative quiz. You  mark which students are present in the classroom today by modifying the _'present_xxx.csv'_ file in the _data/_ directory. 
See the example _'present_example.csv'_ file in the _data/_ directory and keep the same format (i.e. columns, column names, etc.). 
5. Run the picata application by typing, `python picata.py`.  This will prompt you for the course, (independent) quiz to use for the pairing method, the exact filename of _'present_xxx.csv'_ file denoting 
which students are present today, and the pairing method to be used. 
6. Once the picata application has been run, open the _data/_ directory and look for a file that was just created with a name matching the pattern, _'quiz_xxx_pairing_via_xxx.csv'_. 
7. You can then share this list with students in the classroom, and allow them to move around to work with their assigned partner. 

The second workflow, which is not yet implemented in PICATA, involves scoring the collaborative quizzes and awarding bonus points when there is 
evidence that students have discussed and agreed upon the answers to the quiz (as intended). 
To carry this out we currently use a Jupyter notebook (see notebooks directory). 

