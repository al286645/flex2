outputName = 'M1627-M1630.plot.blastn.clean'


#Initialize variables

nOfHits = 0

minAln = 1250
minIdentity = 90

blastFamilies = []

class BlastFamily():
    def __init__(self, parentList):
        self.parents = parentList
        self.blastList = []

    def addBlast(self, BlastHit):
        if set(self.parents) == set(BlastHit.parents):
            self.blastList.append(BlastHit)
        else:
            print('Hit does not pertain to this family')

    def removeOwnHits(self):
        cleanList = []
        tupleList = []
        for BlastHit in self.blastList:
            for tuple in tupleList:
                if set(BlastHit.seq1pos + BlastHit.seq2pos) == set(tuple):
                    break
            else:
                cleanList.append(BlastHit)
                tupleList.append((BlastHit.seq1pos + BlastHit.seq2pos))
        self.blastList = cleanList

    def _equalize(self):
        for BlastHit in self.blastList:
            if BlastHit.parents[0] != self.parents[0]:
                seq2 = BlastHit.seq1pos
                seq1 = BlastHit.seq2pos

                BlastHit.parents = self.parents
                BlastHit.seq1pos = seq2
                BlastHit.seq2pos = seq1

    def sortHits(self):
        self.blastList.sort(key= lambda BlastHit : BlastHit.seq1pos)

    def mergeBlasts(self):
        self._equalize()
        self.sortHits()
        mergeCandidates = []
        count = 0
        for i in range(0, len(self.blastList)-1):
            fstBlast = self.blastList[i]
            scdBlast = self.blastList[i + 1]
            #subThreshold = [1000, 0.76, 1.33]
            #subThreshold = [500, 0.80, 1.20]
            subThreshold = [1500, 0.60, 1.50]

            pos1Dtce = abs(scdBlast.seq1pos[0] - fstBlast.seq1pos[1] + 0.1)
            pos2Dtce = abs(scdBlast.seq2pos[0] - fstBlast.seq2pos[1] + 0.1)
            dtceDiv = pos1Dtce/pos2Dtce
            dtceSub = int(pos1Dtce+pos2Dtce) < subThreshold[0] and pos1Dtce < subThreshold[0]/2 and pos2Dtce < subThreshold[0]/2
            if dtceDiv > subThreshold[1] and dtceDiv < subThreshold[2] and dtceSub:
                count += 1
                mergeCandidates.append([fstBlast, scdBlast])

        print(count,'/', len(self.blastList), 'candidates to merge')

        curatedNonMergeList = []
        for blastHit in self.blastList:
            foundHit = False
            for list in mergeCandidates:
                if blastHit in list:
                    foundHit = True
                    break

            if foundHit == False:
                curatedNonMergeList.append(blastHit)

        print('not merged blasts:', len(curatedNonMergeList))
        print(len(mergeCandidates))
        #Remove concatenated merges
        i = 0
        while i < len(mergeCandidates)-1:
            if mergeCandidates[i][-1] == mergeCandidates[i+1][0]:
                #print('Found')
                newList = [mergeCandidates[i][0], mergeCandidates[i+1][1]]
                mergeCandidates[i] = newList
                mergeCandidates.pop(i+1)
                i = 0
                continue
            else:
                i += 1

        print(len(mergeCandidates))
        finalCandidateList = []
        for candidates in mergeCandidates:
            gaps = str(candidates[0].gaps + candidates[1].gaps)
            mismatches = str(candidates[0].mismatches + candidates[1].mismatches + (candidates[1].seq2pos[0] - candidates[0].seq1pos[1]))
            matchLen = str(candidates[0].matchLen + candidates[1].matchLen + (candidates[1].seq2pos[0] - candidates[0].seq1pos[1]))
            identity = str((candidates[0].identity + candidates[1].identity)/2)
            line = candidates[0].parents[0] + '\t' + candidates[0].parents[1] + '\t' + identity + '\t' + matchLen + '\t' + mismatches + '\t' + str(gaps)+ '\t'
            line2 = str(candidates[0].seq1pos[0]) + '\t' + str(candidates[1].seq1pos[1]) + '\t' + str(candidates[0].seq2pos[0]) + '\t' + str(candidates[1].seq2pos[1]) + '\t' + '0' + '\t' +'0\n'

            newBlastHit = BlastHit(line+line2)
            finalCandidateList.append(newBlastHit)


        newList = finalCandidateList + curatedNonMergeList
        self.blastList = newList
        self.sortHits()

        print(len(self.blastList))

    def printHits(self, filehandle):
        for blastHit in self.blastList:
            line1 = blastHit.parents[0] + '\t' + blastHit.parents[1] + '\t' + '%.2f'%(blastHit.identity) + '\t' + str(blastHit.matchLen) + '\t' + str(blastHit.mismatches) + '\t' + str(blastHit.gaps) + '\t'
            line2 = str(blastHit.seq1pos[0]) + '\t' + str(blastHit.seq1pos[1]) + '\t' + str(blastHit.seq2pos[0]) + '\t' + str(blastHit.seq2pos[1]) + '\t' + '0' + '\t' + '0\n'
            filehandle.write(line1+line2)







