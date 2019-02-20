# -*- coding: UTF-8 -*-

from sympy import pi, cos, sin
from sympy.utilities.lambdify import implemented_function

from sympde.core import Constant
from sympde.calculus import grad, dot, inner, cross, rot, curl, div
from sympde.calculus import laplace, hessian
from sympde.topology import (dx, dy, dz)
from sympde.topology import FunctionSpace, VectorFunctionSpace
from sympde.topology import ScalarField, VectorField
from sympde.topology import ProductSpace
from sympde.topology import ScalarTestFunction
from sympde.topology import VectorTestFunction
from sympde.topology import Boundary, NormalVector, TangentVector
from sympde.topology import Domain, Line, Square, Cube
from sympde.topology import Trace, trace_0, trace_1
from sympde.topology import Union
from sympde.expr import BilinearForm, LinearForm
from sympde.expr import Norm
from sympde.expr import find, EssentialBC

from gelato.expr import GltExpr

from spl.fem.basic   import FemField
from spl.api.discretization import discretize

import numpy as np
from scipy.linalg import eig as eig_solver
from mpi4py import MPI
import pytest


#==============================================================================
def run_poisson_2d_dir(ncells, degree, comm=None):

    # ... abstract model
    domain = Square()

    V = FunctionSpace('V', domain)

    F = ScalarField(V, name='F')

    v = ScalarTestFunction(V, name='v')
    u = ScalarTestFunction(V, name='u')

    a = BilinearForm((v,u), dot(grad(v), grad(u)))

    glt_a = GltExpr(a)
    # ...

    # ... create the computational domain from a topological domain
    domain_h = discretize(domain, ncells=ncells, comm=comm)
    # ...

    # ... discrete spaces
    Vh = discretize(V, domain_h, degree=degree)
    # ...

    # ... dsicretize the equation using Dirichlet bc
    ah = discretize(a, domain_h, [Vh, Vh])
    # ...

    # ... dsicretize the glt symbol
    glt_ah = discretize(glt_a, domain_h, [Vh, Vh])
    # ...

    # ...
    eigh = glt_ah.eig()
    eigh = eigh.ravel()
    eigh.sort()
    # ...

    # ... use eigenvalue solver
    M = ah.assemble().tosparse().todense()
    w, v = eig_solver(M)
    eig = w.real
    eig.sort()
    # ...

    # ...
    error = np.linalg.norm(eig-eigh) / Vh.nbasis
    # ...

    return error

#==============================================================================
def run_field_2d_dir(ncells, degree, comm=None):

    # ... abstract model
    domain = Square()

    V = FunctionSpace('V', domain)

    F = ScalarField(V, name='F')

    v = ScalarTestFunction(V, name='v')
    u = ScalarTestFunction(V, name='u')

    a  = BilinearForm((v,u), dot(grad(v), grad(u)) + F*u*v)
    ae = BilinearForm((v,u), dot(grad(v), grad(u)) + u*v)

    glt_a  = GltExpr(a)
    glt_ae = GltExpr(ae)
    # ...

    # ... create the computational domain from a topological domain
    domain_h = discretize(domain, ncells=ncells, comm=comm)
    # ...

    # ... discrete spaces
    Vh = discretize(V, domain_h, degree=degree)
    # ...

    # ... dsicretize the equation using Dirichlet bc
    ah  = discretize(a, domain_h, [Vh, Vh])
    aeh = discretize(ae, domain_h, [Vh, Vh])
    # ...

    # ...
    x = Vh.vector_space.zeros()
    x[:] = 1.

    phi = FemField( Vh, x )
    # ...

    # ... discretize the glt symbol
    glt_ah  = discretize(glt_a, domain_h, [Vh, Vh])
    glt_aeh = discretize(glt_ae, domain_h, [Vh, Vh])
    # ...

    # ...
    eigh_a = glt_ah.eig(F=phi)
    eigh_a = eigh_a.ravel()
    eigh_a.sort()

    eigh_ae = glt_aeh.eig()
    eigh_ae = eigh_ae.ravel()
    eigh_ae.sort()
    # ...

    # ...
    error = np.linalg.norm(eigh_a-eigh_ae) / Vh.nbasis
    # ...

    return error

###############################################################################
#            SERIAL TESTS
###############################################################################

#==============================================================================
def test_api_glt_poisson_2d_dir_1():

    error = run_poisson_2d_dir(ncells=[2**3,2**3], degree=[2,2])
    assert(np.allclose([error], [0.029738578422276972]))

#==============================================================================
def test_api_glt_field_2d_dir_1():

    error = run_field_2d_dir(ncells=[2**3,2**3], degree=[2,2])
    assert(np.allclose([error], [9.739541824956656e-16]))


#==============================================================================
# CLEAN UP SYMPY NAMESPACE
#==============================================================================

def teardown_module():
    from sympy import cache
    cache.clear_cache()

def teardown_function():
    from sympy import cache
    cache.clear_cache()
