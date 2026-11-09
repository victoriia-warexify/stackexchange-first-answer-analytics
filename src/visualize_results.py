from pathlib import Path

import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
import numpy as np
import pandas as pd


# Результаты моделей на одной выборке (n = 5140)
results = pd.DataFrame({
    "model": [
        "M0: Unadjusted",
        "M1: Account age",
        "M2: Fully adjusted",
    ],
    "or": [1.4411, 1.4886, 1.4704],
    "ci_lower": [1.2050, 1.2421, 1.2239],
    "ci_upper": [1.7236, 1.7840, 1.7664],
})

# Папка с графиками
output_dir = Path("reports/figures")
output_dir.mkdir(parents=True, exist_ok=True)

# Позиции моделей на оси Y
y = np.arange(len(results))

# Асимметричные доверительные интервалы
errors = np.array([
    results["or"] - results["ci_lower"],
    results["ci_upper"] - results["or"],
])

fig, ax = plt.subplots(figsize=(9, 4.5))

ax.errorbar(
    x=results["or"],
    y=y,
    xerr=errors,
    fmt="o",
    markersize=8,
    capsize=5,
    linewidth=2,
)

# Нулевая гипотеза: OR = 1
ax.axvline(
    1,
    linestyle="--",
    linewidth=1.5,
    alpha=0.7,
)

# Подписи моделей
ax.set_yticks(y)
ax.set_yticklabels(results["model"])
ax.invert_yaxis()

# Подписываем оценки справа
for i, row in results.iterrows():
    label = (
        f"{row['or']:.2f} "
        f"[{row['ci_lower']:.2f}, "
        f"{row['ci_upper']:.2f}]"
    )

    ax.text(
        1.82,
        i,
        label,
        va="center",
        fontsize=10,
    )

ax.set_xlim(0.9, 2.3)
ax.set_xlabel("Odds Ratio (95% CI)")
ax.set_title(
    "First Answer Matters?\n"
    "Association between early response and return"
)

ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

# Сохраняем изображение
output_path = output_dir / "odds_ratios_2023.png"

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")


# Фактическая возвращаемость, полная когорта (n = 5240)
retention = pd.DataFrame({
    "group": [
        "No answer within 24h",
        "Answered within 24h",
    ],
    "users": [3121, 2119],
    "returned": [284, 266],
})

retention["rate"] = (
    retention["returned"] / retention["users"]
)

# 95% доверительные интервалы Уилсона
ci_lower, ci_upper = proportion_confint(
    count=retention["returned"],
    nobs=retention["users"],
    alpha=0.05,
    method="wilson",
)

retention["ci_lower"] = ci_lower
retention["ci_upper"] = ci_upper

# Асимметричные интервалы
errors = np.array([
    retention["rate"] - retention["ci_lower"],
    retention["ci_upper"] - retention["rate"],
]) * 100

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    retention["group"],
    retention["rate"] * 100,
    yerr=errors,
    capsize=7,
    width=0.55,
    alpha=0.85,
)

# Подписи размещаем выше доверительных интервалов
for bar, row in zip(bars, retention.itertuples()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        row.ci_upper * 100 + 0.35,
        f"{row.rate * 100:.2f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )


# Показываем разницу между группами
difference_pp = (
    retention.loc[1, "rate"]
    - retention.loc[0, "rate"]
) * 100

ax.text(
    0.5,
    0.95,
    f"Observed difference: +{difference_pp:.2f} pp",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=11,
)

ax.set_ylim(0, 18)
ax.set_ylabel("30-day return rate (%)")

ax.set_title(
    "First Answer Matters?\n"
    "Return outside the first thread (n = 5,240)"
)

ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

output_path = output_dir / "retention_by_answer_2023.png"

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")


# Анализ чувствительности к порогу ответа
# Скорректированные результаты M2 (n = 5140)

thresholds = pd.DataFrame({
    "threshold": [
        "6 hours",
        "12 hours",
        "24 hours",
    ],
    "difference": [3.79, 3.86, 3.59],
    "ci_lower": [1.88, 2.04, 1.85],
    "ci_upper": [5.70, 5.67, 5.34],
})

y = np.arange(len(thresholds))

errors = np.array([
    thresholds["difference"] - thresholds["ci_lower"],
    thresholds["ci_upper"] - thresholds["difference"],
])

fig, ax = plt.subplots(figsize=(9, 4.5))

ax.errorbar(
    thresholds["difference"],
    y,
    xerr=errors,
    fmt="o",
    markersize=8,
    linewidth=2,
    capsize=5,
)

# Линия отсутствия различия
ax.axvline(
    0,
    linestyle="--",
    linewidth=1.5,
    alpha=0.7,
)

ax.set_yticks(y)
ax.set_yticklabels(thresholds["threshold"])
ax.invert_yaxis()

# Подписи результатов
for i, row in thresholds.iterrows():
    label = (
        f"+{row['difference']:.2f} pp "
        f"[{row['ci_lower']:.2f}, "
        f"{row['ci_upper']:.2f}]"
    )

    ax.text(
        6.0,
        i,
        label,
        va="center",
        fontsize=10,
    )

ax.set_xlim(-0.4, 8.6)

ax.set_xlabel(
    "Adjusted difference in return probability (pp)"
)

ax.set_title(
    "First Answer Matters?\n"
    "Sensitivity to the early-answer threshold"
)

ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.tight_layout()

output_path = (
    output_dir / "answer_threshold_sensitivity_2023.png"
)

fig.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight",
)

plt.show()

print(f"Saved: {output_path}")