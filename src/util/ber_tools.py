import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from typing import Tuple, Optional

def estimate_gaussian_params(samples: np.ndarray) -> Tuple[float, float]:
    """
    Estimate mean and standard deviation from samples using unbiased estimator for std dev.

    Parameters:
        samples (np.ndarray): Array of sample values.
    Returns:
        mean (float): Estimated mean of the samples.
        std_dev (float): Estimated standard deviation of the samples.
    """
    mean = float(np.mean(samples))
    std_dev = float(np.std(samples, ddof=1))
    return mean, std_dev

def midpoint_threshold(mean_0: float, mean_1: float) -> float:
    """
    Compute midpoint threshold between two means.
    
    Parameters:
        mean_0 (float): Mean of Gaussian for bit 0.
        mean_1 (float): Mean of Gaussian for bit 1.
    Returns:
        T (float): Midpoint threshold between the two means.
    """
    return 0.5 * (mean_0 + mean_1)

def analytic_error_probs(T: float, mean_0: float, std_dev_0: float, mean_1: float, std_dev_1: float,
                         p_0: float = 0.5, p_1: float = 0.5) -> Tuple[float, float, float]:
    """
    Calculate (P0_err, P1_err, BER) analytically for two Gaussians and threshold T.

    Parameters:
        T (float): Decision threshold.
        mean_0 (float): Mean of Gaussian for bit 0.
        std_dev_0 (float): Standard deviation of Gaussian for bit 0.
        mean_1 (float): Mean of Gaussian for bit 1.
        std_dev_1 (float): Standard deviation of Gaussian for bit 1.
        p_0 (float): Prior probability of bit 0. Default is 0.5.
        p_1 (float): Prior probability of bit 1. Default is 0.5.
    Returns:
        P0_err (float): Probability of error when bit 0 is sent
        P1_err (float): Probability of error when bit 1 is sent
        BER (float): Overall bit error rate.
    """
    z_0 = (T - mean_0) / std_dev_0
    z_1 = (T - mean_1) / std_dev_1
    P_0_err = 1.0 - norm.cdf(z_0)        # P(X0 > T)
    P_1_err = norm.cdf(z_1)              # P(X1 <= T)
    BER = p_0 * P_0_err + p_1 * P_1_err
    return P_0_err, P_1_err, BER

def optimal_threshold(mean_0: float, std_dev_0: float, mean_1: float, std_dev_1: float,
                      p_0: float = 0.5, p_1: float = 0.5) -> float:
    """
    Solve likelihood-ratio threshold for two Gaussians.
    Returns threshold T. If equal-variance, returns closed-form midpoint weighted by priors.
    If two real roots exist, chooses the root between mu0 and mu1 if possible.

    Parameters:
        mean_0 (float): Mean of Gaussian for bit 0.
        std_dev_0 (float): Standard deviation of Gaussian for bit 0.
        mean_1 (float): Mean of Gaussian for bit 1.
        std_dev_1 (float): Standard deviation of Gaussian for bit 1.
        p_0 (float): Prior probability of bit 0. Default is 0.
        p_1 (float): Prior probability of bit 1. Default is 0.
    Returns:
        T (float): Optimal decision threshold.
    """
    # If variances equal, linear solution:
    if abs(std_dev_0 - std_dev_1) < 1e-12:
        # With equal σ, the log-likelihood ratio reduces to linear threshold:
        # T = (mu0 + mu1)/2 + (sigma^2/(mu1-mu0)) * ln(p0/p1)  (but when p0=p1 -> midpoint)
        std_dev = std_dev_0
        if p_0 == p_1:
            return midpoint_threshold(mean_0, mean_1)
        else:
            return 0.5*(mean_0 + mean_1) + (std_dev**2) * np.log(p_0 / p_1) / (mean_1 - mean_0)

    # General unequal-variance: solve quadratic a T^2 + b T + c = 0
    C0 = np.log((p_0 * std_dev_1) / (p_1 * std_dev_0))
    a = 1.0 / (2.0 * std_dev_1**2) - 1.0 / (2.0 * std_dev_0**2)
    b = - mean_1 / (std_dev_1**2) + mean_0 / (std_dev_0**2)
    c = (mean_1**2) / (2.0 * std_dev_1**2) - (mean_0**2) / (2.0 * std_dev_0**2) + C0

    if abs(a) < 1e-18:
        # degenerate -> linear
        if abs(b) < 1e-18:
            return midpoint_threshold(mean_0, mean_1)
        return -c / b

    roots = np.roots([a, b, c])
    # pick the root between means if possible
    candidates = [r.real for r in roots if abs(r.imag) < 1e-8]
    # prefer root between mean_0 and mean_1
    for r in candidates:
        if min(mean_0, mean_1) <= r <= max(mean_0, mean_1):
            return float(r)
    # else return the candidate closest to midpoint
    mid = midpoint_threshold(mean_0, mean_1)
    if candidates:
        return float(min(candidates, key=lambda x: abs(x - mid)))
    return mid

