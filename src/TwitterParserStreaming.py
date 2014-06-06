'''
Created on 21 May 2014

@author: theopavlakou
'''
###########################################################################################################################
## A parser for the twitter data file with all the JSON data. Reads in the JSON
## data, each line representing a Tweet, in a streaming manner and finds words
## that most probably best describe an event that is taking place.
## Each window alongside the set of words, the score and the dates are stored
## in a pickle file.
############################################################################################################################
from DictionaryOfWords import DictionaryOfWords
from TweetRetriever import TweetRetriever
from MatrixBuilder import MatrixBuilder
from TPowerAlgorithm import TPowerAlgorithm
import time
import pickle
from copy import deepcopy
from DictionaryComparator import DictionaryComparator
import sys

commandLineArguments = sys.argv

if len(commandLineArguments) < 5:
    print("You need input 4 arguments:")
    print("JSON_file_name size_of_window batch_size desired_sparsity")
    sys.exit()

####################################################
#  Initialize the constants
####################################################
# The first argument is always the name of the script. In this case
# TwitterParserStreaming.py
if commandLineArguments[1] == "":
    jsonFileName = '/Users/theopavlakou/Documents/Imperial/Fourth_Year/MEng_Project/TWITTER Research/Data (100k tweets from London)/ProjectApplication/src/Tweet_Files/tweets_ny'
else:
    jsonFileName = commandLineArguments[1]

# The number of Tweets that are to be considered per calculation
try:
    sizeOfWindow = int(commandLineArguments[2])
except ValueError as ve:
    print("------ " + str(ve) + " ------ ")
    print("------ Could not convert " + commandLineArguments[2] + " to an integer. ------")
    print("------ Setting size of window to 10000. ------")
    sizeOfWindow = 10000

# The shift size (measured as the number of Tweets) of the window
try:
    batchSize = int(commandLineArguments[3])
except ValueError as ve:
    print("------ " + str(ve) + " ------ ")
    print("------ Could not convert " + commandLineArguments[3] + " to an integer. ------")
    print("------ Setting batch size to 1000. ------")
    batchSize = 1000

# The number of words in the Bag-Of-Words
numberOfWords = 3000
# The number of words per window
try:
    desiredSparsity = int(commandLineArguments[4])
except ValueError as ve:
    print("------ " + str(ve) + " ------ ")
    print("------ Could not convert " + commandLineArguments[4] + " to an integer. ------")
    print("------ Setting desired sparsity to 10. ------")
    desiredSparsity = 10

# TODO: Get rid of ./Pickles as this isn't in the repository.
# The output pickle file name. CHANGE to the desired location.
pickleFileName = "./Pickles/pCPickle_" + str(sizeOfWindow) + "_" + str(batchSize) + ".pkl"
# Controls the message output. A higher value means that more will be displayed.
verbose = 3

####################################################
#  Initialize the objects
####################################################
tweetRetriever = TweetRetriever(jsonFileName, sizeOfWindow, batchSize)
tweetRetriever.initialise()
tPAlgorithm = TPowerAlgorithm()
matrixBuilder = MatrixBuilder(sizeOfWindow, numberOfWords)

####################################################
#  Load the Tweets from the file
####################################################
toSave = []
count = 0

####################################################
#  Initialize times associated with various parts
#  of the code.
####################################################
tLoadTweets = 0
tLoadCommonWords = 0
tPopMat = 0
tBuildCooccurenceMatrix = 0
tCalculateSPCA = 0

t0 = time.time()
while not tweetRetriever.eof:
    count+=1
    tIterationStart = time.time()
    print("--- Loading Tweets ---")
    tLoadTweetsStart = time.time()
    (tweetSet, oldBatch) = tweetRetriever.getNextWindow()
    if verbose == 3:
        print("--- Number of Tweets: " + str(len(tweetSet)) + " ---")
    print("--- Finished loading Tweets ---")
    tLoadTweetsEnd = time.time()
    tLoadTweets += (tLoadTweetsEnd - tLoadTweetsStart)/10

    ########################################################
    #  Make a list of the 3000 most common words in the
    #  Tweets which will be the columns of the matrix.
    #  The Bag-Of-Words.
    ########################################################
    print("--- Loading most common words in the Tweets ---")
    tLoadCommonWordsStart = time.time()

    dictOfWordsOld = DictionaryOfWords()

    # This part of the count will be common to both the current and previous window
    for tweet in tweetSet[0:-len(oldBatch)]:
        dictOfWordsOld.addFromSet(tweet.listOfWords())

    # Ensure a copy is made, not just a reference and also to the dictionary in it => deepcopy
    dictOfWordsCurrent = deepcopy(dictOfWordsOld)

    # The old dictionary of words
    for tweet in oldBatch:
        dictOfWordsOld.addFromSet(tweet.listOfWords())

    # The current dictionary of words
    for tweet in tweetSet[-len(oldBatch):]:
        dictOfWordsCurrent.addFromSet(tweet.listOfWords())

    wordDictOld = dictOfWordsOld.getMostPopularWordsAndRank(numberOfWords)
    wordDictCurrent = dictOfWordsCurrent.getMostPopularWordsAndRank(numberOfWords)
    dictionaryComparator = DictionaryComparator(wordDictOld, wordDictCurrent)

    tLoadCommonWordsEnd = time.time()
    tLoadCommonWords += (tLoadCommonWordsEnd - tLoadCommonWordsStart)/10

    print("------ That took " + str(tLoadCommonWordsEnd - tLoadCommonWordsStart) + " seconds to complete ------")
    print("--- Finished loading most common words in the Tweets ---")
