from feature_groups import *
from data import ShortAnswerInstance
import argparse
import time

# TODO: I am using 'learnerId':'answerID', because there are no learner IDs in the test file
header = {'taskId':'subTask','itemId':'taskField','itemPrompt':'prompt','itemTargets':'target','learnerId':'answerID','answer':'answer', 'label':'correct'}


def parse_instances(filename, sep= '\t'):
    return pd.read_csv(filename,
                         dtype={'taskId':str,'itemId':str,'itemPrompt':str,' itemTargets':str,'learnerId':str,'answer':str,
                                'label':str}, encoding='utf8', sep=sep)

def create_short_answer_instances(datafr:pd.DataFrame):
    sh_ans_inst = []
    for row in datafr.iterrows():
        d = ShortAnswerInstance(taskId=row[1][cols.get_loc(header['taskId'])],
                                itemId=row[1][cols.get_loc(header['itemId'])],
                                itemPrompt=row[1][cols.get_loc(header['itemPrompt'])],
                                itemTargets=[row[1][cols.get_loc(header['itemTargets'])]],
                                learnerId=row[1][cols.get_loc(header['learnerId'])],
                                answer=row[1][cols.get_loc(header['answer'])],
                                label=row[1][cols.get_loc(header['label'])])
        sh_ans_inst.append(d)
    return sh_ans_inst


def compute_elapsed_time(elapsed_time_sec):
    return "{}:{:>02}:{:>05.2f}".format(int(elapsed_time_sec / 3600), int((elapsed_time_sec % 3600) / 60),
                                        elapsed_time_sec % 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test feature extraction')
    parser.add_argument('train', type=str, help='file containing short answer training data')
    parser.add_argument('test', type=str, help='file containing short answer test data')
    args = parser.parse_args()

    s = time.time()
    train_data = parse_instances(args.train)
    data_as_instances = []
    cols = train_data.columns

    # create an instance for each row
    train_data_instances = create_short_answer_instances(train_data)

    # extract sim features
    sim_extractor = SIMGroupExtractor()
    d = sim_extractor.extract(train_data_instances)
    e = time.time()
    print("Sim extractor runtime: ", compute_elapsed_time(e-s))
    # train bow bag on TRAINING data
    bow_extractor = BOWGroupExtractor(train_data_instances)        # the bag is trained in the constructor

    # load and convert TEST data to ShortAnswerInstances
    test_data = parse_instances(args.test, sep=',')
    test_data_instances = create_short_answer_instances(test_data)
    print(test_data_instances)
    print()

    # extract bow features from TEST data
    dfr = bow_extractor.extract(test_data_instances)

    # save feats to file
    d.to_csv("testing/sim_train.tsv", sep='\t', encoding='utf8', index=False)
    print("Saved sim features to testing/sim_test.tsv")

    dfr.to_csv("testing/bow_test.tsv", sep='\t', encoding='utf8', index=False)
    print("Saved bow features to testing/bow_test.tsv")