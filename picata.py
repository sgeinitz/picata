import canvasapi
import os
import requests
import scipy.stats as stats
import scipy.spatial.distance as distance
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sbn
import datetime
import time

# User/instructor must first have created and downloaded a token in Canvas, and
# set up environment vars appropriately (e.g. 'source <file w/ canvas info>'). 
API_URL = os.environ.get("CANVAS_URL")
API_KEY = os.environ.get("CANVAS_TOKEN")
if not (API_URL or API_KEY):
    raise Exception("'CANVAS_' environment variables not set - see installation instructions to resolve this")

# Inform user of location (i.e. current working dir) and prefix of generated content/files. 
default_path = os.getcwd()
default_prefix =  "pica_ta_"
file_prefix = default_path + "/" + default_prefix
print(f"\nUsing '{default_path}' as path and '{default_prefix}' as prefix for all files/content created")

def selectFromList(paginatedList):
    """ 
    A general function that takes a canvasapi object and a function 
    to list sub-objects, lists all of the sub-objects, and prompts the
    user to select one of them. The selected sub-object is returned. 
    """
    i = 0
    subobject_list = []
    for i, so in enumerate(paginatedList):
        print("[", i, "]", so)
        subobject_list.append(so)
    str_index = input("Select item from list above (using index in '[]'): ")
    try: 
        if int(str_index) >= 0 or int(str_index) < i:
            int_index = int(str_index)
    except IndexError:
        print("Invalid selection")
    return subobject_list[int_index]
        

# Initialize a new Canvas object and prompt the user to select a course.
canvas = canvasapi.Canvas(API_URL, API_KEY)
chosen_course = selectFromList(canvas.get_courses())
print(f"\n\nSelected course: {chosen_course.name}")

# Then prompt them to select a quiz to use
chosen_quiz = selectFromList(chosen_course.get_quizzes())
print(f"\n\nSelected quiz: {chosen_quiz.title}")

# Get single obj/ref for all quiz questions (rather than retrieving questions
# from a SubmissionEvent object). This will be used later on when sending messages 
# to students about a specific question (e.g. quiz_question[k].question_text). 
quiz_questions = []
for i, quest in enumerate(chosen_quiz.get_questions()):
    #print("appending question", i, ": ", quest)
    quiz_questions.append(quest)

# Download the student_analysis csv quiz report. This should be fixed so that this 
# only happens when the file doesn't already exist. 
quiz_report_req = chosen_quiz.create_report('student_analysis')
request_id = quiz_report_req.progress_url.split('/')[-1]
print("type(quiz_report_req) = ", type(quiz_report_req))
print("quiz_report_req.__dict__ = ", quiz_report_req.__dict__)
quiz_report_progress = canvas.get_progress(request_id)
while quiz_report_progress.workflow_state != 'completed':
    print(f"\nQuiz report status: {quiz_report_progress.completion}% completed")
    time.sleep(1) 
    quiz_report_progress = canvas.get_progress(request_id)

quiz_report = chosen_quiz.get_quiz_report(quiz_report_req)
quiz_csv_url = quiz_report.file['url']
quiz_csv = requests.get(quiz_csv_url)
csv = open(file_prefix + 'quiz_' + str(chosen_quiz.id)  +'_student_analysis.csv', 'wb') 
for content in quiz_csv.iter_content(chunk_size=2^20):
    if content:
        csv.write(content)
csv.close()

df = pd.read_csv(file_prefix + 'quiz_' + str(chosen_quiz.id)  +'_student_analysis.csv')

# rename columns to be shorter, cleaner, and with question_id as a column
for old_col_name in df.columns:
    new_col_name = old_col_name.split(':')[0].replace(' ', '_').replace('.', '_')
    df.rename(columns={old_col_name: new_col_name}, inplace=True)

# append '_score' question id for columns with individual question scores
quiz_question_ids = [str(c.id) for c in quiz_questions]
for i,col in enumerate(df.columns):
    if col in quiz_question_ids:
        next_col = df.columns[i+1]
        next_col_new_name = col + '_score'
        df.rename(columns={next_col: next_col_new_name}, inplace=True)
        df[next_col_new_name].apply(pd.to_numeric)

n_students = df.shape[0]

