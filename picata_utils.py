import datetime
import requests
import time
import pandas as pd
import scipy.stats as stats
import scipy.spatial.distance as distance
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sbn


def selectFromList(paginated_list, item_type="item"):
    """ 
    A general function that takes a canvasapi paginated_list object 
    and lists each item in it, then prompts user to select one item. 
    """
    i = 0
    subobject_list = []
    for i, so in enumerate(paginated_list):
        print(f"[ {i:2d} ] {so}")
        subobject_list.append(so)
    str_index = input(f"Select {item_type} using index (shown in '[]'): ")

    if int(str_index) < 0 or int(str_index) >= i:
        raise IndexError("Invalid selection")

    return subobject_list[int(str_index)]

        
def selectCourse(canvas):
    """
    Given a canvas instance object, display a list of courses and prompt
    the user to select a course. The selected course is returned.
    """
    valid_courses = []
    for course in canvas.get_courses():
        try:
            # Exclude expired courses without names
            course.name
            valid_courses.append(course)
        except Exception:
            pass
    
    for i, course in enumerate(valid_courses):
        print(f"[ {i:2d} ] {course.name}")
    str_index = int(input("Select a course from the list above (using index in \'[]\'): "))

    if int(str_index) < 0 or int(str_index) >= len(valid_courses):
        raise IndexError("Invalid selection")

    return canvas.get_course(valid_courses[str_index].id)


def sendMessage(pica_course, pairs):
    # Message template to be sent to student pairs in Canvas. The user should be
    # able to customize this message each time the program is run, rather than it
    # being hard-coded here. One option is to prompt the user to input the message
    # when the program runs. Or, to prompt them to specify an input file that will
    # contain the message template.
    message_template = "Hello {},\n  In our upcoming class session the {} of you \
    will meet to work out a problem together. If you don't already know one another, \
    then it may be helpful to plan on meeting in a certain section of the room, or a \
    share a distinguishing feature (e.g. 'I have a red hat on today'). \n\nThere \
    is no preparation required on your part, however, if you want to see the type of \
    problem you'll see today you can refer to the quiz question shown below. Please \
    wait until class for more details. \n\nBest,\nSteve \n \nQuestion from previous quiz: {}"

    message_dict1 = {2: 'two', 3:'three'}
    subject_str = "Today's quiz review session - " + datetime.datetime.today().strftime('%Y.%m.%d')
    question_text = "A question from the quiz will be shown here."

    # Individual messages to be sent
    for pair in pairs:
        num_students = len(pair) - 1
        recipient_canvas_ids = [str(id) for id in pair[0:-1]]
        print("recipients =", recipient_canvas_ids)
        names = [pica_course.canvas_course.get_user(id).name.split()[0] for id in pair[0:-1]]
        names.sort()
        print("names =", names)
        names_str = ", ".join(names)
        message_str = message_template.format(names_str, message_dict1[num_students], question_text)
        print("message =")
        print(message_str)
        #convo = canvas.create_conversation(recipient_canvas_ids, message_str, subject=subject_str)

    # Send a test message (i.e. a Canvas Conversation) to M and S (June 30, 2021)
    #recipients = [str(31078), str(42374)]
    #num_students = 2
    #names = ['S, M']
    #names_str = ", ".join(names)
    #message_str = message_template.format(names_str, message_dict1[num_students], question_text)
    #convo = canvas.create_conversation(recipients, message_str, subject=subject_str)
    #convo = canvas.create_conversation(recipients, message, subject="test message")
    # note: create_convo returns a list, so here convo[0] is the Conversation object
    return None


class PicaCourse:

    def __init__(self, canvas_course, config, verbose=False):
        self.canvas_course = canvas_course
        self.students = []
        enrollments = canvas_course.get_enrollments()
        student = None
        for i, student in enumerate(enrollments):
            if student.role == 'StudentEnrollment' and student.enrollment_state == 'active' and student.sis_user_id != None:
                student.user['total_activity_time'] = student.total_activity_time
                student.user['last_activity_at'] = student.last_activity_at
                self.students.append(student.user)
            #print(f"[ {i:2d} ] {student}")    
            #print(f"  student.role = {student.role}")
            #print(f"  student.user = {student.user}")
            #print(f"  student.enrollment_state = {student.enrollment_state}")
            #print(f"  student.last_activity_at = {student.last_activity_at}")
            #print(f"  student.type = {student.type}")
        #print(f"dir(student): {dir(student)}")
        #print(self.students)


