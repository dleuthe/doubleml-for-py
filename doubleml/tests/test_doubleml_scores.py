import pytest
import numpy as np

from doubleml import DoubleMLPLR, DoubleMLIRM, DoubleMLIIVM, DoubleMLPLIV
from doubleml.datasets import make_plr_CCDDHNR2018, make_irm_data, make_pliv_CHS2015, make_iivm_data

from sklearn.linear_model import Lasso, LogisticRegression

dml_data_plr = make_plr_CCDDHNR2018(n_obs=100)
dml_data_pliv = make_pliv_CHS2015(n_obs=100, dim_z=1)
dml_data_irm = make_irm_data(n_obs=100)
dml_data_iivm = make_iivm_data(n_obs=100)

dml_plr = DoubleMLPLR(dml_data_plr, Lasso(), Lasso())
dml_plr.fit()
dml_pliv = DoubleMLPLIV(dml_data_pliv, Lasso(), Lasso(), Lasso())
dml_pliv.fit()
dml_irm = DoubleMLIRM(dml_data_irm, Lasso(), LogisticRegression())
dml_irm.fit()
dml_iivm = DoubleMLIIVM(dml_data_iivm, Lasso(), LogisticRegression(), LogisticRegression())
dml_iivm.fit()


@pytest.mark.ci
@pytest.mark.parametrize('dml_obj',
                         [dml_plr, dml_pliv, dml_irm, dml_iivm])
def test_linear_score(dml_obj):
    assert np.allclose(dml_obj.psi,
                       dml_obj.psi_a * dml_obj.coef + dml_obj.psi_b,
                       rtol=1e-9, atol=1e-4)


@pytest.mark.ci
def test_plr_callable_vs_str_score():
    plr_score = dml_plr._score_elements
    dml_plr_callable_score = DoubleMLPLR(dml_data_plr, Lasso(), Lasso(),
                                         score=plr_score, draw_sample_splitting=False)
    dml_plr_callable_score.set_sample_splitting(dml_plr.smpls)
    dml_plr_callable_score.fit()
    assert np.allclose(dml_plr.psi,
                       dml_plr_callable_score.psi,
                       rtol=1e-9, atol=1e-4)
    assert np.allclose(dml_plr.coef,
                       dml_plr_callable_score.coef,
                       rtol=1e-9, atol=1e-4)


@pytest.mark.ci
def test_irm_callable_vs_str_score():
    irm_score = dml_irm._score_elements
    dml_irm_callable_score = DoubleMLIRM(dml_data_irm, Lasso(), LogisticRegression(),
                                         score=irm_score, draw_sample_splitting=False)
    dml_irm_callable_score.set_sample_splitting(dml_irm.smpls)
    dml_irm_callable_score.fit()
    assert np.allclose(dml_irm.psi,
                       dml_irm_callable_score.psi,
                       rtol=1e-9, atol=1e-4)
    assert np.allclose(dml_irm.coef,
                       dml_irm_callable_score.coef,
                       rtol=1e-9, atol=1e-4)


@pytest.mark.ci
def test_iivm_callable_vs_str_score():
    iivm_score = dml_iivm._score_elements
    dml_iivm_callable_score = DoubleMLIIVM(dml_data_iivm, Lasso(), LogisticRegression(), LogisticRegression(),
                                           score=iivm_score, draw_sample_splitting=False)
    dml_iivm_callable_score.set_sample_splitting(dml_iivm.smpls)
    dml_iivm_callable_score.fit()
    assert np.allclose(dml_iivm.psi,
                       dml_iivm_callable_score.psi,
                       rtol=1e-9, atol=1e-4)
    assert np.allclose(dml_iivm.coef,
                       dml_iivm_callable_score.coef,
                       rtol=1e-9, atol=1e-4)


@pytest.mark.ci
def test_pliv_callable_vs_str_score():
    pliv_score = dml_pliv._score_elements
    dml_pliv_callable_score = DoubleMLPLIV(dml_data_pliv, Lasso(), Lasso(), Lasso(),
                                           score=pliv_score, draw_sample_splitting=False)
    dml_pliv_callable_score.set_sample_splitting(dml_pliv.smpls)
    dml_pliv_callable_score.fit()
    assert np.allclose(dml_pliv.psi,
                       dml_pliv_callable_score.psi,
                       rtol=1e-9, atol=1e-4)
    assert np.allclose(dml_pliv.coef,
                       dml_pliv_callable_score.coef,
                       rtol=1e-9, atol=1e-4)


@pytest.mark.ci
def test_pliv_callable_not_implemented():
    dml_data_pliv_2z = make_pliv_CHS2015(n_obs=100, dim_z=2)
    pliv_score = dml_pliv._score_elements

    dml_pliv_callable_score = DoubleMLPLIV._partialX(dml_data_pliv_2z, Lasso(), Lasso(), Lasso(),
                                                     score=pliv_score)
    msg = 'Callable score not implemented for DoubleMLPLIV.partialX with several instruments.'
    with pytest.raises(NotImplementedError, match=msg):
        dml_pliv_callable_score.fit()

    dml_pliv_callable_score = DoubleMLPLIV._partialZ(dml_data_pliv_2z, Lasso(),
                                                     score=pliv_score)
    msg = 'Callable score not implemented for DoubleMLPLIV.partialZ.'
    with pytest.raises(NotImplementedError, match=msg):
        dml_pliv_callable_score.fit()

    dml_pliv_callable_score = DoubleMLPLIV._partialXZ(dml_data_pliv_2z, Lasso(), Lasso(), Lasso(),
                                                      score=pliv_score)
    msg = 'Callable score not implemented for DoubleMLPLIV.partialXZ.'
    with pytest.raises(NotImplementedError, match=msg):
        dml_pliv_callable_score.fit()
