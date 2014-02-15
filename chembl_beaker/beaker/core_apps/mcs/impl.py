__author__ = 'mnowotka'

#-----------------------------------------------------------------------------------------------------------------------

from rdkit import Chem
from rdkit.Chem import MCS
from chembl_beaker.beaker.utils.io import _parseMolData

#-----------------------------------------------------------------------------------------------------------------------

def _mcs(data,params):
    ms = _parseMolData(data)
    atomCompare=params.get('atomCompare','elements')
    bondCompare=params.get('bondCompare','bondtypes')
    ringMatchesRingOnly=bool(int(params.get('ringMatchesRingOnly','0')))
    completeRingsOnly=bool(int(params.get('completeRingsOnly','0')))
    threshold=params.get('threshold',None)
    if threshold:
        threshold=float(threshold)
    mcs = MCS.FindMCS(ms,
                      atomCompare=atomCompare,
                      bondCompare=bondCompare,
                      ringMatchesRingOnly=ringMatchesRingOnly,
                      completeRingsOnly=completeRingsOnly,
                      threshold=threshold)
    res = mcs.smarts
    if bool(int(params.get('asSmiles','0'))):
        p = Chem.MolFromSmarts(res)
        for m in ms:
            if m.HasSubstructMatch(p):
                match = m.GetSubstructMatch(p)
                res = Chem.MolFragmentToSmiles(m,atomsToUse=match,isomericSmiles=True,canonical=False)
                break
    return res

#-----------------------------------------------------------------------------------------------------------------------