__author__ = 'mnowotka'

import StringIO
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Draw
import os
import tempfile
from subprocess import PIPE, Popen
from rdkit.Chem import Descriptors
from chembl_beaker.MarvinJSONEncoder import MolToMarvin, MarvinToMol

#-----------------------------------------------------------------------------------------------------------------------

def _ctab2smiles(data):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl]
    sio = StringIO.StringIO()
    w = Chem.SmilesWriter(sio)
    for mol in mols:
        w.write(mol)
    w.flush()
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _smiles2ctab(data):
    suppl = Chem.SmilesMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl]
    for mol in mols:
        AllChem.Compute2DCoords(mol)
    sio = StringIO.StringIO()
    w = Chem.SDWriter(sio)
    for mol in mols:
        w.write(mol)
    w.flush()
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _inchi2ctab(inchis):
    mols = [Chem.MolFromInchi(inch) for inch in inchis.split()]
    for mol in mols:
        AllChem.Compute2DCoords(mol)
    sio = StringIO.StringIO()
    w = Chem.SDWriter(sio)
    for mol in mols:
        w.write(mol)
    w.flush()
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _ctab2inchi(data):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl]
    inchi = []
    for mol in mols:
        inchi.append(Chem.MolToInchi(mol))
    return '\n'.join(inchi)

#-----------------------------------------------------------------------------------------------------------------------

def _inchi2inchiKey(inchis):
    keys = [Chem.InchiToInchiKey(inch) for inch in inchis.split()]
    return '\n'.join(keys)

#-----------------------------------------------------------------------------------------------------------------------

try:
    from rdkit.Chem.Draw import jsonCanvas
except ImportError:
    pass
