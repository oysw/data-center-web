let structureFeaturizers = [
    "DensityFeatures",
    "GlobalSymmetryFeatures",
    "Dimensionality",
    "RadialDistributionFunction",
    "PartialRadialDistributionFunction",
    "ElectronicRadialDistributionFunction",
    "CoulombMatrix",
    "SineCoulombMatrix",
    "OrbitalFieldMatrix",
    "MinimumRelativeDistances",
    "SiteStatsFingerprint",
    "EwaldEnergy",
    "BondFractions",
    "BagofBonds",
    "StructuralHeterogeneity",
    "MaximumPackingEfficiency",
    "ChemicalOrdering",
    "StructureComposition",
    "XRDPowderPattern",
    "CGCNNFeaturizer",
    "JarvisCFID",
    "SOAP",
    "GlobalInstabilityIndex"
];
let compositionFeaturizers = [
    "OxidationStates",
    "AtomicOrbitals",
    "BandCenter",
    "ElectronegativityDiff",
    "ElectronAffinity",
    "Stoichiometry",
    "ValenceOrbital",
    "IonProperty",
    "ElementFraction",
    "TMetalFraction",
    "CohesiveEnergy",
    "Miedema",
    "YangSolidSolution",
    "AtomicPackingEfficiency"
];

function compositionFeaturizersSelector() {
    let html_str = "<option>None</option>";
    for (let i = 0; i < compositionFeaturizers.length; i++){
        let featurizers = compositionFeaturizers[i];
        html_str += '<option value=' + featurizers + '>' + featurizers + '</option>';
    }
    return html_str
}

function structureFeaturizersSelector() {
    let html_str = "<option>None</option>";
    for (let i = 0; i < structureFeaturizers.length; i++){
        let featurizers = structureFeaturizers[i];
        html_str += '<option value=' + featurizers + '>' + featurizers + '</option>';
    }
    return html_str
}