"""
Tool used to maintain the program.
"""
import re
import os
import pandas as pd
import numpy as np
from matminer.featurizers import structure
from matminer.featurizers import composition
from matminer.featurizers import conversions
from matminer.featurizers import site
from pymatgen.core.structure import Structure
from pymatgen.analysis import local_env
import plotly.offline as of
import plotly.graph_objs as go
import joblib
from django.core.cache import cache
from ai4chem.models import Job

structure_featurizers = [
    'DensityFeatures',
    'GlobalSymmetryFeatures',
    'Dimensionality',
    'RadialDistributionFunction',
    'PartialRadialDistributionFunction',
    'ElectronicRadialDistributionFunction',
    'CoulombMatrix',
    'SineCoulombMatrix',
    'OrbitalFieldMatrix',
    'MinimumRelativeDistances',
    'SiteStatsFingerprint',
    'EwaldEnergy',
    'BondFractions',
    'BagofBonds',
    'StructuralHeterogeneity',
    'MaximumPackingEfficiency',
    'ChemicalOrdering',
    'XRDPowderPattern',
    'CGCNNFeaturizer',
    'JarvisCFID',
    'SOAP',
    'GlobalInstabilityIndex'
]

composition_featurizers = [
    'ElementProperty',
    'OxidationStates',
    'AtomicOrbitals',
    'BandCenter',
    'ElectronegativityDiff',
    'ElectronAffinity',
    'Stoichiometry',
    'ValenceOrbital',
    'IonProperty',
    'ElementFraction',
    'TMetalFraction',
    'CohesiveEnergy',
    'Miedema',
    'YangSolidSolution',
    'AtomicPackingEfficiency'
]

conversions_utils = [
    'ConversionFeaturizer',
    'StrToComposition',
    'StructureToComposition',
    'StructureToIStructure',
    'DictToObject',
    'JsonToObject',
    'StructureToOxidStructure',
    'CompositionToOxidComposition',
    'CompositionToStructureFromMP'
]


def username_check(username):
    """
    Valid username contains only letters, numbers and underlines.
    And only start with letters.
    :param username:
    :return: True or false
    """
    num_letter = re.compile(r"^(?!\d+$)[\da-zA-Z_]+$")
    first_letter = re.compile(r"^[a-zA-Z]")
    if first_letter.search(username):
        if num_letter.search(username):
            return True
    return False


def draw_pic(option):
    """
    Generate uploaded file based graph or raw file based graph.
    :param option:
    :return:
    """
    job_id = int(option["job_id"])
    job = Job.objects.get(id=job_id)
    data = pd.read_pickle(job.raw, compression=None)
    x = data[data.columns[0: -1]]
    y = data[data.columns[-1]]
    mod = joblib.load(job.mod)

    # Plot with raw data(Training data)
    if option["choose_data"] == 'raw':
        x_test = x
        y_pred = mod.predict(x_test)

    # Plot with uploaded new data.
    elif option["choose_data"] == 'upload':
        file = job.upload
        try:
            x_test = pd.read_pickle(file, compression=None)
        except Exception as _e:
            print(_e)
            return "", "Uploaded file is invalid."
        try:
            plot_columns = []
            for key in option:
                if option[key] == "on":
                    plot_columns.append(key)
            x_test = x_test[plot_columns]
            y_pred = mod.predict(x_test)
        except ValueError as _e:
            return "", "Uploaded file is unacceptable or mismatches the shape of raw data."
    else:
        return "", "Please choose a data type"

    predict_file_create(y_pred, job.owner)

    try:
        # Select columns need to be plotted.
        f1 = option["feature_1"]
        f2 = option["feature_2"]
    except Exception as e:
        print(e)
        f1 = f2 = "0"
        pass
    if f1 != 'None' and f2 != 'None':
        return draw_pic_3d(option, x, y, x_test, y_pred), ""
    elif f1 != 'None' or f2 != 'None':
        return draw_pic_2d(option, x, y, x_test, y_pred), ""
    else:
        return "", "Please choose feature!"


