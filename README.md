
## PICATA: Data-driven Peer Instruction and Continuous Assessment via a
(digital) Teaching Assistant

### Overview 

PICATA is a tool for instructors who wish to combine Peer Instruction (PI) and
Continuous Assessments (CA) utilizing results from students' earlier CA data.
Currently, this tool works with the Canvas Learning Management System (LMS) and
the interface is console/terminal based. In addition to increased
functionality, the development plans for this project include extending it to
other LMSs and creating a richer interface. Suggestions for the other
functionality/features (see Issues), as well as any feedback on the project,
are welcomed. 

The bulk of the functionality provided by this tool is in automating an
instructor's workflow with the LMS and their own student data. This is
accomplished by utilizing the
[CanvasAPI](https://github.com/ucfopen/canvasapi). 

### Installation (To be completed)

Note that installation and usage of PICATA requires some basic knowledge on how
to use command line in a terminal. If you do not have any familiarity with
this, there are plenty of references (e.g.
[freecodecamp.org](https://www.freecodecamp.org/news/command-line-for-beginners/))
available to quickly provide some background.  

1. The first step to using PICATA is to clone this repository to your local system. 

The easiest way to use the program is to clone this repository to your local system. 






- Instructions on how to generate a Canvas token...
- Installation of canvasapi and other dependencies...
- Cloning/downloading this repo...

### Usage

__Initiating a post-quiz PI/CL sessions__ 

Currently PICA TA does not generate the details/guidelines for the PI/CL
session. Rather, the current functionality focuses on initiating the PI
session, which involves: 1. selecting a quiz and quiz question, 2. selecting
and confirming pairs/groups of students for the PI/CL session, and 3. notifying
students via a Canvas message of who they will work with. 

Thus, in this initial version it is the responsibility of the instructor to
present students with all of the requisite material for the follow-up PI
session. 
