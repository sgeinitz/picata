import os
import re
import sys
import random
import requests
import time
import pandas as pd
import scipy.stats as stats
import scipy.spatial.distance as distance
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sbn
from datetime import datetime

def selectFromList(paginated_list, item_type="item"):
    """
    A general function that takes a canvasapi paginated_list object
    and lists each item in it, then prompts user to select one item.
    """
    print(f"\nOptions:")
    i = 0
    subobject_list = []
    for i, so in enumerate(paginated_list):
        print(f"[ {i:2d} ] {so}")
        subobject_list.append(so)
    str_index = input(f"\nSelect {item_type} from above using index in square brackets: ")

    if int(str_index) < 0 or int(str_index) > i:
        raise IndexError("Invalid selection")

    return subobject_list[int(str_index)]

def selectCourse(canvas):
    """
    Given a canvas instance object, display a list of courses and prompt
    the user to select a course. The selected course is returned.

    1. First prompt the user to choose between past or current courses.
    2. List the selected type of courses (past or current).
    """

    past_courses = []
    current_courses = []
    current_date = datetime.now()

    for course in canvas.get_courses():
        try:
            course_name = course.name

            # Check start and end dates
            start_date = datetime.strptime(course.start_at, '%Y-%m-%dT%H:%M:%SZ') if course.start_at else None
            end_date = datetime.strptime(course.end_at, '%Y-%m-%dT%H:%M:%SZ') if course.end_at else None

            # Separate past and current courses
            if end_date and current_date > end_date:
                past_courses.append(course)
            elif not end_date or current_date <= end_date:
                current_courses.append(course)

        except Exception as e:
            print(f"Error: {e} - exiting")
            sys.exit(1)

    # Prompt user to select between past and current courses
    print("\nSelect Course Type:")
    print("[ 0 ] Past Courses")
    print("[ 1 ] Current Courses")
    selection = input("\nSelect course type (using index in '[ ]'): ")
    selection = int(re.sub(r'\D', '', selection))

    if selection == 0:
        print("\nPast Courses:")
        for i, course in enumerate(past_courses):
            print(f"[ {i:2d} ] {course.name}")
        valid_courses = past_courses

    elif selection == 1:
        print("\nCurrent Courses:")
        for i, course in enumerate(current_courses):
            print(f"[ {i:2d} ] {course.name}")
        valid_courses = current_courses
    else:
        raise IndexError("Invalid selection format. Please select '0' for past or '1' for current.")

    str_index = input("\nSelect a course from the list above (using index in '[ ]'): ")

    # if not str_index.startswith("[") or not str_index.endswith("]"):
    #    raise ValueError("Invalid selection format. Please use '[ ]' around the index.")
    # Convert input into an integer
    # course_index = int(str_index[1:-1])

    # remove any characters that are not digits
    course_index = int(re.sub(r'\D', '', str_index))

    if course_index < 0 or course_index >= len(valid_courses):
        raise IndexError("Invalid course selection.")

    return canvas.get_course(valid_courses[course_index].id)

def sendMessage(canvas, pica_course, pairs):
    """
    Message template to be sent to student pairs in Canvas. The user should be
    able to customize this message each time the program is run, rather than it
    being hard-coded here. One option is to prompt the user to input the message
    when the program runs. Or, to prompt them to specify an input file that will
    contain the message template.
    """
    message_template = "Hello {},\n  In our upcoming class session the {} of you \
    will meet to work out a problem together. If you don't already know one another, \
    then it may be helpful to plan on meeting in a certain section of the room, or a \
    share a distinguishing feature (e.g. 'I have a red hat on today'). \n\nThere \
    is no preparation required on your part, however, if you want to see the type of \
    problem you'll see today you can refer to the quiz question shown below. Please \
    wait until class for more details. \n\nBest,\nSteve \n \nQuestion from previous quiz: {}"

    message_dict1 = {2: 'two', 3: 'three'}
    subject_str = "Today's quiz review session - " + datetime.today().strftime('%Y.%m.%d')
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

        # Create_convo returns a list, so here convo[0] is the conversation object
        convo = canvas.create_conversation(recipient_canvas_ids, message_str, subject=subject_str)

    return convo


