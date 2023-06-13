import datetime
import os
import random
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
    str_index = input(f"\nSelect {item_type} from above using index in square brackets: ")

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

        # Create_convo returns a list, so here convo[0] is the conversation object
        convo = canvas.create_conversation(recipient_canvas_ids, message_str, subject=subject_str)

    return convo


class PicaCourse:
    """ A general class for a course and associated attributes/data. """

    def __init__(self, canvas_course, config, verbose=False):
        """ Retrieve the selected course and get list of all students. """
        self.canvas_course = canvas_course
        self.students = []
        enrollments = canvas_course.get_enrollments()
        student = None
        for i, student in enumerate(enrollments):
            # Use print(f"dir(student): {dir(student)}") to see all attributes
            if student.role == 'StudentEnrollment' and student.enrollment_state == 'active' and student.sis_user_id is not None:
                student.user['total_activity_time'] = student.total_activity_time
                student.user['last_activity_at'] = student.last_activity_at
                self.students.append(student.user)
        if verbose:
            print(self.students)


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
            print(f"  report progress: {quiz_report_progress.completion}% completed")
            time.sleep(0.5)
            quiz_report_progress = self.canvas.get_progress(request_id)

        quiz_report = self.canvas_quiz.get_quiz_report(quiz_report_request)
        quiz_csv_url = quiz_report.file['url']
        quiz_csv = requests.get(quiz_csv_url)
        csv_name = self.config.data_path + self.config.quiz_prefix + str(self.canvas_quiz.id) + "_" + \
            datetime.datetime.today().strftime('%Y%m%d') + "_student_analysis.csv"

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

    def generateQuestionHistograms(self):
        """ Draw a histogram of scores of each question. """
        mpl.style.use('seaborn')
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
                       datetime.datetime.today().strftime('%Y%m%d') + "_histograms.png", dpi=200)
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
                    self.dist_matrix[id1][id2] = dist
                    self.dist_matrix[id2][id1] = dist

        mpl.style.use('seaborn')
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
                    datetime.datetime.today().strftime('%Y%m%d') + "_dist_" + distance_type + ".png", dpi=200)
        plt.close()

    def openPresentCSV(self, csv_path=None):
        """ Prompt user for a local CSV file and return a pandas dataframe. """
        if not csv_path:
            csv_path = self.config.data_path

        # List all files in current directory that begin with the string: 'present_'.
        #present_csvs = [f for f in os.listdir(csv_path) if os.path.isfile(f) and f.startswith('present')]
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
                    "_compare_pairing_methods_" + datetime.datetime.today().strftime('%Y%m%d') + ".png", dpi=200)
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
            "_pairing_via_" + method + "_" + datetime.datetime.today().strftime('%Y%m%d') + ".csv"
        df_pairs.to_csv(pairs_csv, index=False)
