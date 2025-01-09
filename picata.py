#!/usr/bin/env python3
import os
import re
import sys
import canvasapi
import picata_utils as pu
import picata_config as pc

tasks = ['pair', 'bonus', 'activity']
task = None

if len(sys.argv) < 2:
    print(f"Usage: picata {'|'.join(tasks)}")
    sys.exit(1)
else: 
    task = sys.argv[1]

if task not in tasks:
    # prompt the user to select a task
    task_ind = input("Select a valid task: [0] pair, [1] bonus, or [2] activity\n")
    task_ind = int(re.sub(r'\D', '', task_ind))
    if task_ind < 0 or task_ind > 2:
        print("Invalid task selected. Exiting.")
        sys.exit(1)
    else:
        task = tasks[task_ind]

# User/instructor must first have created and downloaded a token in Canvas, and
# set up environment vars appropriately (e.g. 'source <file w/ canvas info>').
API_URL = os.environ.get("CANVAS_URL")
API_KEY = os.environ.get("CANVAS_TOKEN")
if not (API_URL or API_KEY):
    raise Exception("'CANVAS_' environment variables not set - see installation instructions to resolve this")

pica_config = pc.PicataConfig()

# Initialize a new Canvas object
canvas = canvasapi.Canvas(API_URL, API_KEY)

# Prompt user to select a course
#chosen_course = pu.selectFromList(canvas.get_courses(), "course")
chosen_course = pu.selectCourse(canvas)


print(f"\nSelected course: {chosen_course.name}")

pica_course = pu.PicaCourse(chosen_course, pica_config, verbose=False)

if task == 'activity':
    pica_course.saveStudentActivity(pica_config.data_path)

elif task in ['pair', 'bonus']:
    # Prompt user to select a quiz
    chosen_quiz = pu.selectFromList(chosen_course.get_quizzes(), "quiz")
    print(f"\nSelected quiz: {chosen_quiz.title}")

    # Obtain quiz data and generate plots to visualize the data.
    pica_quiz = pu.PicaQuiz(canvas, chosen_quiz, pica_config, verbose=False)
    pica_quiz.generateQuestionHistograms()
    pica_quiz.generateDistanceMatrix(only_present=False)
    pica_quiz.getUserQuizEvents()

    if task == 'pair':
        # Open the CSV file with student data for who is present today and recalculate distance matrix.
        pica_quiz.openPresentCSV()
        pica_quiz.generateDistanceMatrix(only_present=True)

        # Compare all four methods of pairings students
        pica_quiz.comparePairingMethods()

        # Generate pairings for today using the median method
        pica_quiz.createStudentPairings(method='med', write_csv=True)

    elif task == 'bonus':
        # Prompt user to find the pairings CSV file
        pica_quiz.getPastPairingsCSV()

        # Check if paired students have distance of 0
        pica_quiz.checkForBonusEarned()

        # Award bonus points to students who received it by setting fudge points
        pica_quiz.awardBonusPoints()

print("\n** Done ***\n")