else:
    if  hasattr(Draw, 'MolToJSON'):

        def _mols2json(mols,size,legend):
            ret = []
            for mol in mols:
                if not mol.GetNumConformers() or mol.GetConformer().Is3D():
                    AllChem.Compute2DCoords(mol)
                ret.append(Draw.MolToJSON(mol, size=(size,size),legend=mol.GetProp("_Name") or legend))
            return ret

        def _ctab2json(data, size, legend):
            suppl = Chem.SDMolSupplier()
            suppl.SetData(data)
            mols = [x for x in suppl]
            return _mols2json(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

        def _smiles2json(data, size, legend):
            suppl = Chem.SmilesMolSupplier()
            suppl.SetData(data)
            mols = [x for x in suppl]
            return _mols2json(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

try:
    import cairo
except ImportError:
    try:
        import cairocffi
        cairocffi.install_as_pycairo()
        import cairo
    except ImportError:
        cairo = None

if cairo:
    try:
        from rdkit.Chem.Draw import cairoCanvas
    except ImportError:
        cairoCanvas = None
if cairoCanvas:
    def _mols2svg(mols,size,legend):
        for mol in mols:
            if not mol.GetNumConformers() or mol.GetConformer().Is3D():
                AllChem.Compute2DCoords(mol)

        molsPerRow=min(len(mols),4)
        totalWidth=molsPerRow*size
        totalHeight=molsPerRow*size
        imageData = StringIO.StringIO()
        surf = cairo.SVGSurface(imageData,totalWidth,totalHeight)
        ctx = cairo.Context(surf)
        for i, mol in enumerate(mols):
            tx = size*(i%molsPerRow)
            ty = size*(i//molsPerRow)
            ctx.translate(tx, ty)
            canv = cairoCanvas.Canvas(ctx=ctx, size=(size,size), imageType='svg')
            Draw.MolToImage(mol, size=(size,size), legend=mol.GetProp("_Name") or legend, canvas=canv)
            canv.flush()
            ctx.translate(-tx, -ty)
        surf.finish()
        return imageData.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

    def _ctab2svg(data,size,legend):
        suppl = Chem.SDMolSupplier()
        suppl.SetData(data)
        mols = [x for x in suppl]
        return _mols2svg(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

    def _smiles2svg(data,size,legend):
        suppl = Chem.SmilesMolSupplier()
        suppl.SetData(data)
        mols = [x for x in suppl]
        return _mols2svg(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

def _mols2image(mols,size,legend):
    for mol in mols:
        if not mol.GetNumConformers() or mol.GetConformer().Is3D():
            AllChem.Compute2DCoords(mol)
    image = Draw.MolsToGridImage(mols,molsPerRow=min(len(mols),4),subImgSize=(size,size),
                                                                legends=[x.GetProp("_Name") or legend for x in mols])
    imageData = StringIO.StringIO()
    image.save(imageData, "PNG")
    return imageData.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _ctab2image(data,size,legend):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl]

    return _mols2image(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

def _smiles2image(data,size,legend):
    suppl = Chem.SmilesMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl]

    return _mols2image(mols,size,legend)

#-----------------------------------------------------------------------------------------------------------------------

def _image2ctab(img, osra):
    sio = StringIO.StringIO()
    w = Chem.SDWriter(sio)
    fd, fpath = tempfile.mkstemp()
    os.write(fd, img)
    os.close(fd)
    p = Popen([osra, fpath], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    a, err = p.communicate(input=img)
    os.remove(fpath)
    for smiles in filter(bool,a.split('\n')):
        w.write(Chem.MolFromSmiles(smiles))
    w.flush()
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _kekulize(data):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    sio = StringIO.StringIO()
    w = Chem.SDWriter(sio)
    mols = [Chem.Kekulize(x) for x in suppl]
    for m in mols:
        w.write(m)
    w.flush()
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _calc(data, desc_name):
    fn = getattr(Descriptors, desc_name)
    if not fn:
        return None
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    ret = [fn(x) for x in suppl]
    return ret

#-----------------------------------------------------------------------------------------------------------------------

def _descriptors(data, params):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    ds=params.get('descrs','')
    if ds!='':
        ds = ds.split(',')
    ret=[]
    for x in suppl:
        d={}
        if x is not None:
            for nm,fn in Descriptors.descList:
                if not ds or nm in ds:
                    d[nm]=fn(x)
        ret.append(d)
    return ret

#-----------------------------------------------------------------------------------------------------------------------

def _clean2D(mrv):
    mol = Chem.MolFromMolBlock(MarvinToMol(mrv))
    AllChem.Compute2DCoords(mol)
    return MolToMarvin(Chem.MolToMolBlock(mol))

#-----------------------------------------------------------------------------------------------------------------------

def _stereoInfo(mrv):
    ret = {"headers":
               {"tetraHedral":
                    {"name":"tetraHedral","type":"COMPLEX","source":"CALCULATOR"},
                "doubleBond":
                    {"name":"doubleBond","type":"COMPLEX","source":"CALCULATOR"}
               },
           "tetraHedral":[],
           "doubleBond":[]
    }

    mol = Chem.MolFromMolBlock(MarvinToMol(mrv))
    Chem.AssignStereochemistry(mol)
    for atom in mol.GetAtoms():
        stereo = str(atom.GetChiralTag())
        if str(atom.GetChiralTag()) != "CHI_UNSPECIFIED":
            atomIndex = atom.GetIdx() + 1
            if stereo == "CHI_TETRAHEDRAL_CW":
                chirality = "R"
            elif stereo == "CHI_TETRAHEDRAL_CCW":
                chirality = "S"
            else:
                chirality = "R/S"
            ret["tetraHedral"].append({"atomIndex":atomIndex,"chirality":chirality})

    for bond in mol.GetBonds():
        stereo = str(bond.GetStereo())
        if stereo != "STEREONONE":
            atom1Index = bond.GetBeginAtomIdx() + 1
            atom2Index = bond.GetEndAtomIdx() + 1
            bondIndex = bond.GetIdx() + 1
            if stereo == "STEREOANY":
                cistrans = "E/Z"
            elif stereo == "STEREOZ":
                cistrans = "Z"
            elif stereo == "STEREOE":
                cistrans = "E"
            ret["doubleBond"].append({"atom1Index": atom1Index,"atom2Index":atom2Index,"bondIndex":bondIndex,
                                                                                                "cistrans":cistrans})
    return ret

#-----------------------------------------------------------------------------------------------------------------------

def _molExport(structure, input_f, output_f):

    if input_f == 'mrv':
        mol = Chem.MolFromMolBlock(MarvinToMol(structure))
    elif input_f == 'smiles':
        mol = Chem.MolFromSmiles(str(structure))
    elif input_f == 'inchi':
        mol = Chem.MolFromInchi(str(structure))
    else:
        mol = Chem.MolFromMolBlock(structure)

    if not mol.GetNumConformers() or mol.GetConformer().Is3D():
        AllChem.Compute2DCoords(mol)

    if output_f == 'smiles':
        out_structure = Chem.MolToSmiles(mol)

    elif output_f == 'inchi':
        out_structure = Chem.MolToInchi(mol)

    elif output_f == 'inchikey':
        out_structure = Chem.InchiToInchiKey(Chem.MolToInchi(mol))

    elif output_f == 'sdf':
        out_structure = Chem.MolToMolBlock(mol) + '\n$$$$\n'

    elif output_f == 'mrv':
        out_structure = MolToMarvin(Chem.MolToMolBlock(mol))

    return {"structure": out_structure, "format":output_f, "contentUrl":"","contentBaseUrl":""}

#-----------------------------------------------------------------------------------------------------------------------

def _mcs(data,params):
    from rdkit.Chem import MCS
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    ms = [x for x in suppl if x is not None]
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

try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot
except:
    matplotlib=None

#-----------------------------------------------------------------------------------------------------------------------

def _similarityMap(ms,params):
    if matplotlib is None:
        raise ValueError('matplotlib not useable')
    from rdkit.Chem.Draw import SimilarityMaps
    fp=params.get('fingerprint','morgan')
    if fp=='morgan':
        rad = int(params.get('radius',2))
        fn = lambda x,i:SimilarityMaps.GetMorganFingerprint(x,i,radius=rad)
    elif fp=='tt':
        fn = SimilarityMaps.GetAPFingerprint
    elif fp=='ap':
        fn = SimilarityMaps.GetTTFingerprint

    w = int(params.get('w',100))
    h = int(params.get('h',100))

    fig,maxv = SimilarityMaps.GetSimilarityMapForFingerprint(ms[0],ms[1],fn,size=(w,h))
    sio = StringIO.StringIO()
    pyplot.savefig(sio,format='png',bbox_inches='tight',dpi=100)
    
    return sio.getvalue()

#-----------------------------------------------------------------------------------------------------------------------

def _smiles2SimilarityMap(data,params):
    from rdkit.Chem import AllChem
    suppl = Chem.SmilesMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl if x is not None]
    for mol in mols:
        AllChem.Compute2DCoords(mol)
    return _similarityMap(mols,params)

#-----------------------------------------------------------------------------------------------------------------------

def _sdf2SimilarityMap(data,params):
    suppl = Chem.SDMolSupplier()
    suppl.SetData(data)
    mols = [x for x in suppl if x is not None]
    return _similarityMap(mols,params)

#-----------------------------------------------------------------------------------------------------------------------