def draw_pic_2d(option, x, y, x_test, y_pred):
    """
    plot 2d graph
    :param option: graph option
    :param x: x_axis value(raw)
    :param y: y_axis value(raw)
    :param x_test: x_axis value(provided or raw)
    :param y_pred: y_axis value(calculated)
    :return:
    """
    if option["feature_1"] != 'None':
        plot_feature = int(option["feature_1"])
    else:
        plot_feature = int(option["feature_2"])
    x_test = x_test[x_test.columns[plot_feature]]
    x = x[x.columns[plot_feature]]

    trace_raw = go.Scatter(
        x=x,
        y=y,
        name='raw',
        mode='markers',
        marker=dict(
            size=10,
            color=option["raw_color"]
        )
    )
    trace_pred = go.Scatter(
        x=x_test,
        y=y_pred,
        name='predict',
        mode='markers',
        marker=dict(
            size=5,
            color=option["predict_color"]
        )
    )

    layout = go.Layout(
        title=option["title"],
        xaxis=dict(title=x_test.name),
        yaxis=dict(title=y.name)
    )
    data = [trace_raw, trace_pred]
    fig = dict(data=data, layout=layout)
    html = of.plot(fig, output_type="div")
    return html


def draw_pic_3d(option, x, y, x_test, y_pred):
    """
    plot 3d graph
    :param option:
    :param x:
    :param y:
    :param x_test:
    :param y_pred:
    :return:
    """
    plot_feature_1 = int(option["feature_1"])
    plot_feature_2 = int(option["feature_2"])
    x_test_1 = x_test[x_test.columns[plot_feature_1]]
    x_test_2 = x_test[x_test.columns[plot_feature_2]]
    x_1 = x[x.columns[plot_feature_1]]
    x_2 = x[x.columns[plot_feature_2]]

    trace_raw = go.Scatter3d(
        x=x_1,
        y=x_2,
        z=y,
        name='raw',
        mode='markers',
        marker=dict(
            size=10,
            color=option["raw_color"]
        )
    )
    trace_pred = go.Scatter3d(
        x=x_test_1,
        y=x_test_2,
        z=y_pred,
        name='predict',
        mode='markers',
        marker=dict(
            size=5,
            color=option["predict_color"]
        )
    )

    layout = go.Layout(
        title=option["title"],
        scene=go.Scene(
            xaxis=go.layout.scene.XAxis(
                title=x_test_1.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            ),
            yaxis=go.layout.scene.YAxis(
                title=x_test_2.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            ),
            zaxis=go.layout.scene.ZAxis(
                title=y.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            )
        )
    )

    data = [trace_raw, trace_pred]
    fig = dict(data=data, layout=layout)
    html = of.plot(fig, output_type="div")
    return html


def job_error(job, e):
    """
    Used for error processing.
    Switch the status of job to Error!
    :param job:
    :param e:
    :return:
    """
    job.status = 'E'
    job.save()
    cache.set(str(job.id) + "_error", e)
    cache.set("calculating_process_id", None, timeout=None)
    return


