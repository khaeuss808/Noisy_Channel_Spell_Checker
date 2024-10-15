## Assumptions
I made the following assumptions when constructing my model:
- only have incorrectly spelled words, not words that are real words but are not used as intended
- only one spelling error per input word
- assuming spelling error where first letter is deleted is extremely unlikely and not considered
- the Levenshtein model does not consider transposition errors, so we are not accounting for those here
- assuming no capital letters
## Strengths & Weakness, Improvements
Operating under the above assumptions, my model performs very well, and generates logical answers when insertion, substitution or deletion of one letter in the sentence occurs. However, there are certain situations where my model would not be as strong. In the case where the spelling error is a homophone error (ex. typed "where" but intended to say "wear), my model would not process this correctly. Also, because the Levenshtein model does not consider transposition errors, when i give my function "buisness" as an input, I as a human can tell the user likely meant to type "business", but the function returns "busness". Additionally, if we wanted to incorporate context of our misspelled word in a sentence, using say a bi-directional bigram model, i.e. the word before and after the misspelled word, we could be even more confident in our predicted correct word.