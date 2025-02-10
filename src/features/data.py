from pydantic import BaseModel
from typing import List, Optional

class ShortAnswerInstance(BaseModel):
    """
    A single short answer instance, containing all the context needed to evaluate it.

    Attributes
    ----------
    taskId : str
        a string representing the task this answer was produced in
    itemId : str 
        a string representing the item this answer was produced for
    itemPrompt : str
        the prompt string (question) the answer was given in response for
    itemTargets : List[str]
        a list of correct reference answers for the current item
    learnerId: str
        a string identifying the learner who gave the answer
    answer: str
        the answer string itself
    label: Optional[str]
        an optional label expressing the classification (e.g. correct/incorrect) for this answer, needed for training (manual) and produced by prediction (automatic)
    
    """
    
    taskId: str
    itemId: str
    itemPrompt: str
    itemTargets: List[str]
    learnerId: str
    answer: str
    label: Optional[str]
