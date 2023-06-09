
## PICATA: Data-driven Peer Instruction and Continuous Assessment via a (digital) Teaching Assistant

### Overview 

PICATA is a tool for instructors who wish to combine Peer Instruction (PI) and
Continuous Assessments (CA) utilizing results from students' earlier CA data.
Currently, this tool works with the Canvas Learning Management System (LMS)
primarily using the [CanvasAPI](https://github.com/ucfopen/canvasapi). The
interface is console/terminal based.  In addition to increased functionality,
the development plans for this project include extending it to other LMSs and
creating a richer interface. Suggestions for the other functionality/features
(see Issues), as well as any feedback on the project, are welcomed. 


### Installation

Note that installation and usage of PICATA requires some basic knowledge on how
to use command line in a terminal. If necessary, there are many brief
tutorials/lessons available to help in this area, e.g.,
[freecodecamp.org](https://www.freecodecamp.org/news/command-line-for-beginners/).

1. The first step to using PICATA is to clone this repository to your local system. This can either be done 
in just one place on your local system, or separately for each course that it will be used in. The latter option 
is our preferred method since we tend to have a separate directory for each course we teach. 
2. Open a web browser and go to your institution's Canvas LMS. You'll then
navigate to __Account__, then __Settings__. Towards the bottom of this screen
in your LMS you will see a blue button that says, __+ New Access Token__'. You will copy/download this token to your
local system, but be careful not to share it (e.g. do not save it a shared directory). 
3. Once it is cloned, open a command line terminal and navigate (using
'[cd](https://en.wikipedia.org/wiki/Cd_(command))') to the __picata__ directory. 






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
