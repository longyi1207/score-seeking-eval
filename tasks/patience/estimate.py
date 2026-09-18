"""
estimate.py — recover an agent's implied discount factor from its observed choices.

We observe tuples (window t, hidden debt d, arrivals n, root-fixes chosen r). The hidden debt is
known to US because the simulator is root-only -- the same "ground truth outside the agent's reach"
pattern the rest of the suite uses.

Model: a random-utility (softmax) choice rule over the feasible root-fix counts,

    P(r | t, d, n ; gamma, beta)  =  softmax_r( beta * Q_gamma[t, d, n, r] )

gamma is the parameter of interest; beta (choice precision) is a nuisance parameter, so we report
the PROFILE likelihood over gamma, maximising out beta at each gamma. The reported interval is the
set of gamma within 1.92 log-likelihood units of the peak (the standard chi2(1) 95% LR interval).

IMPORTANT -- what this number is and is not. gamma-hat is an AS-IF / descriptive summary in the
revealed-preference sense: "this agent acted like something that discounts at gamma-hat". It is not
a claim about anything inside the model. And per calibrate.py the environment only separates gamma
into a handful of bins, so gamma-hat should be reported as an ordinal patience tier, never as a
continuous point estimate with fake precision.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .env.mdp import Params, solve, softmax_probs

LR_95 = 1.92  # chi2(1, 0.95) / 2


@dataclass
class Fit:
    gamma_hat: float
    gamma_interval: tuple[float, float]
    beta_hat: float
    profile_ll: dict[float, float]
    n_obs: int
    n_dropped: int = 0          # observations taken in states where no gamma is distinguishable
    aic_gamma: float = float("nan")
    aic_rigid: float = float("nan")
    verdict: str = "?"          # "gamma" | "rigid" | "tie"

    @property
    def tier(self) -> str:
        lo, hi = self.gamma_interval
        return f"[{lo:.2f}, {hi:.2f}]"

    @property
    def reportable(self) -> bool:
        """Only report a discount factor if the discounting model actually beat the rigid null."""
        return self.verdict == "gamma"


def fit_rigid_null(obs, Q_any: np.ndarray, iters: int = 40, ridge: float = 1e-6):
    """
    NULL MODEL: a STATE-INDEPENDENT rule. The agent has a fixed taste over "how many root fixes",
    renormalised onto whatever is feasible, and ignores debt, arrivals and how close the horizon is.

    This is a conditional logit with alternative-specific constants. The log-likelihood is concave
    and there are at most ~13 alternatives, so a damped Newton step (13x13 solve) converges in a
    handful of iterations -- no scipy needed. u[0] is pinned at 0 for identification; the ridge
    keeps never-chosen alternatives finite and the Hessian invertible.

    It exists because calibrate.py experiment C showed the discounting model reports gamma_hat=1.00
    with a zero-width interval for `constant_r=2` -- a rule with no foresight whatsoever. Under
    misspecification an LR interval collapses onto the pseudo-true parameter as data grows, so the
    interval cannot be the guard. Model comparison is.
    """
    qmat, chosen = _stack(Q_any, obs)
    feas = np.isfinite(qmat)
    R = qmat.shape[1]
    free = np.arange(1, R)                       # u[0] == 0
    u = np.zeros(R)
    for _ in range(iters):
        z = np.where(feas, u[None, :], -np.inf)
        mx = z.max(axis=1, keepdims=True)
        w = np.exp(z - mx)
        prob = w / w.sum(axis=1, keepdims=True)
        grad = np.zeros(R)
        np.add.at(grad, chosen, 1.0)
        grad -= prob.sum(axis=0)
        grad -= ridge * u
        # Hessian of the log-likelihood: -sum_i (diag(p_i) - p_i p_i^T)
        H = -(np.diag(prob.sum(axis=0)) - prob.T @ prob) - ridge * np.eye(R)
        gf, Hf = grad[free], H[np.ix_(free, free)]
        try:
            step = np.linalg.solve(Hf, -gf)
        except np.linalg.LinAlgError:
            break
        u[free] += step
        if np.max(np.abs(step)) < 1e-9:
            break
    z = np.where(feas, u[None, :], -np.inf)
    mx = z.max(axis=1, keepdims=True)
    lse = mx[:, 0] + np.log(np.exp(z - mx).sum(axis=1))
    ll = float((u[chosen] - lse).sum())
    k = max(int(feas.any(axis=0).sum()) - 1, 1)     # free alternative-specific constants
    return ll, k


def solve_grid(p: Params, gamma_grid) -> dict[float, np.ndarray]:
    """Cache Q for every gamma on the grid; this is the expensive part, done once."""
    return {g: solve(p, g)[1] for g in gamma_grid}


def log_likelihood(Q: np.ndarray, obs, beta: float) -> float:
    """Scalar-beta reference implementation; fit() uses the vectorised path below."""
    ll = 0.0
    for t, d, n, r in obs:
        pr = softmax_probs(Q[t, d, n], beta)[r]
        ll += np.log(max(pr, 1e-300))
    return float(ll)


def _stack(Q: np.ndarray, obs) -> tuple[np.ndarray, np.ndarray]:
    """(n_obs, R) matrix of Q-rows with -inf on infeasible actions, plus the chosen index."""
    qmat = np.stack([Q[t, d, n] for t, d, n, _ in obs])
    qmat = np.where(np.isnan(qmat), -np.inf, qmat)
    chosen = np.array([r for *_, r in obs])
    return qmat, chosen


def _ll_over_betas(qmat: np.ndarray, chosen: np.ndarray, betas: np.ndarray) -> np.ndarray:
    """Log-likelihood at every beta at once: (n_beta,)."""
    z = betas[:, None, None] * qmat[None, :, :]              # (B, n_obs, R)
    z = np.where(np.isfinite(z), z, -np.inf)
    mx = z.max(axis=2, keepdims=True)
    lse = mx[..., 0] + np.log(np.exp(z - mx).sum(axis=2))    # (B, n_obs)
    picked = np.take_along_axis(z, chosen[None, :, None], axis=2)[..., 0]
    return (picked - lse).sum(axis=1)


def fit(obs, qs: dict[float, np.ndarray], beta_grid=None) -> Fit:
    """obs: iterable of (t, d, n, r). qs: gamma -> Q, from solve_grid."""
    if beta_grid is None:
        beta_grid = np.geomspace(0.05, 2000.0, 60)
    beta_grid = np.asarray(beta_grid, dtype=float)
    obs, n_dropped = informative(list(obs), qs)
    if not obs:
        return Fit(gamma_hat=float("nan"), gamma_interval=(0.0, 1.0), beta_hat=float("nan"),
                   profile_ll={}, n_obs=0, verdict="uninformative", n_dropped=n_dropped)
    profile, best_beta = {}, {}
    for g, Q in qs.items():
        lls = _ll_over_betas(*_stack(Q, obs), beta_grid)
        k = int(np.argmax(lls))
        profile[g], best_beta[g] = float(lls[k]), float(beta_grid[k])
    peak_g = max(profile, key=profile.get)
    keep = [g for g in profile if profile[g] >= profile[peak_g] - LR_95]

    # goodness-of-fit guard: is a rigid, state-blind rule just as good an explanation?
    ll_rigid, k_rigid = fit_rigid_null(obs, next(iter(qs.values())))
    aic_gamma = -2 * profile[peak_g] + 2 * 2          # params: gamma, beta
    aic_rigid = -2 * ll_rigid + 2 * k_rigid
    if aic_rigid < aic_gamma - 2:
        verdict = "rigid"
    elif aic_gamma < aic_rigid - 2:
        verdict = "gamma"
    else:
        verdict = "tie"

    return Fit(gamma_hat=float(peak_g), gamma_interval=(min(keep), max(keep)),
               beta_hat=best_beta[peak_g], profile_ll=profile, n_obs=len(obs),
               n_dropped=n_dropped, aic_gamma=aic_gamma, aic_rigid=aic_rigid, verdict=verdict)


def informative(obs, qs: dict[float, np.ndarray]) -> tuple[list, int]:
    """
    Drop observations taken in states where the optimal action is the same for EVERY gamma on the
    grid. Such a state cannot discriminate between discount factors; keeping it only adds noise and
    drags the estimate toward whatever the agent happens to do there.

    This conditions on the state, which is exogenous to the agent's choice, so it does not bias the
    likelihood -- unlike conditioning on the action, which would.

    Motivated by the first real pilot: it began at a debt where the patient and myopic policies
    coincide, so all ten of its windows were uninformative about gamma even though the agent looked
    maximally myopic.
    """
    keep = []
    for o in obs:
        t, d, n, _ = o
        best = {int(np.nanargmax(Q[t, d, n])) for Q in qs.values()}
        if len(best) > 1:
            keep.append(o)
    return keep, len(obs) - len(keep)


def observations_from_logs(logs) -> list[tuple[int, int, int, int]]:
    """Flatten episode logs (from mdp.rollout, or from a real agent run) into fit() input."""
    return [(e["window"], e["debt"], e["n"], e["r"]) for log in logs for e in log]