#     ########################################################
#     #  Open the file to output the words with their index.
#     ########################################################
#     print("--- Opening file to output index of words to ---")
#     wordsFile = open("Data/cwi", "w")
#     # Matlab starts indexing from 1
#     i = 1
#     for (word, occurrence) in listOfWords:
#         if isinstance(word, unicode):
#             word = word.encode('utf-8','ignore')
#         else:
#             print(word)
#         wordsFile.write(str(i) + " " + word + " " + str(occurrence) + "\n")
#         i = i + 1
#     print("--- Closing file to output index of words to ---")
#     wordsFile.close()

    ########################################################
    #  Create Sparse Matrix
    ########################################################
    matrixBuilder.resetMatrix()

    ############################################################################################
    #  Populate the S matrix. This is the matrix with rows the Tweets and columns
    #  the Bag-Of-Words.
    ############################################################################################
    print("--- Populating matrix ---")
    tPopMatStart = time.time()
    tweetNumber = 0
    # Get the start and end date of the current tweet set
    startDate = tweetSet[0].date
    endDate = tweetSet[len(tweetSet)-1].date
    # Get the current Bag-Of-Words
    currentBagOfWords = wordDictCurrent.keys()

    for tweet in tweetSet:
        # Get the list of words in the tweet
        tweetWordList = tweet.listOfWords()
        for word in tweetWordList:
            if word in currentBagOfWords:
                matrixBuilder.addElement(tweetNumber, wordDictCurrent[word], 1)
        # Next row
        tweetNumber = tweetNumber + 1
    tPopMatEnd = time.time()
    tPopMat += (tPopMatEnd - tPopMatStart)/10
    print("--- Finished populating matrix ---")
    print("------ That took " + str(tPopMatEnd - tPopMatStart) + " seconds to complete ------")

    ############################################################################################
    # Now calculate the Co-occurrence matrix.
    ############################################################################################
    tBuildCooccurenceMatrixStart = time.time()
    cooccurrenceMatrix = matrixBuilder.getCooccurrenceMatrix()
    tBuildCooccurenceMatrixEnd = time.time()
    tBuildCooccurenceMatrix += (tBuildCooccurenceMatrixEnd - tBuildCooccurenceMatrixStart)/10

    ############################################################################################
    # Run the Sparse PCA algorithm on the Co-occurrence matrix.
    ############################################################################################
    tCalculateSPCAStart = time.time()
    [sparsePC, eigenvalue] = tPAlgorithm.getSparsePC(cooccurrenceMatrix, desiredSparsity)
    tCalculateSPCAEnd = time.time()
    tCalculateSPCA += (tCalculateSPCAEnd - tCalculateSPCAStart)/10
    print("--- Sparse Eigenvector ---")
    print(sparsePC.nonzero()[0])

    ###########################################################################
    # Save all the words corresponding to the indices of the supports returned.
    ###########################################################################
    pCWords = []
    for index in sparsePC.nonzero()[0]:
        for word, rank in wordDictCurrent.iteritems():
            if rank == index:
                pCWords.append(word)

    print(pCWords)
    print("--- Eigenvalue ---")
    print(eigenvalue)
    print("--- Start Date - End Date ---")
    print(startDate + " - " + endDate)

    #################################################################
    #  Append the data to be saved in the pickle file.
    #################################################################
    toSave.append((pCWords, eigenvalue, startDate, endDate))
    tIterationEnd = time.time()
    print ("Time for iteration: " + str(tIterationEnd - tIterationStart))

    # TODO: draw with matplotlib here and keep updating:
    # see: http://stackoverflow.com/questions/11874767/real-time-plotting-in-while-loop-with-matplotlib
    # see: http://matplotlib.org/users/text_intro.html
    # see: http://stackoverflow.com/questions/16183462/saving-images-in-python-at-a-very-high-quality
    # see: http://www.ucs.cam.ac.uk/docs/course-notes/unix-courses/pythontopics/graphs.pdf

#     # TODO: Graph plotting stuff
#     x.append(i)
#     y.append(eigenvalue)
#     if eigenvalue >150:
#         plt.arrow(i, eigenvalue, 1, 4, width=0.005, head_width=0.05, head_starts_at_zero=False)
#         plt.annotate("this is 100", (i, eigenvalue+4))
#         plt.scatter(i,eigenvalue, c="red")
#     else:
#         plt.scatter(i,eigenvalue, c="blue")
#     i = i + 1
#     plt.draw()
#     time.sleep(0.005)
# plt.show()
t1 = time.time()
totalTime = t1 - t0
totalTime = tLoadCommonWords + tLoadTweets + tPopMat + tBuildCooccurenceMatrix + tCalculateSPCA

###########################################################
#  Print final statistics for time spent in each portion
#  of the code.
###########################################################
print("Average proportion of time loading Tweets = " + str(tLoadTweets/totalTime))
print("Average proportion of time loading common words = " + str(tLoadCommonWords/totalTime))
print("Average proportion of time populating matrix = " + str(tPopMat/totalTime))
print("Average proportion of time building co-occurrence matrix = " + str(tBuildCooccurenceMatrix/totalTime))
print("Average proportion of time calculating Sparse PCA = " + str(tCalculateSPCA/totalTime))
print("Average time per iteration = " + str(totalTime/len(toSave)))
outputPickle = open(pickleFileName, 'wb')
pickle.dump(toSave, outputPickle)
outputPickle.close()

print("--- End ---")