def preprocess(option, file):
    """
    Convert the columns of dataframe and calculate chemical features
    The format of option is [featurizer, target-column, value].
    'featurizer' is the wanted way to process data.
    e.g. rename, strToStructure, structureToComposition, strToComposition
    'target-column' is the column to be processed.
    'value' is the extra needed parameter for featurizer
    e.g. 'rename' method needs new name to proceed.
    If empty list [] is provided, this function will only try to remove NaN columns and rows.
    :param: option (Parameters required by conversion)
    :param: File containing dataframe(Pandas class)
    :return: Dataframe
    """
    try:
        # The file may be json, csv and pickle format.
        file.seek(0)
        df = pd.read_pickle(file, compression=None)
    except Exception as e:
        print(e)
        try:
            file.seek(0)
            df = pd.read_json(file)
        except ValueError:
            try:
                file.seek(0)
                df = pd.read_csv(file)
            except Exception as e:
                return False, repr(e)
    finally:
        file.close()
    if not option:
        df = df.dropna(axis=0, how="all").dropna(axis=1)
    else:
        featurizer = option[0]
        target = option[1]
        value = option[2]
        extra = option[3]
        # Rename one column of dataframe.
        if featurizer == "rename":
            try:
                columns = list(df.columns)
                col_index = columns.index(target)
                columns.remove(target)
                columns.insert(col_index, value)
                df.columns = columns
            except Exception as e:
                return False, repr(e)
        # Delete one column of dataframe.
        elif featurizer == "delete":
            try:
                df.drop(target, axis=1, inplace=True)
            except Exception as e:
                return False, repr(e)
        # Convert json format string to structure(Pymatgen class)
        elif featurizer == "strToStructure":
            try:
                df[target] = [Structure.from_str(i, 'json') for i in df[target]]
            except Exception as e:
                return False, repr(e)
        else:
            # Convert structure(Pymatgen class) to composition(Pymatgen class)
            if featurizer in conversions_utils:
                convert = conversions.__dict__[featurizer]()
            elif featurizer in structure_featurizers:
                # Provided by matminer to process structure(Pymatgen class).
                if featurizer in ["ElectronicRadialDistributionFunction",
                                  "EwaldEnergy",
                                  "BondFractions",
                                  "GlobalInstabilityIndex"]:
                    [i.add_oxidation_state_by_guess() for i in df[target]]
                if featurizer in ["CoulombMatrix",
                                  "PartialRadialDistributionFunction",
                                  "SineCoulombMatrix",
                                  "BondFractions",
                                  "BagofBonds"]:
                    convert = structure.__dict__[featurizer]().fit(df[target])
                elif featurizer == "SiteStatsFingerprint":
                    if value == "CrystalNNFingerprint":
                        [i.add_oxidation_state_by_guess() for i in df[target]]
                        # Warning: Need further exploration!!!!!!!!
                        fingerprint = site.CrystalNNFingerprint.from_preset("cn")
                        # fingerprint = site.CrystalNNFingerprint.from_preset("ops")
                        convert = structure.SiteStatsFingerprint(site_featurizer=fingerprint)
                    elif value == "ChemEnvSiteFingerprint":
                        # If you use the ChemEnv tool for your research,
                        # please consider citing the following reference(s) :
                        # =============================================================
                        # David Waroquiers, Xavier Gonze, Gian-Marco Rignanese,
                        # Cathrin Welker-Nieuwoudt, Frank Rosowski,
                        # Michael Goebel, Stephan Schenk, Peter Degelmann,
                        # Rute Andre, Robert Glaum, and Geoffroy Hautier,
                        # "Statistical analysis of coordination environments in oxides",
                        # Chem. Mater., 2017, 29 (19), pp 8346-8360,
                        # DOI: 10.1021/acs.chemmater.7b02766
                        # Warning: Need further exploration!!!!!!!!
                        fingerprint = site.ChemEnvSiteFingerprint.from_preset("simple")
                        # fingerprint = site.ChemEnvSiteFingerprint.from_preset("multi_weights")
                        convert = structure.SiteStatsFingerprint(site_featurizer=fingerprint)
                    elif value in ["GeneralizedRadialDistributionFunction",
                                   "AngularFourierSeries"]:
                        # Warning: Need further exploration!!!!!!!!
                        fun = site.__dict__[value].from_preset("gaussian")
                        # fun = site.__dict__[value].from_preset("histogram")
                        convert = structure.SiteStatsFingerprint(site_featurizer=fun)
                    elif value in ["AverageBondLength",
                                   "AverageBondAngle"]:
                        method = local_env.__dict__[extra]()
                        fun = site.__dict__[value](method=method)
                        convert = structure.SiteStatsFingerprint(site_featurizer=fun)
                    else:
                        convert = structure.SiteStatsFingerprint(site_featurizer=site.__dict__[value]())
                else:
                    convert = structure.__dict__[featurizer]()
            elif featurizer in composition_featurizers:
                # Provide by matminer to process composition(Pymatgen class).
                if featurizer in ["OxidationStates",
                                  "ElectronegativityDiff",
                                  "ElectronAffinity"]:
                    df[target] = [conversions.CompositionToOxidComposition().featurize(i)[0] for i in df[target]]
                convert = composition.__dict__[featurizer]()
            else:
                return False, "No featurizer available!"
            try:
                df = convert.featurize_dataframe(df, target, ignore_errors=True)
            except Exception as e:
                return False, repr(e)
    df = space_check(df)
    return True, df


def space_check(dataframe):
    """
    Since it's hard for form submission if there are spaces, and there may be unpredictable error on the
    front-end page, we need to convert space to _.
    :param dataframe:
    :return:
    """
    df = dataframe
    columns = list(df.columns)
    new_col = []
    for i in columns:
        new_col.append(i.replace(" ", "_"))
    df.columns = new_col
    return df


def predict_file_create(y_predict, username):
    """
    Generate pure text file containing predict data.
    The file is saved in /tmp/ai4chem/predict/
    :param y_predict:
    :param username:
    :return:
    """
    predict_dir = '/tmp/ai4chem/predict/'
    try:
        os.makedirs(predict_dir)
    except FileExistsError:
        pass
    predict_file = predict_dir + username + '.txt'
    np.savetxt(predict_file, y_predict, fmt="%f", delimiter=',')