class BlastHit():
    def __init__(self, line):
        blastLine = line.split('\t')
        self.parents = (blastLine[0], blastLine[1])
        self.seq1pos = (int(blastLine[6]), int(blastLine[7]))
        self.seq2pos = (int(blastLine[8]), int(blastLine[9]))

        self.mismatches = int(blastLine[4])
        self.gaps = int(blastLine[5])
        self.identity = float(blastLine[2])
        self.matchLen = int(blastLine[3])
        self.bitScore = None

        if 'e' in blastLine[11]:
            bitScoreSplit = blastLine[11].split('e')
            if bitScoreSplit[1][0] == '+':
                self.bitScore = float(bitScoreSplit[0]) * (10 ^ int(bitScoreSplit[1][1:]))
            elif bitScoreSplit[1][0] == '-':
                self.bitScore = float(bitScoreSplit[0]) * (10 ^ int(-bitScoreSplit[1][1:]))
            else:
                print('Something went wrong!')
        else:
            self.bitScore = float(blastLine[11])

#Basic filtering: self hits, min length, min identity
def parseBlastFile(blastFile):
    with open(blastFile, 'r') as blastResults:
        causeDict = {'Self Hits':0, 'Low identity':0, 'Small Match':0}
        nOfHits = 0
        acceptedHits = []
        for line in blastResults:
            nOfHits += 1
            print('procesing hit nº', nOfHits)
            newHit = BlastHit(line)
            # Remove self-hits
            if newHit.parents[0] == newHit.parents[1]:
                print('\tSelf hit, removed')
                causeDict['Self Hits'] += 1
                continue
            # Remove low identity hits
            elif newHit.identity < minIdentity:
                print('\tLow identity, removed:', minIdentity, '>', newHit.identity)
                causeDict['Low identity'] += 1
                continue
            # Remove small hits
            elif newHit.matchLen < minAln:
                print('\tSmall alignment, removed:', minAln, '>', newHit.matchLen)
                causeDict['Small Match'] += 1
                continue
            else:
                print('\tGood hit')
                acceptedHits.append(newHit)
        print(causeDict['Self Hits'], 'self hits removed,', causeDict['Low identity'], 'low identity,', causeDict['Small Match'], 'small matches')
        print(len(acceptedHits), 'hits accepted')
        return acceptedHits


def groupHits(blastList):
    blastFamilies = []
    blastParents = []
    for BlastHit in blastList:
        if len(blastFamilies) == 0:
            newFamily = BlastFamily(BlastHit.parents)
            newFamily.addBlast(BlastHit)
            blastParents.append(BlastHit.parents)
            blastFamilies.append(newFamily)
        else:
            for parent in blastParents:
                if set(BlastHit.parents) == set(parent):
                    blastFamilies[blastParents.index(parent)].addBlast(BlastHit)
                    break
            else:
                print('parents', BlastHit.parents, 'not found in', blastParents)
                newFamily = BlastFamily(BlastHit.parents)
                newFamily.addBlast(BlastHit)
                blastParents.append(BlastHit.parents)
                blastFamilies.append(newFamily)

    return blastFamilies






acceptedHits = parseBlastFile(outputName)
blastFamilies = groupHits(acceptedHits)
with open('test.blastn', 'w') as filehandle:
    for family in blastFamilies:
        print()
        print('parents', family.parents, len(family.blastList))
        family.removeOwnHits()
        print('len after removing duplicates', len(family.blastList))
        family.mergeBlasts()
        #family.printHits(filehandle)






















print('Done')
