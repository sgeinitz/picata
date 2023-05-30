import canvasapi
import os
import picata_utils as pu
import picata_config as pc

# User/instructor must first have created and downloaded a token in Canvas, and
# set up environment vars appropriately (e.g. 'source <file w/ canvas info>').
API_URL = os.environ.get("CANVAS_URL")
API_KEY = os.environ.get("CANVAS_TOKEN")
if not (API_URL or API_KEY):
    raise Exception("'CANVAS_' environment variables not set - see installation instructions to resolve this")

pica_config = pc.PicataConfig()
print(f"\nUsing '{pica_config.path}' as path and '{pica_config.prefix}' as prefix for all files/content created")

# Initialize a new Canvas object
canvas = canvasapi.Canvas(API_URL, API_KEY)

# Prompt user to select a course
chosen_course = pu.selectFromList(canvas.get_courses(), "course")
print(f"\nSelected course: {chosen_course.name}")

pica_course = pu.PicaCourse(chosen_course, pica_config, verbose=True)


# Prompt user to select a quiz
chosen_quiz = pu.selectFromList(chosen_course.get_quizzes(), "quiz")
print(f"\nSelected quiz: {chosen_quiz.title}")

# Obtain quiz data
pica_quiz = pu.PicaQuiz(canvas, chosen_quiz, pica_config, verbose=True)
pica_quiz.generateQuestionHistograms()
pica_quiz.generateDistanceMatrix()

# Prompt user for a task (either generate pairings, or check for bonus points, or ...)
