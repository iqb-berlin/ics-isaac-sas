from abc import ABC,abstractmethod
from pandas import DataFrame
from typing import List
import os
import re
import textdistance as td
import pandas as pd
import sys

# The import must be relative if script is called from elsewhere
ROOT_DIR = os.path.abspath(os.curdir)
if os.path.isfile(ROOT_DIR + "/feature_groups.py"):
    from data import ShortAnswerInstance
else:
    from .data import ShortAnswerInstance


TARGET_DELIMS_PATTERN = re.compile('|'.join(map(re.escape, ["•", "ODER", " / "])))
MEASURES = [
    td.algorithms.edit_based.NeedlemanWunsch(),
    td.algorithms.edit_based.SmithWaterman(),
    td.algorithms.sequence_based.LCSSeq(),
    td.algorithms.sequence_based.LCSStr(),
    td.algorithms.simple.Length(),
    td.algorithms.phonetic.Editex(),
    td.algorithms.phonetic.MRA(),
    td.algorithms.token_based.Overlap(),
    td.algorithms.token_based.Cosine()
]
simCache = {}



class FeatureGroupExtractor(ABC):
    """
        An abstract class providing for FeatureGroupExtractors.
        Subclasses have to implement the extract() method
    """
    @abstractmethod
    def extract(self, instances: List[ShortAnswerInstance]) -> DataFrame:
        return DataFrame()


class SIMGroupExtractor(FeatureGroupExtractor):
    """
        A subclass of FeatureGroupExtractor which provides a method
        to compute similarity values (see the MEASURES variable) between
        "answer" and "itemTargets" and store them as features in a pandas DataFrame.
        For identification purposes, "learnerId" of each ShortAnswerInstance will be stored
        as a separate column ('ID').
    """

    def extract(self, instances: List[ShortAnswerInstance], reference='answer', compar='itemTargets') -> DataFrame:
        """
            Computes similarity values (see the MEASURES variable) between
        "answer" and "itemTargets" and stores them as features in a pandas DataFrame
        :param instances: a list of ShortAnswerInstances
        :return: a pd.DataFrame with similarity features + the learner ID for each ShortAnswerInstance
        """

        # extract student and target answers from ShortAnswerInstances
        st_tgt_answers = [(x.answer, x.itemTargets) for x in instances]
        return pd.DataFrame([self.similarity_features(r, t, MEASURES) for r, t in st_tgt_answers],
                         columns=[type(i).__name__ for i in MEASURES])

    def sim_lookup_str(self, response, a, m):
        return response + "  " + a + " | " + type(m).__name__

    def similarity_features(self, response, targets, measures):

        response = str(response)
        resultScores = []

        for m in measures:
            max_sim = -1.0
            for a in targets:
                a = str(a)
                try:
                    lookup = self.sim_lookup_str(response, a, m)
                    simCache.setdefault(lookup, m.normalized_similarity(response, a))
                    sim = simCache[lookup]
                    if sim > max_sim:
                        max_sim = sim
                except:
                    # this should only happen for German answers and phonetic distance measures
                    print("Error with measure", m, "on strings '", response, "' and '", a, "'", file=sys.stderr)

            resultScores.append(max_sim)

        return resultScores


class BOWGroupExtractor(FeatureGroupExtractor):
    """
        A subclass of GroupFeatureExtractor which extracts bag of words features from
        a list of ShortAnswerInstances and stores them as features in a pandas DataFrame.
        For identification purposes, "learnerId" of each ShortAnswerInstance will be stored
        as a separate column ('ID').
        *** IMPORTANT ***: when instantiating the class, a list of ShortAnswerInstances has to be passed
                   in order for the bag of words to be trained. Subsequent calls to
                   extract() will return features which will be computed based on the trained bag.

    """
    def __init__(self, instances: List[ShortAnswerInstance]):
        self.bag = self.train_bag(" ".join([x.answer for x in instances]))      # trains the bag


    def extract(self, instances: List[ShortAnswerInstance]) -> DataFrame:
        """
            Extract BOW features from a list of ShortAnswerInstances.
        :param instances: a list of ShortAnswerInstances
        :return: a pd.DataFrame with BOW features + the learner ID for each ShortAnswerInstance
        """
        # extract student answers & bow features for them
        bow_feats = self.bow_features([x.answer for x in instances])
        return pd.DataFrame(bow_feats, columns=self.bag)


    def train_bag(self, text, n=500):
        words = [w for w in text.lower().split(" ") if w]
        word_counts = {}
        for w in words:
            if w not in word_counts:
                word_counts[w] = 0.0
            word_counts[w] += 1.0

        sorted_words = sorted(word_counts.keys(), key=lambda x: word_counts[x], reverse=True)
        return sorted_words[:n]

    def bag_representation(self, text):
        text = set(map(lambda w: w.lower(), text.split()))
        return [float(w in text) for w in self.bag]

    def bow_features(self, instances):
        return [self.bag_representation(x) for x in instances]