def monte_carlo_ber(mean_0: float, std_dev_0: float, mean_1: float, std_dev_1: float,
                    T: float, p_0: float = 0.5, n_samples: int = 200000) -> Tuple[float, float, float]:
    """
    Monte Carlo estimate of (P0_err, P1_err, BER) by sampling.

    Parameters:
        mean_0 (float): Mean of Gaussian for bit 0.
        std_dev_0 (float): Standard deviation of Gaussian for bit 0.
        mean_1 (float): Mean of Gaussian for bit 1.
        std_dev_1 (float): Standard deviation of Gaussian for bit 1.
        T (float): Decision threshold.
        p_0 (float): Prior probability of bit 0. Default is 0.
        n_samples (int): Number of samples to draw. Default is 200,000.
    Returns:
        P0_err (float): Probability of error when bit 0 is sent 
        P1_err (float): Probability of error when bit 1 is sent
        BER (float): Overall bit error rate.
    """
    n0 = int(n_samples * p_0)
    n1 = n_samples - n0
    s0 = np.random.normal(mean_0, std_dev_0, size=n0)
    s1 = np.random.normal(mean_1, std_dev_1, size=n1)
    P0_err = np.mean(s0 > T)
    P1_err = np.mean(s1 <= T)
    BER = p_0 * P0_err + (1 - p_0) * P1_err
    return P0_err, P1_err, BER

def plot_histograms_with_threshold(s0: np.ndarray, s1: np.ndarray, T: float,
                                   bins: int = 80, show_fit: bool = True):
    """
    Plot histograms of two sample sets s0 and s1, with decision threshold T.

    Parameters:
        s0 (np.ndarray): Samples for bit 0.
        s1 (np.ndarray): Samples for bit 1.
        T (float): Decision threshold to plot.
        bins (int): Number of histogram bins. Default is 80.
        show_fit (bool): Whether to overlay fitted Gaussian curves. Default is True.
    """
    mu0, sigma0 = estimate_gaussian_params(s0)
    mu1, sigma1 = estimate_gaussian_params(s1)
    plt.figure(figsize=(8,4))
    plt.hist(s0, bins=bins, alpha=0.5, density=True, label=f"bit0 (n={len(s0)})")
    plt.hist(s1, bins=bins, alpha=0.5, density=True, label=f"bit1 (n={len(s1)})")
    xs = np.linspace(min(np.min(s0), np.min(s1)), max(np.max(s0), np.max(s1)), 1000)
    if show_fit:
        plt.plot(xs, norm.pdf(xs, mu0, sigma0), 'b--', label=f"N({mu0:.4g},{sigma0:.4g})")
        plt.plot(xs, norm.pdf(xs, mu1, sigma1), 'r--', label=f"N({mu1:.4g},{sigma1:.4g})")
    plt.axvline(T, color='k', linestyle='-', label=f"threshold T={T:.6g}")
    plt.legend()
    plt.xlabel("Voltage")
    plt.ylabel("Density")
    plt.title("Voltage histograms (bit 0 vs bit 1) with decision threshold")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # TODO Change these to your measured values according to logs
    mean_0, std_dev_0 = 0.03008, 0.00005
    mean_1, std_dev_1 = 0.03034, 0.00005
    p_0 = 0.5

    T_mid = midpoint_threshold(mean_0, mean_1)
    P0, P1, BER_mid = analytic_error_probs(T_mid, mean_0, std_dev_0, mean_1, std_dev_1, p_0, 1-p_0)

    T_opt = optimal_threshold(mean_0, std_dev_0, mean_1, std_dev_1, p_0, 1-p_0)
    P0o, P1o, BER_opt = analytic_error_probs(T_opt, mean_0, std_dev_0, mean_1, std_dev_1, p_0, 1-p_0)
    P0_monte, P1_monte, BER_monte = monte_carlo_ber(mean_0, std_dev_0, mean_1, std_dev_1, T_mid, p_0, n_samples=200_000)

    # Midpoint and Optimal Thresholds are most likely going to be the same because variance of white noise between both distributions, and 
    # prior probabilities of p_0 and p_1 are going to be the same.
    print(f"{'='*40}")
    print(f"{'Thresholds':^40}")
    print(f"{'-'*40}")
    print(f"Midpoint Threshold (T_mid) : {T_mid:.6f}")
    print(f"Optimal Threshold (T_opt)  : {T_opt:.6f}\n")

    print(f"{'Bit Error Rates':^40}")
    print(f"{'-'*40}")
    print(f"Analytic BER at T_mid      : {BER_mid:.6e}")
    print(f"Analytic BER at T_opt      : {BER_opt:.6e}")
    print(f"Monte Carlo BER at T_mid   : {BER_monte:.6e}")
    print(f"{'='*40}\n")

    # Plot sample histograms using synthetic data
    s0 = np.random.normal(mean_0, std_dev_0, size=10000)
    s1 = np.random.normal(mean_1, std_dev_1, size=10000)
    plot_histograms_with_threshold(s0, s1, T_mid)

