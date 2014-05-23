'''
Created on 23 May 2014

@author: theopavlakou
'''
import matplotlib.pyplot as plt
import time

class TwitterGraphPlotter(object):
    '''
    A class to plot graphs given data from the TwitterParserStreaming module.
    '''


    def __init__(self, dataIn, xlabel="Data Point Number", ylabel="Eigenvalue", title="How eigenvalue changes with time"):
        ''' Data given in format:
            [(['word', 'word', 'word'], eigenValue, startDate, endDate), (...), ...]
        '''
        self.data = dataIn
        self.colours = {"no_event": "blue", "event":"red"}
        self.currentColour = self.colours["no_event"]
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ion()

    def plotGraph(self):
        i = 0
        prevEigVal = self.data[0][1]
        numDataPoints = len(self.data)
        currentColour = "blue"
        for dataPoint in self.data:
            eigVal = dataPoint[1]

            if eigVal > prevEigVal*5:
                currentColour = "red"
                plt.annotate(dataPoint[2], (i, eigVal+20))
            elif prevEigVal > eigVal*5:
                currentColour = "blue"
                plt.annotate(dataPoint[3], (i, eigVal+20))
            elif i == 0:
                plt.annotate(dataPoint[2], (i, eigVal+20))
            elif i == numDataPoints - 1:
                plt.annotate(dataPoint[3], (i, eigVal+20))
            prevEigVal = eigVal
            plt.scatter(i,eigVal, c=currentColour)
            i = i + 1
            plt.draw()

    def keepGraphLocked(self):
        plt.show(block=True)