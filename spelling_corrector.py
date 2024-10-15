import numpy as np


def spelling_corrector(bad_word):
    additions = np.genfromtxt(
        "additions.csv", delimiter=",", names=True, dtype=None, encoding="utf-8"
    )
    deletions = np.genfromtxt(
        "deletions.csv", delimiter=",", names=True, dtype=None, encoding="utf-8"
    )

    substitutions = np.genfromtxt(
        "substitutions.csv", delimiter=",", names=True, dtype=None, encoding="utf-8"
    )
    bigram = np.genfromtxt(
        "bigrams.csv", delimiter=",", names=True, dtype=None, encoding="utf-8"
    )
    unigrams = np.genfromtxt(
        "unigrams.csv", delimiter=",", names=True, dtype=None, encoding="utf-8"
    )
    alphabet_list = unigrams["unigram"]

    all_candidates = get_edits(bad_word, alphabet_list)
    all_words_in_universe = get_all_words()
    poss_candidates = get_posscandidates(all_words_in_universe, all_candidates)
    probs_of_candidate_words = candidate_words_probs(
        poss_candidates, all_words_in_universe
    )  # P(w)

    probs_of_candidate_errors = probs_of_errors(
        poss_candidates, additions, deletions, substitutions, bigram, unigrams
    )  # P(x|w)
    product_of_probs = final_prob_calc(
        probs_of_candidate_words, probs_of_candidate_errors
    )

    return max(product_of_probs, key=product_of_probs.get)


def final_prob_calc(probs_of_words, probs_of_errors):
    final_prob_dict = {}
    # multiplying p(x|w) * p(w), also multiplying by 10**9 so they arent so tiny incase of truncating issues
    for key in probs_of_words:
        final_prob_dict[key] = probs_of_words[key] * probs_of_errors[key] * (10**9)

    return final_prob_dict


def probs_of_errors(
    poss_candidates, additions, deletions, substitutions, bigrams, unigrams
):
    error_probs = {}
    for key, sub_dict in poss_candidates.items():
        for sub_key in sub_dict.keys():
            if sub_key.startswith("d"):  # deletion error!
                if (
                    key in error_probs
                ):  # in a case where there are two error paths to get to the same word
                    error_probs[key] = max(
                        error_probs[key], deletion_prob(sub_key, deletions, bigrams)
                    )
                else:
                    error_probs[key] = deletion_prob(sub_key, deletions, bigrams)

            elif sub_key.startswith("s"):  # substitution error!
                if key in error_probs:
                    error_probs[key] = max(
                        error_probs[key],
                        substitution_prob(sub_key, substitutions, unigrams),
                    )
                else:
                    error_probs[key] = substitution_prob(
                        sub_key, substitutions, unigrams
                    )

            elif sub_key.startswith("a"):  # addition/insertion error!
                if key in error_probs:
                    error_probs[key] = max(
                        error_probs[key], addition_prob(sub_key, additions, unigrams)
                    )
                else:
                    error_probs[key] = addition_prob(sub_key, additions, unigrams)

    return error_probs


def deletion_prob(errorcode, deletions_data, bigrams_data):
    errorcode = errorcode.split(":")[1]  # so errorcode would be like #a
    wiminus1 = errorcode[0]
    wi = errorcode[1]
    if wiminus1 == "#":
        return 0  # one of my assumptions is that none of our words will ever begin with an error because it doesnt appear in bigrams
    denom_count = bigrams_data[bigrams_data["bigram"] == errorcode]["count"][0]

    try:  # doing this instead of just calling whats inside try because I tried to find rc in the substiutions.csv and saw it didnt exist there
        del_count = deletions_data[
            (deletions_data["prefix"] == wiminus1) & (deletions_data["deleted"] == wi)
        ]["count"][0]
    except IndexError:
        del_count = 0

    return del_count / denom_count


def substitution_prob(errorcode, substitutions_data, unigrams_data):
    errorcode = errorcode.split(":")[1]
    xi = errorcode[0]
    wi = errorcode[1]
    denom_count = unigrams_data[unigrams_data["unigram"] == wi]["count"][0]
    try:  # doing this instead of just calling whats inside try because I tried to find rc in the substiutions.csv and saw it didnt exist there
        subs_count = substitutions_data[
            (substitutions_data["original"] == xi)
            & (substitutions_data["substituted"] == wi)
        ]["count"][0]
    except IndexError:
        subs_count = 0
    return subs_count / denom_count


def addition_prob(errorcode, additions_data, unigrams_data):
    errorcode = errorcode.split(":")[1]
    wiminus1 = errorcode[0]
    xi = errorcode[1]
    denom_count = unigrams_data[unigrams_data["unigram"] == wiminus1]["count"][0]

    try:  # doing this instead of just calling whats inside try because I tried to find rc in the substiutions.csv and saw it didnt exist there
        ins_count = additions_data[
            (additions_data["prefix"] == wiminus1) & (additions_data["added"] == xi)
        ]["count"][0]
    except IndexError:
        ins_count = 0

    return ins_count / denom_count


def candidate_words_probs(poss_candidates, all_words_in_universe):
    """this is finding p(w) for all our possible candidate words"""
    wordprob_inuniverse = {}

    for word in poss_candidates.keys():
        wordprob_inuniverse[word] = all_words_in_universe[word] / sum(
            all_words_in_universe.values()
        )

    return wordprob_inuniverse


def get_posscandidates(allwordsinuniverse, all_candidate_lst):
    """given the words that exist, which of the combinations of error spellings are real words"""
    possible_candidates = {}
    for error_type, word in all_candidate_lst:
        if word in allwordsinuniverse:
            if word not in possible_candidates:
                possible_candidates[word] = {}

            possible_candidates[word][error_type] = 0

    return possible_candidates


def get_all_words():
    """basically creates a corpus of all the words in the universe of this function"""
    # get list of all words that exist in this world
    with open("count_1w.txt", "r") as file:
        lines = file.readlines()
    allwords_freq = {}
    for line in lines:
        # Split each line by tab ('\t') to separate the word and its frequency, then put in my dictionary
        word, frequency = line.split("\t")
        allwords_freq[word] = int(frequency)

    return allwords_freq


def get_edits(original: str, characters: list[str]) -> list[tuple[str, str]]:
    """This is Patrick's Function"""
    edits = []

    # generate deletions
    for idx, char in enumerate(original):
        previous_char = original[idx - 1] if idx > 0 else "#"
        edits.append((f"d:{previous_char}{char}", original[:idx] + original[idx + 1 :]))

    # generate substitutions
    for idx, old_char in enumerate(original):
        for new_char in characters:
            edits.append(
                (
                    f"s:{old_char}{new_char}",
                    original[:idx] + new_char + original[idx + 1 :],
                )
            )

    # generate additions
    for idx, char in enumerate("#" + original):
        for new_char in characters:
            edits.append(
                (
                    f"a:{char}{new_char}",
                    original[:idx] + new_char + original[idx:],
                )
            )

    return edits


if __name__ == "__main__":
    words = [
        "acress",
        "bouy",
        "buisness",
        "catagory",
        "dissapoint",
        "freiend",
        "grat",
        "where",
    ]
    for word in words:
        print("You typed " + word + ". Did you mean " + spelling_corrector(word) + "?")


# MY ASSUMPTIONS
# only have incorrectly spelled words, not words that are real words but are not used as intended
# only one spelling error per word
# assuming spelling error where first letter is deleted is extremely unlikely and not considered
# the Levenshtein model does not consider transposition errors, so we are not accounting for those here
# assuming no capital letters

# how do we treat the #a in our programming?
