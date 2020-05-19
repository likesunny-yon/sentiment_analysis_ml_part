import numpy as np
import pandas as pd
import re
from spellchecker import SpellChecker
from spacy.matcher import Matcher
from collections import OrderedDict
from sklearn.metrics.pairwise import cosine_similarity

def feature_extraction(df, ft_model, nlp):    
    # Extracting all the single nouns in the corpus
    all_nouns = []

    for review in df['spacyObj']:
        for token in review:
            if token.pos_ == "NOUN":
                all_nouns.append(token.text)
        
    all_nouns = pd.Series(all_nouns)
    unique_nouns = all_nouns.value_counts()

    noun_phrases = []
    
    patterns = [
        [{'TAG': 'NN'}, {'TAG': 'NN'}]
    ]

    matcher = Matcher(nlp.vocab)
    matcher.add('NounPhrasees', patterns)

    for review in df['spacyObj']:
        matches = matcher(review)

        for match_id, start, end in matches:
            noun_phrases.append(review[start:end].text)
            
    noun_phrases = pd.Series(noun_phrases)
    unique_noun_phrases = noun_phrases.value_counts()
            
    # Remove nouns with single or double character
    for noun in unique_nouns.index:
        if len(noun) < 3 or re.match(r".*[0-9].*", noun) is not None:
            del unique_nouns[noun]
            
    # Extracting Top Features
    
    top2 = len(unique_nouns)*0.02
    top2 = int(top2)
    
    top_features = unique_nouns[0:top2]
    
    features_bucket = OrderedDict()
    
    top_features_list = list(top_features.keys())
    top_features_set = set(top_features.keys())
    unique_noun_phrases_set = set(unique_noun_phrases.keys())
    
    for feature1 in top_features_list:
        for feature2 in top_features_list:
            feature_phrase = feature1 + ' ' + feature2
            
            if feature1 in top_features_set and feature2 in top_features_set and feature_phrase in unique_noun_phrases_set:
                # If the condition is true, we have identified a noun phrase which is a combination of two nouns
                # in the top_features. So one of the nouns cn be eliminated from top features.

                # Ex. if "battery life" is found, then "life" can be eliminated from top features as it is not a feature 
                # by itself. It is just part of the feature "battery life"

                # Now we need to find out if frequency of the lesser occuring noun (in our ex., the word "life") matches
                # with the frequency of the noun phrase (in our ex., "battery life") by a certain confidence. 
                # If it does so, then we can be sure that the lesser occuring noun occurs only in that particular noun_phrase
                # i.e in our ex "life" occurs primaryly in the phrase "battery life"

                lesser_occurring_noun = ""
                often_occurring_noun = ""
                if unique_nouns[feature1] < unique_nouns[feature2]:
                    lesser_occurring_noun = feature1
                    often_occurring_noun = feature2
                else:
                    lesser_occurring_noun = feature2
                    often_occurring_noun = feature1

                # assuming confidence interval of 40%
                # i.e. 40% of the occurances of word "life" is as a part of the noun phrase "battery life"

                if unique_noun_phrases[feature_phrase]/unique_nouns[lesser_occurring_noun] > 0.4:
                    try:
                        if often_occurring_noun not in features_bucket:
                            features_bucket[often_occurring_noun] = []
                        features_bucket[often_occurring_noun].append(lesser_occurring_noun)
                        top_features_set.remove(lesser_occurring_noun)
                        print(lesser_occurring_noun)
                    except BaseException as error:
                        print(error)
                        continue
    
    main_features = list(features_bucket.keys())
    top_features_to_add = set(top_features_list[:20])
    
    for feature1 in top_features_list[:20]:
        for feature2 in main_features:
            if feature1 not in features_bucket and feature1 in top_features_set:
                similarity =  cosine_similarity(ft_model.get_word_vector(feature1).reshape(1, -1), 
                                                   ft_model.get_word_vector(feature2).reshape(1, -1))
                if similarity[0][0] > 0.64:
                    top_features_to_add.discard(feature1)

            else:
                top_features_to_add.discard(feature1)

    for feature in top_features_to_add:
        features_bucket[feature] = []
        
    for main_noun in features_bucket.keys():
        top_features_set.remove(main_noun)
        
    top_features_copy = list(top_features_set)
    
    main_features = features_bucket.keys()
    for feature2 in top_features_copy:
        best_similarity = 0
        most_matching_main_feature = ""

        for feature1 in main_features:
            if feature2 in top_features_set:
                similarity =  cosine_similarity(ft_model.get_word_vector(feature1).reshape(1, -1), 
                                               ft_model.get_word_vector(feature2).reshape(1, -1))
                if similarity[0][0] <= 0.99 and similarity[0][0] > 0.64:
                    if similarity[0][0] > best_similarity:
                        best_similarity = similarity[0][0]
                        most_matching_main_feature = feature1

        if best_similarity != 0 and most_matching_main_feature != "":       
            features_bucket[most_matching_main_feature].append(feature2)
            top_features_set.remove(feature2)
            
    final_features = list(features_bucket.items())
    
    final_features_with_counts = []
    for feature in final_features:
        count = unique_nouns[feature[0]]
        final_features_with_counts.append((feature, count))

    final_features_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    final_features = OrderedDict()
    for feature, count in final_features_with_counts:
        final_features[feature[0]] = feature[1]
    
    return final_features