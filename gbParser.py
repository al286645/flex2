from Bio import SeqIO
from itertools import filterfalse
import argparse
import sys
from subprocess import call

#Adapted to produce the current flex input, might be changed later

fosmidList = []

class Fosmid():

    def __init__(self, name, length, seq):
        self.seq = seq
        self.name = name
        self.length = length
        self.features = []
        self.featureDict = {}

    def addFeature(self, feature):
        #Check the feature type and add it to the appropiate list
        for key in self.featureDict:

            if key == feature.type:
                self.featureDict[key] += 1
                feature.id = key.lower() + '_' + str(self.featureDict[key])
        #If the relevant type is not yet in the list, just add it
        if feature.type not in self.featureDict:
            self.featureDict[feature.type] = 1
            feature.id = feature.type + '_0'
        #Finally, add the feature to feature list
        self.features.append(feature)

    def purgeGeneList(self):
        #Some features appear 2 times in GenBank feature list: once as themselves and another as a gene. Both entries have the same
        # locus_tag qualifiers, so use those to remove the gene entries (CDS entries have more info)
        #In case this does not work correctly: db_xref is another possible qualifier, check both features' position

        locusList = []
        geneList = []
        otherList = []

        for feature in self.features:
            try:
                if feature.type != 'gene' and feature.qualifiers['locus_tag'] != None:
                    locusList.append(feature)
                else:
                    geneList.append(feature)
            except(KeyError):
                otherList.append(feature)






        print(len(locusList), len(geneList), len(otherList))


        newGeneList = [feature for feature in self.features if self._checkDuplicates(feature,locusList) == False]
        self.features = locusList + newGeneList + otherList


    def _checkDuplicates(self, gene, cdsList):
        for cds in cdsList:
            try:
                if gene.qualifiers['locus_tag'] == cds.qualifiers['locus_tag']:
                    return True
            except(KeyError) as e:
                #print(str(e))
                return False

        return False









class Feature():

    def __init__(self, Fosmid,  gbFeatList):
        self.id = None
        self.fosmid = Fosmid
        self.type = gbFeatList.type
        self.sequence = None
        #Get position
        self.position = [gbFeatList.location.start.position, gbFeatList.location.end.position, gbFeatList.location.strand]
        if self.position[2] == -1:
            self.position[2] = '-'
        elif self.position[2] == 1:
            self.position[2] = '+'
        self.qualifiers = gbFeatList.qualifiers


    def getFeatureSequence(self, sequence):
        self.sequence = sequence




#Get Filename
gbFiles = []
inputFiles = ['M1627.gbff']



#Parse genbank,
for file in inputFiles:
    print(file)
    inputFile = SeqIO.parse(file, 'genbank')
    for record in inputFile:
        gbFiles.append(record)

print(len(gbFiles), 'records from', len(inputFiles), 'file(s) in input\n')

for gbRecord in gbFiles:

    newFosmid = Fosmid(name=gbRecord.id, length=gbRecord.features[0].location.end, seq=gbRecord.seq)
    featureList = gbRecord.features
    for rawFeature in featureList:
        newFeature = Feature(newFosmid, rawFeature)
        newFeature.getFeatureSequence(str(gbRecord.seq[rawFeature.location.start.position:rawFeature.location.end.position]))
        newFosmid.addFeature(newFeature)

    print(len(newFosmid.features))

    newFosmid.purgeGeneList()

    print(len(newFosmid.features))

    for feat in newFosmid.features:
        if feat.type == 'gene':
            print(feat.qualifiers)


    '''
    print(featureList)
    print(featureList.location)
    print(featureList.type)
    print(featureList.id) #Mostly useless
    print(len(featureList.qualifiers)) #Ordered dict
    '''





