from .feature_groups import *
from .data import ShortAnswerInstance
import pandas as pd


short_answ_header_IQB = {'taskId':'task',
          'itemId':'variable.codebook',
          'itemPrompt':'prompt',
          'itemTargets':'targets',
          'learnerId':'ID',
          'answer':'answer',
          'label':'value.coded.binary'}

TARGET_DELIMS_PATTERN = re.compile('|'.join(map(re.escape, ["•", "ODER", " / "])))

def create_short_answer_instances(datafr:pd.DataFrame, columns, header:dict, targets_delimiter=TARGET_DELIMS_PATTERN):
    """
    Creates short answer instances for IQB/Feedbook data.
    Splits targets at "•", "ODER", " / "
    :param datafr: pandas DataFrame with short answer sentences
    :param header: a dict with ShortAnswerInstance variable names mapped to IQB/feedbook column names
    :param targets_delimiter: a compiled regular expression of delimiters, at which to split the target string,
                            default = re.compile('|'.join(map(re.escape, ["•", "ODER", " / "])))
    :return: a list of ShortAnswerInstances
    """
    sh_ans_inst = []
    for row in datafr.iterrows():
        d = ShortAnswerInstance(taskId=row[1][columns.get_loc(header['taskId'])],
                                itemId=row[1][columns.get_loc(header['itemId'])],
                                itemPrompt=row[1][columns.get_loc(header['itemPrompt'])],
                                # todo: added splitting here
                                itemTargets=targets_delimiter.split(row[1][columns.get_loc(header['itemTargets'])]),
                                learnerId=row[1][columns.get_loc(header['learnerId'])],
                                answer=row[1][columns.get_loc(header['answer'])],
                                label=row[1][columns.get_loc(header['label'])])
        sh_ans_inst.append(d)
    return sh_ans_inst