class PicaCourse:
    """ A general class for a course and associated attributes/data. """

    def __init__(self, canvas_course, config, verbose=False):
        """ Retrieve the selected course and get list of all students. """
        self.canvas_course = canvas_course
        self.students = []
        self.verbose = verbose
        student = None
        for i, student in enumerate(self.canvas_course.get_enrollments()):
            # Use print(f"dir(student): {dir(student)}") to see all attributes
            if student.role == 'StudentEnrollment' and student.enrollment_state == 'active' and student.sis_user_id is not None:
                student.user['total_activity_time'] = student.total_activity_time
                student.user['last_activity_at'] = student.last_activity_at
                self.students.append(student.user)
        if verbose:
            print(self.students)

    def saveStudentActivity(self, data_path):
        """ Save student activity data to a CSV file (unfortunately, trying to get more information
        using, say, u = course.get_user(user=id), and then u.get_pages_views() is not allowed). """
        acts = pd.DataFrame(columns=['name', 'id', 'total_activity_mins', 'last_activity_at'])
        for s in self.students:
            acts.loc[len(acts)] = [s['name'], s['id'], s['total_activity_time'] / 60.0, s['last_activity_at']]

        activity_csv = data_path + "course_activity_" + datetime.today().strftime('%Y%m%d') + ".csv"
        acts.to_csv(activity_csv, index=False)