# dictionary w/ question id as key and summary stats for each question
quiz_question_stats = dict()
for q in quiz_question_ids:
    score_col = q + '_score'
    quiz_question_stats[q] = {
        'mean' : df[score_col].mean(), 
        'var' : df[score_col].var(),
        'n_zeros' : sum(df[score_col] == 0.0),
        'n_ones' : sum(df[score_col] == 1.0),
        'zeros_to_ones' : sum(df[score_col] == 0.0)/sum(df[score_col] == 1.0),
        'entropy' : stats.entropy(df[score_col])
    }

# quick comparison of question stats
for key, val in quiz_question_stats.items():
    print("key =", key, "->", val)

# draw a histogram for scores of each question
mpl.style.use('seaborn')
figure, axis = plt.subplots(1, 5, sharey=True)
figure.set_size_inches(13, 3)
for i, q in enumerate(quiz_question_ids):
    score_col = q + '_score'
    #print("i =", i, ", q =", q, ", sum of col =", df[score_col].sum())
    axis[i].hist(df[score_col], bins=6, facecolor='#00447c', edgecolor='black', alpha=0.8)
    axis[i].set_xlabel('score')
    axis[i].set_title('question: ' + q.split('_')[0])
axis[0].set_ylabel('# of people')
#plt.subplots_adjust(left=0.05, right=0.98, bottom=0.15, top=0.9)
plt.tight_layout()
figure.savefig(file_prefix + 'quiz_' + str(chosen_quiz.id) + "_" + datetime.datetime.today().strftime('%Y%m%d') + ".png", dpi=200)
plt.show()


# create euclidean distance for each pair of students using all 5 questions
student_ids = list(df['id'])
student_ids.sort()
quiz_distances = pd.DataFrame(0.0, columns=student_ids, index=student_ids)

for i, id1 in enumerate(student_ids):
    x = df.loc[df.id == id1, df.columns.str.endswith('_score')]
    #print(id1, "values =", x.values)
    for j, id2 in enumerate(student_ids):
        if i < j:
            #print(id2, "values =", y.values)
            y = df.loc[df.id == id2, df.columns.str.endswith('_score')]
            dist = distance.euclidean(x, y)
            #dist = distance.cosine(x, y)
            quiz_distances[id1][id2] = dist
            quiz_distances[id2][id1] = dist
            #print("dist between ", id1, "and", id2, "=", dist) 

mpl.style.use('seaborn')
plt.figure(figsize=(16,16))
#mask = np.zeros_like(quiz_distances)
#mask[np.triu_indices_from(mask)] = True
#sbn.color_palette("crest", as_cmap=True)
sbn.heatmap(
    quiz_distances,
    #mask=mask,
    square=True,
    #cmap='OrRd',
    cmap="YlGnBu",
    linewidth=0.5,
    annot=True,
    cbar=False
)
plt.tight_layout()
plt.rc('font', size=9)
plt.savefig(file_prefix + 'quiz_' + str(chosen_quiz.id) + "_" + datetime.datetime.today().strftime('%Y%m%d') + "_dist_euclid.png", dpi=200)#, bbox_inches='tight')
plt.show()


# Next step is to create a dataframe with 3 columns: student_1_id, student_2_id,
# dist_student1_to_student2, then to find pairs of students to be grouped
# together (being careful not to include a person more than once). There are
# other, better ways to do this, but this will be the most flexible since we may
# want to include other criteria for selecting pairs/small groups. 
# See np.meshgrid for one example of making the grid, ex:
# https://stackoverflow.com/questions/12130883/r-expand-grid-function-in-python


# What was the most missed question? This will be used in the body of the message. 
# Suggest to the user that they look at the output of the histgram for all quiz questions. 
# Also show the following link and suggest that the user click on it to see the full quiz 
# before finalizing their decision on which question to use (link: chosen_quiz.html_url).


# send a message (i.e. a Canvas Conversation) to a person (testing w/ Malcolm)
# Malcolm's canvas id is 31078
recipients = [str(31078)]
message = "Hi Malcolm, \n\n    I hope everything is going well with you. Don't \
mind this message at all, I'm just working on the tool for 2050 to group \
students together for a quick peer-learning session. Using Slack/MS Teams would\
be better, but Canvas is faster to implement and will help to decide whether it\
it is something work pursuing.  If you are interested in seeing it at all, \
I'll try and put it up on github sooner rather than later although no worries if not.\
\n\nHave a good break! "
print(message)

#convo = canvas.create_conversation(recipients, message, subject="test message")
# note: create_convo returns a list, so here convo[0] is the Conversation object
