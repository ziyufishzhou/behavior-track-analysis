"""统计检验引擎 — 自动正态检验 → 参数/非参数检验 → 效应量"""
from dataclasses import dataclass, field
from scipy import stats
import numpy as np


@dataclass
class TestResult:
    test_name: str
    statistic: float
    p_value: float
    star_label: str
    effect_size: float = None
    effect_name: str = ""
    test_type: str = ""  # 'parametric' / 'nonparametric'


def check_normality(data, alpha=0.05):
    data = np.asarray(data, float)
    data = data[~np.isnan(data)]
    if len(data) < 3:
        return True
    if np.nanstd(data) < 1e-12:
        return True
    try:
        _, p = stats.shapiro(data)
        return p > alpha
    except Exception:
        return True


def cohens_d_paired(g1, g2):
    diff = np.array(g2) - np.array(g1)
    if len(diff) < 2 or np.nanstd(diff, ddof=1) < 1e-12:
        return 0
    return np.mean(diff) / (np.std(diff, ddof=1) + 1e-10)


def cohens_d_unpaired(g1, g2):
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return 0
    s_pooled = np.sqrt(((n1 - 1) * np.var(g1, ddof=1) + (n2 - 1) * np.var(g2, ddof=1)) / (n1 + n2 - 2) + 1e-10)
    return (np.mean(g2) - np.mean(g1)) / s_pooled


def rank_biserial_r(g1, g2):
    """Wilcoxon / Mann-Whitney 效应量"""
    try:
        from scipy.stats import rankdata
        combined = np.concatenate([g1, g2])
        ranks = rankdata(combined)
        n1, n2 = len(g1), len(g2)
        u1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
        return 1 - 2 * u1 / (n1 * n2)
    except Exception:
        return None


def paired_test(g1, g2, alpha=0.05, force_test=""):
    g1, g2 = np.asarray(g1, float), np.asarray(g2, float)
    valid = ~(np.isnan(g1) | np.isnan(g2))
    g1, g2 = g1[valid], g2[valid]
    if len(g1) < 2:
        return TestResult("N/A", 0, 1.0, "ns")
    if np.allclose(g1, g2, equal_nan=True):
        return TestResult("No difference", 0, 1.0, "ns", 0, "Cohen's d_z", "none")

    test = force_test.lower() if force_test else ""
    use_parametric = check_normality(g2 - g1, alpha) if not test else (test in ("t-test", "paired t-test", "ttest"))

    if use_parametric:
        stat, p = stats.ttest_rel(g1, g2, nan_policy='omit')
        if np.isnan(p):
            stat, p = 0, 1.0
        d = cohens_d_paired(g1, g2)
        return TestResult("Paired t-test", stat, p, _star(p, alpha), d, "Cohen's d_z", "parametric")
    else:
        try:
            stat, p = stats.wilcoxon(g1, g2)
        except Exception:
            stat, p = 0, 1.0
        r = rank_biserial_r(g1, g2)
        return TestResult("Wilcoxon signed-rank", stat, p, _star(p, alpha), r, "rank-biserial r", "nonparametric")


def unpaired_test(g1, g2, alpha=0.05, force_test=""):
    g1, g2 = np.asarray(g1, float), np.asarray(g2, float)
    g1, g2 = g1[~np.isnan(g1)], g2[~np.isnan(g2)]
    if len(g1) < 2 or len(g2) < 2:
        return TestResult("N/A", 0, 1.0, "ns")
    if np.nanstd(g1) < 1e-12 and np.nanstd(g2) < 1e-12 and np.isclose(np.nanmean(g1), np.nanmean(g2)):
        return TestResult("No difference", 0, 1.0, "ns", 0, "Cohen's d", "none")

    test = force_test.lower() if force_test else ""
    both_normal = check_normality(g1, alpha) and check_normality(g2, alpha)
    use_parametric = both_normal if not test else (test in ("t-test", "unpaired t-test", "ttest"))

    if use_parametric:
        stat, p = stats.ttest_ind(g1, g2, nan_policy='omit')
        if np.isnan(p):
            stat, p = 0, 1.0
        d = cohens_d_unpaired(g1, g2)
        return TestResult("Unpaired t-test", stat, p, _star(p, alpha), d, "Cohen's d", "parametric")
    else:
        try:
            stat, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
        except Exception:
            stat, p = 0, 1.0
        r = rank_biserial_r(g1, g2)
        return TestResult("Mann-Whitney U", stat, p, _star(p, alpha), r, "rank-biserial r", "nonparametric")


def multi_group_test(groups, paired=False, alpha=0.05):
    groups = [np.asarray(g, float)[~np.isnan(np.asarray(g, float))] for g in groups]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return TestResult("N/A", 0, 1.0, "ns")

    if paired:
        try:
            stat, p = stats.friedmanchisquare(*groups)
            return TestResult("Friedman test", stat, p, _star(p, alpha), None, "", "nonparametric")
        except Exception:
            pass
    all_normal = all(check_normality(g, alpha) for g in groups)
    if all_normal:
        stat, p = stats.f_oneway(*groups)
        return TestResult("One-way ANOVA", stat, p, _star(p, alpha), None, "η²", "parametric")
    else:
        stat, p = stats.kruskal(*groups)
        return TestResult("Kruskal-Wallis", stat, p, _star(p, alpha), None, "ε²", "nonparametric")


def auto_test(g1, g2, paired=True, alpha=0.05, force_test=""):
    if paired:
        return paired_test(g1, g2, alpha, force_test)
    return unpaired_test(g1, g2, alpha, force_test)


def _star(p, alpha=0.05):
    if p is None:
        return 'ns'
    if p < 0.001:
        return '***'
    if p < 0.01:
        return '**'
    if p < alpha:
        return '*'
    return 'ns'