class PicaQuiz:
    """ A class for one quiz and associated attributes/data. """

    def __init__(self, canvas, canvas_quiz, config, verbose=False):
        """ Initialize quiz object by getting all quiz data from Canvas. """
        self.canvas = canvas
        self.canvas_quiz = canvas_quiz
        self.verbose = verbose
        self.config = config
        self.config.quiz_prefix = self.canvas_quiz.title.lower().replace(" ", "_") + "_"
        self.quiz_df = None
        self.n_students = None
        self.question_stats = None
        self.dist_matrix = None
        self.quiz_questions = []  # Can later get text for kth question using quiz_question[k].question_text

        if self.verbose:
            print(f"Quiz title: {self.canvas_quiz.title}")

        for i, quest in enumerate(canvas_quiz.get_questions()):
            self.quiz_questions.append(quest)
            if verbose:
                print(f"Question {i}: {quest}")
        self.quiz_question_ids = [str(c.id) for c in self.quiz_questions]
        self.getQuizData()

    def getQuizData(self):
        """ Download student_analysis csv quiz report. """
        quiz_report_request = self.canvas_quiz.create_report('student_analysis')
        request_id = quiz_report_request.progress_url.split('/')[-1]
        if self.verbose:
            print("type(quiz_report_request) = ", type(quiz_report_request))
            print("quiz_report_request.__dict__ = ", quiz_report_request.__dict__)

        quiz_report_progress = self.canvas.get_progress(request_id)
        while quiz_report_progress.workflow_state != 'completed':
            #print(f"  report progress: {quiz_report_progress.completion}% completed")
            self.progressBar(quiz_report_progress.completion, 100)
            time.sleep(0.1)
            quiz_report_progress = self.canvas.get_progress(request_id)
        self.progressBar(quiz_report_progress.completion, 100)
        print("\nQuiz download complete!")

        quiz_report = self.canvas_quiz.get_quiz_report(quiz_report_request)
        quiz_csv_url = quiz_report.file['url']
        quiz_csv = requests.get(quiz_csv_url)
        csv_name = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + "_" + \
            datetime.today().strftime('%Y%m%d') + "_student_analysis.csv"

        csv = open(csv_name, 'wb')
        for content in quiz_csv.iter_content(chunk_size=2**20):
            if content:
                csv.write(content)
        csv.close()

        self.quiz_df = pd.read_csv(csv_name)

        # rename columns to be shorter, cleaner, and with question_id as a column
        for old_col_name in self.quiz_df.columns:
            new_col_name = old_col_name.split(':')[0].replace(' ', '_').replace('.', '_')
            self.quiz_df.rename(columns={old_col_name: new_col_name}, inplace=True)

        for i, col in enumerate(self.quiz_df.columns):
            if col in self.quiz_question_ids:
                next_col = self.quiz_df.columns[i + 1]
                next_col_new_name = col + '_score'
                self.quiz_df.rename(columns={next_col: next_col_new_name}, inplace=True)
                self.quiz_df[next_col_new_name].apply(pd.to_numeric)

        self.n_students = self.quiz_df.shape[0]

        # dictionary w/ question id as key and summary stats for each question
        self.question_stats = dict()
        for q in self.quiz_question_ids:
            score_col = q + '_score'
            self.question_stats[q] = {
                'mean': self.quiz_df[score_col].mean(),
                'var': self.quiz_df[score_col].var(),
                'n_zeros': sum(self.quiz_df[score_col] == 0.0),
                'n_ones': sum(self.quiz_df[score_col] == 1.0),
                'entropy': stats.entropy(self.quiz_df[score_col])
            }

        if self.verbose:
            for key, val in self.question_stats.items():
                print("key =", key, "->", val)

    def progressBar(self, current, total, bar_length=20):
        """ Displays or updates a console progress bar. """
        progress = current / total
        arrow = '=' * int(progress * bar_length - 1) + '>' if current < total else '=' * bar_length
        spaces = ' ' * (bar_length - len(arrow))
        percent = int(progress * 100)
        sys.stdout.write(f"\r[{arrow}{spaces}] {percent}%")
        sys.stdout.flush()

    def generateQuestionHistograms(self):
        """ Draw a histogram of scores of each question. """
        mpl.style.use('seaborn-v0_8')
        figure, axis = plt.subplots(1, len(self.quiz_question_ids), sharey=True)
        figure.set_size_inches(13, 3)
        for i, q in enumerate(self.quiz_question_ids):
            score_col = q + '_score'
            axis[i].hist(self.quiz_df[score_col], bins=6, facecolor='#00447c', edgecolor='black', alpha=0.8)
            axis[i].set_xlabel('score')
            axis[i].set_title('question: ' + q.split('_')[0])
        axis[0].set_ylabel('# of people')
        plt.tight_layout()  # Or try plt.subplots_adjust(left=0.05, right=0.98, bottom=0.15, top=0.9)
        figure.savefig(self.config.figures_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + "_" +
                       datetime.today().strftime('%Y%m%d') + "_histograms.png", dpi=200)
        plt.close('all')

    def generateDistanceMatrix(self, only_present, distance_type='euclid'):
        """ Calculate vector distance between all possible student pairs. """
        quiz_df_local = self.df_quiz_scores_present.copy() if only_present else self.quiz_df.copy()
        student_ids = list(quiz_df_local['id'])
        student_ids.sort()
        self.dist_matrix = pd.DataFrame(0.0, columns=student_ids, index=student_ids)

        for i, id1 in enumerate(student_ids):
            x = quiz_df_local.loc[quiz_df_local.id == id1, quiz_df_local.columns.str.endswith('_score')].to_numpy().flatten()
            if self.verbose:
                print(id1, "values =", x)
            for j, id2 in enumerate(student_ids):
                if i < j:
                    y = quiz_df_local.loc[quiz_df_local.id == id2, quiz_df_local.columns.str.endswith('_score')].to_numpy().flatten()
                    if self.verbose:
                        print(id2, "    values =", y)
                    if distance_type == 'euclid':
                        dist = distance.euclidean(x, y)
                    elif distance_type == 'cosine':
                        dist = distance.cosine(x, y)
                    if dist == 0:
                        dist = 1E-4
                    #self.dist_matrix.loc[id1][id2] = dist # this won't work with pandas v3
                    self.dist_matrix.loc[id1, id2] = dist
                    self.dist_matrix.loc[id2, id1] = dist

        mpl.style.use('seaborn-v0_8')
        plt.figure(figsize=(16, 16))
        sbn.heatmap(
            self.dist_matrix,
            square=True,
            cmap="YlGnBu",
            linewidth=0.5,
            annot=True,
            cbar=False
        )
        plt.tight_layout()
        plt.rc('font', size=9)
        plt.savefig(self.config.figures_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + "_" +
                    datetime.today().strftime('%Y%m%d') + "_dist_" + distance_type + ".png", dpi=200)
        plt.close()

    def openPresentCSV(self, csv_path=None):
        """ Prompt user for a local CSV file and return a pandas dataframe. """
        if not csv_path:
            csv_path = self.config.data_path

        print("\nCSV Options:")
        # List all files in current directory that begin with the string: 'present_'.
        present_csvs = [f for f in os.listdir(csv_path) if f.startswith('present')]
        present_csvs.sort()
        for i, f in enumerate(present_csvs):
            fstring = f"[ {i:2d} ] {f}" if len(present_csvs) > 10 else f"[ {i} ] {f}"
            if self.verbose:
                print(f"  [ {i:2d} ] {f}")
            print(fstring)

        # Prompt user to select a file from the list above.
        csv_index = input("\nSelect csv of students present from above using index: ")

        print(f"\nSelected csv: {present_csvs[int(csv_index)]}")

        # Open the file and remove those that are not present today, then return this dataframe.
        df_present_all = pd.read_csv(csv_path + present_csvs[int(csv_index)])
        self.df_present = df_present_all[df_present_all['present'] == 1]
        print(f"  *** (double check there are {len(self.df_present)} students present today) ***")

        self.df_quiz_scores_present = pd.merge(self.df_present[['name', 'id']], self.quiz_df, how='left')  # on=['name','id'])
        self.df_quiz_scores_present.fillna(0, inplace=True)  # replace missing values with zero (for people who missed the pre-quiz)
        if self.verbose:
            print(f"self.df_quiz_scores_present.columns = {self.df_quiz_scores_present.columns}")
        assert len(self.df_quiz_scores_present) == len(self.df_present)

    def getPastPairingsCSV(self, csv_path=None):

        """ Prompt for a CSV that contains past pairings for this quiz and return a pandas dataframe. """
        if not csv_path:
            csv_path = self.config.data_path
        print("\nCSV Options:")

        # List all files in current directory that contain the string: 'pairing'.
        pastpairs_csvs = [f for f in os.listdir(csv_path) if 'pairing' in f]
        pastpairs_csvs.sort()
        for i, f in enumerate(pastpairs_csvs):
            fstring = f"[ {i:2d} ] {f}" if len(pastpairs_csvs) > 10 else f"[ {i} ] {f}"
            if self.verbose:
                print(f"  [ {i:2d} ] {f}")
            print(fstring)

        # Prompt user to select a file from the list above.
        csv_index = input("\nSelect csv with student pairings from past quiz using index: ")

        print(f"\nSelected csv: {pastpairs_csvs[int(csv_index)]}")

        # Open the file and return the dataframe
        self.df_past_pairings = pd.read_csv(csv_path + pastpairs_csvs[int(csv_index)])

        # Get list of students who were paired in the past and put into long format
        paired_students1 = self.df_past_pairings[['person1', 'id1']].copy()
        paired_students1.rename(columns={'person1': 'name', 'id1': 'id'}, inplace=True)
        paired_students2 = self.df_past_pairings[['person2', 'id2']].copy()
        paired_students2.rename(columns={'person2': 'name', 'id2': 'id'}, inplace=True)
        paired_students3 = self.df_past_pairings[['person3', 'id3']].copy()
        paired_students3.rename(columns={'person3': 'name', 'id3': 'id'}, inplace=True)

        # Get columns person2, id2, from df_past_pairings and append these rows to paired_students
        paired_students = pd.concat([paired_students1, paired_students2, paired_students3], ignore_index=True)

        # Remove any rows with NaN or -1 values, and reset index
        paired_students.dropna(inplace=True)
        paired_students = paired_students[paired_students['id'] != -1]
        paired_students.reset_index(drop=True, inplace=True)
        self.df_paired_students = paired_students.drop_duplicates()

    def getPastBonusCSV(self, csv_path=None):

        """ Prompt for a CSV that contains past pairings for this quiz and return a pandas dataframe. """
        if not csv_path:
            csv_path = self.config.data_path
        print("\nCSV Options:")

        # List all files in current directory that contain the string: 'pairing'.
        pastbonus_csvs = [f for f in os.listdir(csv_path) if 'w_bonus' in f]
        pastbonus_csvs.sort()
        for i, f in enumerate(pastbonus_csvs):
            fstring = f"[ {i:2d} ] {f}" if len(pastbonus_csvs) > 10 else f"[ {i} ] {f}"
            if self.verbose:
                print(f"  [ {i:2d} ] {f}")
            print(fstring)

        # Prompt user to select a file from the list above.
        csv_index = input("\nSelect csv with past student bonus awards using index: ")

        print(f"\nSelected csv: {pastbonus_csvs[int(csv_index)]}")

        # Open the file and return the dataframe
        self.df_past_bonus = pd.read_csv(csv_path + pastbonus_csvs[int(csv_index)])

    def createStudentPairings(self, method='med', write_csv=True):
        """ Generate student pairings using one of several methods, but not saved unless write_csv is True. """
        dm = self.dist_matrix.copy()
        pairings = []

        while dm.shape[0] > 2:

            # retrieve max entry in each column/row and corresponding index
            # (note that indices and columns are canvas student ids)
            col_maximums = dm.max()
            col_max_indices = dm.idxmax()

            # 'max' is a greedy approach taking largest pair difference first
            if method == 'max':
                person_A = col_maximums.idxmax()
            # 'med' is median difference and generally leads to highest mean diff and lowest variance
            elif method == 'med':
                col_maximums.sort_values(inplace=True)
                person_A = col_maximums.index[len(col_maximums) // 2]
            # 'min' uses conservative approach by taking min pair difference (among maxes) but often leads to high var
            elif method == 'min':
                person_A = col_maximums.idxmin()
            elif method == 'rand':
                people = list(dm.index)
                random.shuffle(people)
                person_A = people[0]
                person_B = people[1]
                pairings.append((person_A, person_B, dm.loc[person_A, person_B]))
            else:
                raise ValueError("vectorDistancePairings(): invalid method")

            if method != 'rand':
                person_B = col_max_indices[person_A]
                pairings.append((person_A, person_B, col_maximums[person_A]))

            dm.drop(index=person_A, axis=0, inplace=True)
            dm.drop(person_A, axis=1, inplace=True)
            dm.drop(index=person_B, axis=0, inplace=True)
            dm.drop(person_B, axis=1, inplace=True)

            assert dm.shape[0] == dm.shape[1]

        # only two people left in dm so they must be paired together
        if dm.shape[0] == 2:
            pairings.append((dm.index[0], dm.index[1], dm.iat[0, 1]))
        # only one person left in dm so add them to the last pair that was created and use max distance among the three 3c2 possible distances among them
        else:
            assert dm.shape == (1, 1)
            temp_tuple = pairings[-1]
            pairings[-1] = (temp_tuple[0], temp_tuple[1], dm.index[0],
                            max(temp_tuple[2], self.dist_matrix.loc[temp_tuple[0], dm.index[0]], self.dist_matrix.loc[temp_tuple[1], dm.index[0]]))

        if self.verbose:
            print("Pairings:")
            print(pairings)

        stats_tmp = [x[-1] for x in pairings]
        mean_pair_dist = sum(stats_tmp) / len(stats_tmp)
        var_pair_dist = sum([(x[-1] - mean_pair_dist)**2 for x in pairings]) / len(stats_tmp)

        if self.verbose:
            print(f"Pairing via {method} method:")
            print(f"    mean(pair distances) = {mean_pair_dist}")
            print(f"     var(pair distances) = {var_pair_dist}")

        if write_csv:
            self.writePairingsCSV(method, pairings)
        return pairings

    def comparePairingMethods(self):
        """ Compare the median, max, min, and rand methods of pairing students. """
        pairs_med = self.createStudentPairings(method='med', write_csv=False)
        pairs_max = self.createStudentPairings(method='max', write_csv=False)
        pairs_min = self.createStudentPairings(method='min', write_csv=False)
        pairs_rand = self.createStudentPairings(method='rand', write_csv=False)
        pairs_med_distances = pd.Series([x[-1] for x in pairs_med])
        pairs_max_distances = pd.Series([x[-1] for x in pairs_max])
        pairs_min_distances = pd.Series([x[-1] for x in pairs_min])
        pairs_rand_distances = pd.Series([x[-1] for x in pairs_rand])

        plt.figure(edgecolor='black')
        fig, axes = plt.subplots(1, 4, figsize=(20, 4))
        fig.patch.set_facecolor('white')
        bin_breaks = [x / 2 for x in range(0, (8 + 1))]
        pairs_med_distances.hist(bins=bin_breaks, ax=axes[0], edgecolor='black')
        pairs_max_distances.hist(bins=bin_breaks, ax=axes[1], edgecolor='black')
        pairs_min_distances.hist(bins=bin_breaks, ax=axes[2], edgecolor='black')
        pairs_rand_distances.hist(bins=bin_breaks, ax=axes[3], edgecolor='black')
        axes[0].set_xlabel('Pairing via: Median-Max Approach')
        axes[1].set_xlabel('Max-Max Approach')
        axes[2].set_xlabel('Min-Max Approach')
        axes[3].set_xlabel('Randomized Pairs')
        axes[1].set_ylim(0, 9)
        axes[0].set_ylim(0, 9)
        axes[2].set_ylim(0, 9)
        axes[3].set_ylim(0, 9)
        axes[0].set_ylabel('# of Student Pairs')
        plt.tight_layout()
        plt.savefig(self.config.figures_path + self.config.quiz_prefix + str(self.canvas_quiz.id) +
                    "_compare_pairing_methods_" + datetime.today().strftime('%Y%m%d') + ".png", dpi=200)
        plt.close()

    def writePairingsCSV(self, method, pairs):
        """ Create an output csv file in data/ with the given student pairings. """
        df = self.df_quiz_scores_present.copy()
        name1 = []
        name2 = []
        name3 = []
        person1 = []
        person2 = []
        person3 = []

        for i, pair in enumerate(pairs):
            name1.append(df.name[df.id == pair[0]].to_string(index=False))
            name2.append(df.name[df.id == pair[1]].to_string(index=False))
            person1.append(pair[0])
            person2.append(pair[1])

            # Only needed for 3-tuple groups since there are 3 possible distances.
            # Note that when there are 3 the first distance is used since first two people were paired intentionally.
            if len(pair) == 2 + 1:
                dists = (self.dist_matrix.loc[pair[0], pair[1]], -1, -1)
            else:
                dists = (self.dist_matrix.loc[pair[0], pair[1]], self.dist_matrix.loc[pair[0], pair[2]], self.dist_matrix.loc[pair[1], pair[2]])

            if self.verbose:
                print(f"pair = {pair}, dists = {dists}")

            if len(pair) == 2 + 1:
                name3.append(None)
                person3.append(-1)
                # print(f"    2-tuple {i+1:2.0f}: {df.name[df.id == pair[0]].to_string(index=False)}, {df.name[df.id == pair[1]].to_string(index=False)}")
            if len(pair) == 3 + 1:
                name3.append(df.name[df.id == pair[2]].to_string(index=False))
                person3.append(pair[2])
                if self.verbose:
                    print(f"    3-tuple {i+1:2.0f}: {df.name[df.id == pair[0]].to_string(index=False)}, \
                          {df.name[df.id == pair[1]].to_string(index=False)}, {df.name[df.id == pair[2]].to_string(index=False)}")
                if self.verbose:
                    print(f"p1, p2, dist = {(pair[0], pair[1], self.dist_matrix.loc[pair[0], pair[1]])}")
                    print(f"p1, p3, dist = {(pair[0], pair[2], self.dist_matrix.loc[pair[0], pair[2]])}")
                    print(f"p2, p3, dist = {(pair[1], pair[2], self.dist_matrix.loc[pair[1], pair[2]])}")

        df_pairs = pd.DataFrame({'person1': name1, 'person2': name2, 'person3': name3,
                                 'id1': person1, 'id2': person2, 'id3': person3, 'distance': [x[-1] for x in pairs]})
        pairs_csv = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + \
            "_pairing_via_" + method + "_" + datetime.today().strftime('%Y%m%d') + ".csv"
        df_pairs.to_csv(pairs_csv, index=False)

    def checkForBonusEarned(self, bonus_amount=0.2):
        """ Check if any students have a distance of 0 with their partner. """

        # Rename the column 'distance' to 'previous_distance' in df_past_pairings
        self.df_past_pairings.rename(columns={'distance': 'previous_distance'}, inplace=True)

        # Create a new column 'distance' in df_past_pairings and set it to 0
        self.df_past_pairings['distance'] = 0.0

        # Create a new column 'bonus' in df_paired_students and set it to 0
        self.df_paired_students['bonus'] = 0.0

        # set bonus_to_add to be added as a percentage of the total points possible, or as a fixed number of points
        if bonus_amount < 1.0:
            bonus = round(bonus_amount * self.canvas_quiz.points_possible)
        else:
            bonus = bonus_amount

        # Iterate through each row of df_past_pairings
        for i, row in self.df_past_pairings.iterrows():
            person1 = row['id1']
            person2 = row['id2']
            dist = self.dist_matrix.loc[person1, person2]
            person3 = row['id3']
            if person3 > 0:
                dist = max(dist, self.dist_matrix.loc[person1, person3], self.dist_matrix.loc[person2, person3])
            self.df_past_pairings.at[i, 'distance'] = dist

            if dist <= 0.01:
                self.df_paired_students.loc[self.df_paired_students['id'] == person1, 'bonus'] = bonus
                self.df_paired_students.loc[self.df_paired_students['id'] == person2, 'bonus'] = bonus
                if person3 > 0:
                    self.df_paired_students.loc[self.df_paired_students['id'] == person3, 'bonus'] = bonus

    def getUserQuizEvents(self):
        quiz_takers = self.quiz_df[['name', 'id']].copy()

        # Define a user_events dataframe with columns 'name', 'id', 'event', 'timestamp'
        user_events = pd.DataFrame(columns=['name', 'id', 'event', 'timestamp'])

        subs = self.canvas_quiz.get_submissions()
        for i, sub in enumerate(subs):
            # Get row from quiz_takers where column 'id' matches sub.user_id
            row = quiz_takers[quiz_takers['id'] == sub.user_id]

            # Get user submission events for this submission
            events = sub.get_submission_events()
            for event in events:
                user_events.loc[len(user_events)] = [row['name'].values[0], sub.user_id, event.event_type, event.created_at]

        user_events_csv = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + \
            "_user_events_" + datetime.today().strftime('%Y%m%d') + ".csv"
        user_events.to_csv(user_events_csv, index=False)

    def awardBonusPoints(self):
        """ Award bonus points to students who received it by setting fudge points. """
        quiz_summary = self.quiz_df[['name', 'id', 'n_correct', 'n_incorrect', 'score']].copy()

        # Left join quiz_summary with df_paired_students on 'id' to get bonus points
        quiz_summary = pd.merge(quiz_summary, self.df_paired_students[['id', 'bonus']], on='id', how='left')

        # Fill NaN values in 'bonus' column with -1.0
        quiz_summary.fillna(-1.0, inplace=True)

        # Create new columns for start, finish, minutes, and score_w_bonus and set them to 0
        quiz_summary['start'] = 'n/a'
        quiz_summary['finish'] = 'n/a'
        quiz_summary['minutes'] = 0.0
        quiz_summary['score_w_bonus'] = 0.0

        # Sort quiz_summary by the second word in 'name' column
        quiz_summary['lastname'] = quiz_summary['name'].str.split().str[1]
        quiz_summary.sort_values(by='lastname', inplace=True)
        quiz_summary.drop(columns='lastname', inplace=True)
        quiz_summary.reset_index(drop=True, inplace=True)

        subs = self.canvas_quiz.get_submissions()
        for i, sub in enumerate(subs):
            # Get row from quiz_summary where column 'id' matches sub.user_id
            row = quiz_summary[quiz_summary['id'] == sub.user_id]

            # Confirm that the sub.score matches row['score'] using an assert statement
            assert abs(sub.score - row['score'].values[0]) < 0.001

            # Set quiz_summary for this user_id and column 'start' with string in sub.started_at
            quiz_summary.at[row.index[0], 'start'] = sub.started_at
            quiz_summary.at[row.index[0], 'finish'] = sub.finished_at
            quiz_summary.at[row.index[0], 'minutes'] = sub.time_spent / 60.0

            # Check if bonus needs to be added
            if row['bonus'].values[0] > 0:

                # Set points before fudget points are added
                newattributes = { 'excused?': True, 'score_before_regrade': sub.score }
                upd1 = sub.set_attributes(newattributes)

                # Now set fudge points
                update_obj = [ { 'attempt': sub.attempt, 'fudge_points': row['bonus'].values[0] } ]
                sub.update_score_and_comments(quiz_submissions=update_obj)

                # Set quiz_summary for this user_id and column 'score_w_bonus' with sub.score + row['bonus']
                quiz_summary.at[row.index[0], 'score_w_bonus'] = row['score'].values[0] + row['bonus'].values[0]

            else:
                quiz_summary.at[row.index[0], 'score_w_bonus'] = row['score'].values[0]

        quiz_summary_csv = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + \
            "_scores_w_bonus_" + datetime.today().strftime('%Y%m%d') + ".csv"
        quiz_summary.to_csv(quiz_summary_csv, index=False)

    # 1) Need to consider making sure this can run multiple times without continually adding bonus 
    #    points (since if it is run twice, then sub.score might include a previously added bonus) one
    #    way is to look and see if sub.fudge_points is already set, and if so, then don't add bonus points
    # 2) also may want to check when get_submissions does not return a student's highest submission, as 
    #    happned with Kevin O'Connel in 4050, Quiz 1B (spring25), where his attempt=3 was 3.93 but get_submissions 
    #    returned attempt=4 with a score of 3.73; could this be addressed with sub.kept_score vs sub.score?
    #    (see https://canvas.instructure.com/doc/api/quiz_submissions.html)
    def reAwardBonusPoints(self):
        """ Re-award bonus points by setting fudge points for the highest submission attempt. """
        past_bonus = self.df_past_bonus.copy()
        past_bonus['new_score'] = past_bonus['score']
        past_bonus['start_new']  = 'n/a'
        past_bonus['finish_new'] = 'n/a'
        past_bonus['minutes_new'] = -1
        past_bonus['new_score_w_bonus'] = past_bonus['score_w_bonus']

        subs = self.canvas_quiz.get_submissions()
        for i, sub in enumerate(subs):

            # no bonus to award if user_id not in past_bonus
            if sub.user_id not in past_bonus['id'].values:
                continue

            # Get row from quiz_summary where column 'id' matches sub.user_id
            row = past_bonus[past_bonus['id'] == sub.user_id]
            if self.verbose:
                print(f"name = {past_bonus.at[row.index[0], 'name']}")
                print(f"  sub.user_id = {sub.user_id}, sub.attempt = {sub.attempt}, sub.score = {sub.score}, sub.fudge_points = {sub.fudge_points}")

            # Update past_bonus df for this user_id
            past_bonus.at[row.index[0], 'new_score'] = sub.score
            past_bonus.at[row.index[0], 'start_new'] = sub.started_at
            past_bonus.at[row.index[0], 'finish_new'] = sub.finished_at
            past_bonus.at[row.index[0], 'minutes_new'] = sub.time_spent / 60.0

            # Check bonus was received before and new score is better than past score (w/o bonus)
            if row['bonus'].values[0] > 0 and sub.score > row['score'].values[0]:

                # Set points before fudget points are added
                newattributes = { 'excused?': True, 'score_before_regrade': sub.score }
                upd1 = sub.set_attributes(newattributes)

                # Now set fudge points
                update_obj = [ { 'attempt': sub.attempt, 'fudge_points': row['bonus'].values[0] } ]
                sub.update_score_and_comments(quiz_submissions=update_obj)

                # Update 'new_score_w_bonus' using sub.score + row['bonus']
                past_bonus.at[row.index[0], 'new_score_w_bonus'] = sub.score + row['bonus'].values[0]

        past_bonus_csv = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + \
            "_scores_w_bonus_new_" + datetime.today().strftime('%Y%m%d') + ".csv"
        past_bonus.to_csv(past_bonus_csv, index=False)
