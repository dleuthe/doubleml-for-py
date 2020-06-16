import numpy as np
import pytest
import math
import scipy

from sklearn.model_selection import KFold
from sklearn.base import clone

from sklearn.linear_model import LinearRegression, Lasso
from sklearn.ensemble import RandomForestRegressor

import doubleml as dml

from doubleml.tests.helper_general import get_n_datasets
from doubleml.tests.helper_plr_manual import plr_dml1, plr_dml2, fit_nuisance_plr, boot_plr


# number of datasets per dgp
n_datasets = get_n_datasets()

@pytest.fixture(scope='module',
                params = range(n_datasets))
def idx(request):
    return request.param


@pytest.fixture(scope='module',
                params = [RandomForestRegressor(max_depth=2, n_estimators=10),
                          LinearRegression()])
def learner(request):
    return request.param


@pytest.fixture(scope='module',
                params = ['IV-type', 'DML2018'])
def inf_model(request):
    return request.param


@pytest.fixture(scope='module',
                params = ['dml1', 'dml2'])
def dml_procedure(request):
    return request.param

@pytest.fixture(scope='module',
                params = [3])
def n_rep_cross_fit(request):
    return request.param


@pytest.fixture(scope="module")
def dml_plr_fixture(generate_data1, idx, learner, inf_model, dml_procedure, n_rep_cross_fit):
    boot_methods = ['normal']
    n_folds = 2
    n_rep_boot = 498

    # collect data
    data = generate_data1[idx]
    X_cols = data.columns[data.columns.str.startswith('X')].tolist()
    
    # Set machine learning methods for m & g
    ml_learners = {'ml_m': clone(learner),
                   'ml_g': clone(learner)}

    np.random.seed(3141)
    obj_dml_data = dml.DoubleMLData(data, 'y', ['d'], X_cols)
    dml_plr_obj = dml.DoubleMLPLR(obj_dml_data,
                                  ml_learners,
                                  n_folds,
                                  n_rep_cross_fit,
                                  inf_model,
                                  dml_procedure)

    dml_plr_obj.fit()
    
    np.random.seed(3141)
    y = data['y'].values
    X = data.loc[:, X_cols].values
    d = data['d'].values
    all_smpls = []
    for i_rep in range(n_rep_cross_fit):
        resampling = KFold(n_splits=n_folds,
                           shuffle=True)
        smpls = [(train, test) for train, test in resampling.split(X)]
        all_smpls.append(smpls)

    thetas = np.zeros(n_rep_cross_fit)
    ses = np.zeros(n_rep_cross_fit)
    all_g_hat = list()
    all_m_hat = list()
    for i_rep in range(n_rep_cross_fit):
        smpls = all_smpls[i_rep]

        g_hat, m_hat = fit_nuisance_plr(y, X, d,
                                        clone(learner), clone(learner), smpls)

        all_g_hat.append(g_hat)
        all_m_hat.append(m_hat)

        if dml_procedure == 'dml1':
            thetas[i_rep], ses[i_rep] = plr_dml1(y, X, d,
                                                 all_g_hat[i_rep], all_m_hat[i_rep],
                                                 smpls, inf_model)
        elif dml_procedure == 'dml2':
            thetas[i_rep], ses[i_rep] = plr_dml2(y, X, d,
                                                 all_g_hat[i_rep], all_m_hat[i_rep],
                                                 smpls, inf_model)

    res_manual = np.median(thetas)
    se_manual = np.sqrt(np.median(np.power(ses, 2) - np.power(thetas - res_manual, 2)))
    
    res_dict = {'coef': dml_plr_obj.coef,
                'coef_manual': res_manual,
                'se': dml_plr_obj.se,
                'se_manual': se_manual,
                'boot_methods': boot_methods
                }
    
    for bootstrap in boot_methods:
        np.random.seed(3141)
        all_boot_theta = list()
        for i_rep in range(n_rep_cross_fit):
            smpls = all_smpls[i_rep]
            boot_theta = boot_plr(thetas[i_rep],
                                  y, d,
                                  all_g_hat[i_rep], all_m_hat[i_rep],
                                  smpls, inf_model,
                                  ses[i_rep],
                                  bootstrap, n_rep_boot,
                                  dml_procedure)
            all_boot_theta.append(boot_theta)

        boot_theta = np.hstack(all_boot_theta)

        np.random.seed(3141)
        dml_plr_obj.bootstrap(method = bootstrap, n_rep=n_rep_boot)
        res_dict['boot_coef' + bootstrap] = dml_plr_obj.boot_coef
        res_dict['boot_coef' + bootstrap + '_manual'] = boot_theta
    
    return res_dict


def test_dml_plr_coef(dml_plr_fixture):
    assert math.isclose(dml_plr_fixture['coef'],
                        dml_plr_fixture['coef_manual'],
                        rel_tol=1e-9, abs_tol=1e-4)


def test_dml_plr_se(dml_plr_fixture):
    assert math.isclose(dml_plr_fixture['se'],
                        dml_plr_fixture['se_manual'],
                        rel_tol=1e-9, abs_tol=1e-4)


def test_dml_plr_boot(dml_plr_fixture):
    for bootstrap in dml_plr_fixture['boot_methods']:
        assert np.allclose(dml_plr_fixture['boot_coef' + bootstrap],
                           dml_plr_fixture['boot_coef' + bootstrap + '_manual'],
                           rtol=1e-9, atol=1e-4)