class PicaQuiz:
    """ A class for one quiz and associated attributes/data. """
    
    def __init__(self, canvas, canvas_quiz, config, verbose=False):
        self.canvas = canvas
        self.canvas_quiz = canvas_quiz
        self.verbose = verbose
        self.config = config
        self.quiz_df = None
        self.n_students = None
        self.question_stats = None
        self.dist_matrix = None
        self.quiz_questions = []
        # quiz_questions is a list of all quiz questions (rather than retrieving questions
        # from a SubmissionEvent object). This will be used later on when sending messages 
        # to students about a specific question (e.g. quiz_question[k].question_text). 
        for i, quest in enumerate(canvas_quiz.get_questions()):
            self.quiz_questions.append(quest)
            if verbose:
                print(f"Question {i}: {quest}")
        self.quiz_question_ids = [str(c.id) for c in self.quiz_questions]
        self.getQuizData(verbose=verbose)


    def getQuizData(self, verbose=False):
        """ Download student_analysis csv quiz report. """
        quiz_report_request = self.canvas_quiz.create_report('student_analysis')
        request_id = quiz_report_request.progress_url.split('/')[-1]
        if verbose:
            print("type(quiz_report_request) = ", type(quiz_report_request))
            print("quiz_report_request.__dict__ = ", quiz_report_request.__dict__)
        
        quiz_report_progress = self.canvas.get_progress(request_id)
        while quiz_report_progress.workflow_state != 'completed':
            print(f"\nQuiz report progress: {quiz_report_progress.completion}% completed")
            time.sleep(0.5)
            quiz_report_progress = self.canvas.get_progress(request_id)

        quiz_report = self.canvas_quiz.get_quiz_report(quiz_report_request)
        quiz_csv_url = quiz_report.file['url']
        quiz_csv = requests.get(quiz_csv_url)
        csv_name = self.config.file_prefix + str(self.canvas_quiz.id)  + "_" + \
                                   datetime.datetime.today().strftime('%Y%m%d') + "_student_analysis.csv"
        csv = open(csv_name, 'wb') 
        for content in quiz_csv.iter_content(chunk_size=2^20):
            if content:
                csv.write(content)
        csv.close()

        self.quiz_df = pd.read_csv(csv_name)

        # rename columns to be shorter, cleaner, and with question_id as a column
        for old_col_name in self.quiz_df.columns:
            new_col_name = old_col_name.split(':')[0].replace(' ', '_').replace('.', '_')
            self.quiz_df.rename(columns={old_col_name: new_col_name}, inplace=True)

        for i,col in enumerate(self.quiz_df.columns):
            if col in self.quiz_question_ids:
                next_col = self.quiz_df.columns[i+1]
                next_col_new_name = col + '_score'
                self.quiz_df.rename(columns={next_col: next_col_new_name}, inplace=True)
                self.quiz_df[next_col_new_name].apply(pd.to_numeric)

        self.n_students = self.quiz_df.shape[0]

        # dictionary w/ question id as key and summary stats for each question
        self.question_stats = dict()
        for q in self.quiz_question_ids:
            score_col = q + '_score'
            self.question_stats[q] = {
                'mean' : self.quiz_df[score_col].mean(),
                'var' : self.quiz_df[score_col].var(),
                'n_zeros' : sum(self.quiz_df[score_col] == 0.0),
                'n_ones' : sum(self.quiz_df[score_col] == 1.0),
                'entropy' : stats.entropy(self.quiz_df[score_col])
            }

        if verbose:
            for key, val in self.question_stats.items():
                print("key =", key, "->", val)


    def generateQuestionHistograms(self, show_plot=True, verbose=False):
        """ Draw a histogram of scores of each question. """
        mpl.style.use('seaborn')
        figure, axis = plt.subplots(1, len(self.quiz_question_ids), sharey=True)
        figure.set_size_inches(13, 3)
        for i, q in enumerate(self.quiz_question_ids):
            score_col = q + '_score'
            #print("i =", i, ", q =", q, ", sum of col =", df[score_col].sum())
            axis[i].hist(self.quiz_df[score_col], bins=6, facecolor='#00447c', edgecolor='black', alpha=0.8)
            axis[i].set_xlabel('score')
            axis[i].set_title('question: ' + q.split('_')[0])
        axis[0].set_ylabel('# of people')
        #plt.subplots_adjust(left=0.05, right=0.98, bottom=0.15, top=0.9)
        plt.tight_layout()
        figure.savefig(self.config.file_prefix + str(self.canvas_quiz.id) + "_" + \
                       datetime.datetime.today().strftime('%Y%m%d') + "_histograms.png", dpi=200)

        if show_plot:
            plt.show()


    def generateDistanceMatrix(self, show_plot=True, verbose=False, distance_type='euclid'):
        """ Calculate vector distance between all possible student pairs. """
        student_ids = list(self.quiz_df['id'])
        student_ids.sort()
        self.dist_matrix = pd.DataFrame(0.0, columns=student_ids, index=student_ids)

        for i, id1 in enumerate(student_ids):
            x = self.quiz_df.loc[self.quiz_df.id == id1, self.quiz_df.columns.str.endswith('_score')].to_numpy().flatten()
            #print(id1, "values =", x.values)
            for j, id2 in enumerate(student_ids):
                if i < j:
                    #print(id2, "values =", y.values)
                    y = self.quiz_df.loc[self.quiz_df.id == id2, self.quiz_df.columns.str.endswith('_score')].to_numpy().flatten()
                    if distance_type == 'euclid':
                        dist = distance.euclidean(x, y)
                    elif distance_type == 'cosine':
                        dist = distance.cosine(x, y)
                    if dist == 0:
                        dist = 1E-4
                    self.dist_matrix[id1][id2] = dist
                    self.dist_matrix[id2][id1] = dist

        mpl.style.use('seaborn')
        plt.figure(figsize=(16,16))
        #mask = np.zeros_like(quiz_distances)
        #mask[np.triu_indices_from(mask)] = True
        #sbn.color_palette("crest", as_cmap=True)
        sbn.heatmap(
            self.dist_matrix,
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
        plt.savefig(self.config.file_prefix + str(self.canvas_quiz.id) + "_" + \
                    datetime.datetime.today().strftime('%Y%m%d') + "_dist_" + distance_type + ".png", dpi=200)#, bbox_inches='tight')

        if show_plot:
            plt.show()
