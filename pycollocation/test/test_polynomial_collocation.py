import unittest

import numpy as np
import sympy as sym

from .. import models
from .. import orthogonal_polynomials
from .. import solutions


class SolowModel(unittest.TestCase):

    @staticmethod
    def steady_state(g, n, s, alpha, delta, sigma):
        """Steady state value for capital (per unit effective labor)."""
        return (s / (g + n + delta))**(1 / (1 - alpha))

    def setUp(self):
        """Set up a Solow model to solve."""
        # define some variables
        t, k, c = sym.symbols('t, k, c')

        # define some parameters
        alpha, sigma = sym.symbols('alpha, sigma')
        rho, theta = sym.symbols('rho, theta')
        g, n, s, delta = sym.symbols('g, n, s, delta')

        # intensive output has the Cobb-Douglas form
        y = k**alpha

        # define the equation of motion for capital
        k_dot = s * y - (g + n + delta) * k
        rhs = {k: k_dot}

        # set some randomly generated parameters
        self.params = {'g': np.random.uniform(),
                       's': np.random.uniform(),
                       'n': np.random.uniform(),
                       'alpha': np.random.uniform(),
                       'sigma': 1.0,
                       'delta': np.random.uniform()}

        # specify some boundary conditions
        kstar = self.steady_state(**self.params)
        if np.random.uniform() < 0.5:
            k0 = 0.5 * kstar
        else:
            k0 = 2.0 * kstar
        bcs = {'lower': [k - k0], 'upper': None}

        # set the model instance
        self.model = models.BoundaryValueProblem(dependent_vars=[k],
                                                 independent_var=t,
                                                 rhs=rhs,
                                                 boundary_conditions=bcs,
                                                 params=self.params)

        # set the solver instance
        self.solver = orthogonal_polynomials.OrthogonalPolynomialSolver(self.model)

        # set the domain
        self.domain = [0, 100]

        # set an initial guess
        ts = np.linspace(self.domain[0], self.domain[1], 1000)
        ks = kstar - (kstar - k0) * np.exp(-ts)
        initial_guess = np.polynomial.Chebyshev.fit(ts, ks, 50, self.domain)
        self.initial_coefs = {k: initial_guess.coef}

    def test_chebyshev_collocation(self):
        """Test collocation solver using Chebyshev polynomials for basis."""
        # compute the solution
        self.solver.solve(kind="Chebyshev",
                          coefs_dict=self.initial_coefs,
                          domain=self.domain)
        solution = solutions.Solution(self.solver)

        # check that solver terminated successfully
        self.assertTrue(solution.solver.result.success, msg="Solver failed!")

        # compute the residuals
        solution.interpolation_knots = np.linspace(self.domain[0],
                                                   self.domain[1],
                                                   1000)
        residuals = solution.residuals.values

        # check that residuals are close to zero on average
        mesg = "Chebyshev residuals:\n{}\n\nDictionary of model params: {}"
        self.assertTrue(np.mean(residuals) < 1e-6,
                        msg=mesg.format(residuals, self.params))

    def test_legendre_collocation(self):
        """Test collocation solver using Legendre polynomials for basis."""
        self.solver.solve(kind="Legendre",
                          coefs_dict=self.initial_coefs,
                          domain=self.domain)
        solution = solutions.Solution(self.solver)

        # check that solver terminated successfully
        self.assertTrue(solution.solver.result.success, msg="Solver failed!")

        # compute the residuals
        solution.interpolation_knots = np.linspace(self.domain[0],
                                                   self.domain[1],
                                                   1000)
        residuals = solution.residuals.values

        # check that residuals are all close to zero
        mesg = "Legendre residuals:\n{}\n\nDictionary of model params: {}"
        self.assertTrue(np.mean(residuals) < 1e-6,
                        msg=mesg.format(residuals, self.params))
